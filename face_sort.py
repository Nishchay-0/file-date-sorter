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

from hashing import get_file_hash, fix_win_long_path

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.heic', '.tiff', '.raw'}
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.mpg', '.mpeg'}


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

    def _init_models(self):
        """Initializes OpenCV YuNet/SFace models if available."""
        self.detector = None
        self.recognizer = None
        if HAS_CV2 and hasattr(cv2, 'FaceDetectorYN_create') and hasattr(cv2, 'FaceRecognizerSF_create'):
            try:
                # Attempts to load YuNet / SFace ONNX models if present
                model_dir = os.path.join(os.path.dirname(__file__), "models")
                yn_path = os.path.join(model_dir, "face_detection_yunet_2023mar.onnx")
                sf_path = os.path.join(model_dir, "face_recognition_sface_2021dec.onnx")
                if os.path.exists(yn_path) and os.path.exists(sf_path):
                    self.detector = cv2.FaceDetectorYN_create(yn_path, "", (320, 320))
                    self.recognizer = cv2.FaceRecognizerSF_create(sf_path, "")
            except Exception:
                pass

    def extract_faces_from_image_array(self, img_bgr):
        """
        Extracts face bounding boxes and 128-d embedding vectors from a BGR image array.
        Returns list of dicts: [{'rect': (x, y, w, h), 'embedding': list, 'crop_bgr': array}]
        """
        if img_bgr is None or img_bgr.size == 0:
            return []

        h, w = img_bgr.shape[:2]
        results = []

        # Strategy A: OpenCV YuNet / SFace ONNX Model
        if self.detector and self.recognizer:
            try:
                self.detector.setInputSize((w, h))
                _, faces = self.detector.detect(img_bgr)
                if faces is not None:
                    for face in faces:
                        box = list(map(int, face[0:4]))
                        x, y, bw, bh = box
                        # Ensure bounds
                        x, y = max(0, x), max(0, y)
                        bw, bh = min(w - x, bw), min(h - y, bh)
                        if bw <= 10 or bh <= 10:
                            continue
                        aligned_face = self.recognizer.alignCrop(img_bgr, face)
                        feat = self.recognizer.feature(aligned_face)
                        embedding = feat.flatten().tolist()
                        crop = img_bgr[y:y+bh, x:x+bw]
                        results.append({
                            'rect': (x, y, bw, bh),
                            'embedding': embedding,
                            'crop_bgr': crop
                        })
                    return results
            except Exception:
                pass

        # Strategy B: OpenCV Haar Cascade / HOG Fallback
        if HAS_CV2:
            try:
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                face_cascade = cv2.CascadeClassifier(cascade_path)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
                for (x, y, bw, bh) in faces:
                    crop = img_bgr[y:y+bh, x:x+bw]
                    # Compute a normalized 128-d color/texture feature vector as embedding
                    crop_resized = cv2.resize(crop, (16, 16))
                    hsv = cv2.cvtColor(crop_resized, cv2.COLOR_BGR2HSV)
                    hist = cv2.calcHist([hsv], [0, 1, 2], None, [4, 4, 8], [0, 180, 0, 256, 0, 256])
                    feat = cv2.normalize(hist, hist).flatten()
                    if len(feat) < 128:
                        feat = np.pad(feat, (0, 128 - len(feat)))
                    else:
                        feat = feat[:128]
                    results.append({
                        'rect': (int(x), int(y), int(bw), int(bh)),
                        'embedding': feat.tolist(),
                        'crop_bgr': crop
                    })
            except Exception:
                pass

        return results

    def process_image_file(self, filepath):
        """Processes a single image file and returns face detection list."""
        if not HAS_CV2:
            return []
        safe_fp = fix_win_long_path(filepath)
        try:
            img = cv2.imread(safe_fp)
            return self.extract_faces_from_image_array(img)
        except Exception:
            return []

    def process_video_file(self, filepath, sample_interval_sec=2.5):
        """Samples video frames every sample_interval_sec seconds and extracts faces."""
        if not HAS_CV2:
            return []
        safe_fp = fix_win_long_path(filepath)
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
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % frame_stride == 0:
                    detected = self.extract_faces_from_image_array(frame)
                    for d in detected:
                        d['timestamp_sec'] = round(frame_idx / fps, 2)
                        faces.append(d)
                frame_idx += 1
            cap.release()
        except Exception:
            pass
        return faces

    def scan_directory(self, target_dir, progress_callback=None, sample_interval_sec=2.5):
        """
        Scans directory for photos & videos, extracts face embeddings using cache,
        clusters faces using DBSCAN, and returns structured People index.
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

            try:
                mtime = os.path.getmtime(fp)
            except Exception:
                mtime = 0

            f_hash = get_file_hash(fp) or fp
            cache_key = f"{f_hash}_{mtime}"

            if cache_key in self.cache:
                cached_faces = self.cache[cache_key]
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
                        'timestamp_sec': rf.get('timestamp_sec', 0)
                    })
                self.cache[cache_key] = cached_faces

            for f_idx, face in enumerate(cached_faces):
                all_embeddings.append(face['embedding'])
                face_metadata.append({
                    'filepath': fp,
                    'rect': face['rect'],
                    'face_idx': f_idx,
                    'timestamp_sec': face.get('timestamp_sec', 0),
                    'is_video': os.path.splitext(fp)[1].lower() in VIDEO_EXTENSIONS
                })

        self._save_json(self.cache, self.cache_file)

        # Cluster embeddings using DBSCAN
        clusters = {}
        unclustered = []

        if len(all_embeddings) > 0:
            X = np.array(all_embeddings)
            # Normalize vectors
            norms = np.linalg.norm(X, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            X_norm = X / norms

            labels = []
            if HAS_SKLEARN:
                db = DBSCAN(eps=0.45, min_samples=1, metric='cosine')
                labels = db.fit_predict(X_norm)
            else:
                # Custom cosine-distance DBSCAN fallback
                labels = self._simple_dbscan(X_norm, eps=0.45, min_samples=1)

            for idx, label in enumerate(labels):
                meta = face_metadata[idx]
                person_id = f"Person_{label + 1}" if label >= 0 else "Unassigned"
                if person_id not in clusters:
                    clusters[person_id] = {
                        'name': f"Person {label + 1}" if label >= 0 else "Unassigned / Other",
                        'faces': []
                    }
                clusters[person_id]['faces'].append(meta)

        index_result = {
            'scanned_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_files': total_files,
            'faces_found': len(all_embeddings),
            'clusters': clusters
        }
        self.index = index_result
        self._save_json(self.index, self.index_file)
        return index_result

    def _simple_dbscan(self, X_norm, eps=0.45, min_samples=1):
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
