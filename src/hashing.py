"""
hashing.py - File Hashing and Similarity Utilities for Smart File Organizer Suite

Provides fast SHA-256 hashing, partial head/tail fast hashing, dHash perceptual image similarity,
Hamming distance calculations, and fuzzy string similarity.
"""
import difflib
import hashlib
import os
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

import ctypes

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from config import (
    FILE_ATTRIBUTE_HIDDEN,
    FILE_ATTRIBUTE_OFFLINE,
    FILE_ATTRIBUTE_READONLY,
    FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS,
    FILE_ATTRIBUTE_RECALL_ON_OPEN,
    FILE_ATTRIBUTE_REPARSE_POINT,
    FILE_ATTRIBUTE_SPARSE_FILE,
    FILE_CHUNK_SIZE,
    INVALID_FILE_ATTRIBUTES,
)
from logger import get_logger
from utils import fix_win_long_path

logger = get_logger("Hashing")


def is_cloud_placeholder(filepath: str) -> Dict[str, Any]:
    """
    Checks if a file is a cloud-only placeholder stub (e.g. OneDrive, iCloud, Dropbox)
    that is NOT fully cached locally on disk.

    Returns dict:
      {
        'is_placeholder': bool,
        'download_required': bool,
        'attributes': int,
        'nominal_size': int,
        'allocated_size': int
      }
    """
    safe_fp = fix_win_long_path(filepath)
    result = {
        'is_placeholder': False,
        'download_required': False,
        'attributes': 0,
        'nominal_size': 0,
        'allocated_size': 0
    }

    if not os.path.exists(safe_fp):
        return result

    try:
        stat = os.stat(safe_fp)
        result['nominal_size'] = stat.st_size
    except Exception as e:
        logger.debug("Stat error on %s: %s", safe_fp, e)

    if sys.platform == 'win32':
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(safe_fp))
            if attrs != INVALID_FILE_ATTRIBUTES:
                result['attributes'] = attrs
                # Check for cloud recall or offline attributes
                is_recall_open = bool(attrs & FILE_ATTRIBUTE_RECALL_ON_OPEN)
                is_recall_data = bool(attrs & FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS)
                is_offline = bool(attrs & FILE_ATTRIBUTE_OFFLINE)

                if is_recall_open or is_recall_data or is_offline:
                    result['is_placeholder'] = True
                    result['download_required'] = True

                # Secondary check: Allocated clusters on disk vs nominal file size
                if result['nominal_size'] > 4096:
                    try:
                        high_dw = ctypes.c_ulong()
                        low_dw = ctypes.windll.kernel32.GetCompressedFileSizeW(str(safe_fp), ctypes.byref(high_dw))
                        if low_dw != 0xFFFFFFFF or ctypes.GetLastError() == 0:
                            allocated = (high_dw.value << 32) + low_dw
                            result['allocated_size'] = allocated
                            if allocated == 0 or (allocated < 4096 and result['nominal_size'] > 65536):
                                result['is_placeholder'] = True
                                result['download_required'] = True
                    except Exception as e:
                        logger.debug("GetCompressedFileSizeW error on %s: %s", safe_fp, e)
        except Exception as e:
            logger.debug("GetFileAttributesW error on %s: %s", safe_fp, e)

    return result


def count_cloud_placeholders(filepath_list: List[str]) -> Dict[str, int]:
    """
    Summarizes cloud-only placeholders in a list of files.
    Returns dict with count of cloud files and total unhydrated bytes.
    """
    cloud_count = 0
    total_bytes = 0
    for fp in filepath_list:
        p_info = is_cloud_placeholder(fp)
        if p_info['is_placeholder'] or p_info['download_required']:
            cloud_count += 1
            total_bytes += p_info['nominal_size']
    return {
        'cloud_count': cloud_count,
        'total_bytes': total_bytes
    }


def verify_safe_overwrite(
    src_path: str,
    dst_path: str,
    size_threshold_ratio: float = 0.5
) -> Tuple[bool, str]:
    """
    CRITICAL OVERWRITE SAFETY GUARD:
    Prevents silent data loss where a cloud placeholder stub (0-byte/small proxy)
    or corrupted payload replaces an existing valid destination file.

    Returns (is_safe: bool, reason: str).
    """
    safe_dst = fix_win_long_path(dst_path)
    if not os.path.exists(safe_dst):
        return True, "Destination file does not exist (New Write)"

    try:
        dst_size = os.path.getsize(safe_dst)
    except Exception:
        dst_size = 0

    if dst_size == 0:
        return True, "Existing destination is 0 bytes"

    # Check source file size / placeholder state
    src_placeholder = is_cloud_placeholder(src_path) if src_path and os.path.exists(fix_win_long_path(src_path)) else None

    if src_placeholder and src_placeholder['is_placeholder'] and src_placeholder['download_required']:
        return False, f"Aborted: Source file '{os.path.basename(src_path)}' is an unhydrated cloud placeholder stub. Overwriting destination would corrupt data."

    # Size ratio sanity check
    if src_path and os.path.exists(fix_win_long_path(src_path)):
        try:
            src_size = os.path.getsize(fix_win_long_path(src_path))
            if dst_size > 102400 and src_size < dst_size * size_threshold_ratio:
                return False, f"Aborted: Source file size ({src_size:,} bytes) is dramatically smaller than existing destination ({dst_size:,} bytes)."
        except Exception as e:
            logger.debug("Size check error during verify_safe_overwrite: %s", e)

    return True, "Overwrite verified safe"


