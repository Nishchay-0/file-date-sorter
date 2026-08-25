import os
import shutil
import tempfile
import unittest

from sorter_core import (
    classify_filename,
    is_random_or_hash_name,
    get_smart_name_destination,
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
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ansh")))

    def test_02_copy_names_grouping(self):
        """
        Rule 2: Files that clearly represent the same logical name (copies/duplicates)
        should be grouped together without destroying meaningful names.
        """
        vacation_files = [
            "Vacation.jpg",
            "Vacation_1.jpg",
            "Vacation_2.png",
            "Vacation (1).jpg",
            "Vacation - Copy.jpg"
        ]
        for fn in vacation_files:
            with open(os.path.join(self.test_dir, fn), "w") as f: f.write("vacation")

        project_files = [
            "Project Report.docx",
            "Project Report (1).docx",
            "Project Report - Copy.pdf"
        ]
        for fn in project_files:
            with open(os.path.join(self.test_dir, fn), "w") as f: f.write("report")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(vacation_files) + len(project_files))

        # Check Vacation folder
        vacation_dir = os.path.join(self.test_dir, "Vacation")
        self.assertTrue(os.path.isdir(vacation_dir))
        for fn in vacation_files:
            self.assertTrue(os.path.exists(os.path.join(vacation_dir, fn)))

        # Check Project Report folder
        report_dir = os.path.join(self.test_dir, "Project Report")
        self.assertTrue(os.path.isdir(report_dir))
        for fn in project_files:
            self.assertTrue(os.path.exists(os.path.join(report_dir, fn)))

    def test_03_camera_video_grouping(self):
        """
        Rule 3: Recognize known structured generated camera/video schemes.
        'ANSHI-VID_...' -> 'ANSHI-VID/' and 'VID_...' -> 'VID/'.
        """
        files = [
            "ANSHI-VID_20230809_190350_257.mp4",
            "ANSHI-VID_20230809_190855_011.mp4",
            "ANSHI-VID_20240205_172813_449.mp4",
            "VID_20230308_214221.mp4",
            "VID_101211201_003350.mp4",
            "VID_115910705_194017.mp4",
            "VID_251651022_030334.mp4"
        ]
        for fname in files:
            with open(os.path.join(self.test_dir, fname), "w") as f: f.write("video")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(files))

        # Check ANSHI-VID
        anshi_dir = os.path.join(self.test_dir, "ANSHI-VID")
        self.assertTrue(os.path.isdir(anshi_dir))
        self.assertTrue(os.path.exists(os.path.join(anshi_dir, "ANSHI-VID_20230809_190350_257.mp4")))

        # Check VID
        vid_dir = os.path.join(self.test_dir, "VID")
        self.assertTrue(os.path.isdir(vid_dir))
        self.assertTrue(os.path.exists(os.path.join(vid_dir, "VID_101211201_003350.mp4")))
        self.assertTrue(os.path.exists(os.path.join(vid_dir, "VID_115910705_194017.mp4")))

        # Verify per-timestamp folders were NOT created
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "VID_101211201_003350")))

    def test_04_snapchat_platform_exports(self):
        """
        Rule 4: Recognize platform/export naming patterns (e.g. Snapchat).
        """
        snap_files = [
            "2022-02-25_media~Snapchat-1499352345.jpg",
            "2022-05-12_media~Snapchat-1104223881.mp4",
            "Snapchat-235837277.zip.nomedia",
            "Snapchat-236253845.jpg",
            "Snapchat-1170321109.jpg"
        ]
        for fname in snap_files:
            with open(os.path.join(self.test_dir, fname), "w") as f: f.write("snap")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(snap_files))

        snap_dir = os.path.join(self.test_dir, "Snapchat")
        self.assertTrue(os.path.isdir(snap_dir))
        for fname in snap_files:
            self.assertTrue(os.path.exists(os.path.join(snap_dir, fname)))

    def test_05_uuid_routing(self):
        """
        Rule 5a: UUIDs must route to Random/UUID/.
        """
        uuid_files = [
            "c6f1a063-299e-4595-be44-739eabc7d4e3.png",
            "A0EEBC99-9C0B-4EF8-BB6D-6BB9BD380A11.jpg"
        ]
        for fname in uuid_files:
            with open(os.path.join(self.test_dir, fname), "w") as f: f.write("uuid")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], 2)

        uuid_dir = os.path.join(self.test_dir, "Random", "UUID")
        self.assertTrue(os.path.isdir(uuid_dir))
        for fname in uuid_files:
            self.assertTrue(os.path.exists(os.path.join(uuid_dir, fname)))

    def test_06_hashes_routing(self):
        """
        Rule 5b: MD5, SHA, and hexadecimal hashes must route to Random/Hashes/.
        """
        hash_files = [
            "5d41402abc4b2a76b9719d911017c592.jpg",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.dat",
            "a89f72b91c04.bin",
            "3E4396DAE40C47DA38821624AA0387A8_video_dashinit.mp4",
            "7B4E3C5FCE469801265733B829B9FCB9_transcode_output_dashinit.mp4"
        ]
        for fname in hash_files:
            with open(os.path.join(self.test_dir, fname), "w") as f: f.write("hash")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(hash_files))

        hash_dir = os.path.join(self.test_dir, "Random", "Hashes")
        self.assertTrue(os.path.isdir(hash_dir))
        for fname in hash_files:
            self.assertTrue(os.path.exists(os.path.join(hash_dir, fname)))

    def test_07_meta_cdn_routing(self):
        """
        Rule 5c: Meta / Facebook / Instagram CDN IDs must route to Random/Meta_CDN/.
        """
        cdn_files = [
            "0_103622762244864_4193263340616068702_n.jpg",
            "0_220501766303801_2249776331757950988_n.mp4"
        ]
        for fname in cdn_files:
            with open(os.path.join(self.test_dir, fname), "w") as f: f.write("cdn")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], 2)

        meta_dir = os.path.join(self.test_dir, "Random", "Meta_CDN")
        self.assertTrue(os.path.isdir(meta_dir))
        for fname in cdn_files:
            self.assertTrue(os.path.exists(os.path.join(meta_dir, fname)))

    def test_08_numeric_ids_routing(self):
        """
        Rule 5d: Pure numeric machine IDs (e.g. 123456789012345678, short 0, 1, 05, 27)
        must route to Random/Numeric_ID/.
        """
        num_files = [
            "123456789012345678.jpg",
            "0.jpg",
            "1.mp4",
            "05.jpg",
            "27.jpg"
        ]
        for fname in num_files:
            with open(os.path.join(self.test_dir, fname), "w") as f: f.write("num")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(num_files))

        num_dir = os.path.join(self.test_dir, "Random", "Numeric_ID")
        self.assertTrue(os.path.isdir(num_dir))
        for fname in num_files:
            self.assertTrue(os.path.exists(os.path.join(num_dir, fname)))

    def test_09_alphanumeric_random_routing(self):
        """
        Rule 5e: Random high-entropy alphanumeric strings must route to Random/Alphanumeric/.
        """
        alpha_files = [
            "infdhw489r09wujf09wej.txt",
            "xkj827hskjw092n.txt"
        ]
        for fname in alpha_files:
            with open(os.path.join(self.test_dir, fname), "w") as f: f.write("alpha")

        stats, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats["processed"], len(alpha_files))

        alpha_dir = os.path.join(self.test_dir, "Random", "Alphanumeric")
        self.assertTrue(os.path.isdir(alpha_dir))
        for fname in alpha_files:
            self.assertTrue(os.path.exists(os.path.join(alpha_dir, fname)))

    def test_10_human_alphanumerics_not_falsely_classified(self):
        """
        Rule 8: Do NOT falsely classify legitimate human alphanumeric filenames as random.
        """
        human_names = [
            "invoice2026final.pdf",
            "Project2026Report.docx",
            "Vacation2024Photos.zip",
            "Nishchay2405.jpg"
        ]
        for fname in human_names:
            info = classify_filename(fname)
            self.assertFalse(info["is_random"], f"False positive on human filename: {fname} (reason: {info['reason']})")

            dest, _ = get_smart_name_destination(fname)
            base = os.path.splitext(fname)[0]
            self.assertEqual(dest, base)

    def test_11_preserve_casing(self):
        """
        Rule: Preserve original casing in folder names.
        """
        f = os.path.join(self.test_dir, "MyDocument_Final.pdf")
        with open(f, "w") as fp: fp.write("content")

        folder_name, is_rand, _ = get_name_sort_folder(f)
        self.assertEqual(folder_name, "MyDocument_Final")

        organize_by_name(self.test_dir, dry_run=False)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "MyDocument_Final", "MyDocument_Final.pdf")))

    def test_12_dry_run_safety(self):
        """
        Rule: Dry-run mode by default does not modify disk.
        """
        f1 = os.path.join(self.test_dir, "ansh_true.jpg")
        with open(f1, "w") as f: f.write("original")

        stats_dry, _ = organize_by_name(self.test_dir, dry_run=True)
        self.assertEqual(stats_dry["processed"], 1)
        self.assertTrue(os.path.exists(f1))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "ansh_true")))

    def test_13_collision_handling(self):
        """
        Rule: Collisions are handled non-destructively with number incrementing.
        """
        sub_dir = os.path.join(self.test_dir, "sub")
        os.makedirs(sub_dir, exist_ok=True)
        f1 = os.path.join(self.test_dir, "ansh_true.jpg")
        f2 = os.path.join(sub_dir, "ansh_true.jpg")

        with open(f1, "w") as f: f.write("original")
        with open(f2, "w") as f: f.write("duplicate copy")

        stats_real, _ = organize_by_name(self.test_dir, dry_run=False, on_conflict='number')
        self.assertEqual(stats_real["processed"], 2)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true_1.jpg")))

    def test_14_preview_execution_exact_match(self):
        """
        Rule: The GUI/CLI preview target and actual execution target MUST be 100% identical.
        """
        f_uuid = os.path.join(self.test_dir, "c6f1a063-299e-4595-be44-739eabc7d4e3.png")
        f_cam = os.path.join(self.test_dir, "ANSHI-VID_20230809_190350_257.mp4")
        f_human = os.path.join(self.test_dir, "ansh_true.jpg")

        with open(f_uuid, "w") as f: f.write("1")
        with open(f_cam, "w") as f: f.write("2")
        with open(f_human, "w") as f: f.write("3")

        preview, _, _ = scan_directory_preview(self.test_dir, sort_category="smart_name")
        self.assertEqual(len(preview), 3)

        uuid_item = next(p for p in preview if "c6f1a063" in p["filename"])
        cam_item = next(p for p in preview if "ANSHI-VID" in p["filename"])
        human_item = next(p for p in preview if "ansh_true" in p["filename"])

        self.assertEqual(uuid_item["rel_target"], os.path.join("Random", "UUID"))
        self.assertEqual(cam_item["rel_target"], "ANSHI-VID")
        self.assertEqual(human_item["rel_target"], "ansh_true")

        # Execute
        organize_by_name(self.test_dir, dry_run=False)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Random", "UUID", "c6f1a063-299e-4595-be44-739eabc7d4e3.png")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ANSHI-VID", "ANSHI-VID_20230809_190350_257.mp4")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "ansh_true", "ansh_true.jpg")))

    def test_15_idempotency_and_no_nested_destinations(self):
        """
        Rule: Running Smart Name Sorter repeatedly must NOT create nested directories
        like Random/Hashes/Random/Hashes/file.jpg.
        """
        f_hash = os.path.join(self.test_dir, "5d41402abc4b2a76b9719d911017c592.jpg")
        with open(f_hash, "w") as f: f.write("hash")

        # First run
        stats1, _ = organize_by_name(self.test_dir, dry_run=False)
        self.assertEqual(stats1["processed"], 1)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Random", "Hashes", "5d41402abc4b2a76b9719d911017c592.jpg")))

        # Second run on the same folder
        stats2, _ = organize_by_name(self.test_dir, dry_run=False)
        # File is already in target folder -> skipped, not re-nested
        self.assertEqual(stats2["skipped"], 1)
        self.assertEqual(stats2["processed"], 0)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "Random", "Hashes", "5d41402abc4b2a76b9719d911017c592.jpg")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "Random", "Hashes", "Random")))

    def test_16_structured_classifier_metadata(self):
        """
        Rule: classify_filename must return complete structured classification metadata.
        """
        info_uuid = classify_filename("c6f1a063-299e-4595-be44-739eabc7d4e3.png")
        self.assertTrue(info_uuid["is_random"])
        self.assertEqual(info_uuid["random_type"], "uuid")
        self.assertGreaterEqual(info_uuid["confidence"], 0.90)

        info_cam = classify_filename("ANSHI-VID_20230809_190350_257.mp4")
        self.assertFalse(info_cam["is_random"])
        self.assertTrue(info_cam["is_structured_camera"])
        self.assertEqual(info_cam["camera_prefix"], "ANSHI-VID")

        info_human = classify_filename("ansh_true.jpg")
        self.assertFalse(info_human["is_random"])
        self.assertIsNone(info_human["random_type"])
        self.assertEqual(info_human["clean_title"], "ansh_true")


if __name__ == "__main__":
    unittest.main()
