"""
Unit Test Suite for Watcher Service & File Debouncing Logic.
Verifies that partially-written files are held during chunked writes and only
organized once file size stabilizes after the debounce window.
"""

import os
import sys
import time
import shutil
import tempfile
from datetime import datetime

from watcher_service import FolderWatcherService
from sorter_core import fix_win_long_path

def run_tests():
    print("==================================================")
    print("RUNNING WATCHER FILE DEBOUNCE TEST SUITE")
    print("==================================================")

    test_dir = tempfile.mkdtemp(prefix="test_watcher_debounce_")
    try:
        notifications = []
        def notify_cb(msg):
            notifications.append(msg)
            print(f"  [NOTIFICATION] {msg}")

        service = FolderWatcherService(callback_notify=notify_cb)
        debounce_sec = 1.0  # Use 1-second debounce window for fast unit testing

        print(f"\n[+] Starting Folder Watcher on '{test_dir}' (Debounce: {debounce_sec}s)...")
        service.start_watching(
            folder_path=test_dir,
            sort_category="category",
            debounce_seconds=debounce_sec
        )
        assert service.is_running is True

        # --- TEST 1: Chunked In-Progress File Write (Simulating active download) ---
        print("\n--- TEST 1: Simulating In-Progress Chunked File Copy ---")
        chunk_file = os.path.join(test_dir, "large_video_download.mp4")

        print("  [+] Writing Chunk 1/3 (10 KB)...")
        with open(chunk_file, "wb") as f:
            f.write(b"X" * 10240)
            f.flush()

        time.sleep(0.4)
        print("  [+] Writing Chunk 2/3 (+20 KB)...")
        with open(chunk_file, "ab") as f:
            f.write(b"Y" * 20480)
            f.flush()

        time.sleep(0.4)
        print("  [+] Writing Chunk 3/3 (+30 KB)...")
        with open(chunk_file, "ab") as f:
            f.write(b"Z" * 30720)
            f.flush()

        # Check that file has NOT been moved yet while actively being written
        print("  [+] Checking file status mid-write...")
        assert os.path.exists(chunk_file), "File should NOT be moved during active writing!"
        assert service.files_organized_count == 0, "No files should be organized yet while writing!"
        print("  [OK] Active writing test PASSED: File remained untouched in watch folder during chunked copy!")

        # --- TEST 2: Wait for Debounce Stabilization ---
        print("\n--- TEST 2: Waiting for File Size Stabilization & Auto-Organize ---")
        print(f"  [+] Waiting {debounce_sec + 0.8:.1f}s for debounce window to elapse...")
        time.sleep(debounce_sec + 0.8)

        expected_dest_folder = os.path.join(test_dir, "Videos", "MP4")
        expected_dest_file = os.path.join(expected_dest_folder, "large_video_download.mp4")

        print(f"  [+] Checking destination: '{expected_dest_file}'")
        assert os.path.exists(expected_dest_file), f"File should be organized into '{expected_dest_file}'"
        assert not os.path.exists(chunk_file), "Original file in root watch folder should be moved."
        assert service.files_organized_count >= 1, "Session organized count should be >= 1"

        print(f"  [OK] Debounce stabilization PASSED: File successfully auto-organized after size stabilized!")

        # --- TEST 3: Stopping Service ---
        print("\n--- TEST 3: Stopping Watcher Service ---")
        service.stop_watching()
        assert service.is_running is False
        print("  [OK] Service shutdown PASSED!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    print("\n==================================================")
    print("ALL WATCHER DEBOUNCE TESTS PASSED PERFECTLY!")
    print("==================================================\n")

if __name__ == "__main__":
    run_tests()