def get_file_hash(
    filepath: str,
    block_size: int = FILE_CHUNK_SIZE,
    cancel_event: Optional[threading.Event] = None
) -> Optional[str]:
    """
    Calculates SHA-256 hash of a file for exact duplicate detection.

    Args:
        filepath: Path to the file.
        block_size: Read chunk size in bytes (default 64 KB).
        cancel_event: Optional threading.Event — if set(), hashing aborts and
                      returns None immediately without raising an exception.

    Returns:
        Hexadecimal SHA-256 digest string, or None if cancelled or an error occurred.
    """
    hasher = hashlib.sha256()
    safe_fp = fix_win_long_path(filepath)
    try:
        with open(safe_fp, 'rb') as f:
            buf = f.read(block_size)
            while len(buf) > 0:
                if cancel_event is not None and cancel_event.is_set():
                    logger.debug("SHA-256 hashing cancelled for %s", safe_fp)
                    return None
                hasher.update(buf)
                buf = f.read(block_size)
        return hasher.hexdigest()
    except FileNotFoundError:
        logger.debug("File not found during hashing: %s", safe_fp)
        return None
    except PermissionError as pe:
        logger.warning("Permission denied reading file for hash: %s (%s)", safe_fp, pe)
        return None
    except OSError as oe:
        logger.warning("OS error reading file for hash %s: %s", safe_fp, oe)
        return None
    except Exception as e:
        logger.error("Unexpected error calculating SHA-256 on %s: %s", safe_fp, e)
        return None


def get_file_fast_hash(
    filepath: str,
    chunk_size: int = FILE_CHUNK_SIZE,
    cancel_event: Optional[threading.Event] = None
) -> Optional[str]:
    """
    Computes a quick partial hash (file size + head 64KB + tail 64KB) for rapid candidate pre-screening.

    Args:
        filepath: Path to the file.
        chunk_size: Head/tail read size in bytes (default 64 KB).
        cancel_event: Optional threading.Event — if set(), hashing aborts and returns None.

    Returns:
        Hexadecimal MD5 digest string of file sample, 'empty_0' if 0 bytes, or None if error.
    """
    safe_fp = fix_win_long_path(filepath)
    try:
        size = os.path.getsize(safe_fp)
        if size == 0:
            return "empty_0"
        if cancel_event is not None and cancel_event.is_set():
            logger.debug("Fast hashing cancelled for %s", safe_fp)
            return None
        hasher = hashlib.md5()
        hasher.update(str(size).encode('utf-8'))
        with open(safe_fp, 'rb') as f:
            head = f.read(chunk_size)
            hasher.update(head)
            if size > chunk_size * 2:
                if cancel_event is not None and cancel_event.is_set():
                    return None
                f.seek(size - chunk_size)
                tail = f.read(chunk_size)
                hasher.update(tail)
        return hasher.hexdigest()
    except FileNotFoundError:
        logger.debug("File not found during fast hash: %s", safe_fp)
        return None
    except PermissionError as pe:
        logger.warning("Permission denied reading file for fast hash: %s (%s)", safe_fp, pe)
        return None
    except OSError as oe:
        logger.warning("OS error reading file for fast hash %s: %s", safe_fp, oe)
        return None
    except Exception as e:
        logger.error("Unexpected error calculating fast hash on %s: %s", safe_fp, e)
        return None


def get_image_perceptual_hash(filepath: str, hash_size: int = 8) -> Optional[Dict[str, Any]]:
    """
    Calculates difference hash (dHash) for perceptual visual similarity comparisons.

    Args:
        filepath: Path to image file.
        hash_size: Grid dimension (default 8 for 64-bit dHash).

    Returns:
        Dictionary with hash integer, hash string, width, height, and megapixels, or None.
    """
    if not HAS_PIL:
        logger.warning("Pillow (PIL) is not installed; perceptual image hashing is unavailable.")
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
    except Exception as e:
        logger.debug("Image perceptual hash failed for '%s': %s", safe_fp, e)
        return None


def calculate_hamming_similarity(hash1_int: Optional[int], hash2_int: Optional[int], bits: int = 64) -> float:
    """Returns float between 0.0 and 1.0 representing visual similarity percentage."""
    if hash1_int is None or hash2_int is None:
        return 0.0
    xor_val = hash1_int ^ hash2_int
    hamming_dist = bin(xor_val).count('1')
    similarity = 1.0 - (hamming_dist / float(bits))
    return max(0.0, min(1.0, similarity))


def calculate_fuzzy_name_similarity(name1: str, name2: str, ignore_extension: bool = True) -> float:
    """Calculates fuzzy similarity ratio between two filenames."""
    n1 = name1.lower()
    n2 = name2.lower()
    if ignore_extension:
        n1 = os.path.splitext(n1)[0]
        n2 = os.path.splitext(n2)[0]
    return difflib.SequenceMatcher(None, n1, n2).ratio()
