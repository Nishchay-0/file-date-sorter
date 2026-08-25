# Known Issues & Bug Status

## Critical (Blocking Release)

| Bug ID | Description | Status | Evidence | Notes |
|--------|-------------|--------|----------|-------|
| — | None currently identified | ✅ Verified OK | Pytest suite passes (18/18 tests) | Last check: 2026-08-25 |

---

## High Priority (Affects Core Features)

| Bug ID | Description | Status | Evidence | Last Activity |
|--------|-------------|--------|----------|----------------|
| **SCROLL-001** | Checkbox state desync during scrolling (scrollable frames) | ✅ **FIXED** | Regression test: `test_gui_atomic_checkbox_sync.py` (3/3 pass) | Atomic repaint engine deployed |
| **SCROLL-002** | Background tab scrolling instead of active tab (mousewheel fallback) | ✅ **FIXED** | Regression test: `test_scrolling_background_fix.py` (5/5 pass) | Active tab detection with mousewheel listener |
| **PEOPLE-001** | Face clustering mega-cluster absorption (outlier merging) | ✅ **FIXED** | Complete-linkage cosine thresholding in `face_sort.py` | Validated in `test_people_sorter.py` |
| **FACE-001** | OpenCV model concurrency crash (thread safety) | ✅ **FIXED** | Thread lock around model inference; `test_people_clustering_tune.py` | Thread-safe locks verified |

---

## Medium Priority (Affects UX, Not Blocking)

| Bug ID | Description | Status | Workaround | Next Steps |
|--------|-------------|--------|-----------|-----------|
| **CACHE-001** | `.people_cache.json` invalidation insufficient (mtime-only check) | ✅ **FIXED** | Content-aware hash + schema version key in `face_sort.py` | Verified in `test_people_sorter.py::test_05_cache_key_changes_when_file_contents_change` |
| **MODEL-001** | Face model auto-download fails silently when offline | 🟡 **OPEN** | User pre-downloads models or connects to internet | Add explicit offline prompt and local model selector |
| **PERF-001** | Duplicate finding (SHA-256) on 100k+ files single-threaded | 🟡 **OPEN** | Run on folder subsets or use quick metadata scan | Implement multi-threaded worker pool for hashing |

---

## Low Priority (Cosmetic / Minor)

| Bug ID | Description | Status | Workaround |
|--------|-------------|--------|-----------|
| **UI-001** | Analytics chart labels tight on low-resolution displays | 🟢 **KNOWN** | Resize main application window |
| **UI-002** | Right-click context menu positioning near screen edges | 🟢 **KNOWN** | Clamped bounding box in `context_menu.py` |

---

## Closed (Fixed & Verified)

| Bug ID | Description | Fixed In / By | Evidence |
|--------|-------------|---------------|----------|
| **EXC-001** | User-selected files excluded if extension not in category list | Fixed in `sorter_core.py` | `test_super_duplicates.py::test_selected_files_bypass_extension_filters` (PASSED) |
| **EXC-002** | Default exclusion folders (`.git`, `node_modules`, `_Duplicates`) skipped across all gathering passes | Fixed in `sorter_core.py` | `test_full_duplicate_tool_verification.py::test_default_exclusions_skip_protected_dirs` (PASSED) |
| **GUI-001** | ModernFileDateSorterGUI class definition import | Fixed in `gui_modules/__init__.py` | `test_gui_import.py` (PASSED) |

---

## Verification Test Status (2026-08-25)

| Test Suite | Result | Details |
|------------|--------|---------|
| `test_scrolling_background_fix.py` | ✅ PASSED (5/5) | Active tab scrolling event delegation |
| `test_gui_atomic_checkbox_sync.py` | ✅ PASSED (3/3) | Atomic checkbox widget repainting |
| `test_people_sorter.py` | ✅ PASSED (6/6) | Synthetic face detection, DBSCAN clustering, cache key invalidation |
| `test_full_duplicate_tool_verification.py` | ✅ PASSED | End-to-end duplicate finder & protected exclusion check |
| `test_super_duplicates.py` | ✅ PASSED | Selected files bypass extension filters |
| `test_cloud_safe_mode.py` | ✅ PASSED (5/5) | Safe cloud placeholder & zero-byte overwrite protection |
