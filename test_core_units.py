"""
test_core_units.py — Core Unit Tests
Smart File Organizer Suite Pro

Unit tests for path handling, file hashing, similarity calculations,
centralized logging, and configuration constants.
"""

import hashlib
import os
import sys
import tempfile
import threading
import unittest

from config import (
    COMMON_STOPWORDS,
    DEFAULT_RANDOM_FOLDER_NAME,
    FILE_CATEGORIES,
    FILE_CHUNK_SIZE,
    MONTH_NAMES,
    WIN_LONG_PATH_THRESHOLD,
)
from hashing import (
    calculate_fuzzy_name_similarity,
    calculate_hamming_similarity,
    get_file_fast_hash,
    get_file_hash,
)
from logger import get_logger, setup_logging
from utils import fix_win_long_path


class TestCorePathUtils(unittest.TestCase):
    """Tests for utils.fix_win_long_path and Windows long-path normalization."""

    def test_empty_and_none_paths(self):
        self.assertEqual(fix_win_long_path(None), "")
        self.assertEqual(fix_win_long_path(""), "")
        self.assertEqual(fix_win_long_path("   "), "")

    def test_strip_quotes(self):
        raw = '"C:\\Users\\Test\\Documents"'
        cleaned = fix_win_long_path(raw)
        self.assertFalse(cleaned.startswith('"'))
        self.assertFalse(cleaned.endswith('"'))

        raw_single = "'C:\\Users\\Test\\Documents'"
        cleaned_single = fix_win_long_path(raw_single)
        self.assertFalse(cleaned_single.startswith("'"))
        self.assertFalse(cleaned_single.endswith("'"))

    def test_short_path_no_extended_prefix(self):
        short = "C:\\Short\\Path\\File.txt"
        fixed = fix_win_long_path(short)
        self.assertFalse(fixed.startswith("\\\\?\\"))

    def test_long_path_extended_prefix(self):
        if sys.platform == 'win32':
            # Create a path string >= 240 chars
            deep_dirs = "C:\\" + "\\".join(["SubFolderWithLongName"] * 12) + "\\file.txt"
            self.assertGreaterEqual(len(deep_dirs), WIN_LONG_PATH_THRESHOLD)
            fixed = fix_win_long_path(deep_dirs)
            self.assertTrue(fixed.startswith("\\\\?\\"))
            # Must not have double \\?\
            self.assertFalse(fixed.startswith("\\\\?\\\\\\?\\"))

    def test_unc_path_prefix(self):
        if sys.platform == 'win32':
            unc_path = "\\\\fileserver\\shared_volume\\" + "\\".join(["DeepFolder"] * 25) + "\\data.bin"
            self.assertGreaterEqual(len(unc_path), WIN_LONG_PATH_THRESHOLD)
            fixed = fix_win_long_path(unc_path)
            self.assertTrue(fixed.startswith("\\\\?\\UNC\\"))
            # Must not be \\?\\server
            self.assertFalse(fixed.startswith("\\\\?\\\\\\"))

    def test_already_prefixed_preserved(self):
        prefixed = "\\\\?\\C:\\VeryLongPath\\File.txt"
        self.assertEqual(fix_win_long_path(prefixed), prefixed)


