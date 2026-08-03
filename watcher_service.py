"""
Background Watcher Service for Smart File Organizer Suite.
Uses watchdog to monitor target directories, debounces in-progress file writes,
and delegates auto-sorting to sorter_core.organize_directory.
"""

import os
import sys
import time
import threading
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    Observer = None
    FileSystemEventHandler = object

from sorter_core import organize_directory, fix_win_long_path
from settings_manager import load_settings, save_settings


class FileDebounceHandler(FileSystemEventHandler):
    """Event handler that captures created/modified files for size-stabilization debouncing."""
    def __init__(self, watcher_service):
        super().__init__()
        self.service = watcher_service

    def on_created(self, event):
        if not event.is_directory:
            self.service.register_file_candidate(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.service.register_file_candidate(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.service.register_file_candidate(event.dest_path)


class FolderWatcherService:
    """
    Background folder monitoring service.
    Debounces file creation/modification events until file sizes stop changing
    and file locks are released, then triggers sorter_core.organize_directory.
    """
    def __init__(self, callback_notify=None):
        self.callback_notify = callback_notify
        self.watched_folder = ""
        self.sort_category = "date"
        self.date_source = "ctime"
        self.structure_format = "YYYY/MM"
        self.debounce_seconds = 3.0
        self.batch_interval_seconds = 60.0

        self.observer = None
        self.is_running = False
        self.pending_files = {}  # filepath -> {"last_size": int, "last_check": float, "stable_since": float}
        self.lock = threading.Lock()

        # Session Stats
        self.files_organized_count = 0
        self.batched_file_counter = 0
        self.last_batch_notify_time = time.time()
        self.worker_thread = None

    def register_file_candidate(self, filepath):
        safe_p = fix_win_long_path(filepath)
        if not os.path.exists(safe_p):
            return

        # Skip hidden OS files or files inside excluded sorting folders
        fname = os.path.basename(filepath)
        if fname.startswith('.') or fname in ['desktop.ini', 'Thumbs.db']:
            return
        if '_Duplicates' in filepath or 'System_Vault' in filepath:
            return

        now = time.time()
        try:
            sz = os.path.getsize(safe_p)
        except Exception:
            sz = -1

        with self.lock:
            if filepath not in self.pending_files:
                self.pending_files[filepath] = {
                    "last_size": sz,
                    "last_check": now,
                    "stable_since": now
                }
            else:
                entry = self.pending_files[filepath]
                if entry["last_size"] != sz or sz == -1:
                    entry["last_size"] = sz
                    entry["last_check"] = now
                    entry["stable_since"] = now
                else:
                    entry["last_check"] = now

    def _debounce_worker_loop(self):
        while self.is_running:
            time.sleep(0.5)
            now = time.time()
            ready_files = []

            with self.lock:
                for filepath, entry in list(self.pending_files.items()):
                    safe_p = fix_win_long_path(filepath)
                    if not os.path.exists(safe_p):
                        del self.pending_files[filepath]
                        continue

                    try:
                        current_sz = os.path.getsize(safe_p)
                    except Exception:
                        current_sz = -1

                    if current_sz == -1 or current_sz != entry["last_size"]:
                        entry["last_size"] = current_sz
                        entry["last_check"] = now
                        entry["stable_since"] = now
                        continue

                    # Check if size has been stable for >= debounce_seconds
                    stable_duration = now - entry["stable_since"]
                    if stable_duration >= self.debounce_seconds:
                        # Verify file is not locked for exclusive write
                        if self._is_file_readable(safe_p):
                            ready_files.append(filepath)
                            del self.pending_files[filepath]

            if ready_files:
                self._process_ready_files(ready_files)

            # Check batched notification flush
            self._check_batch_notification_flush()

    def _is_file_readable(self, filepath):
        try:
            with open(filepath, 'rb') as f:
                f.read(1)
            return True
        except Exception:
            return False

    def _process_ready_files(self, ready_files):
        if not self.watched_folder or not os.path.exists(self.watched_folder):
            return

        for fpath in ready_files:
            try:
                parent_dir = os.path.dirname(fpath)
                stats, manifest = organize_directory(
                    main_folder=parent_dir,
                    selected_files=[fpath],
                    sort_category=self.sort_category,
                    date_source=self.date_source,
                    structure_format=self.structure_format,
                    mode='move'
                )
                processed = stats.get('processed', 0)
                if processed > 0:
                    self.files_organized_count += processed
                    self.batched_file_counter += processed
            except Exception as ex:
                if self.callback_notify:
                    self.callback_notify(f"[!] Auto-organize error on '{os.path.basename(fpath)}': {ex}")

    def _check_batch_notification_flush(self):
        now = time.time()
        if self.batched_file_counter > 0 and (now - self.last_batch_notify_time >= 15.0):
            msg = f"[AUTO WATCHER] Organized {self.batched_file_counter} new file(s) in '{os.path.basename(self.watched_folder)}'"
            if self.callback_notify:
                self.callback_notify(msg)
            self.batched_file_counter = 0
            self.last_batch_notify_time = now

    def start_watching(self, folder_path, sort_category="date", date_source="ctime", structure_format="YYYY/MM", debounce_seconds=3.0):
        if not HAS_WATCHDOG:
            raise RuntimeError("watchdog library is not installed.")

        safe_dir = fix_win_long_path(folder_path)
        if not os.path.exists(safe_dir):
            raise ValueError(f"Folder directory '{folder_path}' does not exist.")

        if self.is_running:
            self.stop_watching()

        self.watched_folder = os.path.abspath(folder_path)
        self.sort_category = sort_category
        self.date_source = date_source
        self.structure_format = structure_format
        self.debounce_seconds = float(debounce_seconds)

        event_handler = FileDebounceHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=self.watched_folder, recursive=False)
        self.observer.start()

        self.is_running = True
        self.last_batch_notify_time = time.time()
        self.batched_file_counter = 0

        self.worker_thread = threading.Thread(target=self._debounce_worker_loop, daemon=True)
        self.worker_thread.start()

        # Save active configuration to settings.json
        save_settings({
            "watched_folder": self.watched_folder,
            "sort_category": self.sort_category,
            "date_source": self.date_source,
            "structure_format": self.structure_format,
            "auto_start_watcher": True,
            "debounce_seconds": self.debounce_seconds
        })

        if self.callback_notify:
            self.callback_notify(f"[AUTO WATCHER] STARTED on '{self.watched_folder}' (Rule: {self.sort_category.upper()})")

        return True

    def stop_watching(self):
        self.is_running = False
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2.0)
            except Exception:
                pass
            self.observer = None

        save_settings({"auto_start_watcher": False})

        if self.callback_notify:
            self.callback_notify("[AUTO WATCHER] STOPPED.")

        return True
