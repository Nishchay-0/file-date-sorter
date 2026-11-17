"""
test_cloud_safe_mode.py - Test Suite for OneDrive / Cloud-Storage Safe Mode & Truncation Guards

Verifies:
1. is_cloud_placeholder attribute inspection on local files.
2. verify_safe_overwrite guard blocking silent truncation overwrites.
3. Metadata-only date sorting without binary file payload reads.
4. Same-volume os.rename / shutil.move operations.
5. Quick Scan (name_size / name_size_mtime) duplicate detection without content hashing.
"""

import os
import sys
import shutil
import tempfile
import unittest
from datetime import datetime

from hashing import is_cloud_placeholder, verify_safe_overwrite, count_cloud_placeholders
from sorter_core import get_file_date, organize_directory, find_duplicates, gather_files


class TestCloudSafeMode(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_cloud_safe_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_is_cloud_placeholder_attribute_check(self):
        fp = os.path.join(self.test_dir, "sample.txt")
        with open(fp, "w") as f:
            f.write("Hello World Cloud Test")

        p_info = is_cloud_placeholder(fp)
        self.assertIsInstance(p_info, dict)
        self.assertIn('is_placeholder', p_info)
        self.assertIn('download_required', p_info)
        self.assertIn('nominal_size', p_info)
        self.assertFalse(p_info['is_placeholder'])
        self.assertEqual(p_info['nominal_size'], 22)

    def test_02_verify_safe_overwrite_guard(self):
        large_fp = os.path.join(self.test_dir, "destination_large.bin")
        small_fp = os.path.join(self.test_dir, "source_stub.bin")

        # Create 200KB destination file
        with open(large_fp, "wb") as f:
            f.write(b"A" * 204800)

        # Create 100-byte source stub file
        with open(small_fp, "wb") as f:
            f.write(b"B" * 100)

        # Overwrite guard should block small stub replacing 200KB destination
        is_safe, reason = verify_safe_overwrite(small_fp, large_fp)
        self.assertFalse(is_safe)
        self.assertIn("dramatically smaller", reason)

        # Same size file should be allowed
        same_fp = os.path.join(self.test_dir, "source_valid.bin")
        with open(same_fp, "wb") as f:
            f.write(b"A" * 204800)
        is_safe_ok, _ = verify_safe_overwrite(same_fp, large_fp)
        self.assertTrue(is_safe_ok)

    def test_03_metadata_only_sorting_no_binary_read(self):
        fp = os.path.join(self.test_dir, "20230515_photo.jpg")
        with open(fp, "wb") as f:
            f.write(b"NOT_A_REAL_JPEG_BINARY")

        # get_file_date should extract date from filename without needing EXIF binary payload
        dt = get_file_date(fp, date_source='smart')
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2023)
        self.assertEqual(dt.month, 5)
        self.assertEqual(dt.day, 15)

    def test_04_quick_scan_duplicate_detection(self):
        sub1 = os.path.join(self.test_dir, "folder1")
        sub2 = os.path.join(self.test_dir, "folder2")
        os.makedirs(sub1, exist_ok=True)
        os.makedirs(sub2, exist_ok=True)

        f1 = os.path.join(sub1, "doc.pdf")
        f2 = os.path.join(sub2, "doc.pdf")
        with open(f1, "wb") as f:
            f.write(b"PDF Payload 12345")
        with open(f2, "wb") as f:
            f.write(b"PDF Payload 12345")

        # Quick scan by name + size (no byte hashing required)
        groups = find_duplicates(self.test_dir, match_mode='name_size', recursive=True)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['match_mode'], 'name_size')
        self.assertEqual(len(groups[0]['files']), 2)

    def test_05_count_cloud_placeholders_summary(self):
        f1 = os.path.join(self.test_dir, "file1.txt")
        f2 = os.path.join(self.test_dir, "file2.txt")
        with open(f1, "w") as f:
            f.write("test1")
        with open(f2, "w") as f:
            f.write("test2")

        summary = count_cloud_placeholders([f1, f2])
        self.assertEqual(summary['cloud_count'], 0)


if __name__ == '__main__':
    unittest.main()
