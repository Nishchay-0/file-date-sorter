import os
import sys
import subprocess
import shutil
import json
import csv
import hashlib
import zipfile
import ctypes
import re
import math
import time
import threading
import difflib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from hashing import (
    get_file_hash,
    get_file_fast_hash,
    get_image_perceptual_hash,
    calculate_hamming_similarity,
    calculate_fuzzy_name_similarity,
    is_cloud_placeholder,
    count_cloud_placeholders,
    verify_safe_overwrite
)

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

# Pre-defined file category mappings
FILE_CATEGORIES = {
    "Images": ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.heic', '.raw', '.tiff', '.ico', '.cr2', '.nef', '.dng'],
    "Documents": ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.csv', '.cvv', '.tsv', '.md', '.rtf', '.odt', '.ods', '.epub', '.mobi'],
    "Videos": ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.m2ts', '.vob', '.mpg', '.mpeg', '.m2v', '.divx', '.ogv'],
    "Audio": ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.mid', '.midi', '.3ga', '.amr', '.opus', '.ape', '.wv', '.mka', '.ra'],
    "Archives": ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso', '.img', '.vmdk'],
    "Design & Graphics": ['.psd', '.ai', '.eps', '.sketch', '.fig', '.xd', '.xcf', '.indd'],
    "3D Models & CAD": ['.stl', '.obj', '.fbx', '.blend', '.dwg', '.dxf', '.step', '.3ds', '.gcode', '.dae'],
    "Database & Data": ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.sql', '.csv', '.cvv', '.tsv', '.json', '.xml'],
    "Code & Scripts": ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.java', '.cpp', '.c', '.h', '.sh', '.bat', '.ps1', '.php', '.rb', '.go', '.rs'],
    "Fonts": ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
    "System & Config": ['.ini', '.cfg', '.env', '.yaml', '.yml', '.sys', '.log', '.bak'],
    "Executables & Installers": ['.exe', '.msi', '.apk', '.dmg', '.deb', '.appimage']
}



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


def get_extensions_for_categories(categories_list):
    """Returns a list of file extensions corresponding to the given category names."""
    exts = set()
    for cat in categories_list:
        if cat in FILE_CATEGORIES:
            exts.update(FILE_CATEGORIES[cat])
    return list(exts)


def get_system_vault_dir(subfolder=""):
    """
    Returns a protected System AppData Vault directory:
    Windows: C:\\Users\\<user>\\AppData\\Local\\SmartFileOrganizer\\Vault\\...
    Mac/Linux: ~/.config/smart_file_organizer/vault/...
    This directory is isolated from user target folders so files can NEVER be accidentally deleted!
    """
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA') or os.path.expanduser("~\\AppData\\Local")
    else:
        base = os.path.expanduser("~/.config")

    vault_path = os.path.join(base, "SmartFileOrganizer", "Vault", subfolder)
    os.makedirs(fix_win_long_path(vault_path), exist_ok=True)
    return vault_path


def hide_path_windows(path):
    """Marks a path as HIDDEN on Windows OS to prevent accidental user deletion."""
    if sys.platform == 'win32' and os.path.exists(path):
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(path), 2)  # 2 = FILE_ATTRIBUTE_HIDDEN
        except Exception:
            pass


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
            # Difference hash (dHash)
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


def calculate_text_similarity(filepath1, filepath2, max_bytes=100000):
    """Calculates normalized text content similarity between two text files."""
    try:
        with open(fix_win_long_path(filepath1), 'r', encoding='utf-8', errors='ignore') as f1:
            t1 = f1.read(max_bytes).strip()
        with open(fix_win_long_path(filepath2), 'r', encoding='utf-8', errors='ignore') as f2:
            t2 = f2.read(max_bytes).strip()
        if not t1 and not t2:
            return 1.0
        if not t1 or not t2:
            return 0.0
        return difflib.SequenceMatcher(None, t1, t2).ratio()
    except Exception:
        return 0.0


def extract_date_from_filename(filename, date_format_preference='DMY'):
    """
    Parses datetime embedded in filename.
    Supports formats:
      - YYYYMMDD, DDMMYYYY, MMDDYYYY (8 digits, e.g. 20022022, 20220220, 08152021)
      - YYYY-MM-DD, YYYY_MM_DD, YYYY.MM.DD
      - DD-MM-YYYY, DD_MM_YYYY, DD.MM.YYYY
      - WhatsApp: IMG-YYYYMMDD-WA..., VID-YYYYMMDD-WA...
      - Screenshots / Camera: Screenshot_YYYYMMDD..., IMG_YYYYMMDD...
      - Year-Month: YYYY-MM, YYYY_MM
      - 4-digit Year: 1970..2099

    Tie-breaking rule for ambiguous 8-digit non-YYYY dates (e.g. 01022023):
      - If date_format_preference='DMY' (default), attempts DDMMYYYY first (01022023 -> Feb 1, 2023).
      - If date_format_preference='MDY', attempts MMDDYYYY first (01022023 -> Jan 2, 2023).

    Returns datetime object or None if no valid date found.
    """
    import re
    from datetime import datetime

    base = os.path.splitext(os.path.basename(filename))[0]

    # Pattern 1: Explicit YYYY-MM-DD or YYYY_MM_DD or YYYY.MM.DD
    m1 = re.search(r'(?<!\d)(19[7-9]\d|20[0-9]\d)[-._/](0[1-9]|1[0-2])[-._/](0[1-9]|[12]\d|3[01])(?!\d)', base)
    if m1:
        try:
            return datetime(int(m1.group(1)), int(m1.group(2)), int(m1.group(3)))
        except ValueError:
            pass

    # Pattern 2: Explicit DD-MM-YYYY or DD_MM_YYYY or DD.MM.YYYY
    m2 = re.search(r'(?<!\d)(0[1-9]|[12]\d|3[01])[-._/](0[1-9]|1[0-2])[-._/](19[7-9]\d|20[0-9]\d)(?!\d)', base)
    if m2:
        try:
            return datetime(int(m2.group(3)), int(m2.group(2)), int(m2.group(1)))
        except ValueError:
            pass

    # Pattern 3: 8 contiguous digits (e.g. 20022022, 20220220, 20210815, 01022023)
    pref = str(date_format_preference).upper()
    if pref.startswith('M'):
        formats = ['MMDDYYYY', 'DDMMYYYY']
    else:
        formats = ['DDMMYYYY', 'MMDDYYYY']

    for m8 in re.finditer(r'(?<!\d)(\d{8})(?!\d)', base):
        s = m8.group(1)

        # Try YYYYMMDD first (if starts with 19xx or 20xx)
        if s.startswith(('19', '20')):
            try:
                y, m, d = int(s[0:4]), int(s[4:6]), int(s[6:8])
                if 1970 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                    return datetime(y, m, d)
            except ValueError:
                pass

        # Try DDMMYYYY / MMDDYYYY according to tie-breaking preference
        if s.endswith(('19', '20')) or s[4:6] in ('19', '20'):
            for fmt in formats:
                if fmt == 'DDMMYYYY':
                    try:
                        d, m, y = int(s[0:2]), int(s[2:4]), int(s[4:8])
                        if 1970 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                            return datetime(y, m, d)
                    except ValueError:
                        pass
                elif fmt == 'MMDDYYYY':
                    try:
                        m, d, y = int(s[0:2]), int(s[2:4]), int(s[4:8])
                        if 1970 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                            return datetime(y, m, d)
                    except ValueError:
                        pass

    # Pattern 4: Year-Month YYYYMM or YYYY-MM (6 digits, e.g. 202202)
    m6 = re.search(r'(?<!\d)(19[7-9]\d|20[0-9]\d)[-._]?(0[1-9]|1[0-2])(?!\d)', base)
    if m6:
        try:
            return datetime(int(m6.group(1)), int(m6.group(2)), 1)
        except ValueError:
            pass

    # Pattern 5: 4-digit Year bounded by non-digits (e.g. Photo_2022.jpg, 1987_archive.pdf)
    m4 = re.search(r'(?<!\d)(19[7-9]\d|20[0-9]\d)(?!\d)', base)
    if m4:
        try:
            return datetime(int(m4.group(1)), 1, 1)
        except ValueError:
            pass

    return None


def sync_file_timestamps_from_filename(filepath):
    """
    Updates file system creation/modification timestamps to match the date parsed from filename.
    Fixes corrupt 1980/1987 OS timestamps on disk!
    """
    dt = extract_date_from_filename(filepath)
    if dt is None:
        return False
    try:
        ts = dt.timestamp()
        safe_p = fix_win_long_path(filepath)
        os.utime(safe_p, (ts, ts))
        if sys.platform == 'win32':
            try:
                import ctypes
                from ctypes import wintypes
                FILE_WRITE_ATTRIBUTES = 0x0100
                OPEN_EXISTING = 3
                FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

                w_path = safe_p
                if not w_path.startswith('\\\\?\\'):
                    w_path = '\\\\?\\' + os.path.abspath(w_path)

                handle = ctypes.windll.kernel32.CreateFileW(
                    w_path, FILE_WRITE_ATTRIBUTES, 7, None, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, None
                )
                if handle and handle != -1:
                    ft_val = int((ts + 11644473600) * 10000000)
                    low = ft_val & 0xFFFFFFFF
                    high = ft_val >> 32
                    filetime = wintypes.FILETIME(low, high)
                    ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(filetime), None, None)
                    ctypes.windll.kernel32.CloseHandle(handle)
            except Exception:
                pass
        return True
    except Exception:
        return False


def get_file_date(filepath, date_source='ctime', date_format_preference='DMY'):
    """
    Extracts datetime from a file using specified date source priority.
    date_source options:
      - 'filename' / 'smart' / 'filename_first': Checks Filename Date -> EXIF -> File System stat
      - 'exif': Camera EXIF -> Filename Date -> File System stat
      - 'ctime': Creation Time (with Filename Date fallback for corrupt OS timestamps)
      - 'mtime': Modification Time (with Filename Date fallback for corrupt OS timestamps)
    """
    dt = None
    safe_fp = fix_win_long_path(filepath)
    filename = os.path.basename(filepath)
    ds_lower = str(date_source).lower()

    # 1. Check Filename Embedded Date if 'smart', 'filename', or '🔤' requested
    if any(k in ds_lower for k in ['smart', 'filename', '🔤', '📅', 'auto']):
        dt = extract_date_from_filename(filename, date_format_preference=date_format_preference)

    # 2. Check EXIF camera metadata if dt is still None and ('exif', 'smart', 'auto') requested
    if dt is None and any(k in ds_lower for k in ['exif', 'smart', 'auto', '📅']):
        # Cloud Safety Guard: Skip binary EXIF file reading if file is an unhydrated cloud placeholder
        placeholder_info = is_cloud_placeholder(safe_fp)
        if HAS_PIL and not placeholder_info['is_placeholder']:
            try:
                ext = os.path.splitext(filepath)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.tiff', '.webp', '.heic']:
                    with Image.open(safe_fp) as img:
                        exif_data = img._getexif()
                        if exif_data:
                            for tag_id, value in exif_data.items():
                                tag_name = TAGS.get(tag_id, tag_id)
                                if tag_name in ['DateTimeOriginal', 'DateTimeDigitized', 'DateTime']:
                                    try:
                                        dt = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                                        break
                                    except Exception:
                                        pass
            except Exception:
                dt = None

    # 3. Fallback to OS file system stat timestamps (ctime/mtime) if dt is still None
    if dt is None:
        try:
            stat = os.stat(safe_fp)
            if 'mtime' in ds_lower:
                timestamp = stat.st_mtime
            else:
                timestamp = getattr(stat, 'st_birthtime', stat.st_ctime)
            dt = datetime.fromtimestamp(timestamp)
        except Exception:
            dt = datetime.now()

    # 4. Corrupt OS Timestamp Guard: If dt year is unreasonably old (< 1990 or > 2099) and filename contains a valid date, override with filename date!
    if dt and (dt.year < 1990 or dt.year > 2099):
        fn_dt = extract_date_from_filename(filename, date_format_preference=date_format_preference)
        if fn_dt:
            dt = fn_dt

    return dt


def get_file_category(filename):
    """Categorizes file into Images, Documents, Videos, etc."""
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def get_file_size_bracket(filepath):
    """Returns size category for file."""
    try:
        size_bytes = os.path.getsize(fix_win_long_path(filepath))
    except Exception:
        return "Unknown Size"

    mb = 1024 * 1024
    gb = 1024 * mb

    if size_bytes < 1 * mb:
        return "Tiny (< 1 MB)"
    elif size_bytes < 10 * mb:
        return "Small (1 - 10 MB)"
    elif size_bytes < 100 * mb:
        return "Medium (10 - 100 MB)"
    elif size_bytes < 1 * gb:
        return "Large (100 MB - 1 GB)"
    else:
        return "Huge (> 1 GB)"


