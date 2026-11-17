"""
utils.py — Cross-Platform Path Utilities & System Helpers
Smart File Organizer Suite Pro
"""
import os
import sys
from typing import Optional, Union

# Windows MAX_PATH limitation threshold (default 260, safe margin at 240)
WIN_LONG_PATH_THRESHOLD: int = 240


def fix_win_long_path(path: Optional[Union[str, os.PathLike]]) -> str:
    """
    Safely cleans path quotes/whitespace and applies the appropriate Windows
    extended-length prefix (\\\\?\\ or \\\\?\\UNC\\) when path length >= 240.

    Handles:
      - Standard drive paths: C:\\path\\... -> \\\\?\\C:\\path\\...
      - UNC network paths:   \\\\server\\share\\... -> \\\\?\\UNC\\server\\share\\...
      - Already-prefixed paths: preserved as-is without double-prefixing
      - Non-Windows platforms: returned as standard normalized path

    Args:
        path: File or directory path string (or PathLike).

    Returns:
        Cleaned, normalized path string with long-path prefix on Windows if necessary.
    """
    if path is None:
        return ""

    if not isinstance(path, str):
        path = str(path)

    path = path.strip().strip('\'"')
    if not path:
        return ""

    if sys.platform == 'win32':
        try:
            # If already has extended-length prefix, return normalized
            if path.startswith("\\\\?\\") or path.startswith("//?/"):
                return path

            abs_path = os.path.abspath(path)

            if len(abs_path) >= WIN_LONG_PATH_THRESHOLD:
                # Handle UNC network shares: \\server\share\... -> \\?\UNC\server\share\...
                if abs_path.startswith("\\\\") and not abs_path.startswith("\\\\?\\"):
                    return "\\\\?\\UNC\\" + abs_path[2:]
                return "\\\\?\\" + abs_path

            return abs_path
        except Exception:
            return path

    return path


# ── Unified File-System Abstraction Layer ─────────────────────────────────────

def safe_exists(path: Optional[Union[str, os.PathLike]]) -> bool:
    """Checks whether a path exists, automatically applying Windows long-path normalization."""
    if not path:
        return False
    try:
        return os.path.exists(fix_win_long_path(path))
    except Exception:
        return False


def safe_isfile(path: Optional[Union[str, os.PathLike]]) -> bool:
    """Checks whether a path is an existing regular file with long-path support."""
    if not path:
        return False
    try:
        return os.path.isfile(fix_win_long_path(path))
    except Exception:
        return False


def safe_isdir(path: Optional[Union[str, os.PathLike]]) -> bool:
    """Checks whether a path is an existing directory with long-path support."""
    if not path:
        return False
    try:
        return os.path.isdir(fix_win_long_path(path))
    except Exception:
        return False


def safe_getsize(path: Optional[Union[str, os.PathLike]]) -> int:
    """Returns file size in bytes with long-path support, or 0 on error."""
    if not path:
        return 0
    try:
        return os.path.getsize(fix_win_long_path(path))
    except Exception:
        return 0


def safe_getmtime(path: Optional[Union[str, os.PathLike]]) -> float:
    """Returns modification timestamp with long-path support, or 0.0 on error."""
    if not path:
        return 0.0
    try:
        return os.path.getmtime(fix_win_long_path(path))
    except Exception:
        return 0.0


def safe_stat(path: Optional[Union[str, os.PathLike]]) -> Optional[os.stat_result]:
    """Returns os.stat_result with long-path support, or None on error."""
    if not path:
        return None
    try:
        return os.stat(fix_win_long_path(path))
    except Exception:
        return None


def safe_listdir(path: Optional[Union[str, os.PathLike]]) -> list[str]:
    """Lists directory contents with long-path support, or empty list on error."""
    if not path:
        return []
    try:
        return os.listdir(fix_win_long_path(path))
    except Exception:
        return []


def safe_scandir(path: Optional[Union[str, os.PathLike]]):
    """Returns os.scandir iterator with long-path support."""
    if not path:
        raise ValueError("Invalid path for safe_scandir")
    return os.scandir(fix_win_long_path(path))


def safe_remove(path: Optional[Union[str, os.PathLike]]) -> bool:
    """Safely removes a file, resetting read-only/hidden attributes on Windows if necessary."""
    if not path:
        return False
    safe_fp = fix_win_long_path(path)
    try:
        import stat
        os.chmod(safe_fp, stat.S_IWRITE | stat.S_IREAD)
    except Exception:
        pass
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(safe_fp), 0x80)  # FILE_ATTRIBUTE_NORMAL
        except Exception:
            pass
    try:
        os.remove(safe_fp)
        return True
    except Exception:
        return False


def safe_rmdir(path: Optional[Union[str, os.PathLike]]) -> bool:
    """Safely removes an empty directory, resetting attributes on Windows if necessary."""
    if not path:
        return False
    safe_fp = fix_win_long_path(path)
    try:
        import stat
        os.chmod(safe_fp, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    except Exception:
        pass
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(safe_fp), 0x80)  # FILE_ATTRIBUTE_NORMAL
        except Exception:
            pass
    try:
        os.rmdir(safe_fp)
        return True
    except Exception:
        return False

