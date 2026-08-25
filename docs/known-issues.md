# Known Issues & Bug Status

## 🟢 Confirmed Fixed Bugs

| Bug ID | Description | Status | Evidence | Notes |
|--------|-------------|--------|----------|-------|
| **CONV-001** | `start_converter_execution` parameter mismatch (`items` vs `preview_items`) & dict keys | ✅ **FIXED** | Verified in `test_audit_fixes.py::test_06_run_converter_batch_signature_and_keys` | Fixed keyword parameter and key fallback in `gui_modules/app.py` |
| **CLI-001** | Missing `--path` guard caused `TypeError` crash on empty CLI args | ✅ **FIXED** | Added `if not args.path: parser.print_help()` in `cli.py` | CLI prints help cleanly when invoked without args |
| **EXC-003** | `clean_empty_dirs` and `scan_empty_dirs_preview` missing `DEFAULT_EXCLUDED_FOLDERS` | ✅ **FIXED** | Verified in `test_audit_fixes.py::test_01_empty_dirs_exclusions_protection` | Protected folders (.git, node_modules) skipped in empty folder passes |
| **EXC-004** | `is_path_excluded` skipped basename check when `target_norm == base_norm` | ✅ **FIXED** | Verified in `test_audit_fixes.py::test_02_delete_empty_folder_batch_protects_exclusions` | Self-path relative `.` check now properly evaluates basename rule |
| **DUP-001** | `move_duplicate_files` failed when multiple duplicates share identical names | ✅ **FIXED** | Verified in `test_audit_fixes.py::test_03_move_duplicate_files_collision_resolution` | Uses `resolve_filename_collision` |
| **CONV-002** | `convert_single_file` skipped export to `dest_dir` when source matched target extension | ✅ **FIXED** | Verified in `test_audit_fixes.py::test_04_convert_single_file_same_ext_dest_export` | Copies/moves file to output directory |
| **RENAME-001** | `batch_rename_files` camelCase tokenization index error & collision overwrite | ✅ **FIXED** | Verified in `test_audit_fixes.py::test_05_batch_rename_camel_case_and_collision` | Guards token list and resolves destination collisions |
| **DEAD-001** | Orphaned unreachable code block after `return False` in `face_sort.py` | ✅ **FIXED** | Removed dead code block in `face_sort.py` | Cleaned module structure |
| **SCROLL-001** | Checkbox state desync during scrolling (scrollable frames) | ✅ **FIXED** | Regression test: `test_gui_atomic_checkbox_sync.py` (3/3 pass) | Atomic repaint engine deployed |
| **SCROLL-002** | Background tab scrolling instead of active tab (mousewheel fallback) | ✅ **FIXED** | Regression test: `test_scrolling_background_fix.py` (5/5 pass) | Active tab detection with mousewheel listener |
| **PEOPLE-001** | Face clustering mega-cluster absorption (outlier merging) | ✅ **FIXED** | Complete-linkage cosine thresholding in `face_sort.py` | Validated in `test_people_sorter.py` |
| **FACE-001** | OpenCV model concurrency crash (thread safety) | ✅ **FIXED** | Thread lock around model inference; `test_people_clustering_tune.py` | Thread-safe locks verified |
| **DUP-002** | Missing `count_cloud_placeholders` import in `gui_modules/app.py` caused NameError on Duplicate Scan | ✅ **FIXED** | Verified in Pytest suite (34/34 passed) | Added import and wrapped cloud pre-check in try/except |
| **CLN-001** | Empty folder cleaner failed to delete directories containing read-only OS junk (`desktop.ini`, `thumbs.db`) or when root path had quotes | ✅ **FIXED** | Verified in `test_audit_fixes.py::test_07_clean_empty_dirs_with_readonly_os_junk` | Added `_force_remove_file` & `_force_rmdir` with `os.chmod` permission overrides and path sanitization |

---

## 🟡 Open Considerations & Edge Behaviors

| Feature / Area | Behavior | Mitigation / Workaround | Status |
|----------------|----------|-------------------------|--------|
| **MODEL-001** | Face model auto-download fails when offline | Pre-download models to `models/` directory or connect to internet | 🟡 Open UX refinement |
| **PERF-001** | Duplicate finding (SHA-256) on 100k+ files | Run on folder subsets or use quick metadata match mode | 🟡 Open performance enhancement |
| **UI-001** | Analytics chart labels tight on low-resolution displays | Resize main application window | 🟢 Known minor UI |
| **UI-002** | Right-click context menu positioning near screen edges | Clamped bounding box in `context_menu.py` | 🟢 Known minor UI |

---

## 🧪 Master Test Suite Verification (2026-08-25)

| Test Suite | Result | Details |
|------------|--------|---------|
| `test_audit_fixes.py` | ✅ PASSED (6/6) | Empty dir exclusions, collision resolution, converter args & keys |
| `test_deployment.py` | ✅ PASSED (12/12) | Master end-to-end deployment verification of all 12 engines |
| `test_scrolling_background_fix.py` | ✅ PASSED (5/5) | Active tab scrolling event delegation |
| `test_gui_atomic_checkbox_sync.py` | ✅ PASSED (3/3) | Atomic checkbox widget repainting |
| `test_people_sorter.py` | ✅ PASSED (6/6) | Synthetic face detection, DBSCAN clustering, cache key invalidation |
| `test_full_duplicate_tool_verification.py` | ✅ PASSED | End-to-end duplicate finder & protected exclusion check |
| `test_super_duplicates.py` | ✅ PASSED | Selected files bypass extension filters |
| `test_cloud_safe_mode.py` | ✅ PASSED (5/5) | Safe cloud placeholder & zero-byte overwrite protection |
