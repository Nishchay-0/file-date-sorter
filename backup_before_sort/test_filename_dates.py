import os
import shutil
import tempfile
from datetime import datetime
from sorter_core import extract_date_from_filename, get_file_date, organize_directory, sync_file_timestamps_from_filename

def run_tests():
    print("==================================================")
    print("RUNNING FILENAME EMBEDDED DATE PARSER TEST SUITE")
    print("==================================================")

    # --- TEST 1: Extract Date Patterns ---
    print("\n--- TEST 1: Parsing Various Filename Date Conventions ---")
    test_cases = [
        ("20022022_vacation.jpg", datetime(2022, 2, 20)),
        ("20220220_photo.png", datetime(2022, 2, 20)),
        ("IMG_20210815_123045.jpg", datetime(2021, 8, 15)),
        ("VID-20190504-WA0001.mp4", datetime(2019, 5, 4)),
        ("Screenshot_2023-11-05-14-22.png", datetime(2023, 11, 5)),
        ("Scan_20-02-2022.pdf", datetime(2022, 2, 20)),
        ("Archive_1987.pdf", datetime(1987, 1, 1)),
        ("Report_20181225.docx", datetime(2018, 12, 25)),
    ]

    for fname, expected_dt in test_cases:
        parsed = extract_date_from_filename(fname)
        print(f"  [+] '{fname}' -> Parsed: {parsed.strftime('%Y-%m-%d') if parsed else 'NONE'}")
        assert parsed is not None, f"Failed to parse date from '{fname}'"
        assert parsed.year == expected_dt.year, f"Expected year {expected_dt.year}, got {parsed.year}"
        assert parsed.month == expected_dt.month, f"Expected month {expected_dt.month}, got {parsed.month}"

    print("  [OK] TEST 1 PASSED: All Filename Date Formats Parsed Accurately")

    # --- TEST 2: Corrupt OS Timestamp Recovery ---
    print("\n--- TEST 2: Corrupt 1987 OS Timestamp Override ---")
    test_dir = tempfile.mkdtemp(prefix="test_filename_dates_")
    try:
        # Create a file named '20022022_photo.jpg'
        file_path = os.path.join(test_dir, "20022022_photo.jpg")
        with open(file_path, "w") as f:
            f.write("dummy photo payload")

        # Force OS timestamp to 1987-01-01 (1987 timestamp = 536457600)
        dt_1987 = datetime(1987, 1, 1).timestamp()
        os.utime(file_path, (dt_1987, dt_1987))

        # Check get_file_date with filename date source and smart auto
        resolved_dt = get_file_date(file_path, date_source='smart')
        print(f"  [+] File OS Date was 1987/2026. Resolved Date: {resolved_dt.strftime('%Y-%m-%d')}")
        assert resolved_dt.year == 2022, f"Expected 2022, got {resolved_dt.year}"
        print("  [OK] TEST 2 PASSED: Filename Date '20022022' Correctly Resolved to Year 2022")

        # --- TEST 3: Full Directory Organization by Filename Date ---
        print("\n--- TEST 3: Full Directory Organization to 2022/ Folder ---")
        stats, manifest = organize_directory(
            test_dir,
            sort_category='date',
            date_source='filename',
            structure_format='YYYY/MM',
            mode='move'
        )
        expected_dest_folder = os.path.join(test_dir, "2022", "02")
        expected_dest_file = os.path.join(expected_dest_folder, "20022022_photo.jpg")
        print(f"  [+] Organized into destination: {expected_dest_folder}")
        assert os.path.exists(expected_dest_file), f"File should be in '{expected_dest_file}'"
        print("  [OK] TEST 3 PASSED: File '20022022_photo.jpg' Sorted into '2022/02' Folder!")

        # --- TEST 4: Sync File System Timestamps on Disk ---
        print("\n--- TEST 4: Sync File System Timestamps on Disk ---")
        synced = sync_file_timestamps_from_filename(expected_dest_file)
        print(f"  [+] Timestamp Sync Operation: {synced}")
        assert synced is True
        mtime = datetime.fromtimestamp(os.path.getmtime(expected_dest_file))
        assert mtime.year == 2022
        print(f"  [+] On-Disk File System mtime updated to: {mtime.strftime('%Y-%m-%d')}")
        # --- TEST 5: Ambiguous 8-Digit Date Tie-Breaking Rule ---
        print("\n--- TEST 5: Ambiguous 8-Digit Date Tie-Breaking Rule ---")
        ambiguous_fname = "01022023_document.pdf"
        parsed_dmy = extract_date_from_filename(ambiguous_fname, date_format_preference='DMY')
        parsed_mdy = extract_date_from_filename(ambiguous_fname, date_format_preference='MDY')

        print(f"  [+] '01022023' with preference 'DMY' -> Parsed: {parsed_dmy.strftime('%Y-%m-%d')}")
        print(f"  [+] '01022023' with preference 'MDY' -> Parsed: {parsed_mdy.strftime('%Y-%m-%d')}")

        assert parsed_dmy == datetime(2023, 2, 1), f"Expected 2023-02-01 under DMY, got {parsed_dmy}"
        assert parsed_mdy == datetime(2023, 1, 2), f"Expected 2023-01-02 under MDY, got {parsed_mdy}"
        print("  [OK] TEST 5 PASSED: Ambiguous date '01022023' correctly resolved under both DMY and MDY preferences!")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    print("\nALL FILENAME EMBEDDED DATE TESTS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    run_tests()