def format_bytes(size):
    """Formats bytes into human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


UUID_REGEX = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
HEX_HASH_REGEX = re.compile(r'^[0-9a-fA-F]{12,}$')
META_CDN_REGEX = re.compile(r'^\d+_\d{10,}_\d{10,}_[a-zA-Z0-9]+$', re.IGNORECASE)
CDN_MEDIA_SUFFIX_REGEX = re.compile(r'[_-](video_dashinit|transcode_output_dashinit|transcode_oil_output_dashinit|video_init|audio_dashinit|media_dashinit|dash_init)(?:[_-]\d+)?$', re.IGNORECASE)
CONSONANT_CLUSTER_REGEX = re.compile(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]{5,}')
COMMON_HUMAN_WORD_ROOTS = {
    'image', 'photo', 'picture', 'screenshot', 'screen', 'video', 'vid',
    'doc', 'document', 'scan', 'recording', 'audio', 'track', 'song',
    'file', 'report', 'backup', 'copy', 'final', 'draft', 'test', 'data',
    'invoice', 'resume', 'note', 'notes', 'paper', 'project', 'presentation',
    'movie', 'clip', 'music', 'sound', 'chapter', 'part', 'page', 'sample',
    'vacation', 'trip', 'holiday', 'family', 'wedding', 'birthday', 'party',
    'work', 'school', 'home', 'house', 'car', 'travel', 'summer', 'winter',
    'spring', 'autumn', 'fall', 'january', 'february', 'march', 'april',
    'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'
}


def strip_all_extensions(filename_or_basename):
    """
    Iteratively strips compound file extensions (e.g. '.zip.nomedia', '.jpg.nomedia', '.tar.gz', '.mp4.tmp').
    """
    if not filename_or_basename:
        return ""
    name = os.path.basename(filename_or_basename)
    while True:
        base, ext = os.path.splitext(name)
        if ext and len(ext) > 1 and ' ' not in ext:
            name = base
        else:
            break
    return name


CONSONANT_CLUSTER_REGEX = re.compile(r'[bcdfghjklmnpqrstvwxyz]{4,}', re.IGNORECASE)
COMMON_STOPWORDS = {
    'the', 'a', 'an', 'this', 'that', 'these', 'those',
    'my', 'your', 'our', 'their', 'his', 'her', 'its'
}


def natural_sort_key(text):
    """
    Natural alphanumeric sorting key:
    Numbers are compared numerically, text lexicographically (case-insensitive).
    """
    chunks = [c for c in re.split(r'(\d+)', str(text)) if c]
    return [(0, int(c)) if c.isdigit() else (1, c.lower()) for c in chunks]


def extract_meaningful_group(filename):
    """
    Extracts the meaningful title / multi-word group from a filename:
    - Strips extension and leading/trailing underscores/hyphens/spaces.
    - Filters out machine hashes, pure numbers, UUIDs, Meta CDN IDs, and interleaved gibberish.
    - Removes common leading stopwords ('the', 'a', 'an', 'my', 'your', etc.) to prevent false collisions.
    - Preserves multi-word title prefixes before the first digit or date pattern.
    - If filename starts with a leading numeric prefix (e.g. '2024_report.pdf'), strips leading digits to extract the topic word.
    - Returns clean underscore-joined title group (e.g. 'june_pearl', 'silent_eyes', 'document', 'guru_finance_report'),
      or None if no meaningful alphabetic words exist.

    Examples:
      '_the_june_pearl_-12102022-0001.mp4' -> 'june_pearl'
      'the_silent_eyes_145-07062022-0001.mp4' -> 'silent_eyes'
      'my_document_2024.pdf' -> 'document'
      'a_nice_photo.jpg' -> 'nice_photo'
      'guru_finance_report.xls' -> 'guru_finance_report'
      '2024_report.pdf' -> 'report'
      '336101256_21499.jpg' -> None
      'hfqgifcbkj9.png' -> None
      '323f9w8ehf8awjefi.docx' -> None
    """
    if not filename:
        return None

    stem = strip_all_extensions(filename).strip()
    stem = stem.strip(' _-.')
    if not stem:
        return None

    # UUID Check
    if UUID_REGEX.match(stem):
        return None

    # Pure numeric strings (e.g. 336101256, 123456789)
    if stem.isdigit():
        return None

    # Separator-only or punctuation-only artifacts
    if re.match(r'^[\s_\-\.]+$', stem):
        return None

    # Hexadecimal hash >= 12 chars (e.g. MD5, SHA1, SHA256)
    if HEX_HASH_REGEX.match(stem) and any(c.isdigit() for c in stem) and any(c.isalpha() for c in stem):
        return None

    # Meta / Facebook / Instagram CDN ID pattern
    if META_CDN_REGEX.match(stem):
        return None

    # Interleaved hash/random alphanumeric strings (e.g. 323f9w8ehf8awjefi, 4f8a2c9e1b)
    if re.search(r'\d+[a-zA-Z]\d+|\d+[a-zA-Z]{1,2}\d+', stem):
        return None

    # Multi-digit numeric ID sequences with separators (10+ digits with no word letters)
    clean_no_sep = re.sub(r'[_\-\.\s]', '', stem)
    if clean_no_sep.isdigit() and len(clean_no_sep) >= 10:
        return None

    # If stem starts with a leading numeric prefix like '2024_' or '01-', strip it for semantic fallback
    work_stem = stem
    if re.match(r'^\d+[\s_\-]+', work_stem):
        work_stem = re.sub(r'^\d+[\s_\-]+', '', work_stem).strip(' _-.')

    # Extract alphabetical/underscore prefix before the first digit or date pattern
    m = re.match(r'^([a-zA-Z\s_\-]+?)(?=[0-9]|$)', work_stem)
    if not m:
        return None

    prefix = m.group(1).strip(' _-.')
    if not prefix:
        return None

    # Tokenize prefix into alphabetical words
    raw_tokens = re.findall(r'[a-zA-Z]+', prefix)
    if not raw_tokens:
        return None

    # If first token is a common stopword, remove it and use remaining tokens
    if raw_tokens[0].lower() in COMMON_STOPWORDS:
        if len(raw_tokens) > 1:
            raw_tokens = raw_tokens[1:]
        else:
            return None

    # Filter valid tokens (must contain vowel, not consonant cluster, >= 2 chars)
    valid_tokens = []
    for tok in raw_tokens:
        t = tok.lower()
        vowels = sum(1 for c in t if c in 'aeiou')
        if vowels == 0:
            continue
        # Exclude consonant clusters (4+ consecutive consonants)
        if CONSONANT_CLUSTER_REGEX.search(t):
            continue
        # Minimum vowel ratio (at least 20% vowels)
        if (vowels / len(t)) < 0.20:
            continue
        if len(t) < 2:
            continue
        valid_tokens.append(t)

    if not valid_tokens:
        return None

    return '_'.join(valid_tokens)


# Backward compatibility alias
def extract_word_base(filename):
    """Alias to extract_meaningful_group."""
    return extract_meaningful_group(filename)


def is_random_or_hash_name(filename_or_basename):
    """
    Checks if a filename lacks a meaningful alphabetical word or title group.
    Returns (is_random: bool, reason: str).
    """
    group = extract_meaningful_group(filename_or_basename)
    if group:
        return False, f"Meaningful title group '{group}' found"
    return True, "No meaningful word found in filename"


def extract_clean_title_prefix(filename_or_basename):
    """
    Returns the extracted meaningful title group for a filename, or empty string.
    """
    group = extract_meaningful_group(filename_or_basename)
    return group if group else ""


# File category buckets used for Unsorted subdivision
_UNSORTED_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.heic', '.raw', '.tiff', '.ico', '.cr2', '.nef', '.dng'}
_UNSORTED_VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.m2ts', '.vob', '.mpg', '.mpeg', '.m2v', '.divx', '.ogv'}


def get_unsorted_subfolder(filepath, subdivide='none'):
    """
    Returns the sub-path inside the catch-all Random folder when subdivision is enabled.
    subdivide options:
      'none' : flat — all random files in _Random/ (default)
      'type' : by file category — _Random/Images/, _Random/Videos/, _Random/Other/
      'date' : by modification month — _Random/YYYY-MM/
    Returns '' (empty string) for 'none', otherwise the sub-path.
    """
    if not subdivide or subdivide == 'none':
        return ''
    if subdivide == 'type':
        ext = os.path.splitext(filepath)[1].lower()
        if ext in _UNSORTED_IMAGE_EXTS:
            return 'Images'
        elif ext in _UNSORTED_VIDEO_EXTS:
            return 'Videos'
        else:
            return 'Other'
    if subdivide == 'date':
        try:
            mtime = os.path.getmtime(fix_win_long_path(filepath))
            dt = datetime.fromtimestamp(mtime)
            return f"{dt.year:04d}-{dt.month:02d}"
        except Exception:
            return 'Unknown'
    return ''


def get_name_sort_folder(filename, random_folder_name="_Random", filepath=None, unsorted_subdivide='none'):
    """
    Computes destination subfolder for Meaningful Title & Multi-Word Grouping:
      - Extracts meaningful multi-word title group skipping stopwords (e.g. 'june_pearl', 'silent_eyes', 'document').
      - If found: routes to folder named after the group.
      - If no meaningful title group found: routes to ONE shared catch-all folder (default: '_Random'),
        optionally subdivided by type or date via unsorted_subdivide.
    Returns (folder_name: str, is_random: bool, reason: str).
    """
    group = extract_meaningful_group(filename)
    if group:
        return group, False, f"Extracted title group '{group}'"

    base_name = random_folder_name if (random_folder_name and str(random_folder_name).strip()) else "_Random"
    if unsorted_subdivide and unsorted_subdivide != 'none' and filepath:
        sub = get_unsorted_subfolder(filepath, unsorted_subdivide)
        folder_name = os.path.join(base_name, sub) if sub else base_name
    else:
        folder_name = base_name

    return folder_name, True, "No meaningful word found (routed to random catch-all)"


def get_alphabetical_folder(filename):
    """Returns A-Z, 0-9, or Symbols folder name based on first letter."""
    name = filename.strip()
    if not name:
        return "Symbols"
    first_char = name[0].upper()
    if first_char.isalpha():
        return first_char
    elif first_char.isdigit():
        return "0-9"
    else:
        return "Symbols & Others"


def get_destination_folder(base_folder, filepath, sort_category, date_source='ctime', structure_format='YYYY/MM', is_duplicate=False, isolate_duplicates=False, dest_folder=None, random_folder_name="_Random", unsorted_subdivide='none'):
    """
    Generates target folder path depending on sort_category & optional custom dest_folder.
    New params:
      unsorted_subdivide: 'none' | 'type' | 'date' — for smart_name random catch-all subdivision.
    """
    filename = os.path.basename(filepath)
    target_root = os.path.abspath(dest_folder) if (dest_folder and str(dest_folder).strip()) else base_folder

    if isolate_duplicates and is_duplicate:
        return os.path.join(target_root, "_Duplicates")

    if sort_category == 'date':
        date_obj = get_file_date(filepath, date_source)
        year_str = f"{date_obj.year:04d}"
        month_num = f"{date_obj.month:02d}"
        day_num = f"{date_obj.day:02d}"
        month_name = MONTH_NAMES.get(date_obj.month, month_num)

        if structure_format == 'YYYY/MM - Month':
            return os.path.join(target_root, year_str, f"{month_num} - {month_name}")
        elif structure_format == 'YYYY-MM':
            return os.path.join(target_root, f"{year_str}-{month_num}")
        elif structure_format == 'YYYY/MM/DD':
            return os.path.join(target_root, year_str, month_num, day_num)
        else:
            return os.path.join(target_root, year_str, month_num)

    elif sort_category == 'category':
        cat_name = get_file_category(filename)
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        ext_folder = ext.upper() if ext else "NO_EXT"
        return os.path.join(target_root, cat_name, ext_folder)

    elif sort_category == 'extension':
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        ext_folder = ext.upper() if ext else "NO_EXT"
        return os.path.join(target_root, ext_folder)

    elif sort_category in ('smart_name', 'name', 'full_name'):
        folder_name, is_random, reason = get_name_sort_folder(
            filename,
            random_folder_name=random_folder_name,
            filepath=filepath,
            unsorted_subdivide=unsorted_subdivide
        )
        return os.path.join(target_root, folder_name)

    elif sort_category == 'alphabetical':
        alpha_folder = get_alphabetical_folder(filename)
        return os.path.join(target_root, f"Alphabetical_{alpha_folder}")

    elif sort_category == 'size':
        size_folder = get_file_size_bracket(filepath)
        return os.path.join(target_root, size_folder)

    else:
        return target_root


def resolve_filename_collision(target_dir, filename):
    """
    Generates a numbered non-colliding filename (e.g. filename_1.ext).
    """
    dest_path = os.path.join(target_dir, filename)
    if not os.path.exists(fix_win_long_path(dest_path)):
        return dest_path

    name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(fix_win_long_path(dest_path)):
        new_filename = f"{name}_{counter}{ext}"
        dest_path = os.path.join(target_dir, new_filename)
        counter += 1
    return dest_path


def is_manifest_file(filename):
    return (filename.startswith(".date_sorter_manifest_") or filename.startswith(".date_sorter_backup_")) and filename.endswith(".json")


def create_safety_backup_zip(main_folder, file_list, progress_callback=None):
    """
    Creates a full safety ZIP backup of target files and saves it to BOTH:
    1. Protected System AppData Vault: %LOCALAPPDATA%\\SmartFileOrganizer\\Vault\\SafetyZipBackups\\ (Safe from accidental user deletion!)
    2. Local hidden .backups/ folder in main_folder
    """
    main_folder = os.path.abspath(main_folder)

    vault_dir = get_system_vault_dir("SafetyZipBackups")
    local_backup_dir = os.path.join(main_folder, ".backups")
    os.makedirs(fix_win_long_path(local_backup_dir), exist_ok=True)
    hide_path_windows(local_backup_dir)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"safety_backup_{timestamp_str}.zip"
    vault_zip_path = os.path.join(vault_dir, zip_filename)
    local_zip_path = os.path.join(local_backup_dir, zip_filename)

    total = len(file_list)
    added = 0
    with zipfile.ZipFile(fix_win_long_path(vault_zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for idx, fp in enumerate(file_list, 1):
            try:
                safe_fp = fix_win_long_path(fp)
                if os.path.exists(safe_fp):
                    rel = os.path.relpath(fp, main_folder)
                    zipf.write(safe_fp, rel)
                    added += 1
                    if progress_callback:
                        progress_callback(idx, total, fp, f"📦 Vault Backup -> {rel}", "info")
            except Exception:
                pass

    try:
        shutil.copy2(fix_win_long_path(vault_zip_path), fix_win_long_path(local_zip_path))
    except Exception:
        pass

    return vault_zip_path, added


def compile_exclusion_rules(exclude_folders, base_folder=None):
    """
    Compiles an exclusion list into a high-performance O(1) lookup rule dictionary.
    """
    if not exclude_folders:
        return None
    if isinstance(exclude_folders, dict) and "abs" in exclude_folders:
        return exclude_folders

    if isinstance(exclude_folders, (str, bytes)):
        exclude_folders = [p.strip() for p in str(exclude_folders).replace(',', ';').split(';') if p.strip()]

    abs_rules = set()
    name_rules = set()
    rel_rules = set()
    base_abs = os.path.normpath(os.path.abspath(base_folder)).lower().rstrip('\\/') if base_folder else None

    for ef in exclude_folders:
        ef_str = str(ef).strip()
        if not ef_str:
            continue
        ef_norm = os.path.normpath(ef_str).lower().rstrip('\\/')
        if not ef_norm:
            continue

        if (len(ef_norm) > 1 and ef_norm[1] == ':') or ef_norm.startswith('\\') or ef_norm.startswith('/'):
            abs_rules.add(os.path.normpath(os.path.abspath(ef_norm)).lower().rstrip('\\/'))
            bname = os.path.basename(ef_norm).lower()
            if bname:
                name_rules.add(bname)
        elif '\\' not in ef_norm and '/' not in ef_norm:
            name_rules.add(ef_norm)
        else:
            rel_rules.add(ef_norm)
            bname = os.path.basename(ef_norm).lower()
            if bname:
                name_rules.add(bname)

    return {"abs": abs_rules, "names": name_rules, "rels": rel_rules, "base": base_abs}


def is_path_excluded(path_to_check, exclude_folders, base_folder=None):
    """
    High-speed O(1) path exclusion check. Supports pre-compiled rule dicts or raw lists.
    """
    if not exclude_folders or not path_to_check:
        return False

    compiled = compile_exclusion_rules(exclude_folders, base_folder) if not (isinstance(exclude_folders, dict) and "abs" in exclude_folders) else exclude_folders
    if not compiled:
        return False

    target_norm = os.path.normpath(os.path.abspath(path_to_check)).lower().rstrip('\\/')

    # 1. Simple folder/filename matching (evaluated relative to base_folder so parent dirs do not block scan)
    if compiled["names"]:
        base_norm = compiled.get("base") or (os.path.normpath(os.path.abspath(base_folder)).lower().rstrip('\\/') if base_folder else None)
        if base_norm and target_norm.startswith(base_norm):
            try:
                rel_parts_str = os.path.relpath(target_norm, base_norm).lower().rstrip('\\/')
                if rel_parts_str != '.':
                    rel_parts = set(rel_parts_str.split(os.sep))
                    if rel_parts.intersection(compiled["names"]):
                        return True
                elif os.path.basename(target_norm) in compiled["names"]:
                    return True
            except Exception:
                pass
        else:
            b_name = os.path.basename(target_norm)
            if b_name in compiled["names"]:
                return True

    # 2. Absolute path matching
    if compiled["abs"]:
        for exc_abs in compiled["abs"]:
            if target_norm == exc_abs or target_norm.startswith(exc_abs + os.sep):
                return True

    # 3. Relative path matching
    if compiled["rels"] and compiled["base"]:
        try:
            rel_target = os.path.relpath(target_norm, compiled["base"]).lower().rstrip('\\/')
            if rel_target != '.':
                for rel_exc in compiled["rels"]:
                    if rel_target == rel_exc or rel_target.startswith(rel_exc + os.sep):
                        return True
        except Exception:
            pass

    return False


def gather_files(main_folder, recursive=True, include_exts=None, exclude_exts=None, exclude_folders=None, exclude_files=None, selected_files=None, progress_callback=None):
    """
    Helper to collect files based on filter parameters, excluded subfolders/files, OR explicit selected_files list.
    Emits live progress_callback during directory traversal.
    """
    inc_ext_set = set(e.lower().strip() if e.startswith('.') else f".{e.lower().strip()}" for e in include_exts) if include_exts else None
    exc_ext_set = set(e.lower().strip() if e.startswith('.') else f".{e.lower().strip()}" for e in exclude_exts) if exclude_exts else set()

    exc_files_set = set(f.lower().strip() for f in exclude_files) if exclude_files else set()

    # Combine user exclude_folders and exclude_files with default internal exclusions
    all_exc_folders = list(DEFAULT_EXCLUDED_FOLDERS)
    if exclude_folders:
        if isinstance(exclude_folders, (list, tuple, set)):
            all_exc_folders.extend(list(exclude_folders))
        elif isinstance(exclude_folders, str):
            all_exc_folders.extend([p.strip() for p in exclude_folders.replace(',', ';').split(';') if p.strip()])
    if exclude_files:
        if isinstance(exclude_files, (list, tuple, set)):
            all_exc_folders.extend(list(exclude_files))
        elif isinstance(exclude_files, str):
            all_exc_folders.extend([p.strip() for p in exclude_files.replace(',', ';').split(';') if p.strip()])

    # If explicit individual files were selected by user, honor the user's exact choice.
    # General folder/category extension filters should not silently remove files that were
    # deliberately picked by the user from a file dialog.
    if selected_files:
        files_to_process = []
        for fp in selected_files:
            if not os.path.isfile(fix_win_long_path(fp)):
                continue
            fname = os.path.basename(fp)
            if is_manifest_file(fname) or (exc_files_set and fname.lower().strip() in exc_files_set):
                continue
            if is_path_excluded(fp, all_exc_folders, base_folder=main_folder):
                continue
            files_to_process.append(fp)
        return files_to_process

    # Otherwise scan directory (supports multiple folder paths separated by ';' or ',')
    folders_list = []
    if main_folder and isinstance(main_folder, str):
        raw_parts = [p.strip().strip('\'"') for p in main_folder.replace(',', ';').split(';') if p.strip().strip('\'"')]
        for p in raw_parts:
            safe_p = fix_win_long_path(p)
            if os.path.isdir(safe_p):
                folders_list.append(os.path.abspath(safe_p))

    if not folders_list and main_folder:
        safe_m = fix_win_long_path(main_folder)
        if os.path.isdir(safe_m):
            folders_list = [os.path.abspath(safe_m)]

    files_to_process = []
    for fld in folders_list:
        compiled_exc = compile_exclusion_rules(all_exc_folders, base_folder=fld)

        if recursive:
            for root, dirs, files in os.walk(fld):
                if is_path_excluded(root, compiled_exc, base_folder=fld):
                    dirs[:] = []
                    continue

                # Prune subdirectories before walking into them
                dirs[:] = [d for d in dirs if not is_path_excluded(os.path.join(root, d), compiled_exc, base_folder=fld)]

                for f in files:
                    if is_manifest_file(f) or (exc_files_set and f.lower().strip() in exc_files_set):
                        continue
                    full_path = os.path.join(root, f)
                    if is_path_excluded(full_path, compiled_exc, base_folder=fld):
                        continue

                    ext = os.path.splitext(f)[1].lower()
                    if exc_ext_set and ext in exc_ext_set:
                        continue
                    if inc_ext_set and ext not in inc_ext_set:
                        continue

                    files_to_process.append(full_path)
                    if progress_callback and (len(files_to_process) % 100 == 0):
                        progress_callback(len(files_to_process), 0, f"Gathering directory files ({len(files_to_process):,} found)...", f)

        else:
            try:
                entries = os.listdir(fld)
            except Exception:
                entries = []

            for item in entries:
                full_path = os.path.join(fld, item)
                if is_path_excluded(full_path, all_exc_folders, base_folder=fld):
                    continue
                if os.path.isfile(fix_win_long_path(full_path)) and not is_manifest_file(item):
                    if exc_files_set and item.lower().strip() in exc_files_set:
                        continue

                    ext = os.path.splitext(item)[1].lower()

                    if exc_ext_set and ext in exc_ext_set:
                        continue
                    if inc_ext_set and ext not in inc_ext_set:
                        continue

                    files_to_process.append(full_path)
                    if progress_callback and (len(files_to_process) % 100 == 0):
                        progress_callback(len(files_to_process), 0, f"Gathering directory files ({len(files_to_process):,} found)...", item)

    return files_to_process


VIDEO_FILE_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.ts', '.m2ts', '.divx', '.mpg', '.mpeg'}
DEFAULT_EXCLUDED_FOLDERS = [
    '.git', 'node_modules', '_Duplicates', '.backups', '.trash_duplicates',
    'System Volume Information', '$RECYCLE.BIN', '__pycache__', '.venv', 'venv',
    '.idea', '.vscode', 'tmp', 'temp'
]


def get_video_file_info(file_path):
    """
    Extracts video duration (secs & formatted string), resolution (width x height & 1080p/4K tag), and FPS using OpenCV.
    Uses multi-pass duration calculation (frame count ratio -> POS_AVI_RATIO millisecond probe).
    """
    safe_p = fix_win_long_path(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in VIDEO_FILE_EXTENSIONS:
        return None
    
    info = {'duration_secs': 0, 'duration_str': '', 'res_str': '', 'width': 0, 'height': 0, 'fps': 0}
    try:
        import cv2
        cap = cv2.VideoCapture(safe_p)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0

            duration_secs = 0.0
            if fps > 0 and frames > 0:
                duration_secs = frames / fps

            # Fallback Pass: Jump to end via POS_AVI_RATIO=1 to read duration in ms
            if duration_secs <= 0:
                try:
                    cap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
                    ms = cap.get(cv2.CAP_PROP_POS_MSEC)
                    if ms and ms > 0:
                        duration_secs = ms / 1000.0
                except Exception:
                    pass

            cap.release()

            if duration_secs > 0:
                info['duration_secs'] = duration_secs
                mins, secs = divmod(int(duration_secs), 60)
                hrs, mins = divmod(mins, 60)
                if hrs > 0:
                    info['duration_str'] = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                else:
                    info['duration_str'] = f"{mins:02d}:{secs:02d}"

            if w > 0 and h > 0:
                info['width'] = w
                info['height'] = h
                if w >= 3840 or h >= 2160:
                    tag = "4K Ultra HD"
                elif w >= 2560 or h >= 1440:
                    tag = "2K QHD"
                elif w >= 1920 or h >= 1080:
                    tag = "1080p Full HD"
                elif w >= 1280 or h >= 720:
                    tag = "720p HD"
                elif w >= 854 or h >= 480:
                    tag = "480p SD"
                else:
                    tag = f"{w}x{h}"
                info['res_str'] = f"{w}x{h} ({tag})"
                info['fps'] = int(fps) if fps else 0
    except Exception:
        pass

    return info


find_duplicate_groups = None  # defined after find_duplicates below

def find_duplicates(
    main_folder,
    match_mode='content',
    recursive=True,
    exclude_folders=None,
    exclude_files=None,
    selected_files=None,
    similarity_threshold=0.9,
    progress_callback=None,
    include_exts=None,
    exclude_exts=None,
    allow_other_exts=True
):
    """
    Super Duplicate & Similar Files Finder Engine.
    Supports match_mode:
      - 'content'          : Exact SHA-256 Byte Content (with fast multi-threaded pre-hashing)
      - 'perceptual_image' : Visual Image Similarity (dHash + Hamming Distance)
      - 'fuzzy_name'       : Fuzzy File Name Similarity (SequenceMatcher)
      - 'text_similarity'  : Text Content Similarity (SequenceMatcher)
      - 'name_size'        : Same Name & Size (Cloud Friendly)
      - 'name_size_mtime'  : Name + Size + Modification Date
    """
    if not selected_files:
        if not main_folder:
            return []
        raw_parts = [p.strip() for p in str(main_folder).replace(',', ';').split(';') if p.strip()]
        valid_dirs = [p for p in raw_parts if os.path.isdir(fix_win_long_path(p))]
        if not valid_dirs:
            return []

    if progress_callback:
        progress_callback(0, 100, "Gathering directory files...", "")

    files = gather_files(main_folder, recursive, include_exts, exclude_exts, exclude_folders, exclude_files, selected_files=selected_files, progress_callback=progress_callback)
    if not files:
        return []

    if include_exts is not None and not selected_files:
        known_cat_exts = {
            '.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.heif', '.raw', '.cr2', '.nef', '.svg', '.ico', '.psd',
            '.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls', '.csv', '.pptx', '.ppt', '.rtf', '.odt', '.ods', '.odp', '.epub', '.md', '.log', '.xml', '.json',
            '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.vob', '.mts', '.m2ts', '.ts',
            '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.opus', '.aiff', '.mid', '.midi'
        }
        filtered = []
        for fp in files:
            ext = os.path.splitext(fp)[1].lower()
            if ext in include_exts:
                filtered.append(fp)
            elif allow_other_exts and ext not in known_cat_exts:
                filtered.append(fp)
        files = filtered

    if not files:
        return []

    total_files = len(files)
    try:
        threshold = float(similarity_threshold)
    except (ValueError, TypeError):
        threshold = 0.9

    file_items = []

    # Gather file metadata and extract image resolution info
    step_idx = max(1, total_files // 100)
    for idx, fp in enumerate(files):
        curr_num = idx + 1
        if progress_callback and (curr_num % step_idx == 0 or curr_num == total_files):
            progress_callback(curr_num, total_files, f"Indexing files & metadata ({curr_num}/{total_files})...", os.path.basename(fp))

        safe_fp = fix_win_long_path(fp)
        try:
            stat = os.stat(safe_fp)
            size_bytes = stat.st_size
            mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            filename = os.path.basename(fp)
        except Exception:
            continue

        rel_path = filename
        if main_folder and isinstance(main_folder, str) and os.path.isdir(fix_win_long_path(main_folder)):
            try:
                rel_path = os.path.relpath(fp, main_folder)
            except Exception:
                rel_path = filename

        item = {
            'path': fp,
            'rel_path': rel_path,
            'filename': filename,
            'size_bytes': size_bytes,
            'size_str': format_bytes(size_bytes),
            'mtime_str': mtime_str,
            'stat_mtime': stat.st_mtime,
            'match_percent': 100.0,
            'width': 0,
            'height': 0,
            'megapixels': 0.0,
            'res_str': ''
        }

        ext = os.path.splitext(filename)[1].lower()
        # Cloud Safety Guard: Skip video/image binary file reads if file is an unhydrated cloud placeholder
        p_check = is_cloud_placeholder(safe_fp)
        if not p_check['is_placeholder']:
            if ext in VIDEO_FILE_EXTENSIONS:
                v_info = get_video_file_info(fp)
                if v_info:
                    item['duration_str'] = v_info.get('duration_str', '')
                    item['duration_secs'] = v_info.get('duration_secs', 0)
                    item['width'] = v_info.get('width', 0)
                    item['height'] = v_info.get('height', 0)
                    item['res_str'] = v_info.get('res_str', '')
                    item['fps'] = v_info.get('fps', 0)
                    item['is_video'] = True
            elif match_mode == 'perceptual_image' and HAS_PIL and ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif']:
                p_data = get_image_perceptual_hash(fp)
                if p_data:
                    item['phash'] = p_data['hash_int']
                    item['phash_str'] = p_data['hash_str']
                    item['width'] = p_data['width']
                    item['height'] = p_data['height']
                    item['megapixels'] = p_data['megapixels']
                    item['res_str'] = p_data['res_str']

        file_items.append(item)

    final_groups = []
    group_counter = 1

    # MODE 1: Exact Byte Content (SHA-256 with Multi-Threaded Fast Pre-Hashing)
    if match_mode == 'content':
        # Step A: Group candidates by file size first
        size_groups = {}
        for item in file_items:
            sz = item['size_bytes']
            if sz not in size_groups:
                size_groups[sz] = []
            size_groups[sz].append(item)

        candidates = [items for sz, items in size_groups.items() if len(items) > 1]
        
        # Step B: Fast pre-hash (Head/Tail MD5) for candidates > 1MB
        fast_hash_map = {}
        def compute_fast_hash(it):
            h = get_file_fast_hash(it['path']) if it['size_bytes'] > 1048576 else get_file_hash(it['path'])
            return it['path'], h

        files_to_fast_hash = [it for group in candidates for it in group]
        if files_to_fast_hash:
            tot_fh = len(files_to_fast_hash)
            step_fh = max(1, tot_fh // 50)
            done_fh = 0
            with ThreadPoolExecutor(max_workers=min(16, os.cpu_count() or 4)) as executor:
                fast_results = executor.map(compute_fast_hash, files_to_fast_hash)
                for path, h in fast_results:
                    fast_hash_map[path] = h
                    done_fh += 1
                    if progress_callback and (done_fh % step_fh == 0 or done_fh == tot_fh):
                        progress_callback(done_fh, tot_fh, f"Pre-hashing duplicate candidates ({done_fh}/{tot_fh})...", os.path.basename(path))

        fast_groups = {}
        for group in candidates:
            for item in group:
                h = fast_hash_map.get(item['path']) or f"sz_{item['size_bytes']}"
                if h not in fast_groups:
                    fast_groups[h] = []
                fast_groups[h].append(item)

        # Step C: Full SHA-256 for matching fast-hash candidates
        sha_hash_map = {}
        def compute_full_hash(it):
            return it['path'], get_file_hash(it['path'])

        files_to_full_hash = [it for h, items in fast_groups.items() if len(items) > 1 for it in items]
        if files_to_full_hash:
            tot_full = len(files_to_full_hash)
            step_full = max(1, tot_full // 50)
            done_full = 0
            with ThreadPoolExecutor(max_workers=min(16, os.cpu_count() or 4)) as executor:
                full_results = executor.map(compute_full_hash, files_to_full_hash)
                for path, h in full_results:
                    sha_hash_map[path] = h
                    done_full += 1
                    if progress_callback and (done_full % step_full == 0 or done_full == tot_full):
                        progress_callback(done_full, tot_full, f"SHA-256 content hashing ({done_full}/{tot_full})...", os.path.basename(path))

        final_hash_groups = {}
        for h, items in fast_groups.items():
            if len(items) < 2:
                continue
            for item in items:
                full_h = sha_hash_map.get(item['path']) or f"fallback_{item['filename']}"
                if full_h not in final_hash_groups:
                    final_hash_groups[full_h] = []
                final_hash_groups[full_h].append(item)

        for h, items in final_hash_groups.items():
            if len(items) > 1:
                items.sort(key=lambda x: x['stat_mtime'])
                for idx, it in enumerate(items):
                    it['is_original'] = (idx == 0)
                    it['match_percent'] = 100.0
                sig_display = f"SHA256: {h[:12]}..." if not h.startswith("fallback_") else f"Metadata: {items[0]['filename']}"
                final_groups.append({
                    'group_id': group_counter,
                    'signature': sig_display,
                    'match_mode': 'content',
                    'files': items
                })
                group_counter += 1

    # MODE 2: Visual Image Similarity (Perceptual Hashing)
    elif match_mode == 'perceptual_image':
        image_items = [it for it in file_items if 'phash' in it]
        visited = set()

        for i, item1 in enumerate(image_items):
            if item1['path'] in visited:
                continue
            group_members = [item1]

            for j in range(i + 1, len(image_items)):
                item2 = image_items[j]
                if item2['path'] in visited:
                    continue
                sim = calculate_hamming_similarity(item1['phash'], item2['phash'])
                if sim >= threshold:
                    item2_copy = dict(item2)
                    item2_copy['match_percent'] = round(sim * 100.0, 1)
                    group_members.append(item2_copy)
                    visited.add(item2['path'])

            if len(group_members) > 1:
                visited.add(item1['path'])
                group_members[0]['match_percent'] = 100.0
                group_members.sort(key=lambda x: (-x.get('megapixels', 0), x['stat_mtime']))
                for idx, it in enumerate(group_members):
                    it['is_original'] = (idx == 0)
                
                final_groups.append({
                    'group_id': group_counter,
                    'signature': f"👁️ Visual Similarity ({round(threshold*100)}%+ Match)",
                    'match_mode': 'perceptual_image',
                    'files': group_members
                })
                group_counter += 1

    # MODE 3: Fuzzy File Name Similarity
    elif match_mode == 'fuzzy_name':
        visited = set()
        for i, item1 in enumerate(file_items):
            if item1['path'] in visited:
                continue
            group_members = [item1]

            for j in range(i + 1, len(file_items)):
                item2 = file_items[j]
                if item2['path'] in visited:
                    continue
                sim = calculate_fuzzy_name_similarity(item1['filename'], item2['filename'])
                if sim >= threshold:
                    item2_copy = dict(item2)
                    item2_copy['match_percent'] = round(sim * 100.0, 1)
                    group_members.append(item2_copy)
                    visited.add(item2['path'])

            if len(group_members) > 1:
                visited.add(item1['path'])
                group_members[0]['match_percent'] = 100.0
                group_members.sort(key=lambda x: x['stat_mtime'])
                for idx, it in enumerate(group_members):
                    it['is_original'] = (idx == 0)
                
                final_groups.append({
                    'group_id': group_counter,
                    'signature': f"🔤 Fuzzy Name Similarity ({round(threshold*100)}%+ Match)",
                    'match_mode': 'fuzzy_name',
                    'files': group_members
                })
                group_counter += 1

    # MODE 4: Text Content Similarity
    elif match_mode == 'text_similarity':
        text_exts = {'.txt', '.csv', '.py', '.js', '.html', '.css', '.json', '.md', '.log', '.xml', '.yaml', '.yml'}
        text_items = [it for it in file_items if os.path.splitext(it['filename'])[1].lower() in text_exts]
        visited = set()

        for i, item1 in enumerate(text_items):
            if item1['path'] in visited:
                continue
            group_members = [item1]

            for j in range(i + 1, len(text_items)):
                item2 = text_items[j]
                if item2['path'] in visited:
                    continue
                sim = calculate_text_similarity(item1['path'], item2['path'])
                if sim >= threshold:
                    item2_copy = dict(item2)
                    item2_copy['match_percent'] = round(sim * 100.0, 1)
                    group_members.append(item2_copy)
                    visited.add(item2['path'])

            if len(group_members) > 1:
                visited.add(item1['path'])
                group_members[0]['match_percent'] = 100.0
                group_members.sort(key=lambda x: x['stat_mtime'])
                for idx, it in enumerate(group_members):
                    it['is_original'] = (idx == 0)
                
                final_groups.append({
                    'group_id': group_counter,
                    'signature': f"📝 Text Content Similarity ({round(threshold*100)}%+ Match)",
                    'match_mode': 'text_similarity',
                    'files': group_members
                })
                group_counter += 1

    # MODE 5 & 6: Metadata Matching (name_size, name_size_mtime)
    else:
        groups_dict = {}
        for item in file_items:
            fn = item['filename']
            sz = item['size_bytes']
            mt = item['mtime_str']
            if match_mode == 'name_size':
                sig_key = f"name:{fn.lower()}|size:{sz}"
            elif match_mode == 'name_size_mtime':
                sig_key = f"name:{fn.lower()}|size:{sz}|mtime:{mt}"
            else:
                sig_key = f"size:{sz}"

            if sig_key not in groups_dict:
                groups_dict[sig_key] = []
            groups_dict[sig_key].append(item)

        for sig_key, items in groups_dict.items():
            if len(items) > 1:
                items.sort(key=lambda x: x['stat_mtime'])
                for idx, it in enumerate(items):
                    it['is_original'] = (idx == 0)
                    it['match_percent'] = 100.0
                final_groups.append({
                    'group_id': group_counter,
                    'signature': f"Metadata Match: {items[0]['filename']}",
                    'match_mode': match_mode,
                    'files': items
                })
                group_counter += 1

    return final_groups


find_duplicate_groups = find_duplicates



# ---------------------------------------------------------------------------
# DELETION MODE CONSTANTS
# ---------------------------------------------------------------------------
DELETE_MODE_RECYCLE = "recycle"      # Send to Windows Recycle Bin (default)
DELETE_MODE_VAULT   = "vault"        # Move to System Vault Backup folder
DELETE_MODE_PERMANENT = "permanent"  # Permanent delete (use with caution!)

# Global app-wide deletion mode (can be changed via GUI setting)
_APP_DELETE_MODE = DELETE_MODE_RECYCLE


def set_app_delete_mode(mode):
    """Set the global deletion mode for all safe_delete() calls."""
    global _APP_DELETE_MODE
    if mode in (DELETE_MODE_RECYCLE, DELETE_MODE_VAULT, DELETE_MODE_PERMANENT):
        _APP_DELETE_MODE = mode


def get_app_delete_mode():
    return _APP_DELETE_MODE


def safe_delete(file_path, mode=None):
    """
    Unified safe file deletion.

    Modes:
      'recycle'   — Sends file to Windows Recycle Bin (default). User can restore anytime.
      'vault'     — Moves file to %LOCALAPPDATA%\\SmartFileOrganizer\\Vault\\TrashDuplicates
      'permanent' — Permanently deletes (use ONLY when explicitly chosen by user).

    Falls back to 'vault' if send2trash is unavailable and mode='recycle'.
    Returns True on success, False on error.
    """
    global _APP_DELETE_MODE
    effective_mode = mode if mode else _APP_DELETE_MODE
    safe_fp = fix_win_long_path(file_path)

    if not os.path.exists(safe_fp):
        return False

    try:
        if effective_mode == DELETE_MODE_RECYCLE:
            if HAS_SEND2TRASH:
                # send2trash requires the real (non \\?\ prefixed) path
                send2trash.send2trash(os.path.normpath(file_path))
                return True
            else:
                # Fallback to vault if library unavailable
                effective_mode = DELETE_MODE_VAULT

        if effective_mode == DELETE_MODE_VAULT:
            vault_trash = get_system_vault_dir("TrashDuplicates")
            name, ext = os.path.splitext(os.path.basename(file_path))
            target_path = os.path.join(vault_trash, os.path.basename(file_path))
            safe_target = fix_win_long_path(target_path)
            if os.path.exists(safe_target):
                target_path = os.path.join(vault_trash, f"{name}_{int(time.time())}{ext}")
                safe_target = fix_win_long_path(target_path)
            shutil.move(safe_fp, safe_target)
            return True

        if effective_mode == DELETE_MODE_PERMANENT:
            os.remove(safe_fp)
            return True

    except Exception:
        return False

    return False





def delete_duplicate_files(file_paths, use_trash_backup=True, main_folder=None, delete_mode=None):
    """
    Safe file deletion handler with 3-mode support.

    delete_mode options:
      'recycle'   — Windows Recycle Bin (default, user can restore anytime via Recycle Bin)
      'vault'     — Move to System AppData Vault Trash (always recoverable via Restore Manager)
      'permanent' — Permanent delete (only when explicitly chosen by user)

    use_trash_backup=True is a legacy alias for delete_mode='vault'.
    """
    deleted = 0
    errors = 0

    # Resolve effective mode
    if delete_mode:
        effective_mode = delete_mode
    elif use_trash_backup:
        effective_mode = DELETE_MODE_VAULT   # legacy behaviour
    else:
        effective_mode = _APP_DELETE_MODE    # respect global app setting

    for fp in file_paths:
        ok = safe_delete(fp, mode=effective_mode)
        if ok:
            deleted += 1
        else:
            errors += 1

    return {"deleted": deleted, "errors": errors, "safety_trash": use_trash_backup}




def move_duplicate_files(file_paths, dest_folder):
    """Moves list of file paths to dest_folder. Returns count of moved files and errors."""
    dest_folder = os.path.abspath(dest_folder)
    os.makedirs(fix_win_long_path(dest_folder), exist_ok=True)
    moved = 0
    errors = 0
    for fp in file_paths:
        safe_fp = fix_win_long_path(fp)
        try:
            if os.path.exists(safe_fp):
                target_path = resolve_filename_collision(dest_folder, os.path.basename(fp))
                safe_target = fix_win_long_path(target_path)
                is_safe, reason = verify_safe_overwrite(safe_fp, safe_target)
                if not is_safe:
                    errors += 1
                    continue
                shutil.move(safe_fp, safe_target)
                moved += 1
        except Exception:
            errors += 1
    return {"moved": moved, "errors": errors}


def replace_duplicates_with_links(duplicate_file_paths, original_file_path, link_type='hard'):
    """
    Replaces specified duplicate files with hard links (or symbolic links) pointing to original_file_path.
    Reclaims physical disk space instantly while preserving file paths for applications!
    """
    linked = 0
    errors = 0
    safe_orig = fix_win_long_path(os.path.abspath(original_file_path))

    if not os.path.exists(safe_orig):
        return {"linked": 0, "errors": len(duplicate_file_paths)}

    for dup_fp in duplicate_file_paths:
        safe_dup = fix_win_long_path(os.path.abspath(dup_fp))
        if safe_dup == safe_orig or not os.path.exists(safe_dup):
            continue
        try:
            # Create a temporary backup link destination, remove original file, create link
            temp_dup = safe_dup + ".tmp_link"
            if os.path.exists(temp_dup):
                os.remove(temp_dup)
            
            if link_type == 'hard':
                os.link(safe_orig, temp_dup)
            else:
                os.symlink(safe_orig, temp_dup)
            
            os.remove(safe_dup)
            os.rename(temp_dup, safe_dup)
            linked += 1
        except Exception:
            errors += 1

    return {"linked": linked, "errors": errors}


def export_duplicates_report(groups, output_filepath, report_format='csv'):
    """
    Exports detected duplicate groups summary to CSV or JSON file.
    Returns True on success, False on error.
    """
    try:
        safe_out = fix_win_long_path(os.path.abspath(output_filepath))
        os.makedirs(os.path.dirname(safe_out), exist_ok=True)

        if report_format.lower() == 'json':
            with open(safe_out, 'w', encoding='utf-8') as f:
                json.dump(groups, f, indent=2)
            return True
        else:
            with open(safe_out, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Group ID", "Signature", "Match Type", "Similarity %",
                    "Is Original", "File Name", "File Path", "Size Bytes",
                    "Size Str", "Modification Date", "Resolution"
                ])
                for g in groups:
                    g_id = g.get('group_id', '')
                    sig = g.get('signature', '')
                    match_mode = g.get('match_mode', '')
                    for f_item in g.get('files', []):
                        writer.writerow([
                            g_id,
                            sig,
                            match_mode,
                            f_item.get('match_percent', 100.0),
                            "YES" if f_item.get('is_original') else "NO",
                            f_item.get('filename', ''),
                            f_item.get('path', ''),
                            f_item.get('size_bytes', 0),
                            f_item.get('size_str', ''),
                            f_item.get('mtime_str', ''),
                            f_item.get('res_str', 'N/A')
                        ])
            return True
    except Exception:
        return False


def scan_directory_preview(
    main_folder,
    sort_category='date',
    recursive=True,
    date_source='ctime',
    structure_format='YYYY/MM',
    include_exts=None,
    exclude_exts=None,
    exclude_folders=None,
    exclude_files=None,
    isolate_duplicates=False,
    dest_folder=None,
    selected_files=None,
    random_folder_name="_Random",
    unsorted_subdivide='none'
):
    """
    Generates a full preview array of proposed file moves, stats, and duplicate analysis.
    Does NOT modify files on disk.
    """
    if not selected_files:
        if not main_folder or not str(main_folder).strip():
            return [], {}, {"total_files": 0, "total_size_bytes": 0, "duplicate_count": 0}


    files = gather_files(main_folder, recursive, include_exts, exclude_exts, exclude_folders, exclude_files, selected_files=selected_files)

    seen_hashes = {}
    duplicates = set()

    if isolate_duplicates:
        for fp in files:
            h = get_file_hash(fp)
            if h:
                if h in seen_hashes:
                    duplicates.add(fp)
                else:
                    seen_hashes[h] = fp

    preview_items = []
    category_counts = {}
    total_bytes = 0

    base_dir = main_folder if main_folder else (os.path.dirname(files[0]) if files else os.getcwd())
    target_base = os.path.abspath(dest_folder) if (dest_folder and str(dest_folder).strip()) else base_dir

    for fp in files:
        filename = os.path.basename(fp)
        # Route zero-byte / unreadable files for review (flagged, not moved here — just marked)
        try:
            _file_size_bytes = os.path.getsize(fix_win_long_path(fp))
        except Exception:
            _file_size_bytes = -1
        cat = get_file_category(filename)
        category_counts[cat] = category_counts.get(cat, 0) + 1

        try:
            sz = os.path.getsize(fix_win_long_path(fp))
        except Exception:
            sz = 0
        total_bytes += sz

        is_dup = fp in duplicates
        target_dir = get_destination_folder(
            base_dir, fp, sort_category, date_source, structure_format, is_dup, isolate_duplicates, dest_folder=dest_folder, random_folder_name=random_folder_name
        )
        target_path = os.path.join(target_dir, filename)
        rel_target = os.path.relpath(target_dir, target_base)

        status_str = "DUPLICATE" if is_dup else "Ready"
        if os.path.exists(fix_win_long_path(target_path)) and os.path.abspath(os.path.dirname(fp)) != os.path.abspath(target_dir):
            status_str = "WILL SKIP (Target Exists)"

        is_rand, rand_reason = is_random_or_hash_name(filename)

        preview_items.append({
            "filename": filename,
            "src": fp,
            "rel_src": os.path.relpath(fp, base_dir) if base_dir else filename,
            "target_dir": target_dir,
            "target_path": target_path,
            "rel_target": rel_target,
            "category": cat,
            "size_str": format_bytes(sz),
            "size_bytes": sz,
            "is_duplicate": is_dup,
            "status_str": status_str,
            "is_random": is_rand,
            "classification_reason": rand_reason
        })

    summary = {
        "total_files": len(files),
        "total_size_bytes": total_bytes,
        "total_size_str": format_bytes(total_bytes),
        "duplicate_count": len(duplicates),
        "category_counts": category_counts
    }

    return preview_items, category_counts, summary


def _force_remove_file(file_path):
    safe_path = fix_win_long_path(file_path)
    try:
        import stat
        os.chmod(safe_path, stat.S_IWRITE | stat.S_IREAD)
    except Exception:
        pass
    try:
        os.remove(safe_path)
        return True
    except Exception:
        return False


def _force_rmdir(dir_path):
    safe_path = fix_win_long_path(dir_path)
    try:
        import stat
        os.chmod(safe_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    except Exception:
        pass
    try:
        os.rmdir(safe_path)
        return True
    except Exception:
        return False


def clean_empty_dirs(folder, remove_os_junk=True, max_passes=10, exclude_folders=None):
    """
    Recursively removes empty directories within folder.
    """
    if not folder:
        return 0
    folder = os.path.abspath(str(folder).strip().strip('\'"'))
    if not os.path.isdir(fix_win_long_path(folder)):
        return 0

    merged_excludes = list(DEFAULT_EXCLUDED_FOLDERS)
    if exclude_folders:
        if isinstance(exclude_folders, (list, tuple, set)):
            merged_excludes.extend(list(exclude_folders))
        elif isinstance(exclude_folders, str):
            merged_excludes.extend([p.strip() for p in exclude_folders.replace(',', ';').split(';') if p.strip()])

    OS_JUNK_FILES = {'desktop.ini', 'thumbs.db', '.ds_store', '.bridgeortcache', '.bridgeortcachet'}

    cleaned_count = 0
    pass_count = 0

    while pass_count < max_passes:
        pass_count += 1
        removed_in_pass = 0
        for root, dirs, files in os.walk(folder, topdown=False):
            if os.path.abspath(root) == os.path.abspath(folder):
                continue

            if is_path_excluded(root, merged_excludes, base_folder=folder):
                continue

            safe_root = fix_win_long_path(root)
            try:
                entries = os.listdir(safe_root)
                if remove_os_junk:
                    non_junk_files = [f for f in entries if f.lower() not in OS_JUNK_FILES]
                    if not non_junk_files:
                        for item in entries:
                            item_path = os.path.join(root, item)
                            try:
                                _force_remove_file(item_path)
                            except Exception:
                                pass
                        entries = os.listdir(safe_root)

                if not entries:
                    if _force_rmdir(root):
                        removed_in_pass += 1
                        cleaned_count += 1
            except Exception:
                pass

        if removed_in_pass == 0:
            break

    return cleaned_count


def scan_empty_dirs_preview(folder, remove_os_junk=True, exclude_folders=None):
    """
    Scans folder directory tree and returns a list of empty (or OS-junk-only) directories for preview.
    Does NOT delete any directories on disk.
    """
    if not folder:
        return []
    folder = os.path.abspath(str(folder).strip().strip('\'"'))
    if not os.path.isdir(fix_win_long_path(folder)):
        return []

    merged_excludes = list(DEFAULT_EXCLUDED_FOLDERS)
    if exclude_folders:
        if isinstance(exclude_folders, (list, tuple, set)):
            merged_excludes.extend(list(exclude_folders))
        elif isinstance(exclude_folders, str):
            merged_excludes.extend([p.strip() for p in exclude_folders.replace(',', ';').split(';') if p.strip()])

    OS_JUNK_FILES = {'desktop.ini', 'thumbs.db', '.ds_store', '.bridgeortcache', '.bridgeortcachet'}
    known_empty_dirs = set()
    empty_folders = []

    for pass_num in range(10):
        found_new = False
        for root, dirs, files in os.walk(folder, topdown=False):
            if os.path.abspath(root) == os.path.abspath(folder):
                continue

            if is_path_excluded(root, merged_excludes, base_folder=folder):
                continue

            abs_root = os.path.abspath(root)
            if abs_root in known_empty_dirs:
                continue

            safe_root = fix_win_long_path(root)
            try:
                entries = os.listdir(safe_root)
                active_subdirs = [d for d in entries if os.path.isdir(os.path.join(root, d)) and os.path.abspath(os.path.join(root, d)) not in known_empty_dirs]

                if active_subdirs:
                    continue

                remaining_files = [f for f in entries if os.path.isfile(os.path.join(root, f))]

                is_empty = False
                reason = ""
                if not remaining_files:
                    is_empty = True
                    reason = "0 Files / 0 Subfolders"
                elif remove_os_junk:
                    non_junk = [f for f in remaining_files if f.lower() not in OS_JUNK_FILES]
                    if not non_junk:
                        is_empty = True
                        junk_names = ", ".join(f for f in remaining_files)
                        reason = f"Only OS Junk ({junk_names})"

                if is_empty:
                    known_empty_dirs.add(abs_root)
                    empty_folders.append({
                        "path": root,
                        "folder_name": os.path.basename(root),
                        "rel_path": os.path.relpath(root, folder),
                        "reason": reason
                    })
                    found_new = True
            except Exception:
                pass

        if not found_new:
            break

    empty_folders.sort(key=lambda x: x['path'].count(os.sep), reverse=True)
    return empty_folders


def delete_empty_folder_batch(folder_paths, remove_os_junk=True, exclude_folders=None):
    """
    Deletes a specific list of empty directory paths safely.
    """
    if not folder_paths:
        return {"deleted": 0, "errors": 0}

    merged_excludes = list(DEFAULT_EXCLUDED_FOLDERS)
    if exclude_folders:
        if isinstance(exclude_folders, (list, tuple, set)):
            merged_excludes.extend(list(exclude_folders))
        elif isinstance(exclude_folders, str):
            merged_excludes.extend([p.strip() for p in exclude_folders.replace(',', ';').split(';') if p.strip()])

    OS_JUNK_FILES = {'desktop.ini', 'thumbs.db', '.ds_store', '.bridgeortcache', '.bridgeortcachet'}
    deleted = 0
    errors = 0

    sorted_paths = sorted(folder_paths, key=lambda x: os.path.abspath(x).count(os.sep), reverse=True)

    for fp in sorted_paths:
        if is_path_excluded(fp, merged_excludes):
            continue
        safe_fp = fix_win_long_path(fp)
        if not os.path.isdir(safe_fp):
            continue
        try:
            entries = os.listdir(safe_fp)
            if remove_os_junk:
                for item in entries:
                    item_path = os.path.join(fp, item)
                    if item.lower() in OS_JUNK_FILES:
                        _force_remove_file(item_path)
                entries = [e for e in os.listdir(safe_fp) if e.lower() not in OS_JUNK_FILES]
            
            if not entries:
                if _force_rmdir(fp):
                    deleted += 1
                else:
                    errors += 1
            else:
                errors += 1
        except Exception:
            errors += 1

    return {"deleted": deleted, "errors": errors}


def organize_directory(
    main_folder,
    sort_category='date',
    recursive=True,
    date_source='ctime',
    structure_format='YYYY/MM',
    include_exts=None,
    exclude_exts=None,
    exclude_folders=None,
    exclude_files=None,
    mode='move',
    dry_run=False,
    clean_empty=False,
    isolate_duplicates=False,
    dest_folder=None,
    enable_zip_backup=False,
    on_conflict='skip',
    conflict_resolver_callback=None,
    progress_callback=None,
    selected_files=None,
    skipped_handling='stay',
    skipped_dest_folder=None,
    random_folder_name="_Random",
    unsorted_subdivide='none',
    iso_date_prefix=False,
    route_corrupted=False,
    corrupted_folder_name='Review_Corrupted'
):
    """
    Scans and organizes files safely. Supports selected_files list and smart_name matching.
    """
    if not selected_files:
        main_folder = os.path.abspath(main_folder) if main_folder else None
        if not main_folder or not os.path.isdir(fix_win_long_path(main_folder)):
            raise ValueError(f"Directory non-existent: {main_folder}")

    files_to_process = gather_files(main_folder, recursive, include_exts, exclude_exts, exclude_folders, exclude_files, selected_files=selected_files)
    total_files = len(files_to_process)

    base_folder = main_folder if main_folder else (os.path.dirname(files_to_process[0]) if files_to_process else os.getcwd())

    zip_backup_path = None
    if enable_zip_backup and not dry_run and files_to_process:
        zip_backup_path, _ = create_safety_backup_zip(base_folder, files_to_process, progress_callback=progress_callback)

    seen_hashes = {}
    duplicates = set()
    if isolate_duplicates:
        for fp in files_to_process:
            h = get_file_hash(fp)
            if h:
                if h in seen_hashes:
                    duplicates.add(fp)
                else:
                    seen_hashes[h] = fp

    operations = []
    skipped_errors = []
    stats = {
        'total': total_files,
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'duplicates_found': len(duplicates),
        'mode': mode,
        'sort_category': sort_category,
        'dry_run': dry_run,
        'zip_backup': zip_backup_path,
        'skipped_errors': skipped_errors,
        'cleaned_empty_folders': 0
    }

    target_base = os.path.abspath(dest_folder) if (dest_folder and str(dest_folder).strip()) else base_folder

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest_filename = f".date_sorter_manifest_{timestamp_str}.json"

    vault_manifest_path = os.path.join(get_system_vault_dir("Manifests"), manifest_filename)
    local_manifest_path = os.path.join(base_folder, manifest_filename)

    explicitly_skipped_or_errored_files = []

    for idx, file_path in enumerate(files_to_process, 1):
        safe_src = fix_win_long_path(file_path)
        try:
            if not os.path.exists(safe_src):
                stats['skipped'] += 1
                explicitly_skipped_or_errored_files.append(file_path)
                continue

            is_dup = file_path in duplicates

            # Route zero-byte / corrupted files to Review_Corrupted folder (opt-in)
            try:
                _sz = os.path.getsize(safe_src)
            except Exception:
                _sz = -1
            if route_corrupted and _sz == 0:
                target_dir = os.path.join(
                    os.path.abspath(dest_folder) if (dest_folder and str(dest_folder).strip()) else base_folder,
                    corrupted_folder_name
                )
            else:
                target_dir = get_destination_folder(
                    base_folder, file_path, sort_category, date_source, structure_format,
                    is_dup, isolate_duplicates, dest_folder=dest_folder,
                    random_folder_name=random_folder_name, unsorted_subdivide=unsorted_subdivide
                )
            filename = os.path.basename(file_path)

            # ISO date prefix renaming (opt-in, smart_name mode)
            if iso_date_prefix and sort_category in ('smart_name', 'name', 'full_name'):
                try:
                    date_obj = get_file_date(file_path, date_source)
                    date_prefix = f"{date_obj.year:04d}-{date_obj.month:02d}-{date_obj.day:02d}_"
                    stem, ext = os.path.splitext(filename)
                    # Only add prefix if not already prefixed with an ISO date
                    if not re.match(r'^\d{4}-\d{2}-\d{2}_', stem):
                        filename = f"{date_prefix}{stem}{ext}"
                except Exception:
                    pass

            if os.path.abspath(os.path.dirname(file_path)) == os.path.abspath(target_dir):
                stats['skipped'] += 1
                if progress_callback:
                    progress_callback(idx, total_files, file_path, "Skipped (Already in target folder)", "skipped")
                continue

            target_path = os.path.join(target_dir, filename)
            safe_dst = fix_win_long_path(target_path)

            if os.path.exists(safe_dst):
                conflict_choice = on_conflict
                if conflict_choice == 'ask' and conflict_resolver_callback:
                    conflict_choice = conflict_resolver_callback(file_path, target_path)

                if conflict_choice == 'number':
                    target_path = resolve_filename_collision(target_dir, filename)
                    safe_dst = fix_win_long_path(target_path)
                elif conflict_choice == 'replace':
                    vault_trash = get_system_vault_dir("TrashDuplicates")
                    trash_path = os.path.join(vault_trash, f"{os.path.splitext(filename)[0]}_{int(time.time())}{os.path.splitext(filename)[1]}")
                    try:
                        shutil.move(safe_dst, fix_win_long_path(trash_path))
                    except Exception:
                        pass
                else:
                    stats['skipped'] += 1
                    explicitly_skipped_or_errored_files.append(file_path)
                    if progress_callback:
                        progress_callback(idx, total_files, file_path, f"Skipped (File with same name already exists in {os.path.relpath(target_dir, target_base)})", "skipped")
                    continue

            op_record = {
                "src": file_path,
                "dst": target_path,
                "target_dir": target_dir,
                "mode": mode,
                "filename": filename,
                "is_duplicate": is_dup
            }

            if not dry_run:
                os.makedirs(fix_win_long_path(target_dir), exist_ok=True)
                if mode == 'move':
                    shutil.move(safe_src, safe_dst)
                else:
                    shutil.copy2(safe_src, safe_dst)

            operations.append(op_record)
            stats['processed'] += 1
            if progress_callback:
                status_type = "dryrun" if dry_run else "success"
                status_msg = f"[DRY RUN] Would {mode}" if dry_run else f"Successfully {mode}d"
                if is_dup:
                    status_msg += " (DUPLICATE)"
                progress_callback(idx, total_files, file_path, f"{status_msg} -> {os.path.relpath(target_path, target_base)}", status_type)

        except Exception as e:
            stats['errors'] += 1
            explicitly_skipped_or_errored_files.append(file_path)
            err_entry = {
                "file": file_path,
                "filename": os.path.basename(file_path),
                "error": str(e)
            }
            skipped_errors.append(err_entry)
            if progress_callback:
                progress_callback(idx, total_files, file_path, f"⚠️ SKIPPED ERROR: {str(e)}", "error")

    # Move ONLY explicitly errored/skipped files if skipped_handling is enabled
    if skipped_handling != 'stay' and not dry_run and explicitly_skipped_or_errored_files:
        if skipped_dest_folder and str(skipped_dest_folder).strip():
            skip_target = os.path.abspath(skipped_dest_folder)
        elif base_folder:
            skip_target = os.path.join(base_folder, "_Skipped_Files")
        else:
            skip_target = None

        if skip_target:
            moved_skipped_count = 0
            for fp in explicitly_skipped_or_errored_files:
                safe_fp = fix_win_long_path(fp)
                if not os.path.exists(safe_fp) or is_manifest_file(os.path.basename(fp)):
                    continue
                try:
                    f_name = os.path.basename(fp)
                    dst_fp = resolve_filename_collision(skip_target, f_name)
                    os.makedirs(fix_win_long_path(skip_target), exist_ok=True)
                    shutil.move(safe_fp, fix_win_long_path(dst_fp))
                    moved_skipped_count += 1
                    operations.append({
                        "src": fp,
                        "dst": dst_fp,
                        "target_dir": skip_target,
                        "mode": "move",
                        "filename": f_name,
                        "is_duplicate": False,
                        "is_skipped_move": True
                    })
                    if progress_callback:
                        progress_callback(total_files, total_files, fp, f"📁 Moved Error/Skipped File -> {os.path.basename(dst_fp)}", "info")
                except Exception:
                    pass
            stats['moved_skipped_files'] = moved_skipped_count

    if clean_empty and recursive and not dry_run and base_folder:
        cleaned_dirs = clean_empty_dirs(base_folder, exclude_folders=exclude_folders)
        stats['cleaned_empty_folders'] = cleaned_dirs
        if progress_callback and cleaned_dirs > 0:
            progress_callback(total_files, total_files, base_folder, f"🧹 Cleaned {cleaned_dirs} empty folder(s)", "info")


    manifest_data = {
        "timestamp": timestamp_str,
        "main_folder": base_folder,
        "dest_folder": dest_folder,
        "mode": mode,
        "sort_category": sort_category,
        "structure_format": structure_format,
        "zip_backup": zip_backup_path,
        "operations": operations,
        "skipped_errors": skipped_errors
    }

    if not dry_run and operations:
        try:
            with open(fix_win_long_path(vault_manifest_path), 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2)
            try:
                with open(fix_win_long_path(local_manifest_path), 'w', encoding='utf-8') as f:
                    json.dump(manifest_data, f, indent=2)
                hide_path_windows(local_manifest_path)
            except Exception:
                pass
            stats['manifest'] = vault_manifest_path
        except Exception as e:
            stats['manifest_error'] = str(e)

    return stats, manifest_data


def organize_by_name(
    folder,
    dest_folder=None,
    dry_run=True,
    random_folder_name="_Random",
    mode='move',
    on_conflict='number',
    selected_files=None,
    recursive=True,
    exclude_folders=None,
    exclude_files=None,
    progress_callback=None,
    unsorted_subdivide='none',
    iso_date_prefix=False,
    route_corrupted=False,
    corrupted_folder_name='Review_Corrupted'
):
    """
    Dedicated high-performance Smart Word-Based Sorter:
      1. Extracts first meaningful alphabetical word (e.g. 'amazon', 'guru', 'invoice').
      2. Creates ONE folder per unique word (e.g. 'amazon/', 'guru/').
      3. All files without a meaningful word are routed to ONE shared catch-all folder (default: '_Random'),
         optionally subdivided by file type ('type') or modification month ('date').
      4. Optional ISO date prefix renaming: 'YYYY-MM-DD_filename.ext'.
      5. Optional routing of zero-byte / corrupted files to 'Review_Corrupted/'.
      6. Dry-run support by default, safe non-overwriting collision handling, and full audit logging.
    """
    return organize_directory(
        main_folder=folder,
        sort_category='smart_name',
        recursive=recursive,
        exclude_folders=exclude_folders,
        exclude_files=exclude_files,
        mode=mode,
        dry_run=dry_run,
        dest_folder=dest_folder,
        on_conflict=on_conflict,
        selected_files=selected_files,
        random_folder_name=random_folder_name,
        progress_callback=progress_callback,
        unsorted_subdivide=unsorted_subdivide,
        iso_date_prefix=iso_date_prefix,
        route_corrupted=route_corrupted,
        corrupted_folder_name=corrupted_folder_name
    )


def generate_smart_name_plan(folder, random_folder_name="_Random", unsorted_subdivide='none',
                             recursive=True, exclude_folders=None, exclude_files=None,
                             route_corrupted=False, selected_files=None):
    """
    Step 5 of the File Sorting Super Prompt: generates a structured plan BEFORE execution.
    Returns a dict with:
      - 'proposed_folders': list of {name, file_count, sample_files} for Type A/C (meaningful) folders
      - 'unsorted_count': total count of random/hash-named files going to Unsorted
      - 'unsorted_breakdown': dict of sub-folder -> count (populated when unsorted_subdivide != 'none')
      - 'review_needed': list of {path, reason} for files requiring manual review (zero-byte, no name)
      - 'total_files': total files scanned
    Does NOT modify the filesystem.
    """
    from collections import defaultdict

    files = gather_files(
        folder,
        recursive=recursive,
        exclude_folders=exclude_folders,
        exclude_files=exclude_files,
        selected_files=selected_files
    )

    proposed_folders = defaultdict(list)   # folder_name -> [filename, ...]
    unsorted_breakdown = defaultdict(int)  # sub_folder -> count
    review_needed = []                     # [{path, reason}]
    unsorted_count = 0

    for fp in files:
        filename = os.path.basename(fp)
        # Zero-byte / corrupted check
        try:
            sz = os.path.getsize(fix_win_long_path(fp))
        except Exception:
            sz = -1

        if route_corrupted and sz == 0:
            review_needed.append({'path': fp, 'reason': 'Zero-byte / corrupted file'})
            continue

        if not filename or not os.path.splitext(filename)[0].strip():
            review_needed.append({'path': fp, 'reason': 'No usable filename (extension-only or empty)'})
            continue

        folder_name, is_random, reason = get_name_sort_folder(
            filename,
            random_folder_name=random_folder_name,
            filepath=fp,
            unsorted_subdivide=unsorted_subdivide
        )

        if is_random:
            unsorted_count += 1
            if unsorted_subdivide and unsorted_subdivide != 'none':
                sub = get_unsorted_subfolder(fp, unsorted_subdivide)
                unsorted_breakdown[sub] += 1
            else:
                unsorted_breakdown['(flat)'] += 1
        else:
            proposed_folders[folder_name].append(filename)

    # Build sorted proposed folder list
    proposed_list = [
        {
            'name': k,
            'file_count': len(v),
            'sample_files': v[:5]  # up to 5 sample names
        }
        for k, v in sorted(proposed_folders.items(), key=lambda x: x[0].lower())
    ]

    return {
        'proposed_folders': proposed_list,
        'unsorted_count': unsorted_count,
        'unsorted_breakdown': dict(unsorted_breakdown),
        'review_needed': review_needed,
        'total_files': len(files)
    }


def list_manifest_files(main_folder=None):
    """
    Finds all undo manifest files across BOTH System Vault AppData AND local folder.
    """
    search_dirs = [get_system_vault_dir("Manifests")]
    if main_folder and os.path.isdir(fix_win_long_path(main_folder)):
        search_dirs.append(os.path.abspath(main_folder))

    manifests = []
    seen_paths = set()

    for s_dir in search_dirs:
        safe_s_dir = fix_win_long_path(s_dir)
        if not os.path.isdir(safe_s_dir):
            continue
        try:
            entries = os.listdir(safe_s_dir)
        except Exception:
            entries = []

        for item in entries:
            if is_manifest_file(item):
                full_path = os.path.join(s_dir, item)
                safe_fp = fix_win_long_path(full_path)
                if safe_fp in seen_paths:
                    continue
                seen_paths.add(safe_fp)
                try:
                    with open(safe_fp, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        manifests.append({
                            "path": full_path,
                            "filename": item,
                            "timestamp": data.get("timestamp"),
                            "main_folder": data.get("main_folder"),
                            "count": len(data.get("operations", [])),
                            "zip_backup": data.get("zip_backup"),
                            "errors_count": len(data.get("skipped_errors", []))
                        })
                except Exception:
                    pass

    manifests.sort(key=lambda x: x['timestamp'], reverse=True)
    return manifests


def undo_manifest(manifest_path, progress_callback=None):
    """
    Reverses operations recorded in a manifest file.
    """
    manifest_path = os.path.abspath(manifest_path)
    safe_manifest = fix_win_long_path(manifest_path)

    if not os.path.isfile(safe_manifest):
        raise ValueError(f"Manifest file not found: {manifest_path}")

    with open(safe_manifest, 'r', encoding='utf-8') as f:
        data = json.load(f)

    operations = data.get("operations", [])
    total = len(operations)
    mode = data.get("mode", "move")

    stats = {
        "total": total,
        "undone": 0,
        "errors": 0
    }

    for idx, op in enumerate(reversed(operations), 1):
        src = op["src"]
        dst = op["dst"]
        safe_src = fix_win_long_path(src)
        safe_dst = fix_win_long_path(dst)
        try:
            if os.path.exists(safe_dst):
                if mode == "move":
                    os.makedirs(os.path.dirname(safe_src), exist_ok=True)
                    shutil.move(safe_dst, safe_src)
                elif mode == "copy":
                    os.remove(safe_dst)
                stats["undone"] += 1
                if progress_callback:
                    progress_callback(idx, total, dst, f"Restored -> {src}", "success")
            else:
                stats["errors"] += 1
                if progress_callback:
                    progress_callback(idx, total, dst, "File missing in sorted folder", "error")
        except Exception as e:
            stats["errors"] += 1
            if progress_callback:
                progress_callback(idx, total, dst, f"Undo error: {str(e)}", "error")

    try:
        os.remove(safe_manifest)
    except Exception:
        pass

    return stats


def batch_rename_files(
    file_paths,
    naming_pattern="{OriginalName}",
    case_transform="none",
    search_text="",
    replace_text="",
    prefix="",
    suffix="",
    progress_callback=None
):
    """
    Batch renames files based on custom pattern, case transformation, search/replace, prefix & suffix.
    """
    total = len(file_paths)
    renamed = 0
    errors = 0
    operations = []

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest_filename = f".date_sorter_manifest_{timestamp_str}.json"
    vault_manifest_path = os.path.join(get_system_vault_dir("Manifests"), manifest_filename)

    for idx, fp in enumerate(file_paths, 1):
        safe_fp = fix_win_long_path(fp)
        if not os.path.exists(safe_fp):
            continue

        dir_name = os.path.dirname(fp)
        old_filename = os.path.basename(fp)
        base_name, ext = os.path.splitext(old_filename)

        new_base = base_name

        if search_text:
            new_base = new_base.replace(search_text, replace_text)

        if case_transform == "upper":
            new_base = new_base.upper()
        elif case_transform == "lower":
            new_base = new_base.lower()
        elif case_transform == "title":
            new_base = new_base.title()
        elif case_transform == "camel":
            words = [w for w in re.split(r'[\s_\-]+', new_base) if w]
            if words:
                new_base = words[0].lower() + "".join(w.capitalize() for w in words[1:])

        date_obj = get_file_date(fp, 'ctime')
        cat = get_file_category(old_filename)

        new_name = naming_pattern.replace("{OriginalName}", new_base)
        new_name = new_name.replace("{YYYY}", f"{date_obj.year:04d}")
        new_name = new_name.replace("{MM}", f"{date_obj.month:02d}")
        new_name = new_name.replace("{DD}", f"{date_obj.day:02d}")
        new_name = new_name.replace("{Category}", cat)
        new_name = new_name.replace("{001}", f"{idx:03d}")

        final_filename = f"{prefix}{new_name}{suffix}{ext}"
        new_filepath = os.path.join(dir_name, final_filename)

        if new_filepath == fp:
            continue

        if os.path.exists(fix_win_long_path(new_filepath)):
            new_filepath = resolve_filename_collision(dir_name, final_filename)
            final_filename = os.path.basename(new_filepath)

        safe_new_fp = fix_win_long_path(new_filepath)

        try:
            shutil.move(safe_fp, safe_new_fp)
            renamed += 1
            operations.append({
                "src": fp,
                "dst": new_filepath,
                "filename": final_filename,
                "mode": "move"
            })
            if progress_callback:
                progress_callback(idx, total, fp, f"Renamed -> {final_filename}", "success")
        except Exception as e:
            errors += 1
            if progress_callback:
                progress_callback(idx, total, fp, f"Rename Error: {str(e)}", "error")

    if operations:
        manifest_data = {
            "timestamp": timestamp_str,
            "mode": "move",
            "operations": operations
        }
        with open(fix_win_long_path(vault_manifest_path), 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)

    return {"total": total, "renamed": renamed, "errors": errors, "manifest": vault_manifest_path if operations else None}


def scan_junk_and_large_files(folder, exclude_folders=None, exclude_files=None, exclude_exts=None):
    folders_list = []
    if folder and isinstance(folder, str):
        raw_parts = [p.strip() for p in folder.replace(',', ';').split(';') if p.strip()]
        for p in raw_parts:
            if os.path.isdir(fix_win_long_path(p)):
                folders_list.append(os.path.abspath(p))

    if not folders_list:
        return {"junk_files": [], "large_files": [], "total_junk_bytes": 0, "total_junk_size_str": "0.0 B"}

    JUNK_EXTS = {'.tmp', '.crdownload', '.part', '.log', '.bak', '.dmp', '.cache'}
    JUNK_NAMES = {'thumbs.db', '.ds_store', 'desktop.ini', 'ehthumbs.db'}

    junk_files = []
    large_files = []
    total_junk_bytes = 0

    exc_files_set = set(f.lower().strip() for f in exclude_files) if exclude_files else set()
    exc_ext_set = set(e.lower().strip() if e.startswith('.') else f".{e.lower().strip()}" for e in exclude_exts) if exclude_exts else set()

    for fld in folders_list:
        if is_path_excluded(fld, exclude_folders, base_folder=fld):
            continue
        for root, dirs, files in os.walk(fld):
            if is_path_excluded(root, exclude_folders, base_folder=fld):
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if not is_path_excluded(os.path.join(root, d), exclude_folders, base_folder=fld)]

            for f in files:
                fp = os.path.join(root, f)
                if is_path_excluded(fp, exclude_folders, base_folder=fld):
                    continue
                if exc_files_set and f.lower().strip() in exc_files_set:
                    continue
                ext = os.path.splitext(f)[1].lower()
                if exc_ext_set and ext in exc_ext_set:
                    continue

                safe_fp = fix_win_long_path(fp)
                try:
                    stat = os.stat(safe_fp)
                    sz = stat.st_size
                    mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue

                is_junk = (sz == 0) or (ext in JUNK_EXTS) or (f.lower() in JUNK_NAMES)

                if is_junk:
                    junk_files.append({
                        "path": fp,
                        "filename": f,
                        "size_bytes": sz,
                        "size_str": format_bytes(sz),
                        "mtime_str": mtime_str,
                        "rel_path": os.path.relpath(fp, fld),
                        "reason": "0-Byte File" if sz == 0 else f"Temp / OS Junk ({ext if ext else f})"
                    })
                    total_junk_bytes += sz
                elif sz >= 50 * 1024 * 1024:
                    large_files.append({
                        "path": fp,
                        "filename": f,
                        "size_bytes": sz,
                        "size_str": format_bytes(sz),
                        "mtime_str": mtime_str,
                        "rel_path": os.path.relpath(fp, fld),
                        "category": get_file_category(f)
                    })

    large_files.sort(key=lambda x: x['size_bytes'], reverse=True)

    return {
        "junk_files": junk_files,
        "large_files": large_files[:100],
        "total_junk_bytes": total_junk_bytes,
        "total_junk_size_str": format_bytes(total_junk_bytes)
    }


def analyze_storage_insights(folder, exclude_folders=None, exclude_files=None, exclude_exts=None):
    """
    Calculates detailed category breakdown, date range span, and largest subfolders.
    """
    folder = os.path.abspath(folder)
    if not os.path.isdir(fix_win_long_path(folder)):
        return {}

    if is_path_excluded(folder, exclude_folders, base_folder=folder):
        return {}

    cat_bytes = {cat: 0 for cat in FILE_CATEGORIES.keys()}
    cat_bytes["Other"] = 0

    cat_counts = {cat: 0 for cat in FILE_CATEGORIES.keys()}
    cat_counts["Other"] = 0

    subfolder_sizes = {}
    total_bytes = 0
    total_files = 0

    oldest_file = None
    newest_file = None

    exc_files_set = set(f.lower().strip() for f in exclude_files) if exclude_files else set()
    exc_ext_set = set(e.lower().strip() if e.startswith('.') else f".{e.lower().strip()}" for e in exclude_exts) if exclude_exts else set()

    for root, dirs, files in os.walk(folder):
        if is_path_excluded(root, exclude_folders, base_folder=folder):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not is_path_excluded(os.path.join(root, d), exclude_folders, base_folder=folder)]

        rel_sub = os.path.relpath(root, folder)
        sub_key = rel_sub.split(os.sep)[0] if rel_sub != "." else "Root Level"

        for f in files:
            fp = os.path.join(root, f)
            if is_path_excluded(fp, exclude_folders, base_folder=folder):
                continue
            if exc_files_set and f.lower().strip() in exc_files_set:
                continue
            ext = os.path.splitext(f)[1].lower()
            if exc_ext_set and ext in exc_ext_set:
                continue

            safe_fp = fix_win_long_path(fp)
            try:
                stat = os.stat(safe_fp)
                sz = stat.st_size
                mtime = stat.st_mtime
            except Exception:
                continue

            total_bytes += sz
            total_files += 1

            cat = get_file_category(f)
            cat_bytes[cat] = cat_bytes.get(cat, 0) + sz
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

            subfolder_sizes[sub_key] = subfolder_sizes.get(sub_key, 0) + sz

            if oldest_file is None or mtime < oldest_file['mtime']:
                oldest_file = {"filename": f, "mtime": mtime, "date_str": datetime.fromtimestamp(mtime).strftime("%d-%m-%Y")}
            if newest_file is None or mtime > newest_file['mtime']:
                newest_file = {"filename": f, "mtime": mtime, "date_str": datetime.fromtimestamp(mtime).strftime("%d-%m-%Y")}

    top_subfolders = sorted([{"folder": k, "size_bytes": v, "size_str": format_bytes(v)} for k, v in subfolder_sizes.items()], key=lambda x: x['size_bytes'], reverse=True)[:10]

    category_percentages = {}
    for cat, b in cat_bytes.items():
        pct = (b / total_bytes * 100) if total_bytes > 0 else 0
        category_percentages[cat] = {
            "bytes": b,
            "size_str": format_bytes(b),
            "count": cat_counts[cat],
            "percentage": round(pct, 1)
        }

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_size_str": format_bytes(total_bytes),
        "categories": category_percentages,
        "top_subfolders": top_subfolders,
        "oldest_file": oldest_file,
        "newest_file": newest_file
    }


SYSTEM_EXCLUDED_EXTS = {
    ".dll", ".sys", ".dat", ".bin", ".ini", ".inf", ".cur", ".cat",
    ".manifest", ".msi", ".drv", ".ocx", ".ax", ".tmp", ".log", ".bak",
    ".edb", ".evtx", ".etl", ".pfx", ".cer", ".chk", ".dmp", ".sys"
}


def scan_folder_extensions(main_folder=None, selected_files=None, include_system=False, exclude_folders=None, exclude_files=None, exclude_exts=None):
    """
    Scans a directory or list of files and returns all unique file extensions present
    with count, size, and category. Excludes OS system files by default unless include_system=True.
    """
    ext_data = {}
    files_to_scan = []
    exc_files_set = set(f.lower().strip() for f in exclude_files) if exclude_files else set()
    exc_ext_set = set(e.lower().strip() if e.startswith('.') else f".{e.lower().strip()}" for e in exclude_exts) if exclude_exts else set()

    if selected_files:
        for fp in selected_files:
            if not is_path_excluded(fp, exclude_folders, base_folder=main_folder):
                files_to_scan.append(fp)
    elif main_folder:
        raw_parts = [p.strip() for p in str(main_folder).replace(',', ';').split(';') if p.strip()]
        for p in raw_parts:
            safe_p = fix_win_long_path(p)
            if os.path.isdir(safe_p):
                if is_path_excluded(safe_p, exclude_folders, base_folder=safe_p):
                    continue
                for root, dirs, files in os.walk(safe_p):
                    if is_path_excluded(root, exclude_folders, base_folder=safe_p):
                        dirs[:] = []
                        continue
                    dirs[:] = [d for d in dirs if not is_path_excluded(os.path.join(root, d), exclude_folders, base_folder=safe_p)]
                    for f in files:
                        fp = os.path.join(root, f)
                        if not is_path_excluded(fp, exclude_folders, base_folder=safe_p):
                            files_to_scan.append(fp)


    for fp in files_to_scan:
        name = os.path.basename(fp)
        ext = os.path.splitext(name)[1].lower()
        if not ext:
            ext = "[No Ext]"

        if not include_system and ext in SYSTEM_EXCLUDED_EXTS:
            continue


        safe_fp = fix_win_long_path(fp)
        sz = 0
        try:
            sz = os.path.getsize(safe_fp)
        except Exception:
            pass

        if ext not in ext_data:
            cat = get_file_category(name) if ext != "[No Ext]" else "Other"
            ext_data[ext] = {
                "ext": ext,
                "count": 0,
                "size_bytes": 0,
                "category": cat
            }

        ext_data[ext]["count"] += 1
        ext_data[ext]["size_bytes"] += sz

    result = list(ext_data.values())
    for item in result:
        item["size_str"] = format_bytes(item["size_bytes"])

    result.sort(key=lambda x: (x["count"], x["size_bytes"]), reverse=True)
    return result


class FolderWatcherService:
    def __init__(self, target_folder, sort_category="date", on_organized_callback=None):
        self.target_folder = os.path.abspath(target_folder)
        self.sort_category = sort_category
        self.on_organized_callback = on_organized_callback
        self.is_running = False
        self._thread = None
        self._seen_files = set()

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._seen_files = set(gather_files(self.target_folder, recursive=False))
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False

    def _watch_loop(self):
        while self.is_running:
            time.sleep(3)
            if not os.path.isdir(fix_win_long_path(self.target_folder)):
                continue

            current_files = set(gather_files(self.target_folder, recursive=False))
            new_files = current_files - self._seen_files

            if new_files:
                time.sleep(2)
                for fp in list(new_files):
                    if not os.path.exists(fix_win_long_path(fp)):
                        continue
                    try:
                        sz1 = os.path.getsize(fix_win_long_path(fp))
                        time.sleep(0.5)
                        sz2 = os.path.getsize(fix_win_long_path(fp))
                        if sz1 == sz2:
                            stats, _ = organize_directory(self.target_folder, sort_category=self.sort_category, recursive=False, mode='move')
                            if self.on_organized_callback:
                                self.on_organized_callback(stats)
                            break
                    except Exception:
                        pass
                self._seen_files = set(gather_files(self.target_folder, recursive=False))


def detect_file_format_by_magic(filepath):
    """
    Analyzes binary magic byte header of filepath to identify real file type, MIME category, and extension.
    Handles misnamed, raw header, 3GA, OPUS, VOB, HEIC, WEBP, and extension-less files.
    """
    safe_fp = fix_win_long_path(filepath)
    if not os.path.isfile(safe_fp):
        return {"category": "error", "ext": None, "format": "File Not Found"}

    try:
        with open(safe_fp, 'rb') as f:
            header = f.read(64)
        if not header:
            return {"category": "empty", "ext": ".empty", "format": "0-Byte Empty File"}
        if all(b == 0 for b in header):
            return {"category": "corrupt", "ext": ".corrupt", "format": "Null-Padded Corrupt / Empty File (All 0x00 Bytes)"}

        # 1. Image formats
        if header.startswith(b'\xff\xd8\xff'):
            return {"category": "image", "ext": ".jpg", "format": "JPEG Image"}
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return {"category": "image", "ext": ".png", "format": "PNG Image"}
        if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return {"category": "image", "ext": ".gif", "format": "GIF Image"}
        if header.startswith(b'BM'):
            return {"category": "image", "ext": ".bmp", "format": "BMP Image"}
        if header.startswith(b'RIFF') and b'WEBP' in header[8:16]:
            return {"category": "image", "ext": ".webp", "format": "WEBP Image"}
        if header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
            return {"category": "image", "ext": ".tif", "format": "TIFF Image"}
        if header.startswith(b'\x00\x00\x01\x00') or header.startswith(b'\x00\x00\x02\x00'):
            return {"category": "image", "ext": ".ico", "format": "ICO Icon"}

        # 2. Audio formats
        if header.startswith(b'OggS'):
            return {"category": "audio", "ext": ".opus", "format": "OGG/Opus Audio"}
        if header.startswith(b'ID3') or (len(header) > 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
            return {"category": "audio", "ext": ".mp3", "format": "MP3 Audio"}
        if header.startswith(b'RIFF') and b'WAVE' in header[8:16]:
            return {"category": "audio", "ext": ".wav", "format": "WAV Audio"}
        if header.startswith(b'#!AMR'):
            return {"category": "audio", "ext": ".amr", "format": "AMR Voice Audio"}
        if header.startswith(b'fLaC'):
            return {"category": "audio", "ext": ".flac", "format": "FLAC Audio"}

        # 3. Video / Media containers (MP4, 3GP, 3GA, M4A, MOV, MKV, AVI, FLV, VOB)
        if len(header) >= 12 and header[4:8] == b'ftyp':
            brand = header[8:12].lower()
            if b'3gp' in brand or b'3ga' in brand:
                return {"category": "audio", "ext": ".3ga", "format": "Samsung 3GA/3GP Audio"}
            elif b'm4a' in brand:
                return {"category": "audio", "ext": ".m4a", "format": "M4A Audio"}
            elif b'heic' in brand or b'heix' in brand or b'mif1' in brand:
                return {"category": "image", "ext": ".heic", "format": "HEIC Photo"}
            return {"category": "video", "ext": ".mp4", "format": "MP4 Video"}

        if header.startswith(b'\x1a\x45\xdf\xa3'):
            return {"category": "video", "ext": ".mkv", "format": "MKV/WEBM Video"}
        if header.startswith(b'RIFF') and b'AVI ' in header[8:16]:
            return {"category": "video", "ext": ".avi", "format": "AVI Video"}
        if header.startswith(b'FLV\x01'):
            return {"category": "video", "ext": ".flv", "format": "FLV Video"}
        if header.startswith(b'\x00\x00\x01\xba') or header.startswith(b'\x00\x00\x01\xb3'):
            return {"category": "video", "ext": ".vob", "format": "DVD VOB/MPEG Video"}

        # 4. Documents & Archives
        if header.startswith(b'%PDF'):
            return {"category": "document", "ext": ".pdf", "format": "PDF Document"}
        if header.startswith(b'PK\x03\x04'):
            return {"category": "archive", "ext": ".zip", "format": "ZIP Archive / Office Doc"}
        if header.startswith(b'Rar!\x1a\x07'):
            return {"category": "archive", "ext": ".rar", "format": "RAR Archive"}
        if header.startswith(b'7z\xbc\xaf\x27\x1c'):
            return {"category": "archive", "ext": ".7z", "format": "7Z Archive"}

        ext = os.path.splitext(filepath)[1].lower()
        cat = get_file_category(filepath)
        return {"category": cat.lower() if cat else "unknown", "ext": ext if ext else ".dat", "format": f"Generic ({ext if ext else 'Data'})"}
    except Exception as e:
        return {"category": "error", "ext": None, "format": str(e)}


def scan_converter_preview(main_folder=None, selected_files=None, conversion_mode="auto", target_format=None, exclude_folders=None):
    """
    Scans files and generates a conversion preview plan.
    Identifies misnamed extensions, audio/video/image conversion targets.
    """
    files_to_scan = []
    if selected_files:
        files_to_scan = [f for f in selected_files if not is_path_excluded(f, exclude_folders, base_folder=main_folder)]
    elif main_folder:
        files_to_scan = gather_files(main_folder, recursive=True, exclude_folders=exclude_folders)

    preview_items = []
    category_counts = {"audio": 0, "video": 0, "image": 0, "fix_ext": 0, "total": 0}

    AUDIO_EXTS = {'.3ga', '.opus', '.amr', '.ogg', '.wav', '.flac', '.m4a', '.wma', '.aac', '.ra', '.mid', '.midi', '.aiff', '.ape', '.wv', '.mka'}
    VIDEO_EXTS = {'.vob', '.3gp', '.mkv', '.avi', '.flv', '.webm', '.ts', '.mov', '.mpg', '.mpeg', '.m2ts', '.m4v', '.wmv', '.divx', '.ogv', '.f4v', '.rm', '.rmvb'}
    IMAGE_EXTS = {'.webp', '.heic', '.bmp', '.tiff', '.tif', '.ico', '.cur', '.tgs', '.psd', '.svg'}

    for fp in files_to_scan:
        fname = os.path.basename(fp)
        curr_ext = os.path.splitext(fname)[1].lower()
        info = detect_file_format_by_magic(fp)
        real_cat = info["category"]
        real_ext = info["ext"]
        fmt_label = info["format"]

        action = None
        target_name = fname
        target_ext = curr_ext

        if real_cat in ["corrupt", "empty"]:
            action = f"⚠️ Unreadable / Corrupt File ({fmt_label})"
            target_name = "[Unreadable File]"
            target_ext = curr_ext
            category_counts["fix_ext"] += 1

        elif conversion_mode == "audio_to_mp3" or (conversion_mode == "auto" and (curr_ext in AUDIO_EXTS or real_cat == "audio")):
            if curr_ext != ".mp3":
                target_ext = ".mp3" if not target_format else target_format
                base_name = os.path.splitext(fname)[0]
                target_name = base_name + target_ext
                action = "🎵 Convert to MP3 Audio"
                category_counts["audio"] += 1

        elif conversion_mode == "video_to_mp4" or (conversion_mode == "auto" and (curr_ext in VIDEO_EXTS or real_cat == "video")):
            if curr_ext != ".mp4":
                target_ext = ".mp4" if not target_format else target_format
                base_name = os.path.splitext(fname)[0]
                target_name = base_name + target_ext
                action = "🎬 Convert to MP4 Video"
                category_counts["video"] += 1

        elif conversion_mode == "image_to_jpg" or (conversion_mode == "auto" and (curr_ext in IMAGE_EXTS or real_cat == "image")):
            if curr_ext not in [".jpg", ".jpeg", ".png"]:
                target_ext = ".jpg" if not target_format else target_format
                base_name = os.path.splitext(fname)[0]
                target_name = base_name + target_ext
                action = f"🖼️ Convert Image to {target_ext.upper()[1:]}"
                category_counts["image"] += 1

        if not action and real_ext and real_ext != curr_ext and real_ext != ".empty":
            if curr_ext in [".dat", ".tmp", ".bin", ".file", "", "[no ext]"] or not curr_ext or curr_ext.startswith(".~") or real_cat in ["image", "video", "audio", "document"]:
                base_name = os.path.splitext(fname)[0] if curr_ext else fname
                target_ext = real_ext
                target_name = base_name + target_ext
                action = f"🏷️ Fix Extension -> {real_ext}"
                category_counts["fix_ext"] += 1

        if action:
            rel_path = os.path.relpath(fp, main_folder) if main_folder else fname
            sz_str = format_bytes(os.path.getsize(fix_win_long_path(fp))) if os.path.exists(fix_win_long_path(fp)) else "0 B"
            category_counts["total"] += 1
            preview_items.append({
                "src": fp,
                "filename": fname,
                "rel_path": rel_path,
                "detected_format": fmt_label,
                "action": action,
                "target_name": target_name,
                "target_ext": target_ext,
                "size_str": sz_str,
                "status": "Ready to Convert" if "Unreadable" not in action else "Unreadable File"
            })

    return preview_items, category_counts


def convert_single_file(src_path, dest_dir=None, target_ext=".mp3", delete_original=False):
    """
    Converts or renames a single file to target format using PIL, multi-pass ffmpeg, OpenCV, or extension repair.
    """
    safe_src = fix_win_long_path(src_path)
    if not os.path.exists(safe_src):
        return False, "File does not exist"

    base_name = os.path.splitext(os.path.basename(src_path))[0]
    out_dir = dest_dir if dest_dir else os.path.dirname(src_path)
    out_path = resolve_filename_collision(out_dir, base_name + target_ext)
    safe_out = fix_win_long_path(out_path)

    os.makedirs(fix_win_long_path(out_dir), exist_ok=True)

    curr_ext = os.path.splitext(src_path)[1].lower()
    if curr_ext == target_ext.lower():
        if os.path.abspath(out_dir) == os.path.abspath(os.path.dirname(src_path)):
            return True, out_path
        try:
            shutil.copy2(safe_src, safe_out)
            if delete_original:
                try: os.remove(safe_src)
                except Exception: pass
            return True, out_path
        except Exception as e:
            return False, str(e)

    # Check for corrupt null-padded files (all 0x00 bytes)
    try:
        with open(safe_src, 'rb') as test_f:
            head_sample = test_f.read(64)
            if not head_sample or all(b == 0 for b in head_sample):
                return False, "File is corrupt or contains only 0x00 null bytes (incomplete download or corrupted file)."
    except Exception:
        pass

    startupinfo = None
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # 1. Image Conversions via PIL (Pillow) first
    if target_ext.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"]:
        try:
            from PIL import Image
            with Image.open(safe_src) as img:
                if target_ext.lower() in [".jpg", ".jpeg"] and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(safe_out)
            if os.path.exists(safe_out) and os.path.getsize(safe_out) > 0:
                if delete_original:
                    try: os.remove(safe_src)
                    except Exception: pass
                return True, out_path
        except Exception:
            pass

    # 2. Audio Conversions via ffmpeg
    if target_ext.lower() in [".mp3", ".wav", ".m4a", ".aac", ".ogg"]:
        cmd = ['ffmpeg', '-y', '-i', safe_src, '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', safe_out]
        try:
            ret = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            if ret.returncode == 0 and os.path.exists(safe_out) and os.path.getsize(safe_out) > 0:
                if delete_original:
                    try: os.remove(safe_src)
                    except Exception: pass
                return True, out_path
            else:
                return False, f"ffmpeg audio conversion failed: {ret.stderr or ret.stdout or 'Unknown error'}"
        except FileNotFoundError:
            return False, "ffmpeg not found in system PATH. Install ffmpeg for audio/video conversion."
        except Exception as e:
            return False, f"Audio conversion error: {str(e)}"

    # 3. Video Conversions via Multi-Pass ffmpeg & OpenCV (includes VOB, MKV, AVI, WEBM, MP4, 3GP, MOV, etc.)
    if target_ext.lower() in [".mp4", ".mkv", ".avi", ".webm"]:
        passes = [
            # Pass 1: Standard re-encode
            ['ffmpeg', '-y', '-i', safe_src, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', '-b:a', '192k', safe_out],
            # Pass 2: Timestamp generation & corrupt packet tolerance
            ['ffmpeg', '-y', '-fflags', '+genpts+discardcorrupt', '-err_detect', 'ignore_err', '-i', safe_src, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-c:a', 'aac', safe_out],
            # Pass 3: Stream copy
            ['ffmpeg', '-y', '-i', safe_src, '-c', 'copy', safe_out],
            # Pass 4: Default ffmpeg auto codec
            ['ffmpeg', '-y', '-i', safe_src, safe_out],
            # Pass 5: Video-only stream (if audio stream is corrupt or unsupported)
            ['ffmpeg', '-y', '-i', safe_src, '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-an', safe_out],
        ]

        last_err = "ffmpeg video conversion failed"
        for cmd in passes:
            try:
                ret = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
                if ret.returncode == 0 and os.path.exists(safe_out) and os.path.getsize(safe_out) > 0:
                    if delete_original:
                        try: os.remove(safe_src)
                        except Exception: pass
                    return True, out_path
                else:
                    if ret.stderr:
                        lines = [l.strip() for l in ret.stderr.strip().split('\n') if l.strip()]
                        if lines: last_err = lines[-1]
            except FileNotFoundError:
                return False, "ffmpeg not found in system PATH. Install ffmpeg for video conversion."
            except Exception as e:
                last_err = str(e)

        # Pass 6: OpenCV video transcode fallback if available
        try:
            import cv2
            cap = cv2.VideoCapture(safe_src)
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                if width > 0 and height > 0:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out_writer = cv2.VideoWriter(safe_out, fourcc, fps, (width, height))
                    frames_written = 0
                    while True:
                        ret_frame, frame = cap.read()
                        if not ret_frame: break
                        out_writer.write(frame)
                        frames_written += 1
                    cap.release()
                    out_writer.release()
                    if frames_written > 0 and os.path.exists(safe_out) and os.path.getsize(safe_out) > 0:
                        if delete_original:
                            try: os.remove(safe_src)
                            except Exception: pass
                        return True, out_path
        except Exception:
            pass

        return False, f"Video conversion failed: {last_err}"

    # 4. Image Conversions fallback via ffmpeg
    if target_ext.lower() in [".jpg", ".jpeg", ".png", ".bmp"]:
        cmd = ['ffmpeg', '-y', '-i', safe_src, safe_out]
        try:
            ret = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            if ret.returncode == 0 and os.path.exists(safe_out) and os.path.getsize(safe_out) > 0:
                if delete_original:
                    try: os.remove(safe_src)
                    except Exception: pass
                return True, out_path
        except Exception:
            pass

    # 5. Extension Repair / Copy fallback
    try:
        shutil.copy2(safe_src, safe_out)
        if delete_original:
            try: os.remove(safe_src)
            except Exception: pass
        return True, out_path
    except Exception as e:
        return False, str(e)


def run_converter_batch(preview_items, output_dir=None, delete_original=False, progress_callback=None, max_workers=1):
    """
    Runs batch conversion for a list of preview items with optional parallel thread pool.
    """
    import concurrent.futures

    total = len(preview_items)
    processed = 0
    errors = 0
    skipped_corrupt = 0
    converted_files = []

    if max_workers > 1 and total > 1:
        lock = threading.Lock()

        def process_item(item_info):
            nonlocal processed, errors, skipped_corrupt
            idx, item = item_info
            src = item["src"]
            target_ext = item["target_ext"]
            action = item.get("action", "")

            if "Unreadable" in action or "Corrupt" in action:
                with lock:
                    skipped_corrupt += 1
                if progress_callback:
                    progress_callback(idx, total, src, "⚠️ Skipped: File is corrupt / filled with 0x00 null bytes", "error")
                return None

            ok, res_msg = convert_single_file(src, dest_dir=output_dir, target_ext=target_ext, delete_original=delete_original)
            with lock:
                if ok:
                    processed += 1
                    converted_files.append(res_msg)
                else:
                    errors += 1

            if progress_callback:
                if ok:
                    progress_callback(idx, total, src, f"✓ Converted -> {os.path.basename(res_msg)}", "success")
                else:
                    progress_callback(idx, total, src, f"⚠️ Error: {res_msg}", "error")
            return res_msg if ok else None

        indexed_items = list(enumerate(preview_items, 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(executor.map(process_item, indexed_items))

    else:
        for idx, item in enumerate(preview_items, 1):
            src = item["src"]
            target_ext = item["target_ext"]
            action = item.get("action", "")

            if "Unreadable" in action or "Corrupt" in action:
                skipped_corrupt += 1
                if progress_callback:
                    progress_callback(idx, total, src, "⚠️ Skipped: File is corrupt / filled with 0x00 null bytes", "error")
                continue

            ok, res_msg = convert_single_file(src, dest_dir=output_dir, target_ext=target_ext, delete_original=delete_original)
            if ok:
                processed += 1
                converted_files.append(res_msg)
                if progress_callback:
                    progress_callback(idx, total, src, f"✓ Converted -> {os.path.basename(res_msg)}", "success")
            else:
                errors += 1
                if progress_callback:
                    progress_callback(idx, total, src, f"⚠️ Error: {res_msg}", "error")

    return {"processed": processed, "errors": errors, "skipped_corrupt": skipped_corrupt, "total": total, "converted_files": converted_files}

