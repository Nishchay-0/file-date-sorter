import os
import shutil
import tempfile
import unittest

from sorter_core import (
    is_random_or_hash_name,
    get_name_sort_folder,
    organize_by_name,
    organize_directory,
    scan_directory_preview
)


class TestSmartNameSorter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_name_sorter_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_name_matching_no_prefix_truncation(self):
        """
        Rule 1: Use full filename minus extension, never a truncated prefix.
        'ansh_true' and 'ansh_rao' must stay in separate groups.
        """
        f1 = os.path.join(self.test_dir, "ansh_true.jpg")
        f2 = os.path.join(self.test_dir, "ansh_rao.png")
        with open(f1, "w") as f: f.write("true photo")
        with open(f2, "w") as f: f.write("rao photo")

        folder1, is_rand1, reason1 = get_name_sort_folder(f1)
        folder2, is_rand2, reason2 = get_name_sort_folder(f2)

        self.assertEqual(folder1, "ansh_true")
        self.assertEqual(folder2, "ansh_rao")
        self.assertFalse(is_rand1)
        self.assertFalse(is_rand2)
        self.assertNotEqual(folder1, folder2)

        # Run organization
        stats, manifest = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], 2)

        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_rao", "ansh_rao.png")))
        # Verify no shared prefix folder was created
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ansh")))

    def test_02_random_hash_heuristics_detection(self):
        """
        Rule 2: Detect machine-generated/hash names like 'infdhw489r09wujf09wej',
        MD5/SHA hashes, and UUIDs.
        """
        random_names = [
            "infdhw489r09wujf09wej.txt",
            "5d41402abc4b2a76b9719d911017c592.jpg",
            "c6f1a063-299e-4595-be44-739eabc7d4e3.png",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.dat",
            "a89f72b91c04.bin"
        ]

        for fname in random_names:
            is_rand, reason = is_random_or_hash_name(fname)
            self.assertTrue(is_rand, f"Failed to detect random name: {fname} (reason: {reason})")

        human_names = [
            "ansh_true.jpg",
            "ansh_rao.png",
            "my_vacation_photo.jpeg",
            "Project Report 2026.docx",
            "Screenshot 2024-01-01.png",
            "invoice-1042.pdf",
            "document.txt"
        ]

        for fname in human_names:
            is_rand, reason = is_random_or_hash_name(fname)
            self.assertFalse(is_rand, f"False positive on human name: {fname} (reason: {reason})")

    def test_03_catch_all_single_folder_for_random_names(self):
        """
        Rule 3: All files flagged as random go into ONE shared catch-all folder ('Unsorted').
        Never create a folder per random name.
        """
        f1 = os.path.join(self.test_dir, "infdhw489r09wujf09wej.txt")
        f2 = os.path.join(self.test_dir, "5d41402abc4b2a76b9719d911017c592.jpg")
        f3 = os.path.join(self.test_dir, "c6f1a063-299e-4595-be44-739eabc7d4e3.png")

        with open(f1, "w") as f: f.write("file1")
        with open(f2, "w") as f: f.write("file2")
        with open(f3, "w") as f: f.write("file3")

        stats, manifest = organize_by_name(self.test_dir, random_folder_name="Unsorted", dry_run=False)
        self.assertEqual(stats["processed"], 3)

        # Verify all 3 random files are together inside Unsorted/
        unsorted_dir = os.path.join(self.test_dir, "Unsorted")
        self.assertTrue(os.path.isdir(unsorted_dir))
        self.assertTrue(os.path.exists(os.path.join(unsorted_dir, "infdhw489r09wujf09wej.txt")))
        self.assertTrue(os.path.exists(os.path.join(unsorted_dir, "5d41402abc4b2a76b9719d911017c592.jpg")))
        self.assertTrue(os.path.exists(os.path.join(unsorted_dir, "c6f1a063-299e-4595-be44-739eabc7d4e3.png")))

        # Verify NO individual folders were created per random hash
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "infdhw489r09wujf09wej")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "5d41402abc4b2a76b9719d911017c592")))

    def test_04_preserve_original_casing_and_exact_match(self):
        """
        Rule 4: Preserve original casing when creating folders.
        """
        f = os.path.join(self.test_dir, "MyDocument_Final.pdf")
        with open(f, "w") as fp: fp.write("content")

        folder_name, is_rand, _ = get_name_sort_folder(f)
        self.assertEqual(folder_name, "MyDocument_Final")

        organize_by_name(self.test_dir, dry_run=False)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "MyDocument_Final", "MyDocument_Final.pdf")))

    def test_05_safety_dry_run_and_collision_handling(self):
        """
        Rule 5: Dry-run mode by default does not modify disk, and collisions
        are handled non-destructively with number incrementing.
        """
        sub_dir = os.path.join(self.test_dir, "sub")
        os.makedirs(sub_dir, exist_ok=True)
        f1 = os.path.join(self.test_dir, "ansh_true.jpg")
        f2 = os.path.join(sub_dir, "ansh_true.jpg")

        with open(f1, "w") as f: f.write("original")
        with open(f2, "w") as f: f.write("duplicate copy with same name")

        # Dry run test
        stats_dry, _ = organize_by_name(self.test_dir, dry_run=True)
        self.assertEqual(stats_dry["processed"], 2)
        # Original files must remain intact
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ansh_true")))

        # Real run with collision resolution ('number')
        stats_real, _ = organize_by_name(self.test_dir, dry_run=False, on_conflict='number')
        self.assertEqual(stats_real["processed"], 2)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true_1.jpg")))

    def test_06_preview_classification_reasoning(self):
        """
        Verify scan_directory_preview returns is_random and classification_reason.
        """
        f_rand = os.path.join(self.test_dir, "infdhw489r09wujf09wej.txt")
        f_human = os.path.join(self.test_dir, "ansh_true.jpg")
        with open(f_rand, "w") as f: f.write("1")
        with open(f_human, "w") as f: f.write("2")

        preview, _, summary = scan_directory_preview(self.test_dir, sort_category="smart_name")
        self.assertEqual(len(preview), 2)

        rand_item = next(p for p in preview if "infdhw" in p["filename"])
        human_item = next(p for p in preview if "ansh_true" in p["filename"])

        self.assertTrue(rand_item["is_random"])
        self.assertIn("Random", rand_item["classification_reason"])
        self.assertIn("Unsorted", rand_item["target_dir"])

        self.assertFalse(human_item["is_random"])
        self.assertIn("ansh_true", human_item["target_dir"])

    def test_07_timestamp_and_camera_prefix_grouping(self):
        """
        Verify timestamped camera files like 'ANSHI-VID_20230809_190350_257' and
        'VID_20230308_214221' group under 'ANSHI-VID' and 'VID'.
        """
        files = [
            "ANSHI-VID_20230809_190350_257.mp4",
            "ANSHI-VID_20230809_190855_011.mp4",
            "ANSHI-VID_20240205_172813_449.mp4",
            "VID_20230308_214221.mp4",
            "VID_20230308_214256.mp4",
            "VID_20250501_105916_619.mp4"
        ]

        for fname in files:
            fp = os.path.join(self.test_dir, fname)
            with open(fp, "w") as f: f.write("video content")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], 6)

        # Verify ANSHI-VID folder
        anshi_dir = os.path.join(self.test_dir, "ANSHI-VID")
        self.assertTrue(os.path.isdir(anshi_dir))
        self.assertTrue(os.path.exists(os.path.join(anshi_dir, "ANSHI-VID_20230809_190350_257.mp4")))
        self.assertTrue(os.path.exists(os.path.join(anshi_dir, "ANSHI-VID_20240205_172813_449.mp4")))

        # Verify VID folder
        vid_dir = os.path.join(self.test_dir, "VID")
        self.assertTrue(os.path.isdir(vid_dir))
        self.assertTrue(os.path.exists(os.path.join(vid_dir, "VID_20230308_214221.mp4")))
        self.assertTrue(os.path.exists(os.path.join(vid_dir, "VID_20250501_105916_619.mp4")))

        # Ensure individual timestamp folders were NOT created
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ANSHI-VID_20230809_190350_257")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "VID_20230308_214221")))


if __name__ == "__main__":
    unittest.main()
