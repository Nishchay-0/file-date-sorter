# Known Issues & Bug Status

## 🟢 Confirmed Fixed Bugs

<<<<<<< HEAD
| Bug ID | Description | Status | Evidence | Notes |
|--------|-------------|--------|----------|-------|
| — | None currently identified | ✅ Verified OK | Pytest suite passes (18/18 tests) | Last check: 2026-08-25 |
=======
### 1. CustomTkinter Checkbox Desync Sliver Bug (SCROLL-001)
- **Issue**: Checkbox indicator state and background canvas desynchronized or showed visual slivers when scrolling rapidly inside `CTkScrollableFrame`.
- **Root Cause**: CustomTkinter redraw lag during rapid scroll coordinate recalculation without atomic variable binding.
- **Fix**: Implemented `create_atomic_checkbox` helper in [`gui_modules/components.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/components.py) with explicit atomic `BooleanVar` repaint synchronization.
- **Evidence / Verification**: Validated across all 10 views in [`test_full_app_gui_atomic_sync.py`](file:///c:/file-date-sorter%20-%20Copy/test_full_app_gui_atomic_sync.py) and [`test_gui_atomic_checkbox_sync.py`](file:///c:/file-date-sorter%20-%20Copy/test_gui_atomic_checkbox_sync.py).

### 2. Face Clustering Mega-Cluster Absorption (PEOPLE-001)
- **Issue**: High-density DBSCAN single-linkage chaining absorbed distinct individuals into a single mega-cluster.
- **Root Cause**: Low density threshold (`eps`) chaining together similar intermediary face embeddings.
- **Fix**: Added secondary complete-linkage cosine distance thresholding step in [`face_sort.py`](file:///c:/file-date-sorter%20-%20Copy/face_sort.py).
- **Evidence / Verification**: Verified with cluster separation tests in [`test_people_clustering_tune.py`](file:///c:/file-date-sorter%20-%20Copy/test_people_clustering_tune.py).

### 3. Cloud Placeholder Stub Unintended Hydration (CLOUD-001)
- **Issue**: Standard hashing or reading cloud placeholders (OneDrive/iCloud/Dropbox stubs) forced full file downloads over the network.
- **Root Cause**: Opening files without checking `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS` or `FILE_ATTRIBUTE_OFFLINE`.
- **Fix**: Introduced `is_cloud_placeholder` in [`hashing.py`](file:///c:/file-date-sorter%20-%20Copy/hashing.py) to check Windows file attributes and bypass content reads for unhydrated stubs.
- **Evidence / Verification**: Tested in [`test_cloud_safe_mode.py`](file:///c:/file-date-sorter%20-%20Copy/test_cloud_safe_mode.py).
>>>>>>> origin/main

---

## 🟡 Open Considerations & Edge Behaviors

<<<<<<< HEAD
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
=======
### 1. Very Fast Video Face Appearances
- **Behavior**: Faces appearing for less than the sampling interval (default 2.5 seconds) in long videos may not be sampled.
- **Mitigation / Workaround**: Sampling interval is configurable in [`face_sort.py`](file:///c:/file-date-sorter%20-%20Copy/face_sort.py); users with dense fast-action video can lower the sampling interval.

### 2. Deep Windows Paths (>= 260 Characters)
- **Behavior**: Standard Windows APIs without `\\?\` prefix fail on paths exceeding `MAX_PATH` (260 chars).
- **Mitigation**: All path operations must route through `fix_win_long_path` in [`sorter_core.py`](file:///c:/file-date-sorter%20-%20Copy/sorter_core.py) and [`hashing.py`](file:///c:/file-date-sorter%20-%20Copy/hashing.py).
>>>>>>> origin/main
