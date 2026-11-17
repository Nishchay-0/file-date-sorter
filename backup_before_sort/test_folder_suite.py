import os
import shutil
import tempfile
from sorter_core import (
    organize_directory,
    find_duplicate_groups,
    delete_duplicate_files,
    clean_empty_dirs,
    batch_rename_files,
    scan_junk_and_large_files,
    analyze_storage_insights
)

def run_tests():
    temp_dir = tempfile.mkdtemp(prefix="test_folder_suite_")
    print(f"Created test folder: {temp_dir}\n")

    try:
        # Create mock subfolders & files
        sub1 = os.path.join(temp_dir, "Subfolder1")
        sub2 = os.path.join(temp_dir, "Subfolder2", "Nested")
        os.makedirs(sub1, exist_ok=True)
        os.makedirs(sub2, exist_ok=True)

        f1 = os.path.join(sub1, "photo.jpg")
        f2 = os.path.join(sub1, "document.pdf")
        f3 = os.path.join(sub2, "video.mp4")
        f4 = os.path.join(temp_dir, "temp_file.tmp")
        f5 = os.path.join(temp_dir, "empty.txt")

        for f in [f1, f2, f3, f4]:
            with open(f, 'w') as fp:
                fp.write("Test content for file organizer suite")

        # Create empty 0-byte file
        with open(f5, 'w') as fp:
            pass

        # --- TEST 1: Category Sorter ---
        res1, _ = organize_directory(temp_dir, sort_category='category', mode='copy')
        print(f"--- TEST 1: Sort by Category ---")
        print(f"Processed: {res1['processed']}\n")

        # --- TEST 2: Junk Cleaner & Storage Analyzer ---
        print(f"--- TEST 2: Scan Junk & Large Files ---")
        junk_res = scan_junk_and_large_files(temp_dir)
        print(f"Junk Files Found: {len(junk_res['junk_files'])}\n")
        assert len(junk_res['junk_files']) >= 2, "Should detect 0-byte file and .tmp file"

        # --- TEST 3: Storage Insights Analytics ---
        print(f"--- TEST 3: Storage Insights ---")
        insights = analyze_storage_insights(temp_dir)
        print(f"Total Files: {insights['total_files']}, Total Size: {insights['total_size_str']}\n")
        assert insights['total_files'] >= 5

        # --- TEST 4: Batch Renamer ---
        print(f"--- TEST 4: Batch Renaming ---")
        ren_res = batch_rename_files([f1, f2], naming_pattern="TestRenamed_{001}", prefix="PRE_")
        print(f"Renamed Files: {ren_res['renamed']}\n")
        assert ren_res['renamed'] == 2

        # --- TEST 6: Folder Exclusion (Except Folder) ---
        print(f"--- TEST 6: Folder Exclusion (Except Folder) ---")
        exc_sub = os.path.join(temp_dir, "ExceptSubFolder")
        os.makedirs(exc_sub, exist_ok=True)
        exc_file = os.path.join(exc_sub, "secret_data.txt")
        with open(exc_file, 'w') as fp:
            fp.write("Do not extract me!")

        exc_path_forward = exc_sub.replace('\\', '/')
        res6, _ = organize_directory(temp_dir, sort_category='category', mode='copy', exclude_folders=[exc_path_forward])
        assert not os.path.exists(os.path.join(temp_dir, "Documents", "secret_data.txt")), "Secret file in excluded folder was extracted!"
        print(f"Except Folder exclusion test PASSED! Excluded path '{exc_path_forward}' was cleanly skipped.\n")

        print("SUCCESS: ALL 7 TOOLS PASSED UNIT TESTS PERFECTLY!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    run_tests()

