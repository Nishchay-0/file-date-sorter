"""
hashing.py - File Hashing and Similarity Utilities for Smart File Organizer Suite

Provides fast SHA-256 hashing, partial head/tail fast hashing, dHash perceptual image similarity,
Hamming distance calculations, and fuzzy string similarity.
"""
import os
import sys
import hashlib
import difflib

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def fix_win_long_path(path):
    """
    Safely cleans path quotes/whitespace and adds \\\\?\\ prefix on Windows for long paths.
    """
    if isinstance(path, str):
        path = path.strip().strip('\'"')
        if not path:
            return ""
        if sys.platform == 'win32':
            try:
                abs_path = os.path.abspath(path)
                if len(abs_path) >= 240 and not abs_path.startswith("\\\\?\\"):
                    return "\\\\?\\" + abs_path
                return abs_path
            except Exception:
                return path
    return path


def get_file_hash(filepath, block_size=65536):
    """Calculates SHA-256 hash of a file for exact duplicate detection."""
    hasher = hashlib.sha256()
    safe_fp = fix_win_long_path(filepath)
    try:
        with open(safe_fp, 'rb') as f:
            buf = f.read(block_size)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(block_size)
        return hasher.hexdigest()
    except Exception:
        return None


def get_file_fast_hash(filepath, chunk_size=65536):
    """
    Computes a quick partial hash (file size + head 64KB + tail 64KB) for rapid candidate pre-screening.
    """
    safe_fp = fix_win_long_path(filepath)
    try:
        size = os.path.getsize(safe_fp)
        if size == 0:
            return "empty_0"
        hasher = hashlib.md5()
        hasher.update(str(size).encode('utf-8'))
        with open(safe_fp, 'rb') as f:
            head = f.read(chunk_size)
            hasher.update(head)
            if size > chunk_size * 2:
                f.seek(size - chunk_size)
                tail = f.read(chunk_size)
                hasher.update(tail)
        return hasher.hexdigest()
    except Exception:
        return None


def get_image_perceptual_hash(filepath, hash_size=8):
    """
    Calculates difference hash (dHash) for perceptual visual similarity comparisons.
    Returns dict with hash integer, hash string, width, height, and megapixels, or None.
    """
    if not HAS_PIL:
        return None
    safe_fp = fix_win_long_path(filepath)
    try:
        with Image.open(safe_fp) as img:
            width, height = img.size
            mp = round((width * height) / 1000000.0, 2)
            resample_filter = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else getattr(Image, 'ANTIALIAS', Image.BICUBIC)
            img_gray = img.convert('L').resize((hash_size + 1, hash_size), resample_filter)
            pixels = list(img_gray.getdata())
            diff = []
            for row in range(hash_size):
                for col in range(hash_size):
                    left = pixels[row * (hash_size + 1) + col]
                    right = pixels[row * (hash_size + 1) + col + 1]
                    diff.append(1 if left > right else 0)
            
            decimal_val = 0
            for bit in diff:
                decimal_val = (decimal_val << 1) | bit
            
            return {
                'hash_int': decimal_val,
                'hash_str': f"{decimal_val:016x}",
                'width': width,
                'height': height,
                'megapixels': mp,
                'res_str': f"{width}x{height} ({mp} MP)"
            }
    except Exception:
        return None


def calculate_hamming_similarity(hash1_int, hash2_int, bits=64):
    """Returns float between 0.0 and 1.0 representing visual similarity percentage."""
    if hash1_int is None or hash2_int is None:
        return 0.0
    xor_val = hash1_int ^ hash2_int
    hamming_dist = bin(xor_val).count('1')
    similarity = 1.0 - (hamming_dist / float(bits))
    return max(0.0, min(1.0, similarity))


def calculate_fuzzy_name_similarity(name1, name2, ignore_extension=True):
    """Calculates fuzzy similarity ratio between two filenames."""
    n1 = name1.lower()
    n2 = name2.lower()
    if ignore_extension:
        n1 = os.path.splitext(n1)[0]
        n2 = os.path.splitext(n2)[0]
    return difflib.SequenceMatcher(None, n1, n2).ratio()
