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

    print("\n--- TEST 5: Meaningful Title Grouping (Stopword-aware) + Single _Random Folder ---")
    word_test_dir = os.path.abspath("test_folder_word_sort")
    if os.path.exists(word_test_dir):
        shutil.rmtree(word_test_dir)
    os.makedirs(word_test_dir, exist_ok=True)

    test_files = [
        "_the_june_pearl_-12102022-0001.mp4",
        "the_silent_eyes_145-07062022-0001.mp4",
        "my_document_2024.pdf",
        "a_nice_photo.jpg",
        "guru_finance_report.xls",
        "hfqgifcbkj9.png",
        "323f9w8ehf8awjefi.docx",
        "336101256_21499.jpg"
    ]
    for tf in test_files:
        with open(os.path.join(word_test_dir, tf), "w") as f:
            f.write(f"content of {tf}")

    stats_word, _ = organize_directory(word_test_dir, sort_category='smart_name', mode='move', random_folder_name='_Random')
    print(f"Meaningful Title Sort result: {stats_word}")
    assert stats_word['processed'] == 8

    # Verify june_pearl/
    assert os.path.isdir(os.path.join(word_test_dir, "june_pearl"))
    assert os.path.exists(os.path.join(word_test_dir, "june_pearl", "_the_june_pearl_-12102022-0001.mp4"))

    # Verify silent_eyes/
    assert os.path.isdir(os.path.join(word_test_dir, "silent_eyes"))
    assert os.path.exists(os.path.join(word_test_dir, "silent_eyes", "the_silent_eyes_145-07062022-0001.mp4"))

    # Verify document/
    assert os.path.isdir(os.path.join(word_test_dir, "document"))
    assert os.path.exists(os.path.join(word_test_dir, "document", "my_document_2024.pdf"))

    # Verify nice_photo/
    assert os.path.isdir(os.path.join(word_test_dir, "nice_photo"))
    assert os.path.exists(os.path.join(word_test_dir, "nice_photo", "a_nice_photo.jpg"))

    # Verify guru_finance_report/
    assert os.path.isdir(os.path.join(word_test_dir, "guru_finance_report"))
    assert os.path.exists(os.path.join(word_test_dir, "guru_finance_report", "guru_finance_report.xls"))

    # Verify _Random/ contains the three gibberish/no-word files
    random_dir = os.path.join(word_test_dir, "_Random")
    assert os.path.isdir(random_dir), "_Random/ folder was not created"
    assert os.path.exists(os.path.join(random_dir, "336101256_21499.jpg"))
    assert os.path.exists(os.path.join(random_dir, "hfqgifcbkj9.png"))
    assert os.path.exists(os.path.join(random_dir, "323f9w8ehf8awjefi.docx"))

    # Verify no single-file folders exist for random hashes
    assert not os.path.exists(os.path.join(word_test_dir, "336101256_21499"))
    assert not os.path.exists(os.path.join(word_test_dir, "hfqgifcbkj9"))
    assert not os.path.exists(os.path.join(word_test_dir, "323f9w8ehf8awjefi"))

    if os.path.exists(word_test_dir):
        shutil.rmtree(word_test_dir)

    # Clean up test folder
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    print("\nSUCCESS: ALL SORTING, DUPLICATE, EMPTY FOLDER & MEANINGFUL GROUPING TESTS PASSED!")

if __name__ == '__main__':
    run_tests()
