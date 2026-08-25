"""
face_sort.py - Face-Based People Photo & Video Sorter Engine

Architecture & Design Decisions:
1. ONNX Runtime & OpenCV Pipeline:
   - Uses OpenCV (cv2) and ONNX models (YuNet detector / SFace recognizer) for fast, cross-platform
     face detection and embedding generation.
   - Chosen over dlib/face_recognition to avoid heavy C++ compilation requirements and PyInstaller binary bloat.
2. Video Frame Sampling:
   - Samples video files (.mp4, .mkv, .mov, .avi, etc.) at configurable time intervals (default: 2.5s).
3. DBSCAN Clustering:
   - Clusters high-dimensional face embeddings without requiring an a priori person count.
4. Caching & Performance:
   - Caches embeddings keyed by (file_hash, mtime) in `.people_cache.json` using hashing.py.
5. Non-Destructive Index & Opt-In Shortcuts:
   - Default mode builds an index (.people_index.json) without moving original files.
   - Opt-in action creates Windows .url / shell shortcuts in `People/<PersonName>/`.
"""

import os
import sys
import json
import time
import shutil
import numpy as np
from datetime import datetime

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from sklearn.cluster import DBSCAN
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from concurrent.futures import ThreadPoolExecutor
import base64
from concurrent.futures import ThreadPoolExecutor
from hashing import get_file_hash, fix_win_long_path, is_cloud_placeholder

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.heic', '.tiff', '.raw'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.mpg', '.mpeg'}
CACHE_SCHEMA_VERSION = 2


def crop_to_b64(crop_bgr, target_size=(90, 90)):
    """Encodes a BGR image crop into a compact JPEG Base64 string for instant GUI thumbnail rendering."""
    if not HAS_CV2 or crop_bgr is None or crop_bgr.size == 0:
        return ""
    try:
        resized = cv2.resize(crop_bgr, target_size, interpolation=cv2.INTER_AREA)
        success, encoded = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if success:
            return base64.b64encode(encoded.tobytes()).decode('ascii')
    except Exception:
        pass
    return ""


