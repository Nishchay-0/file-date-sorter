"""
Settings Manager for Smart File Organizer Suite.
Persists watcher and application configuration to JSON.
"""

import os
import json
import sys

DEFAULT_SETTINGS = {
    "watched_folder": "",
    "sort_category": "date",
    "date_source": "ctime",
    "structure_format": "YYYY/MM",
    "auto_start_watcher": False,
    "debounce_seconds": 3.0,
    "batch_notification_interval": 300.0
}

def get_settings_dir():
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~/AppData/Local')
    else:
        base = os.path.expanduser('~/.config')
    settings_dir = os.path.join(base, "SmartFileOrganizer")
    os.makedirs(settings_dir, exist_ok=True)
    return settings_dir

def get_settings_filepath():
    return os.path.join(get_settings_dir(), "settings.json")

def load_settings():
    filepath = get_settings_filepath()
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                merged = dict(DEFAULT_SETTINGS)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)

def save_settings(settings):
    filepath = get_settings_filepath()
    try:
        current = load_settings()
        current.update(settings)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=2)
        return True
    except Exception:
        return False
