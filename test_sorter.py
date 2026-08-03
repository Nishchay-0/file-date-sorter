import os
import shutil
from sorter_core import (
    organize_directory,
    undo_manifest,
    list_manifest_files,
    find_duplicate_groups,
    delete_duplicate_files,
    clean_empty_dirs
)

def create_dummy_files():
    test_dir = os.path.abspath("test_folder_advanced")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    os.makedirs(os.path.join(test_dir, "sub1"), exist_ok=True)
    os.makedirs(os.path.join(test_dir, "sub2"), exist_ok=True)

    files = [
        os.path.join(test_dir, "alpha_doc.pdf"),
        os.path.join(test_dir, "sub1", "photo_beach.jpg"),
        os.path.join(test_dir, "sub2", "script_main.py"),
        os.path.join(test_dir, "notes.txt"),
        # Duplicates
        os.path.join(test_dir, "sub1", "alpha_doc_copy.pdf"),
        os.path.join(test_dir, "sub2", "photo_beach_dup.jpg")
    ]

    # Identical content for duplicates
    contents = {
        os.path.join(test_dir, "alpha_doc.pdf"): "pdf document payload",
        os.path.join(test_dir, "sub1", "alpha_doc_copy.pdf"): "pdf document payload",
        os.path.join(test_dir, "sub1", "photo_beach.jpg"): "image byte data",
        os.path.join(test_dir, "sub2", "photo_beach_dup.jpg"): "image byte data",
        os.path.join(test_dir, "sub2", "script_main.py"): "print('hello')",
        os.path.join(test_dir, "notes.txt"): "my notes"
    }

    for fp, content in contents.items():
        with open(fp, "w") as f:
            f.write(content)

    print(f"Created test folder: {test_dir}")
    return test_dir

def run_tests():
    test_dir = create_dummy_files()

    print("\n--- TEST 1: Sort by Category ---")
    stats_cat, _ = organize_directory(test_dir, sort_category='category', mode='move')
    print(f"Category Sort result: {stats_cat}")
    assert stats_cat['processed'] == 6

    manifests = list_manifest_files(test_dir)
    undo_stats = undo_manifest(manifests[0]['path'])
    assert undo_stats['undone'] == 6

    print("\n--- TEST 2: Find Duplicate Groups (SHA-256 Content Match) ---")
    groups = find_duplicate_groups(test_dir, match_mode='content', recursive=True)
    print(f"Found {len(groups)} duplicate groups")
    assert len(groups) == 2 # 2 pairs of duplicate files

    # Verify duplicate paths
    to_delete = []
    for g in groups:
        for f in g['files']:
            if not f['is_original']:
                to_delete.append(f['path'])

    assert len(to_delete) == 2

    print("\n--- TEST 3: Delete Duplicate Files ---")
    del_res = delete_duplicate_files(to_delete)
    print(f"Delete result: {del_res}")
    assert del_res['deleted'] == 2

    print("\n--- TEST 4: Clean Empty Directories ---")
    # Create empty nested directories with desktop.ini OS junk
    empty_sub = os.path.join(test_dir, "empty_parent", "empty_child")
    os.makedirs(empty_sub, exist_ok=True)
    with open(os.path.join(empty_sub, "desktop.ini"), "w") as f:
        f.write("[.ShellClassInfo]\nIconResource=C:\\Windows\\system32\\SHELL32.dll,4\n")

    cleaned = clean_empty_dirs(test_dir, remove_os_junk=True)
    print(f"Cleaned {cleaned} empty directories!")
    assert cleaned >= 2
    assert not os.path.exists(os.path.join(test_dir, "empty_parent"))

    # Clean up test folder
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("\nSUCCESS: ALL SORTING, DUPLICATE & EMPTY FOLDER CLEANUP TESTS PASSED!")

if __name__ == '__main__':
    run_tests()
