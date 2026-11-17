import os
import shutil
import tempfile
import unittest

from sorter_core import (
    extract_meaningful_group,
    extract_word_base,
    is_random_or_hash_name,
    extract_clean_title_prefix,
    get_name_sort_folder,
    organize_by_name,
    scan_directory_preview,
    generate_smart_name_plan
)


class TestSmartNameSorter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_name_sorter_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_word_base_extraction(self):
        """
        Test 1 — Meaningful title & multi-word group extraction:
        Extracts meaningful title group, skipping common leading stopwords ('the', 'a', 'my', etc.).
        """
        test_cases = {
            "_the_june_pearl_-12102022-0001.mp4": "june_pearl",
            "the_silent_eyes_145-07062022-0001.mp4": "silent_eyes",
            "my_document_2024.pdf": "document",
            "a_nice_photo.jpg": "nice_photo",
            "guru_finance_report.xls": "guru_finance_report",
            "amazon_bill_123.pdf": "amazon_bill",
            "amazon_receipt_456.pdf": "amazon_receipt",
            "invoice_001.pdf": "invoice",
            "report-2026.pdf": "report",
            "336101256_21499.jpg": None,
            "hfqgifcbkj9.png": None,
            "323f9w8ehf8awjefi.docx": None,
            "c6f1a063-299e-4595-be44-739eabc7d4e3.png": None,
            "5d41402abc4b2a76b9719d911017c592.jpg": None,
        }
        for fn, expected in test_cases.items():
            group = extract_meaningful_group(fn)
            self.assertEqual(group, expected, f"Failed for {fn}: got {group}, expected {expected}")

    def test_02_master_prompt_files_grouping(self):
        """
        Test 2 — Master Prompt Specification:
        Given:
          - _the_june_pearl_-12102022-0001.mp4 -> june_pearl/
          - the_silent_eyes_145-07062022-0001.mp4 -> silent_eyes/
          - my_document_2024.pdf -> document/
          - a_nice_photo.jpg -> nice_photo/
          - guru_finance_report.xls -> guru_finance_report/
          - hfqgifcbkj9.png -> _Random/
          - 323f9w8ehf8awjefi.docx -> _Random/
          - 336101256_21499.jpg -> _Random/
        """
        files = [
            "_the_june_pearl_-12102022-0001.mp4",
            "the_silent_eyes_145-07062022-0001.mp4",
            "my_document_2024.pdf",
            "a_nice_photo.jpg",
            "guru_finance_report.xls",
            "hfqgifcbkj9.png",
            "323f9w8ehf8awjefi.docx",
            "336101256_21499.jpg"
        ]
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("content")

        stats, _ = organize_by_name(self.test_dir, dry_run=False, random_folder_name="_Random")
        self.assertEqual(stats["processed"], 8)

        june_dir = os.path.join(self.test_dir, "june_pearl")
        eyes_dir = os.path.join(self.test_dir, "silent_eyes")
        doc_dir = os.path.join(self.test_dir, "document")
        photo_dir = os.path.join(self.test_dir, "nice_photo")
        guru_dir = os.path.join(self.test_dir, "guru_finance_report")
        random_dir = os.path.join(self.test_dir, "_Random")

        self.assertTrue(os.path.isdir(june_dir))
        self.assertTrue(os.path.isdir(eyes_dir))
        self.assertTrue(os.path.isdir(doc_dir))
        self.assertTrue(os.path.isdir(photo_dir))
        self.assertTrue(os.path.isdir(guru_dir))
        self.assertTrue(os.path.isdir(random_dir))

        self.assertTrue(os.path.exists(os.path.join(june_dir, "_the_june_pearl_-12102022-0001.mp4")))
        self.assertTrue(os.path.exists(os.path.join(eyes_dir, "the_silent_eyes_145-07062022-0001.mp4")))
        self.assertTrue(os.path.exists(os.path.join(doc_dir, "my_document_2024.pdf")))
        self.assertTrue(os.path.exists(os.path.join(photo_dir, "a_nice_photo.jpg")))
        self.assertTrue(os.path.exists(os.path.join(guru_dir, "guru_finance_report.xls")))
        self.assertTrue(os.path.exists(os.path.join(random_dir, "336101256_21499.jpg")))
        self.assertTrue(os.path.exists(os.path.join(random_dir, "hfqgifcbkj9.png")))
        self.assertTrue(os.path.exists(os.path.join(random_dir, "323f9w8ehf8awjefi.docx")))

        # Ensure NO separate per-hash folders
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "336101256_21499")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "hfqgifcbkj9")))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "323f9w8ehf8awjefi")))

    def test_03_random_detection(self):
        """
        Test 3 — Machine & random names detected as random:
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
            folder, is_rand2, _ = get_name_sort_folder(fn, random_folder_name="_Random")
            self.assertTrue(is_rand2)
            self.assertEqual(folder, "_Random")

    def test_04_dry_run_safety(self):
        """
        Test 4 — Dry run leaves disk untouched.
        """
        fn = "my_document_2024.pdf"
        fp = os.path.join(self.test_dir, fn)
        with open(fp, "w") as f:
            f.write("test")

        stats, _ = organize_by_name(self.test_dir, dry_run=True)
        self.assertEqual(stats["processed"], 1)
        self.assertTrue(os.path.exists(fp))
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "document")))

    def test_05_preview_matches_execution(self):
        """
        Test 5 — Scan preview matches real destination.
        """
        files = ["my_document_2024.pdf", "336101256_21499.jpg"]
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("content")

        preview, _, _ = scan_directory_preview(self.test_dir, sort_category="smart_name", random_folder_name="_Random")
        self.assertEqual(len(preview), 2)
        p_map = {p["filename"]: p["rel_target"] for p in preview}
        self.assertEqual(p_map["my_document_2024.pdf"], "document")
        self.assertEqual(p_map["336101256_21499.jpg"], "_Random")

    def test_06_unsorted_subdivide_by_type(self):
        """
        Test 6 — Subdividing random files by type:
        _Random/Images/, _Random/Videos/, _Random/Other/
        """
        files = [
            "336101256_21499.jpg",
            "1C45F804E1DD671AB.mp4",
            "5d41402abc4b2a76b9719d911017c592.dat"
        ]
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("content")

        stats, _ = organize_by_name(self.test_dir, dry_run=False, random_folder_name="_Random", unsorted_subdivide="type")
        self.assertEqual(stats["processed"], 3)

        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "_Random", "Images", "336101256_21499.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "_Random", "Videos", "1C45F804E1DD671AB.mp4")))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "_Random", "Other", "5d41402abc4b2a76b9719d911017c592.dat")))

    def test_07_iso_date_prefix_renaming(self):
        """
        Test 7 — ISO date prefix renaming option:
        Renames file to YYYY-MM-DD_filename.ext on sort.
        """
        fn = "my_document_2024.pdf"
        with open(os.path.join(self.test_dir, fn), "w") as f:
            f.write("content")

        stats, _ = organize_by_name(self.test_dir, dry_run=False, iso_date_prefix=True)
        self.assertEqual(stats["processed"], 1)

        doc_dir = os.path.join(self.test_dir, "document")
        self.assertTrue(os.path.isdir(doc_dir))
        entries = os.listdir(doc_dir)
        self.assertEqual(len(entries), 1)
        # Should have YYYY-MM-DD_ prefix
        self.assertTrue(entries[0].endswith("my_document_2024.pdf"))
        self.assertTrue(len(entries[0]) > len("my_document_2024.pdf"))

    def test_08_generate_smart_name_plan(self):
        """
        Test 8 — Pre-execution plan summary:
        Returns proposed folders, unsorted count, and review needed.
        """
        files = [
            "my_document_2024.pdf",
            "guru_finance_report.xls",
            "336101256_21499.jpg"
        ]
        for fn in files:
            with open(os.path.join(self.test_dir, fn), "w") as f:
                f.write("content")

        plan = generate_smart_name_plan(self.test_dir, random_folder_name="_Random")
        self.assertEqual(plan["total_files"], 3)
        self.assertEqual(plan["unsorted_count"], 1)
        folder_names = [f["name"] for f in plan["proposed_folders"]]
        self.assertIn("document", folder_names)
        self.assertIn("guru_finance_report", folder_names)


if __name__ == "__main__":
    unittest.main()

