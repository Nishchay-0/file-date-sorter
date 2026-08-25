# Known Issues & Bug Status

## 🟢 Confirmed Fixed Bugs

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

---

## 🟡 Open Considerations & Edge Behaviors

### 1. Very Fast Video Face Appearances
- **Behavior**: Faces appearing for less than the sampling interval (default 2.5 seconds) in long videos may not be sampled.
- **Mitigation / Workaround**: Sampling interval is configurable in [`face_sort.py`](file:///c:/file-date-sorter%20-%20Copy/face_sort.py); users with dense fast-action video can lower the sampling interval.

### 2. Deep Windows Paths (>= 260 Characters)
- **Behavior**: Standard Windows APIs without `\\?\` prefix fail on paths exceeding `MAX_PATH` (260 chars).
- **Mitigation**: All path operations must route through `fix_win_long_path` in [`sorter_core.py`](file:///c:/file-date-sorter%20-%20Copy/sorter_core.py) and [`hashing.py`](file:///c:/file-date-sorter%20-%20Copy/hashing.py).