class TestCoreHashing(unittest.TestCase):
    """Tests for hashing.py functions: SHA-256, Fast Hash, and Similarity."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_hashing_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_file_hash_exact(self):
        content = b"Hello, Smart File Organizer Suite Pro! Deterministic hashing test."
        expected_sha256 = hashlib.sha256(content).hexdigest()

        test_file = os.path.join(self.temp_dir, "sample.txt")
        with open(test_file, "wb") as f:
            f.write(content)

        actual_hash = get_file_hash(test_file)
        self.assertEqual(actual_hash, expected_sha256)

    def test_get_file_hash_empty_file(self):
        empty_file = os.path.join(self.temp_dir, "empty.txt")
        with open(empty_file, "wb") as f:
            pass

        expected_sha256 = hashlib.sha256(b"").hexdigest()
        actual_hash = get_file_hash(empty_file)
        self.assertEqual(actual_hash, expected_sha256)

    def test_get_file_hash_non_existent(self):
        non_existent = os.path.join(self.temp_dir, "does_not_exist.bin")
        self.assertIsNone(get_file_hash(non_existent))

    def test_get_file_hash_cancellation(self):
        large_file = os.path.join(self.temp_dir, "large.bin")
        with open(large_file, "wb") as f:
            f.write(b"A" * (FILE_CHUNK_SIZE * 4))

        cancel_evt = threading.Event()
        cancel_evt.set()  # Pre-cancelled

        result = get_file_hash(large_file, cancel_event=cancel_evt)
        self.assertIsNone(result)

    def test_get_file_fast_hash_empty(self):
        empty_file = os.path.join(self.temp_dir, "empty.bin")
        with open(empty_file, "wb") as f:
            pass

        self.assertEqual(get_file_fast_hash(empty_file), "empty_0")

    def test_get_file_fast_hash_content(self):
        content_file = os.path.join(self.temp_dir, "content.bin")
        with open(content_file, "wb") as f:
            f.write(b"Fast Hash Test Block" * 100)

        fast_hash = get_file_fast_hash(content_file)
        self.assertIsNotNone(fast_hash)
        self.assertNotEqual(fast_hash, "empty_0")
        self.assertEqual(len(fast_hash), 32)  # MD5 hex length

    def test_hamming_similarity(self):
        h1 = 0b1111000011110000
        # Identical
        self.assertAlmostEqual(calculate_hamming_similarity(h1, h1, bits=16), 1.0)
        # None inputs
        self.assertEqual(calculate_hamming_similarity(None, h1), 0.0)
        self.assertEqual(calculate_hamming_similarity(h1, None), 0.0)
        # Inverted bits
        h_inverted = 0b0000111100001111
        self.assertAlmostEqual(calculate_hamming_similarity(h1, h_inverted, bits=16), 0.0)

    def test_fuzzy_name_similarity(self):
        self.assertAlmostEqual(calculate_fuzzy_name_similarity("photo_2024.jpg", "photo_2024.jpg"), 1.0)
        self.assertAlmostEqual(calculate_fuzzy_name_similarity("PHOTO_2024.JPG", "photo_2024.png", ignore_extension=True), 1.0)
        self.assertGreater(calculate_fuzzy_name_similarity("report_final_v1.docx", "report_final_v2.docx"), 0.8)


class TestConfigConstants(unittest.TestCase):
    """Tests for configuration integrity in config.py."""

    def test_required_categories_exist(self):
        required_cats = ["Images", "Documents", "Videos", "Audio", "Archives"]
        for cat in required_cats:
            self.assertIn(cat, FILE_CATEGORIES)
            self.assertGreater(len(FILE_CATEGORIES[cat]), 0)

    def test_stopwords_integrity(self):
        self.assertIn("the", COMMON_STOPWORDS)
        self.assertIn("a", COMMON_STOPWORDS)
        self.assertIn("my", COMMON_STOPWORDS)

    def test_month_names_complete(self):
        self.assertEqual(len(MONTH_NAMES), 12)
        self.assertEqual(MONTH_NAMES[1], "January")
        self.assertEqual(MONTH_NAMES[12], "December")

    def test_thresholds(self):
        self.assertEqual(WIN_LONG_PATH_THRESHOLD, 240)
        self.assertEqual(FILE_CHUNK_SIZE, 65536)
        self.assertEqual(DEFAULT_RANDOM_FOLDER_NAME, "_Random")


class TestCentralizedLogging(unittest.TestCase):
    """Tests for logger.py."""

    def test_get_logger(self):
        log = get_logger("TestSubsystem")
        self.assertEqual(log.name, "SmartFileOrganizer.TestSubsystem")

    def test_setup_logging(self):
        import logging
        root_log = setup_logging(level=logging.DEBUG)
        self.assertEqual(root_log.name, "SmartFileOrganizer")
        self.assertEqual(root_log.level, logging.DEBUG)


if __name__ == "__main__":
    unittest.main()
