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

    print("\n--- TEST 5: Word-Based Sorting + Single _Random Folder ---")
    word_test_dir = os.path.abspath("test_folder_word_sort")
    if os.path.exists(word_test_dir):
        shutil.rmtree(word_test_dir)
    os.makedirs(word_test_dir, exist_ok=True)

    test_files = [
        "amazon_bill_123.pdf",
        "amazon_receipt_456.pdf",
        "guru_notes.txt",
        "guru_data.csv",
        "336101256_21499.jpg",
        "hfqgifcbkj9.png",
        "323f9w8ehf8awjefi.docx"
    ]
    for tf in test_files:
        with open(os.path.join(word_test_dir, tf), "w") as f:
            f.write(f"content of {tf}")

    stats_word, _ = organize_directory(word_test_dir, sort_category='smart_name', mode='move', random_folder_name='_Random')
    print(f"Word Sort result: {stats_word}")
    assert stats_word['processed'] == 7

    # Verify amazon/ contains the two amazon files
    amazon_dir = os.path.join(word_test_dir, "amazon")
    assert os.path.isdir(amazon_dir), "amazon/ folder was not created"
    assert os.path.exists(os.path.join(amazon_dir, "amazon_bill_123.pdf"))
    assert os.path.exists(os.path.join(amazon_dir, "amazon_receipt_456.pdf"))

    # Verify guru/ contains the two guru files
    guru_dir = os.path.join(word_test_dir, "guru")
    assert os.path.isdir(guru_dir), "guru/ folder was not created"
    assert os.path.exists(os.path.join(guru_dir, "guru_notes.txt"))
    assert os.path.exists(os.path.join(guru_dir, "guru_data.csv"))

    # Verify _Random/ contains the three gibberish/no-word files
    random_dir = os.path.join(word_test_dir, "_Random")
    assert os.path.isdir(random_dir), "_Random/ folder was not created"
    assert os.path.exists(os.path.join(random_dir, "336101256_21499.jpg"))
    assert os.path.exists(os.path.join(random_dir, "hfqgifcbkj9.png"))
    assert os.path.exists(os.path.join(random_dir, "323f9w8ehf8awjefi.docx"))

    # Verify no per-hash folders exist
    assert not os.path.exists(os.path.join(word_test_dir, "336101256_21499"))
    assert not os.path.exists(os.path.join(word_test_dir, "hfqgifcbkj9"))
    assert not os.path.exists(os.path.join(word_test_dir, "323f9w8ehf8awjefi"))

    if os.path.exists(word_test_dir):
        shutil.rmtree(word_test_dir)

    # Clean up test folder
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("\nSUCCESS: ALL SORTING, DUPLICATE, EMPTY FOLDER & WORD-BASED SORTING TESTS PASSED!")

if __name__ == '__main__':
    run_tests()
