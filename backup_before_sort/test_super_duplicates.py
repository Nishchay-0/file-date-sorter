import os
import shutil
import tempfile
import time
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from sorter_core import (
    find_duplicate_groups,
    delete_duplicate_files,
    replace_duplicates_with_links,
    export_duplicates_report,
    get_image_perceptual_hash,
    calculate_hamming_similarity,
    calculate_fuzzy_name_similarity,
    calculate_text_similarity
)


def test_selected_files_bypass_extension_filters():
    temp_dir = tempfile.mkdtemp(prefix="selected_dup_")
    try:
        f1 = os.path.join(temp_dir, "alpha.txt")
        f2 = os.path.join(temp_dir, "beta.txt")
        with open(f1, "w", encoding="utf-8") as f:
            f.write("same-content")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("same-content")

        groups = find_duplicate_groups(
            temp_dir,
            match_mode='content',
            recursive=True,
            selected_files=[f1, f2],
            include_exts=['.jpg'],
        )

        assert len(groups) == 1, f"Expected selected files to bypass extension filters, got {groups}"
        assert {item['filename'] for item in groups[0]['files']} == {'alpha.txt', 'beta.txt'}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_super_duplicate_tests():
    test_dir = os.path.abspath("test_super_duplicates_temp")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)

    print("==================================================")
    print("RUNNING SUPER DUPLICATE & SIMILAR FILES TEST SUITE")
    print("==================================================")

    try:
        # --- TEST 1: Exact Byte Content (SHA-256 Multi-threaded) ---
        print("\n--- TEST 1: Exact SHA-256 Content Duplicate Scanner ---")
        file1 = os.path.join(test_dir, "document.pdf")
        file2 = os.path.join(test_dir, "document_copy.pdf")
        file3 = os.path.join(test_dir, "unique.pdf")

        content = "SUPER_DUPLICATE_TEST_PAYLOAD_" + ("X" * 500)
        with open(file1, "w") as f: f.write(content)
        with open(file2, "w") as f: f.write(content)
        with open(file3, "w") as f: f.write("UNIQUE_PAYLOAD")

        progress_logs = []
        def test_cb(proc, tot, stage, fn):
            progress_logs.append((proc, tot, stage))

        groups = find_duplicate_groups(test_dir, match_mode='content', recursive=True, progress_callback=test_cb)
        print(f"  [+] Found {len(groups)} duplicate group(s), received {len(progress_logs)} progress event(s)")
        assert len(groups) == 1, f"Expected 1 group, got {len(groups)}"
        assert len(groups[0]['files']) == 2
        assert len(progress_logs) > 0, "progress_callback should record scanning events!"
        print("  [OK] TEST 1 PASSED: SHA-256 Exact Content Scan with Live Progress Meter")

        # --- TEST 2: Visual Image Similarity (Perceptual Hashing) ---
        print("\n--- TEST 2: Visual Image Perceptual Similarity ---")
        if HAS_PIL:
            img_dir = os.path.join(test_dir, "images")
            os.makedirs(img_dir, exist_ok=True)

            img1_path = os.path.join(img_dir, "photo_original.jpg")
            img2_path = os.path.join(img_dir, "photo_resized.png")
            img3_path = os.path.join(img_dir, "photo_different.jpg")

            img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
            img1.save(img1_path)

            img2 = Image.new("RGB", (50, 50), color=(255, 0, 0))
            img2.save(img2_path)

            img3 = Image.new("RGB", (100, 100), color=(0, 0, 255))
            img3.save(img3_path)

            p1 = get_image_perceptual_hash(img1_path)
            p2 = get_image_perceptual_hash(img2_path)
            p3 = get_image_perceptual_hash(img3_path)

            sim_1_2 = calculate_hamming_similarity(p1['hash_int'], p2['hash_int'])
            sim_1_3 = calculate_hamming_similarity(p1['hash_int'], p3['hash_int'])

            print(f"  [+] Visual Similarity (Original vs Resized): {round(sim_1_2*100, 1)}%")
            print(f"  [+] Visual Similarity (Red vs Blue): {round(sim_1_3*100, 1)}%")
            assert sim_1_2 >= 0.95, "Identical colored images should have >=95% similarity!"

            img_groups = find_duplicate_groups(img_dir, match_mode='perceptual_image', similarity_threshold=0.90)
            print(f"  [+] Perceptual Scanner Detected {len(img_groups)} visual conflict group(s)")
            assert len(img_groups) == 1, "Should group the two red boxes together!"
            print("  [OK] TEST 2 PASSED: Perceptual Image Visual Similarity Scan")
        else:
            print("  [!] PIL not installed in environment, skipping visual perceptual test.")

        # --- TEST 3: Fuzzy File Name Similarity ---
        print("\n--- TEST 3: Fuzzy File Name Similarity ---")
        fn_dir = os.path.join(test_dir, "names")
        os.makedirs(fn_dir, exist_ok=True)

        f_a = os.path.join(fn_dir, "Financial_Report_2025_Final.docx")
        f_b = os.path.join(fn_dir, "Financial_Report_2025_Final (1).docx")
        f_c = os.path.join(fn_dir, "Unrelated_Vaccine_Data.docx")

        with open(f_a, "w") as f: f.write("A")
        with open(f_b, "w") as f: f.write("B")
        with open(f_c, "w") as f: f.write("C")

        fn_sim = calculate_fuzzy_name_similarity(os.path.basename(f_a), os.path.basename(f_b))
        print(f"  [+] Fuzzy Name Similarity: {round(fn_sim*100, 1)}%")
        assert fn_sim >= 0.80

        fn_groups = find_duplicate_groups(fn_dir, match_mode='fuzzy_name', similarity_threshold=0.80)
        assert len(fn_groups) == 1
        print("  [OK] TEST 3 PASSED: Fuzzy Name Match Scan")

        # --- TEST 4: Text Content Similarity ---
        print("\n--- TEST 4: Text Content Similarity ---")
        txt_dir = os.path.join(test_dir, "texts")
        os.makedirs(txt_dir, exist_ok=True)

        txt1 = os.path.join(txt_dir, "article_v1.txt")
        txt2 = os.path.join(txt_dir, "article_v2.txt")

        with open(txt1, "w") as f: f.write("The quick brown fox jumps over the lazy dog repeatedly.")
        with open(txt2, "w") as f: f.write("The quick brown fox jumps over the lazy dog continuously.")

        txt_sim = calculate_text_similarity(txt1, txt2)
        print(f"  [+] Text Similarity Ratio: {round(txt_sim*100, 1)}%")
        assert txt_sim >= 0.85

        txt_groups = find_duplicate_groups(txt_dir, match_mode='text_similarity', similarity_threshold=0.80)
        assert len(txt_groups) == 1
        print("  [OK] TEST 4 PASSED: Text Content Similarity Scan")

        # --- TEST 5: Hard Link Deduplication ---
        print("\n--- TEST 5: Hard Link Replacement ---")
        link_orig = os.path.join(test_dir, "master_file.txt")
        link_dup = os.path.join(test_dir, "duplicate_to_link.txt")

        with open(link_orig, "w") as f: f.write("HARD_LINK_CONTENT_STAYS_INTACT")
        with open(link_dup, "w") as f: f.write("HARD_LINK_CONTENT_STAYS_INTACT")

        link_res = replace_duplicates_with_links([link_dup], link_orig, link_type='hard')
        print(f"  [+] Hard link operation result: {link_res}")
        assert link_res['linked'] == 1
        assert os.path.exists(link_dup)
        with open(link_dup, "r") as f: content_read = f.read()
        assert content_read == "HARD_LINK_CONTENT_STAYS_INTACT"
        print("  [OK] TEST 5 PASSED: Hard Link Deduplication")

        # --- TEST 6: Audit Report Export (CSV & JSON) ---
        print("\n--- TEST 6: Duplicate Audit Report Export ---")
        csv_path = os.path.join(test_dir, "report.csv")
        json_path = os.path.join(test_dir, "report.json")

        all_groups = find_duplicate_groups(test_dir, match_mode='content', recursive=True)
        ok_csv = export_duplicates_report(all_groups, csv_path, report_format='csv')
        ok_json = export_duplicates_report(all_groups, json_path, report_format='json')

        assert ok_csv and os.path.exists(csv_path)
        assert ok_json and os.path.exists(json_path)
        print(f"  [+] CSV Report size: {os.path.getsize(csv_path)} bytes")
        print(f"  [+] JSON Report size: {os.path.getsize(json_path)} bytes")
        print("  [OK] TEST 6 PASSED: Report Export")

    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)

    print("\nALL SUPER DUPLICATE & SIMILAR FILES TESTS PASSED PERFECTLY!")


if __name__ == '__main__':
    run_super_duplicate_tests()
