import os
import shutil
import tempfile
import pytest
from sorter_core import (
    cleanup_filename_str,
    extract_file_metadata,
    build_renamed_filename,
    batch_rename_files,
    undo_manifest,
    list_manifest_files
)

@pytest.fixture
def temp_rename_dir():
    temp_dir = tempfile.mkdtemp(prefix="smart_renamer_test_")
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_01_cleanup_filename_str():
    """Verify illegal characters, extra spaces, and duplicate markers are stripped."""
    assert cleanup_filename_str("Photo:Vacation*2024?.jpg") == "PhotoVacation2024.jpg"
    assert cleanup_filename_str("My Document (1) - Copy.pdf") == "My Document.pdf"
    assert cleanup_filename_str("File__With___Multiple____Underscores.txt") == "File_With_Multiple_Underscores.txt"
    assert cleanup_filename_str("  Spaced   Out   Name  .png") == "Spaced Out Name.png"


def test_02_case_conversions():
    """Verify camelCase, snake_case, kebab-case, uppercase, and lowercase."""
    src = "c:/fake/hello_world_sample_file.txt"
    assert build_renamed_filename(src, case_transform="camel") == "helloWorldSampleFile.txt"
    assert build_renamed_filename(src, case_transform="snake") == "hello_world_sample_file.txt"
    assert build_renamed_filename(src, case_transform="kebab") == "hello-world-sample-file.txt"
    assert build_renamed_filename(src, case_transform="upper") == "HELLO_WORLD_SAMPLE_FILE.txt"
    assert build_renamed_filename(src, case_transform="lower") == "hello_world_sample_file.txt"


def test_03_regex_search_and_replace():
    """Verify regex pattern substitution and capture groups."""
    src = "c:/fake/IMG_20240815_9999.jpg"
    pattern = r"IMG_(\d{4})(\d{2})(\d{2})_(\d+)"
    replacement = r"Trip_\1-\2-\3_Num\4"
    res = build_renamed_filename(src, search_text=pattern, replace_text=replacement, use_regex=True)
    assert res == "Trip_2024-08-15_Num9999.jpg"


def test_04_sequential_numbering_custom():
    """Verify custom numbering start, step, and padding."""
    src = "c:/fake/document.pdf"
    res1 = build_renamed_filename(src, naming_pattern="Doc_{001}", counter_idx=1, counter_start=10, counter_step=5, counter_padding=4)
    assert res1 == "Doc_0010.pdf"

    res2 = build_renamed_filename(src, naming_pattern="Doc_{001}", counter_idx=2, counter_start=10, counter_step=5, counter_padding=4)
    assert res2 == "Doc_0015.pdf"


def test_05_metadata_tags(temp_rename_dir):
    """Verify metadata tag substitutions on real files."""
    fp = os.path.join(temp_rename_dir, "sample.txt")
    with open(fp, "w", encoding="utf-8") as f:
        f.write("Hello metadata world!")

    meta = extract_file_metadata(fp)
    assert meta["Category"] == "Documents"
    assert int(meta["SizeBytes"]) > 0

    res = build_renamed_filename(fp, naming_pattern="{OriginalName}_{Category}_{SizeKB}KB")
    assert "sample_Documents_" in res
    assert res.endswith(".txt")


def test_06_batch_rename_execution_and_undo(temp_rename_dir):
    """Verify execution of batch rename on disk and 1-click restore via manifest."""
    f1 = os.path.join(temp_rename_dir, "report_draft (1) - Copy.docx")
    f2 = os.path.join(temp_rename_dir, "invoice_june (2).pdf")
    with open(f1, "w") as f:
        f.write("doc1")
    with open(f2, "w") as f:
        f.write("doc2")

    res = batch_rename_files(
        [f1, f2],
        naming_pattern="{CleanName}",
        case_transform="title",
        prefix="FIN_",
        cleanup=True
    )

    assert res["renamed"] == 2
    assert res["manifest"] is not None

    # Check files renamed on disk
    expected_f1 = os.path.join(temp_rename_dir, "FIN_Report_Draft.docx")
    expected_f2 = os.path.join(temp_rename_dir, "FIN_Invoice_June.pdf")
    assert os.path.exists(expected_f1)
    assert os.path.exists(expected_f2)

    # 1-Click Undo
    undo_stats = undo_manifest(res["manifest"])
    assert undo_stats["undone"] == 2
    assert os.path.exists(f1)
    assert os.path.exists(f2)


def test_07_conflict_modes(temp_rename_dir):
    """Verify collision resolution modes: number, skip, replace."""
    f1 = os.path.join(temp_rename_dir, "a.txt")
    f2 = os.path.join(temp_rename_dir, "b.txt")
    with open(f1, "w") as f:
        f.write("A")
    with open(f2, "w") as f:
        f.write("B")

    # Both renaming to target "shared.txt"
    res_num = batch_rename_files([f1, f2], naming_pattern="shared", on_conflict="number")
    assert res_num["renamed"] == 2
    assert os.path.exists(os.path.join(temp_rename_dir, "shared.txt"))
    assert os.path.exists(os.path.join(temp_rename_dir, "shared_1.txt"))
