import os
import shutil
import tempfile
import unittest
import sys

from sorter_core import (
    clean_empty_dirs,
    scan_empty_dirs_preview,
    delete_empty_folder_batch,
    move_duplicate_files,
    convert_single_file,
    batch_rename_files,
    run_converter_batch,
    DEFAULT_EXCLUDED_FOLDERS
)


class TestAuditFixes(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_audit_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_empty_dirs_exclusions_protection(self):
        """Verify clean_empty_dirs and scan_empty_dirs_preview protect default excluded folders."""
        git_dir = os.path.join(self.test_dir, ".git", "empty_sub")
        node_dir = os.path.join(self.test_dir, "node_modules", "empty_pkg")
        normal_empty = os.path.join(self.test_dir, "normal_empty")

        os.makedirs(git_dir, exist_ok=True)
        os.makedirs(node_dir, exist_ok=True)
        os.makedirs(normal_empty, exist_ok=True)

        preview = scan_empty_dirs_preview(self.test_dir)
        preview_paths = [p["path"] for p in preview]

        self.assertIn(normal_empty, preview_paths)
        self.assertFalse(any(".git" in p for p in preview_paths))
        self.assertFalse(any("node_modules" in p for p in preview_paths))

        cleaned = clean_empty_dirs(self.test_dir)
        self.assertEqual(cleaned, 1)
        self.assertTrue(os.path.exists(git_dir))
        self.assertTrue(os.path.exists(node_dir))
        self.assertFalse(os.path.exists(normal_empty))

    def test_02_delete_empty_folder_batch_protects_exclusions(self):
        """Verify delete_empty_folder_batch ignores protected directories."""
        git_dir = os.path.join(self.test_dir, ".git")
        os.makedirs(git_dir, exist_ok=True)

        res = delete_empty_folder_batch([git_dir])
        self.assertEqual(res["deleted"], 0)
        self.assertTrue(os.path.exists(git_dir))

    def test_03_move_duplicate_files_collision_resolution(self):
        """Verify move_duplicate_files resolves name collisions when moving duplicates."""
        src_a = os.path.join(self.test_dir, "folder_a")
        src_b = os.path.join(self.test_dir, "folder_b")
        dest = os.path.join(self.test_dir, "duplicates_dest")

        os.makedirs(src_a, exist_ok=True)
        os.makedirs(src_b, exist_ok=True)
        os.makedirs(dest, exist_ok=True)

        file_a = os.path.join(src_a, "photo.jpg")
        file_b = os.path.join(src_b, "photo.jpg")

        with open(file_a, "wb") as f: f.write(b"content_a")
        with open(file_b, "wb") as f: f.write(b"content_b")

        res = move_duplicate_files([file_a, file_b], dest)
        self.assertEqual(res["moved"], 2)
        self.assertEqual(res["errors"], 0)

        dest_files = os.listdir(dest)
        self.assertEqual(len(dest_files), 2)
        self.assertIn("photo.jpg", dest_files)
        self.assertIn("photo_1.jpg", dest_files)

    def test_04_convert_single_file_same_ext_dest_export(self):
        """Verify convert_single_file transfers files with matching target extension to dest_dir."""
        src_file = os.path.join(self.test_dir, "source.mp3")
        dest_dir = os.path.join(self.test_dir, "converted_output")

        with open(src_file, "wb") as f: f.write(b"fake_mp3_content")

        ok, out_p = convert_single_file(src_file, dest_dir=dest_dir, target_ext=".mp3", delete_original=False)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(out_p))
        self.assertEqual(os.path.dirname(out_p), os.path.abspath(dest_dir))

    def test_05_batch_rename_camel_case_and_collision(self):
        """Verify batch_rename_files handles edge-case tokenization and avoids collision overwrite."""
        f1 = os.path.join(self.test_dir, "my_cool_photo.jpg")
        f2 = os.path.join(self.test_dir, "---.jpg")
        f_existing = os.path.join(self.test_dir, "target.jpg")

        with open(f1, "w") as f: f.write("1")
        with open(f2, "w") as f: f.write("2")
        with open(f_existing, "w") as f: f.write("existing")

        batch_rename_files([f1, f2], case_transform="camel", naming_pattern="{OriginalName}")
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "myCoolPhoto.jpg")))

        # Test collision resolution with existing target
        renamed_f1 = os.path.join(self.test_dir, "myCoolPhoto.jpg")
        batch_rename_files([renamed_f1], naming_pattern="target")
        self.assertTrue(os.path.exists(f_existing))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "target_1.jpg")))

    def test_06_run_converter_batch_signature_and_keys(self):
        """Verify run_converter_batch accepts preview_items and returns processed/skipped_corrupt keys."""
        src_txt = os.path.join(self.test_dir, "notes.log")
        with open(src_txt, "w") as f: f.write("hello world")

        preview_items = [{
            "src": src_txt,
            "target_ext": ".txt",
            "action": "Copy / Rename -> .txt"
        }]

        stats = run_converter_batch(preview_items=preview_items, output_dir=None, delete_original=False)
        self.assertIn("processed", stats)
        self.assertIn("skipped_corrupt", stats)
        self.assertIn("errors", stats)
        self.assertEqual(stats["processed"], 1)


if __name__ == "__main__":
    unittest.main()
