import os
import sys

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