class FaceSorterEngine:
    def __init__(self, cache_file=".people_cache.json", index_file=".people_index.json"):
        self.cache_file = cache_file
        self.index_file = index_file
        self.cache = self._load_json(self.cache_file)
        self.index = self._load_json(self.index_file)
        self._init_models()

    def _load_json(self, filepath):
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_json(self, data, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _cache_key_for_file(self, filepath):
        """Build a versioned, content-aware cache key for face embeddings.

        The previous implementation keyed cache entries by path + size + mtime only,
        which could return stale results if a file was rewritten without changing
        those metadata values. Adding a SHA-256 fingerprint and schema version makes
        the cache self-invalidating when contents change while preserving fast hits.
        """
        safe_fp = fix_win_long_path(filepath)
        try:
            stat = os.stat(safe_fp)
            size = stat.st_size
            mtime = getattr(stat, 'st_mtime_ns', stat.st_mtime)
            file_hash = get_file_hash(safe_fp) or "unknown"
            return f"{safe_fp}|{size}|{mtime}|{file_hash}|v{CACHE_SCHEMA_VERSION}"
        except Exception:
            return f"{safe_fp}|unknown|v{CACHE_SCHEMA_VERSION}"

    def _init_models(self):
        """Initializes OpenCV YuNet/SFace models and ONNX Runtime session if available."""
        self.detector = None
        self.recognizer = None
        self.ort_session = None

        if HAS_CV2 and hasattr(cv2, 'FaceDetectorYN_create') and hasattr(cv2, 'FaceRecognizerSF_create'):
            try:
                model_dir = os.path.join(os.path.dirname(__file__), "models")
                yn_path = os.path.join(model_dir, "face_detection_yunet_2023mar.onnx")
                sf_path = os.path.join(model_dir, "face_recognition_sface_2021dec.onnx")
                if os.path.exists(yn_path) and os.path.exists(sf_path):
                    self.detector = cv2.FaceDetectorYN_create(yn_path, "", (320, 320))
                    self.recognizer = cv2.FaceRecognizerSF_create(sf_path, "")
            except Exception:
                pass

        try:
            import onnxruntime as ort
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = max(1, os.cpu_count() or 4)
            sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
            providers = ['DmlExecutionProvider', 'CPUExecutionProvider'] if sys.platform == 'win32' else ['CPUExecutionProvider']
            self.ort_sess_options = sess_options
            self.ort_providers = providers
        except Exception:
            pass

    def extract_faces_from_image_array(self, img_bgr, max_det_dim=640):
        """
        Extracts face bounding boxes, 128-d embedding vectors, and JPEG Base64 thumbnails.
        Quality Filter: Ignores boxes < 36px or low-confidence detector artifacts.
        """
        if img_bgr is None or img_bgr.size == 0:
            return []

        orig_h, orig_w = img_bgr.shape[:2]
        results = []

        max_dim = max(orig_h, orig_w)
        if max_dim > max_det_dim:
            scale = max_det_dim / float(max_dim)
            det_w = int(orig_w * scale)
            det_h = int(orig_h * scale)
            det_img = cv2.resize(img_bgr, (det_w, det_h), interpolation=cv2.INTER_AREA) if HAS_CV2 else img_bgr
        else:
            scale = 1.0
            det_w, det_h = orig_w, orig_h
            det_img = img_bgr

        # Strategy A: OpenCV YuNet / SFace ONNX Model
        if self.detector and self.recognizer and HAS_CV2:
            try:
                self.detector.setInputSize((det_w, det_h))
                _, faces = self.detector.detect(det_img)
                if faces is not None:
                    for face in faces:
                        box = list(map(float, face[0:4]))
                        # Quality Guard: YuNet detection confidence score (face[14])
                        score = float(face[14]) if len(face) > 14 else 1.0
                        if score < 0.65:
                            continue

                        x = int(box[0] / scale)
                        y = int(box[1] / scale)
                        bw = int(box[2] / scale)
                        bh = int(box[3] / scale)

                        x, y = max(0, x), max(0, y)
                        bw, bh = min(orig_w - x, bw), min(orig_h - y, bh)

                        # Minimum Size Guard: Reject tiny noise boxes < 36px
                        if bw < 36 or bh < 36:
                            continue

                        aligned_face = self.recognizer.alignCrop(img_bgr, face)
                        feat = self.recognizer.feature(aligned_face)
                        embedding = feat.flatten().tolist()
                        crop = img_bgr[y:y+bh, x:x+bw]
                        thumb_b64 = crop_to_b64(crop)

                        results.append({
                            'rect': (x, y, bw, bh),
                            'embedding': embedding,
                            'crop_bgr': crop,
                            'thumbnail_b64': thumb_b64
                        })
                    return results
            except Exception:
                pass

        # Strategy B: OpenCV Haar Cascade / HOG Fallback with downscaling & quality filter
        if HAS_CV2:
            try:
                gray = cv2.cvtColor(det_img, cv2.COLOR_BGR2GRAY)
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                face_cascade = cv2.CascadeClassifier(cascade_path)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(32, 32))
                for (x_s, y_s, bw_s, bh_s) in faces:
                    x = int(x_s / scale)
                    y = int(y_s / scale)
                    bw = int(bw_s / scale)
                    bh = int(bh_s / scale)
                    x, y = max(0, x), max(0, y)
                    bw, bh = min(orig_w - x, bw), min(orig_h - y, bh)
                    if bw < 36 or bh < 36:
                        continue
                    crop = img_bgr[y:y+bh, x:x+bw]
                    crop_resized = cv2.resize(crop, (16, 16))
                    hsv = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2HSV)
                    hist = cv2.calcHist([hsv], [0, 1, 2], None, [4, 4, 8], [0, 180, 0, 256, 0, 256])
                    feat = cv2.normalize(hist, hist).flatten()
                    if len(feat) < 128:
                        feat = np.pad(feat, (0, 128 - len(feat)))
                    else:
                        feat = feat[:128]
                    thumb_b64 = crop_to_b64(crop)
                    results.append({
                        'rect': (x, y, bw, bh),
                        'embedding': feat.tolist(),
                        'crop_bgr': crop,
                        'thumbnail_b64': thumb_b64
                    })
            except Exception:
                pass

        return results

    def process_image_file(self, filepath):
        """Processes a single image file and returns face detection list."""
        if not HAS_CV2:
            return []
        safe_fp = fix_win_long_path(filepath)
        p_check = is_cloud_placeholder(safe_fp)
        if p_check['is_placeholder'] and p_check['download_required']:
            return []
        try:
            img = cv2.imread(safe_fp)
            return self.extract_faces_from_image_array(img)
        except Exception:
            return []

    def process_video_file(self, filepath, sample_interval_sec=2.5):
        """Samples video frames and extracts faces with frame difference filter."""
        if not HAS_CV2:
            return []
        safe_fp = fix_win_long_path(filepath)
        p_check = is_cloud_placeholder(safe_fp)
        if p_check['is_placeholder'] and p_check['download_required']:
            return []

        faces = []
        try:
            cap = cv2.VideoCapture(safe_fp)
            if not cap.isOpened():
                return []
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            frame_stride = int(fps * sample_interval_sec)
            if frame_stride < 1:
                frame_stride = 1

            frame_idx = 0
            prev_small_gray = None
            last_detected = []

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % frame_stride == 0:
                    small_gray = cv2.cvtColor(cv2.resize(frame, (160, 120)), cv2.COLOR_BGR2GRAY)
                    if prev_small_gray is not None:
                        diff = np.mean(cv2.absdiff(small_gray, prev_small_gray))
                        if diff < 3.5 and len(last_detected) > 0:
                            for d in last_detected:
                                d_copy = dict(d)
                                d_copy['timestamp_sec'] = round(frame_idx / fps, 2)
                                faces.append(d_copy)
                            prev_small_gray = small_gray
                            frame_idx += 1
                            continue

                    prev_small_gray = small_gray
                    detected = self.extract_faces_from_image_array(frame)
                    last_detected = detected
                    for d in detected:
                        d['timestamp_sec'] = round(frame_idx / fps, 2)
                        faces.append(d)
                frame_idx += 1
            cap.release()
        except Exception:
            pass
        return faces

    def _complete_linkage_cluster(self, X_norm, distance_threshold=0.34):
        """
        Complete-linkage agglomerative clustering ensuring every face pair in a cluster
        has cosine distance <= distance_threshold. Completely eliminates the mega-cluster chaining bug!
        """
        n = len(X_norm)
        if n == 0:
            return []
        sim_matrix = np.dot(X_norm, X_norm.T)
        dist_matrix = np.clip(1.0 - sim_matrix, 0.0, 2.0)

        clusters = [[i] for i in range(n)]

        while len(clusters) > 1:
            best_dist = 999.0
            best_pair = (-1, -1)

            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    # Complete linkage distance: maximum distance between any element in cluster i and cluster j
                    max_d = max(dist_matrix[x, y] for x in clusters[i] for y in clusters[j])
                    if max_d < best_dist:
                        best_dist = max_d
                        best_pair = (i, j)

            if best_dist <= distance_threshold and best_pair != (-1, -1):
                c1, c2 = best_pair
                merged = clusters[c1] + clusters[c2]
                clusters.pop(c2)
                clusters[c1] = merged
            else:
                break

        labels = [-1] * n
        for c_idx, cluster in enumerate(clusters):
            for member in cluster:
                labels[member] = c_idx
        return labels

    def _simple_dbscan(self, X_norm, eps=0.34, min_samples=1, distance_threshold=None):
        thresh = distance_threshold if distance_threshold is not None else eps
        return self._complete_linkage_cluster(X_norm, distance_threshold=thresh)

    def _flag_outlier_clusters(self, clusters):
        """Identifies and flags unusually large clusters that absorb disproportionate faces."""
        sizes = [len(c.get('faces', [])) for c in clusters.values()]
        if not sizes or len(sizes) <= 2:
            return clusters

        total_faces = sum(sizes)
        med_size = float(np.median(sizes))

        for pid, c in clusters.items():
            f_count = len(c.get('faces', []))
            is_outlier = (f_count > 15 and f_count > med_size * 3.0 and (f_count / float(total_faces)) > 0.15)
            c['is_outlier'] = is_outlier
            if is_outlier:
                c['outlier_warning'] = "⚠️ Unusually large — review for mixed people"
            else:
                c['outlier_warning'] = ""
        return clusters

    def _calculate_cluster_date_ranges(self, clusters):
        """Calculates human-readable date ranges (e.g. 'Jan 2023 – Aug 2026') for each cluster."""
        from sorter_core import get_file_date
        for pid, c in clusters.items():
            faces = c.get('faces', [])
            dts = []
            for f in faces:
                fp = f.get('filepath')
                if fp and os.path.exists(fix_win_long_path(fp)):
                    dt = get_file_date(fp, date_source='smart')
                    if dt:
                        dts.append(dt)
            if dts:
                dts.sort()
                min_dt = dts[0]
                max_dt = dts[-1]
                if min_dt.year == max_dt.year and min_dt.month == max_dt.month:
                    date_str = min_dt.strftime("%b %Y")
                else:
                    date_str = f"{min_dt.strftime('%b %Y')} – {max_dt.strftime('%b %Y')}"
                c['date_range_str'] = date_str
                c['min_timestamp'] = min_dt.timestamp()
                c['max_timestamp'] = max_dt.timestamp()
            else:
                c['date_range_str'] = "Date Unknown"
                c['min_timestamp'] = 0
                c['max_timestamp'] = 0
        return clusters

    def scan_directory(self, target_dir, progress_callback=None, sample_interval_sec=2.5, distance_threshold=0.34):
        """
        Scans directory for photos & videos, extracts face embeddings using cache,
        clusters faces using Complete-Linkage Cosine distance thresholding,
        flags outliers, calculates date ranges, and returns structured People index.
        """
        target_dir = fix_win_long_path(target_dir)
        if not os.path.exists(target_dir):
            return {'clusters': {}, 'unclustered': [], 'total_files': 0, 'faces_found': 0}

        all_files = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS:
                    all_files.append(os.path.join(root, file))

        total_files = len(all_files)
        all_embeddings = []
        face_metadata = []

        for idx, fp in enumerate(all_files):
            if progress_callback:
                progress_callback(idx + 1, total_files, os.path.basename(fp))

            cache_key = self._cache_key_for_file(fp)

            if cache_key in self.cache:
                cached_faces = self.cache[cache_key]
            else:
                p_check = is_cloud_placeholder(fp)
                if p_check['is_placeholder'] and p_check['download_required']:
                    cached_faces = []
                else:
                    ext = os.path.splitext(fp)[1].lower()
                    if ext in VIDEO_EXTENSIONS:
                        raw_faces = self.process_video_file(fp, sample_interval_sec=sample_interval_sec)
                    else:
                        raw_faces = self.process_image_file(fp)

                    cached_faces = []
                    for rf in raw_faces:
                        cached_faces.append({
                            'rect': rf['rect'],
                            'embedding': rf['embedding'],
                            'thumbnail_b64': rf.get('thumbnail_b64', ''),
                            'timestamp_sec': rf.get('timestamp_sec', 0)
                        })
                    self.cache[cache_key] = cached_faces

            for f_idx, face in enumerate(cached_faces):
                all_embeddings.append(face['embedding'])
                face_metadata.append({
                    'filepath': fp,
                    'rect': face['rect'],
                    'face_idx': f_idx,
                    'thumbnail_b64': face.get('thumbnail_b64', ''),
                    'timestamp_sec': face.get('timestamp_sec', 0),
                    'is_video': os.path.splitext(fp)[1].lower() in VIDEO_EXTENSIONS
                })

        self._save_json(self.cache, self.cache_file)

        # Cluster embeddings using Complete Linkage Cosine Clustering
        clusters = {}

        if len(all_embeddings) > 0:
            X = np.array(all_embeddings)
            norms = np.linalg.norm(X, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            X_norm = X / norms

            if HAS_SKLEARN:
                try:
                    from sklearn.cluster import AgglomerativeClustering
                    cluster_model = AgglomerativeClustering(
                        n_clusters=None,
                        distance_threshold=distance_threshold,
                        metric='cosine',
                        linkage='complete'
                    )
                    labels = cluster_model.fit_predict(X_norm)
                except Exception:
                    labels = self._complete_linkage_cluster(X_norm, distance_threshold=distance_threshold)
            else:
                labels = self._complete_linkage_cluster(X_norm, distance_threshold=distance_threshold)

            for idx, label in enumerate(labels):
                meta = face_metadata[idx]
                person_id = f"Person_{label + 1}" if label >= 0 else "Unassigned"
                if person_id not in clusters:
                    clusters[person_id] = {
                        'name': f"Person {label + 1}" if label >= 0 else "Unassigned / Other",
                        'faces': []
                    }
                clusters[person_id]['faces'].append(meta)

        self._flag_outlier_clusters(clusters)
        self._calculate_cluster_date_ranges(clusters)

        index_result = {
            'scanned_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_files': total_files,
            'faces_found': len(all_embeddings),
            'clusters': clusters
        }
        self.index = index_result
        self._save_json(self.index, self.index_file)
        return index_result

    def merge_clusters(self, source_pids, target_pid):
        """Merges specified source_pids into target_pid in self.index."""
        if not self.index or 'clusters' not in self.index:
            return False

        clusters = self.index['clusters']
        if target_pid not in clusters:
            return False

        target_faces = clusters[target_pid]['faces']
        existing_keys = set((f['filepath'], f.get('face_idx', 0)) for f in target_faces)

        for spid in source_pids:
            if spid == target_pid or spid not in clusters:
                continue
            source_faces = clusters[spid].pop('faces', [])
            for sf in source_faces:
                key = (sf['filepath'], sf.get('face_idx', 0))
                if key not in existing_keys:
                    target_faces.append(sf)
                    existing_keys.add(key)
            del clusters[spid]

        self._flag_outlier_clusters(clusters)
        self._calculate_cluster_date_ranges(clusters)
        self._save_json(self.index, self.index_file)
        return True

    def remove_face_from_cluster(self, pid, filepath, face_idx=0):
        """Removes a face entry from cluster `pid` and moves it to 'Unassigned'."""
        if not self.index or 'clusters' not in self.index:
            return False

        clusters = self.index['clusters']
        if pid not in clusters:
            return False

        faces = clusters[pid].get('faces', [])
        removed_face = None
        remaining_faces = []

        for f in faces:
            if f.get('filepath') == filepath and f.get('face_idx', 0) == face_idx:
                removed_face = f
            else:
                remaining_faces.append(f)

        if removed_face:
            clusters[pid]['faces'] = remaining_faces
            if len(remaining_faces) == 0:
                del clusters[pid]

            unassigned_id = "Unassigned"
            if unassigned_id not in clusters:
                clusters[unassigned_id] = {
                    'name': "Unassigned / Other",
                    'faces': []
                }
            clusters[unassigned_id]['faces'].append(removed_face)

            self._flag_outlier_clusters(clusters)
            self._calculate_cluster_date_ranges(clusters)
            self._save_json(self.index, self.index_file)
            return True

        return False
        """Pure numpy cosine distance DBSCAN clustering implementation."""
        n = len(X_norm)
        labels = [-1] * n
        cluster_id = 0
        visited = [False] * n

        # Pairwise cosine distance matrix
        sim_matrix = np.dot(X_norm, X_norm.T)
        dist_matrix = 1.0 - sim_matrix

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            neighbors = np.where(dist_matrix[i] <= eps)[0].tolist()
            if len(neighbors) < min_samples:
                labels[i] = -1
            else:
                labels[i] = cluster_id
                k = 0
                while k < len(neighbors):
                    neighbor_idx = neighbors[k]
                    if not visited[neighbor_idx]:
                        visited[neighbor_idx] = True
                        n_neighbors = np.where(dist_matrix[neighbor_idx] <= eps)[0].tolist()
                        if len(n_neighbors) >= min_samples:
                            neighbors.extend(n_neighbors)
                    if labels[neighbor_idx] == -1:
                        labels[neighbor_idx] = cluster_id
                    k += 1
                cluster_id += 1

        return labels

    def create_people_shortcuts(self, destination_dir):
        """
        OPT-IN ACTION: Creates Windows .url / shell shortcuts in `People/<PersonName>/`
        pointing to original photos/videos without moving or copying original files.
        """
        destination_dir = fix_win_long_path(destination_dir)
        people_base = os.path.join(destination_dir, "People")
        os.makedirs(people_base, exist_ok=True)

        created_count = 0
        clusters = self.index.get('clusters', {})

        for person_id, cluster in clusters.items():
            name = cluster.get('name', person_id)
            clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
            person_dir = os.path.join(people_base, clean_name)
            os.makedirs(fix_win_long_path(person_dir), exist_ok=True)

            seen_files = set()
            for face in cluster.get('faces', []):
                src_path = face['filepath']
                if src_path in seen_files or not os.path.exists(src_path):
                    continue
                seen_files.add(src_path)

                base_filename = os.path.basename(src_path)
                shortcut_name = f"{os.path.splitext(base_filename)[0]}.url"
                shortcut_path = os.path.join(person_dir, shortcut_name)

                # Create Windows URL shortcut pointing to local file
                try:
                    with open(fix_win_long_path(shortcut_path), 'w', encoding='utf-8') as f:
                        f.write(f"[InternetShortcut]\nURL=file:///{src_path.replace('\\', '/')}\n")
                    created_count += 1
                except Exception:
                    pass

        return {'created_shortcuts': created_count, 'people_dir': people_base}
