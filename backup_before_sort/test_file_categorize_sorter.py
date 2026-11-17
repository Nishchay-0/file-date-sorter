"""
Unit tests for file_categorize_sorter.py
"""

import os
import shutil
import tempfile
import pytest
from file_categorize_sorter import (
    natural_sort_key,
    categorize_item,
    scan_and_categorize,
    execute_plan,
    rollback_manifest,
)


def test_natural_sort_key():
    items = ["file10", "file2", "file1", "file20", "file3", "05", "1", "10", "2"]
    sorted_items = sorted(items, key=natural_sort_key)
    assert sorted_items == ["1", "2", "05", "10", "file1", "file2", "file3", "file10", "file20"]


def test_categorize_numeric():
    cat, norm, reason = categorize_item("1", is_directory=True)
    assert cat == "numeric"
    assert norm == "01"

    cat, norm, reason = categorize_item("0.jpg", is_directory=False)
    assert cat == "numeric"
    assert norm == "00.jpg"

    cat, norm, reason = categorize_item("05", is_directory=True)
    assert cat == "numeric"
    assert norm == "05"

    cat, norm, reason = categorize_item("100.txt", is_directory=False)
    assert cat == "numeric"
    assert norm == "100.txt"


def test_categorize_hex_and_hashes():
    # 32-char MD5/Hex
    md5_hash = "0bf9bc0e41324e3e99ae576e00104ffc"
    cat, norm, reason = categorize_item(md5_hash, is_directory=True)
    assert cat == "hash"
    assert norm == md5_hash.lower()

    # Uppercase Hex with CDN dashinit suffix
    cdn_hash = "3E4396DAE40C47DA38821624AA0387A8_video_dashinit.mp4"
    cat, norm, reason = categorize_item(cdn_hash, is_directory=False)
    assert cat == "hash"
    assert norm == cdn_hash.lower()

    # UUID
    uuid_str = "A0EEBC99-9C0B-4EF8-BB6D-6BB9BD380A11"
    cat, norm, reason = categorize_item(uuid_str, is_directory=True)
    assert cat == "hash"
    assert norm == uuid_str.lower()


def test_categorize_standard_text():
    cat, norm, reason = categorize_item("my_vacation_photo.jpg", is_directory=False)
    assert cat == "standard"
    assert norm == "my_vacation_photo.jpg"

    cat, norm, reason = categorize_item("Project_Alpha_2026", is_directory=True)
    assert cat == "standard"


def test_scan_and_execute_move_and_undo():
    temp_dir = tempfile.mkdtemp(prefix="test_sorter_")
    try:
        # Create test items
        os.makedirs(os.path.join(temp_dir, "0"))
        os.makedirs(os.path.join(temp_dir, "1"))
        os.makedirs(os.path.join(temp_dir, "05"))
        os.makedirs(os.path.join(temp_dir, "3E4396DAE40C47DA38821624AA0387A8_video_dashinit"))
        os.makedirs(os.path.join(temp_dir, "0bf9bc0e41324e3e99ae576e00104ffc"))

        with open(os.path.join(temp_dir, "file10.txt"), "w") as f:
            f.write("content 10")
        with open(os.path.join(temp_dir, "file2.txt"), "w") as f:
            f.write("content 2")

        categories = scan_and_categorize(temp_dir)
        assert len(categories["numeric"]) == 3
        assert len(categories["hash"]) == 2
        assert len(categories["standard"]) == 2

        # Verify natural sort order in categories
        numeric_norms = [x["normalized_name"] for x in categories["numeric"]]
        assert numeric_norms == ["00", "01", "05"]

        standard_norms = [x["normalized_name"] for x in categories["standard"]]
        assert standard_norms == ["file2.txt", "file10.txt"]

        # Dry run - no files moved
        dry_ops = execute_plan(temp_dir, categories, mode="move", dry_run=True)
        assert len(dry_ops) == 0
        assert os.path.exists(os.path.join(temp_dir, "1"))

        # Real Execution
        undo_ops = execute_plan(temp_dir, categories, mode="move", dry_run=False)
        assert len(undo_ops) == 7

        # Check destination folders exist
        assert os.path.exists(os.path.join(temp_dir, "01_Numeric", "00"))
        assert os.path.exists(os.path.join(temp_dir, "01_Numeric", "01"))
        assert os.path.exists(os.path.join(temp_dir, "01_Numeric", "05"))
        assert os.path.exists(os.path.join(temp_dir, "02_Standard", "file2.txt"))
        assert os.path.exists(os.path.join(temp_dir, "02_Standard", "file10.txt"))
        assert os.path.exists(os.path.join(temp_dir, "03_Hashes", "0bf9bc0e41324e3e99ae576e00104ffc"))

        # Test Undo Rollback
        manifests = [f for f in os.listdir(temp_dir) if f.startswith(".undo_categorize_manifest_")]
        assert len(manifests) == 1
        manifest_path = os.path.join(temp_dir, manifests[0])

        rollback_success = rollback_manifest(manifest_path)
        assert rollback_success is True

        # Ensure original items are restored
        assert os.path.exists(os.path.join(temp_dir, "1"))
        assert os.path.exists(os.path.join(temp_dir, "file10.txt"))
        assert os.path.exists(os.path.join(temp_dir, "3E4396DAE40C47DA38821624AA0387A8_video_dashinit"))

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
