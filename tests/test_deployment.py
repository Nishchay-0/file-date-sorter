import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import shutil
import tempfile
import json
import subprocess
from sorter_core import (
    organize_directory,
    scan_directory_preview,
    find_duplicate_groups,
    delete_duplicate_files,
    move_duplicate_files,
    clean_empty_dirs,
    batch_rename_files,
    scan_junk_and_large_files,
    analyze_storage_insights,
    scan_folder_extensions,
    create_safety_backup_zip,
    list_manifest_files,
    undo_manifest,
    is_path_excluded
)

def run_master_deployment_test():
    print("==========================================================")
    print("      MASTER FILE ORGANIZER SUITE - DEPLOYMENT VERIFICATION")
    print("==========================================================")
    
    temp_dir = tempfile.mkdtemp(prefix="sorter_deploy_test_")
    print(f"[+] Isolated Test Directory: {temp_dir}\n")

    try:
        # Create directory hierarchy
        sub_docs = os.path.join(temp_dir, "Documents", "SubDocs")
        sub_photos = os.path.join(temp_dir, "Photos", "Camera")
        sub_excluded = os.path.join(temp_dir, "ExcludedFolder", "NestedSecret")
        os.makedirs(sub_docs, exist_ok=True)
        os.makedirs(sub_photos, exist_ok=True)
        os.makedirs(sub_excluded, exist_ok=True)

        # 1. Create sample files
        doc1 = os.path.join(sub_docs, "report_2024.pdf")
        doc2 = os.path.join(sub_docs, "notes.txt")
        img1 = os.path.join(sub_photos, "photo_001.jpg")
        img2_dup = os.path.join(sub_photos, "photo_001_copy.jpg")
        tmp1 = os.path.join(temp_dir, "scratch.tmp")
        zero1 = os.path.join(temp_dir, "empty_log.log")
        exc1 = os.path.join(sub_excluded, "do_not_touch.pdf")

        test_text = "Universal file content for hash and sorting validation."
        with open(doc1, "w") as f: f.write("Report content")
        with open(doc2, "w") as f: f.write("Notes content")
        with open(img1, "w") as f: f.write(test_text)
        with open(img2_dup, "w") as f: f.write(test_text) # Exact duplicate of img1
        with open(tmp1, "w") as f: f.write("Temp data")
        with open(zero1, "w") as f: pass # 0-byte file
        with open(exc1, "w") as f: f.write("Secret data in excluded folder")

        print("--- [TEST 1] Path Exclusion Logic Verification ---")
        exc_path_forward = sub_excluded.replace("\\", "/")
        assert is_path_excluded(exc1, [exc_path_forward]), "Failed to recognize file in excluded folder with forward slashes!"
        assert is_path_excluded(sub_excluded, [exc_path_forward]), "Failed to recognize excluded subfolder!"
        assert not is_path_excluded(doc1, [exc_path_forward]), "Incorrectly marked non-excluded file as excluded!"
        print("  ✓ Path Exclusion Engine: PASSED\n")

        print("--- [TEST 2] Category Sorting & Preview Map ---")
        preview_items, cat_counts, summary = scan_directory_preview(
            temp_dir, sort_category="category", exclude_folders=[exc_path_forward]
        )
        assert summary["total_files"] == 6, f"Expected 6 files in preview, got {summary['total_files']}"
        assert not any(item["src"] == exc1 for item in preview_items), "Excluded file appeared in preview map!"
        print(f"  ✓ Preview Scan: Found {summary['total_files']} files | Categories: {list(cat_counts.keys())}")
        print("  ✓ Category Sorting Preview: PASSED\n")

        print("--- [TEST 3] Execution & Safety Zip Backup ---")
        res3, manifest_path = organize_directory(
            temp_dir,
            sort_category="category",
            mode="copy",
            enable_zip_backup=True,
            exclude_folders=[exc_path_forward]
        )
        assert res3["processed"] == 6, f"Expected 6 processed files, got {res3['processed']}"
        assert os.path.exists(doc1), "Original file missing in copy mode!"
        assert not os.path.exists(os.path.join(temp_dir, "Documents", "do_not_touch.pdf")), "Excluded file was copied into Documents!"
        print(f"  ✓ Processed: {res3['processed']} files | Safety Backup Zip created: {bool(res3['zip_backup'])}")
        print("  ✓ Organization Execution: PASSED\n")

        print("--- [TEST 4] Duplicate Scanner Engine ---")
        dup_groups = find_duplicate_groups(temp_dir, match_mode="content", exclude_folders=[exc_path_forward])
        assert len(dup_groups) >= 1, "Duplicate scanner failed to detect identical photo files!"
        print(f"  ✓ Detected {len(dup_groups)} duplicate group(s)")
        print("  ✓ Duplicate Detection: PASSED\n")

        print("--- [TEST 5] Subfolder File Extractor ---")
        ext_dest = os.path.join(temp_dir, "ExtractedOutput")
        res5, _ = organize_directory(
            temp_dir,
            sort_category="flat",
            dest_folder=ext_dest,
            mode="copy",
            exclude_folders=[exc_path_forward],
            skipped_handling="stay"
        )
        assert os.path.isdir(ext_dest), "Extractor failed to create destination directory!"
        assert not os.path.exists(os.path.join(ext_dest, "do_not_touch.pdf")), "Extractor extracted file from Except Folder!"
        print(f"  ✓ Extracted {res5['processed']} file(s) into flat directory: '{os.path.basename(ext_dest)}'")
        print("  ✓ Subfolder Extractor: PASSED\n")

        print("--- [TEST 6] Batch Renamer Engine ---")
        files_to_ren = [doc1, doc2]
        ren_res = batch_rename_files(files_to_ren, naming_pattern="Doc_{YYYY}_{001}", prefix="FINAL_")
        assert ren_res["renamed"] == 2, f"Expected 2 renamed files, got {ren_res['renamed']}"
        assert os.path.exists(ren_res["manifest"]), "Rename manifest missing!"
        print(f"  ✓ Batch Renamed {ren_res['renamed']} file(s) with custom naming pattern")
        print("  ✓ Batch Renamer: PASSED\n")

        print("--- [TEST 6b] Skipped Files Mover Engine ---")
        unmatched_file = os.path.join(temp_dir, "unmatched.xyz")
        with open(unmatched_file, "w") as f: f.write("Unmatched content")
        skip_res, _ = organize_directory(
            temp_dir,
            sort_category="category",
            include_exts=[".pdf", ".jpg"],
            mode="copy",
            skipped_handling="move"
        )
        assert os.path.isdir(os.path.join(temp_dir, "_Skipped_Files")), "Failed to create _Skipped_Files folder!"
        print(f"  ✓ Moved {skip_res.get('moved_skipped_files', 0)} skipped file(s) into '_Skipped_Files'")
        print("  ✓ Skipped Files Mover Engine: PASSED\n")

        print("--- [TEST 7] Junk Cleaner & Storage Analytics ---")
        junk_res = scan_junk_and_large_files(temp_dir, exclude_folders=[exc_path_forward])
        assert len(junk_res["junk_files"]) >= 2, "Failed to identify .tmp and 0-byte junk files!"
        insights = analyze_storage_insights(temp_dir, exclude_folders=[exc_path_forward])
        assert insights["total_files"] >= 6, "Storage analytics count mismatch!"
        print(f"  ✓ Junk Files Identified: {len(junk_res['junk_files'])} | Total Analyzed Storage: {insights['total_size_str']}")
        print("  ✓ Junk & Analytics Engine: PASSED\n")

        print("--- [TEST 8] Extension Auto-Detector ---")
        ext_list = scan_folder_extensions(temp_dir, include_system=True, exclude_folders=[exc_path_forward])
        ext_names = [item["ext"] for item in ext_list]
        assert len(ext_names) > 0, "Extension scanner failed to detect any extensions!"
        print(f"  ✓ Extensions Detected: {ext_names}")
        print("  ✓ Extension Selector: PASSED\n")

        print("--- [TEST 9] Undo Manifest Engine ---")
        manifests = list_manifest_files(temp_dir)
        assert len(manifests) >= 1, "No manifest files recorded!"
        undo_res = undo_manifest(manifests[0]["path"])
        assert undo_res["undone"] >= 1, "Undo operation failed to restore files!"
        print(f"  ✓ Undone {undo_res['undone']} operations using manifest: '{manifests[0]['filename']}'")
        print("  ✓ Undo System: PASSED\n")

        print("--- [TEST 10] CLI Command Line Operations ---")
        cli_py = os.path.join(os.path.dirname(__file__), "cli.py")
        cmd = [sys.executable, cli_py, "--path", temp_dir, "--sort-category", "extension", "--dry-run", "--exclude-folders", exc_path_forward]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"CLI command failed with output:\n{result.stderr}"
        assert "STARTING SMART FILE ORGANIZER" in result.stdout, "CLI stdout output mismatch!"
        print("  ✓ CLI Execution: PASSED\n")

        print("--- [TEST 11] Standalone Empty Folder Cleaner & CLI ---")
        from sorter_core import scan_empty_dirs_preview, delete_empty_folder_batch
        test_empty_parent = os.path.join(temp_dir, "TestEmptyParent", "SubEmpty")
        os.makedirs(test_empty_parent, exist_ok=True)
        preview_empty = scan_empty_dirs_preview(temp_dir)
        assert len(preview_empty) >= 1, "Failed to preview empty folders!"
        cmd_clean = [sys.executable, cli_py, "--path", temp_dir, "--clean-empty-only"]
        res_clean = subprocess.run(cmd_clean, capture_output=True, text=True)
        assert res_clean.returncode == 0, f"CLI clean-empty-only failed: {res_clean.stderr}"
        assert "CLEANING EMPTY SUBFOLDERS" in res_clean.stdout, "CLI clean-empty output mismatch!"
        print(f"  ✓ Previewed {len(preview_empty)} empty subfolder(s) & executed CLI clean-empty-only")
        print("  ✓ Standalone Empty Folder Cleaner: PASSED\n")

        print("--- [TEST 12] Magic Byte Header & Format Converter Engine ---")
        from sorter_core import detect_file_format_by_magic, scan_converter_preview, run_converter_batch
        fake_jpg = os.path.join(temp_dir, "unknown_data.DAT")
        with open(fake_jpg, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01") # Genuine JPEG Magic Byte Header

        info = detect_file_format_by_magic(fake_jpg)
        assert info["category"] == "image" and info["ext"] == ".jpg", f"Magic detector failed: {info}"

        fake_vob = os.path.join(temp_dir, "sample_movie.VOB")
        with open(fake_vob, "wb") as f:
            f.write(b"\x00\x00\x01\xba\x44\x00\x04\x00\x04\x01\x01\x86\xa3\xf8") # DVD VOB Video Header

        vob_info = detect_file_format_by_magic(fake_vob)
        assert vob_info["category"] == "video" and vob_info["ext"] == ".vob", f"VOB magic detector failed: {vob_info}"

        # Test selected_files mode for custom picked files
        vob_items, vob_counts = scan_converter_preview(selected_files=[fake_vob], conversion_mode="auto")
        assert len(vob_items) == 1 and vob_items[0]["action"] == "🎬 Convert to MP4 Video", f"VOB preview failed: {vob_items}"

        conv_items, conv_counts = scan_converter_preview(temp_dir, conversion_mode="auto")
        assert len(conv_items) >= 2, "Converter preview failed to detect misnamed files!"
        
        conv_res = run_converter_batch(conv_items)
        assert conv_res["processed"] >= 1, "Batch converter failed!"
        print(f"  ✓ Magic byte identified JPEG (.DAT) and DVD VOB video (.VOB) & auto-converted {conv_res['processed']} file(s)")
        print("  ✓ Magic File Converter & Format Fixer: PASSED\n")

        print("==========================================================")
        print("🎉 ALL 12 DEPLOYMENT TESTS PASSED WITH 100% SUCCESS!")
        print("==========================================================")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_master_deployment_test()
