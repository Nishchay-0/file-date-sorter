import os
import shutil
import tempfile
import unittest

from sorter_core import (
    is_random_or_hash_name,
    extract_clean_title_prefix,
    get_name_sort_folder,
    organize_by_name,
    scan_directory_preview
)


class TestSmartNameSorter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_name_sorter_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_exact_human_filenames(self):
        """
        Test 1 — Exact human filenames:
        'ansh_true' and 'ansh_rao' must remain in separate folders.
        'MyDocument_Final.pdf' -> 'MyDocument_Final/'
        'document.txt' -> 'document/'
        """
        files = {
            "ansh_true.jpg": "ansh_true",
            "ansh_rao.png": "ansh_rao",
            "MyDocument_Final.pdf": "MyDocument_Final",
            "document.txt": "document"
        }
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("content")

        for fn, expected_folder in files.items():
            folder, is_rand, _ = get_name_sort_folder(os.path.join(self.test_dir, fn))
            self.assertEqual(folder, expected_folder, f"Failed folder match for {fn}")
            self.assertFalse(is_rand, f"Incorrectly marked as random: {fn}")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], 4)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_rao", "ansh_rao.png")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "MyDocument_Final", "MyDocument_Final.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "document", "document.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ansh")))

    def test_02_numeric_human_suffixes_preserved(self):
        """
        Test 2 — Numeric human suffixes:
        Legitimate human filenames with trailing numbers must NOT be stripped.
        'invoice-1042.pdf' -> 'invoice-1042'
        'report-2026.pdf' -> 'report-2026'
        'project-42.docx' -> 'project-42'
        'Nishchay-2405.jpg' -> 'Nishchay-2405'
        'Vacation-2026.jpg' -> 'Vacation-2026'
        """
        files = {
            "invoice-1042.pdf": "invoice-1042",
            "report-2026.pdf": "report-2026",
            "project-42.docx": "project-42",
            "Nishchay-2405.jpg": "Nishchay-2405",
            "Vacation-2026.jpg": "Vacation-2026"
        }
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("content")

        for fn, expected_folder in files.items():
            folder, is_rand, _ = get_name_sort_folder(os.path.join(self.test_dir, fn))
            self.assertEqual(folder, expected_folder, f"Failed suffix preservation for {fn}")
            self.assertFalse(is_rand, f"Incorrectly marked as random: {fn}")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(files))
        for fn, expected_folder in files.items():
            self.assertTrue(os.path.exists(os.path.join(self.test_dir, expected_folder, fn)))

    def test_03_human_alphanumeric_not_random(self):
        """
        Test 3 — Human alphanumeric:
        Legitimate alphanumeric human names must NOT be classified as random or sent to Unsorted.
        'Nishchay2405.jpg' -> 'Nishchay2405'
        'invoice2026final.pdf' -> 'invoice2026final'
        'Project2026Report.docx' -> 'Project2026Report'
        'Vacation2024Photos.jpg' -> 'Vacation2024Photos'
        """
        files = {
            "Nishchay2405.jpg": "Nishchay2405",
            "invoice2026final.pdf": "invoice2026final",
            "Project2026Report.docx": "Project2026Report",
            "Vacation2024Photos.jpg": "Vacation2024Photos"
        }
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("content")

        for fn, expected_folder in files.items():
            is_rand, reason = is_random_or_hash_name(fn)
            self.assertFalse(is_rand, f"False positive random on {fn} (reason: {reason})")
            folder, is_rand2, _ = get_name_sort_folder(fn)
            self.assertEqual(folder, expected_folder)
            self.assertFalse(is_rand2)

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(files))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "Unsorted")))

    def test_04_random_detection(self):
        """
        Test 4 — Random:
        Deterministic random machine-generated names must be detected as random.
        """
        random_files = [
            "infdhw489r09wujf09wej.txt",
            "5d41402abc4b2a76b9719d911017c592.jpg",
            "c6f1a063-299e-4595-be44-739eabc7d4e3.png",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.dat",
            "0_103622762244864_4193263340616068702_n.jpg",
            "123456789012345678.jpg",
            "0.jpg",
            "1.mp4",
            "05.jpg",
            "27.jpg"
        ]
        for fn in random_files:
            is_rand, reason = is_random_or_hash_name(fn)
            self.assertTrue(is_rand, f"Failed to detect machine/random name: {fn} (reason: {reason})")
            folder, is_rand2, _ = get_name_sort_folder(fn)
            self.assertTrue(is_rand2)
            self.assertEqual(folder, "Unsorted")

    def test_05_all_random_to_single_unsorted_folder(self):
        """
        Test 5 — All random -> ONE Unsorted folder:
        Verify random files all go into a single 'Unsorted/' folder (not separate per-file or Random/ subfolders).
        """
        random_files = [
            "infdhw489r09wujf09wej.txt",
            "5d41402abc4b2a76b9719d911017c592.jpg",
            "c6f1a063-299e-4595-be44-739eabc7d4e3.png"
        ]
        for fn in random_files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("data")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(random_files))

        unsorted_dir = os.path.join(self.test_dir, "Unsorted")
        self.assertTrue(os.path.isdir(unsorted_dir))
        for fn in random_files:
            self.assertTrue(os.path.exists(os.path.join(unsorted_dir, fn)))

        # Ensure no Random/ subfolders or per-file folders were created
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "Random")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "5d41402abc4b2a76b9719d911017c592")))

    def test_06_camera_video_patterns(self):
        """
        Test 6 — Camera patterns:
        'ANSHI-VID_20230809_190350_257.mp4' -> 'ANSHI-VID'
        'ANSHI-VID_20230809_190855_011.mp4' -> 'ANSHI-VID'
        'VID_101211201_003350.mp4' -> 'VID'
        'VID_115910705_194017.mp4' -> 'VID'
        """
        files = {
            "ANSHI-VID_20230809_190350_257.mp4": "ANSHI-VID",
            "ANSHI-VID_20230809_190855_011.mp4": "ANSHI-VID",
            "VID_101211201_003350.mp4": "VID",
            "VID_115910705_194017.mp4": "VID"
        }
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("video")

        for fn, expected_folder in files.items():
            folder, is_rand, _ = get_name_sort_folder(fn)
            self.assertEqual(folder, expected_folder)
            self.assertFalse(is_rand)

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(files))

        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ANSHI-VID", "ANSHI-VID_20230809_190350_257.mp4")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "VID", "VID_101211201_003350.mp4")))

    def test_07_snapchat_and_platform_exports(self):
        """
        Test 7 — Snapchat & Platform Exports:
        'Snapchat-236253845.jpg' -> 'Snapchat'
        '2022-02-25_media~Snapchat-1499352345.jpg' -> 'Snapchat'
        '2022-05-12_media~Snapchat-1104223881.mp4' -> 'Snapchat'
        """
        files = [
            "Snapchat-236253845.jpg",
            "2022-02-25_media~Snapchat-1499352345.jpg",
            "2022-05-12_media~Snapchat-1104223881.mp4"
        ]
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("snap")

        for fn in files:
            folder, is_rand, _ = get_name_sort_folder(fn)
            self.assertEqual(folder, "Snapchat")
            self.assertFalse(is_rand)

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(files))

        snap_dir = os.path.join(self.test_dir, "Snapchat")
        self.assertTrue(os.path.isdir(snap_dir))
        for fn in files:
            self.assertTrue(os.path.exists(os.path.join(snap_dir, fn)))

    def test_08_copy_suffix_stripped_vs_meaningful_dates(self):
        """
        Test 8 — Copy suffix:
        'Vacation.jpg' -> 'Vacation'
        'Vacation (1).jpg' -> 'Vacation'
        'Vacation (2).jpg' -> 'Vacation'
        'Vacation - Copy.jpg' -> 'Vacation'
        'Vacation_copy.jpg' -> 'Vacation'
        BUT 'Vacation-2026.jpg' -> 'Vacation-2026'
        """
        vacation_copies = [
            "Vacation.jpg",
            "Vacation (1).jpg",
            "Vacation (2).jpg",
            "Vacation - Copy.jpg",
            "Vacation_copy.jpg"
        ]
        for fn in vacation_copies:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("copy")

        with open(os.path.join(self.test_dir, "Vacation-2026.jpg"), "w") as f:
            f.write("2026")

        for fn in vacation_copies:
            folder, is_rand, _ = get_name_sort_folder(fn)
            self.assertEqual(folder, "Vacation")
            self.assertFalse(is_rand)

        folder_2026, is_rand_2026, _ = get_name_sort_folder("Vacation-2026.jpg")
        self.assertEqual(folder_2026, "Vacation-2026")
        self.assertFalse(is_rand_2026)

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(vacation_copies) + 1)

        vacation_dir = os.path.join(self.test_dir, "Vacation")
        self.assertTrue(os.path.isdir(vacation_dir))
        for fn in vacation_copies:
            self.assertTrue(os.path.exists(os.path.join(vacation_dir, fn)))

        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Vacation-2026", "Vacation-2026.jpg")))

    def test_09_idempotency_and_no_nested_folders(self):
        """
        Test 9 — Idempotency:
        Running Smart Name Sorter twice on already organized folders leaves them intact
        and does NOT create nested folders like 'Unsorted/Unsorted/' or 'ansh_true/ansh_true/'.
        """
        f_human = os.path.join(self.test_dir, "ansh_true.jpg")
        f_rand = os.path.join(self.test_dir, "5d41402abc4b2a76b9719d911017c592.jpg")
        with open(f_human, "w") as f: f.write("human")
        with open(f_rand, "w") as f: f.write("rand")

        # First run
        stats1, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats1["processed"], 2)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Unsorted", "5d41402abc4b2a76b9719d911017c592.jpg")))

        # Second run on the same folder
        stats2, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats2["skipped"], 2)
        self.assertEqual(stats2["processed"], 0)

        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "Unsorted", "Unsorted")))

    def test_10_dry_run_and_collision_handling(self):
        """
        Test 10 — Dry-Run Safety & Collision Handling:
        Dry run leaves files untouched.
        Real run resolves collisions safely with numbered suffixes (_1).
        """
        sub_dir = os.path.join(self.test_dir, "sub")
        os.makedirs(sub_dir, exist_ok=True)
        f1 = os.path.join(self.test_dir, "ansh_true.jpg")
        f2 = os.path.join(sub_dir, "ansh_true.jpg")
        with open(f1, "w") as f: f.write("orig")
        with open(f2, "w") as f: f.write("dup")

        # Dry run test
        stats_dry, _ = organize_by_name(self.test_dir, dry_run=True)
        self.assertEqual(stats_dry["processed"], 2)
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ansh_true")))

        # Real run test with conflict resolution
        stats_real, _ = organize_by_name(self.test_dir, dry_run=False, on_conflict="number")
        self.assertEqual(stats_real["processed"], 2)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true_1.jpg")))

    def test_11_preview_matches_execution_exactly(self):
        """
        Test 11 — Preview Consistency:
        Verify preview output exactly matches execution destination.
        """
        f_human = os.path.join(self.test_dir, "invoice-1042.pdf")
        f_cam = os.path.join(self.test_dir, "ANSHI-VID_20230809_190350_257.mp4")
        f_rand = os.path.join(self.test_dir, "c6f1a063-299e-4595-be44-739eabc7d4e3.png")
        with open(f_human, "w") as f: f.write("1")
        with open(f_cam, "w") as f: f.write("2")
        with open(f_rand, "w") as f: f.write("3")

        preview, _, _ = scan_directory_preview(self.test_dir, sort_category="smart_name")
        self.assertEqual(len(preview), 3)

        item_human = next(p for p in preview if "invoice-1042" in p["filename"])
        item_cam = next(p for p in preview if "ANSHI-VID" in p["filename"])
        item_rand = next(p for p in preview if "c6f1a063" in p["filename"])

        self.assertEqual(item_human["rel_target"], "invoice-1042")
        self.assertEqual(item_cam["rel_target"], "ANSHI-VID")
        self.assertEqual(item_rand["rel_target"], "Unsorted")


    def test_12_multiple_hash_names_share_one_unsorted_folder(self):
        """
        Test 12 — Multiple hash files -> ONE shared Unsorted/ folder:
        All hash/random files must land in a single 'Unsorted/' directory,
        not per-file subfolders. Also verify scan_directory_preview() shows
        same Unsorted grouping (preview must match real run).
        """
        files = [
            "4fd9410fe1d24572aa4b0b45e7560b23.jpg",
            "36e505829dfc4a77bdbbbf178daa720b.jpg",
            "6B479171A31EEACBB382B96C37C97A82_video_dashinit.mp4",
            "8E4DD8ED0CA7D0F25CFB758C02D566B3_transcode_output_dashinit.mp4",
            "4845B3B2A8C31D0FF940DBCA464195AB_transcode_oil_output_dashinit.mp4",
        ]
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("hash")

        # All must be detected as random and route to "Unsorted"
        for fn in files:
            folder, is_rand, reason = get_name_sort_folder(fn)
            self.assertTrue(is_rand, f"Not detected as random: {fn} (reason: {reason})")
            self.assertEqual(folder, "Unsorted", f"Wrong folder for {fn}: got {folder!r}")

        # Preview must show same destination
        preview, _, _ = scan_directory_preview(self.test_dir, sort_category="smart_name")
        self.assertEqual(len(preview), len(files))
        for item in preview:
            self.assertEqual(
                item["rel_target"], "Unsorted",
                f"Preview shows wrong target for {item['filename']}: {item['rel_target']!r}"
            )

        # Execute and verify ONE Unsorted folder, not per-file folders
        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(files))

        unsorted_dir = os.path.join(self.test_dir, "Unsorted")
        self.assertTrue(os.path.isdir(unsorted_dir))

        for fn in files:
            self.assertTrue(
                os.path.exists(os.path.join(unsorted_dir, fn)),
                f"File not in Unsorted/: {fn}"
            )

        # No per-file hash folders
        for fn in files:
            stem = os.path.splitext(fn)[0]
            self.assertFalse(
                os.path.exists(os.path.join(self.test_dir, stem)),
                f"Per-file folder incorrectly created: {stem}/"
            )


if __name__ == "__main__":
    unittest.main()
