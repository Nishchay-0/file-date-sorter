import os
import sys

def fix_win_long_path(path):
    """Safely cleans path and adds \\?\ prefix on Windows for long paths."""
    if not path:
        return path
    path = os.path.abspath(path).replace('"', '').strip()
    if sys.platform == 'win32' and not path.startswith('\\\\?\'):
        return '\\\\?\' + path
    return path
