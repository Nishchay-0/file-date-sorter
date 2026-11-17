"""
config.py — Centralized Configuration & Constants
Smart File Organizer Suite Pro

Defines global constant mappings, regex patterns, stopwords,
system thresholds, and configurable folder rules.
"""

import re
from typing import Dict, List, Pattern, Set

# Windows MAX_PATH threshold (default 260, safe margin at 240)
WIN_LONG_PATH_THRESHOLD: int = 240

# File chunk size for streaming reads and SHA-256 / MD5 hashing (64 KB)
FILE_CHUNK_SIZE: int = 65536

# Windows File Attribute bitmasks
FILE_ATTRIBUTE_READONLY: int = 0x00000001
FILE_ATTRIBUTE_HIDDEN: int = 0x00000002
FILE_ATTRIBUTE_SYSTEM: int = 0x00000004
FILE_ATTRIBUTE_DIRECTORY: int = 0x00000010
FILE_ATTRIBUTE_ARCHIVE: int = 0x00000020
FILE_ATTRIBUTE_SPARSE_FILE: int = 0x00000200
FILE_ATTRIBUTE_REPARSE_POINT: int = 0x00000400
FILE_ATTRIBUTE_OFFLINE: int = 0x00001000
FILE_ATTRIBUTE_RECALL_ON_OPEN: int = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS: int = 0x00400000
INVALID_FILE_ATTRIBUTES: int = 0xFFFFFFFF

# Common stopwords stripped only when they appear at the start of filenames
COMMON_STOPWORDS: Set[str] = {
    'the', 'a', 'an', 'this', 'that', 'these', 'those',
    'my', 'your', 'our', 'their', 'his', 'her', 'its'
}

# Single default random folder name for unclassifiable / hash / gibberish files
DEFAULT_RANDOM_FOLDER_NAME: str = "_Random"

# Pre-defined file category mappings
FILE_CATEGORIES: Dict[str, List[str]] = {
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

# Month names lookup
MONTH_NAMES: Dict[int, str] = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

# Protected directory names skipped during reorganization
DEFAULT_PROTECTED_DIRS: Set[str] = {
    '01_Numeric', '02_Standard', '03_Hashes',
    'indexed_folders', 'hash_folders', 'Unsorted', '_Random',
    '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
    'node_modules', '$RECYCLE.BIN', 'System Volume Information'
}

# Date detection regex patterns
DATE_REGEX_PATTERNS: List[Pattern] = [
    re.compile(r'(\d{4})[-_.](\d{2})[-_.](\d{2})'),       # YYYY-MM-DD
    re.compile(r'(\d{2})[-_.](\d{2})[-_.](\d{4})'),       # DD-MM-YYYY
    re.compile(r'(\d{4})(\d{2})(\d{2})'),                 # YYYYMMDD
    re.compile(r'IMG[-_](\d{8})[-_](\d{6})', re.I),       # IMG_YYYYMMDD_HHMMSS
    re.compile(r'VID[-_](\d{8})[-_](\d{6})', re.I),       # VID_YYYYMMDD_HHMMSS
]
