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
