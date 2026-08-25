# AGENTS.md

> Read this file fully before searching or scanning the codebase. Only search for something if it's not already documented here. If you do have to search, add what you found back into this file before finishing, so the next session doesn't have to search again.

---

## ⚡ Critical Project Directives & Non-Negotiables (Must Read First)

1. **Zero Data Loss Guarantee**: All file manipulation operations must default to non-destructive behavior. Every file move/organize/extract operation must support dry-run preview, System Vault safety Zip backups, and 1-click JSON undo manifests. Deletions must route through `send2trash` (Recycle Bin) unless explicitly instructed otherwise.
2. **100% Offline & Private**: Zero outbound telemetry or cloud API calls. All facial detection, embedding calculation, clustering, magic byte inspections, and file hashing execute strictly locally on the user's CPU/GPU.
3. **Cloud Placeholder Safety**: Always inspect Windows sparse/reparse cloud stub attributes (`is_cloud_placeholder` in `hashing.py`) before reading files to prevent triggering unintentional gigabyte downloads on OneDrive, iCloud, or Dropbox synced directories.
4. **Windows Path Resilience**: All paths must pass through `fix_win_long_path` (`\\?\` prefix support) and sanitize invalid NTFS characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`).
5. **No Regressions Baseline**: All 12 deployment test verification suites in `test_deployment.py` must pass with 100% success before any task completion.
6. **Continuous GitHub Sync & Automated Commits**: Always stage, commit with clear descriptive messages, and push all verified changes and task outputs to GitHub (`origin/main`) upon task completion, ensuring secrets hygiene and test verification before pushing.

---

## 🧭 Project Overview

- **Project Name**: Smart File Organizer Suite Pro
- **Author**: Nishchay
- **Version**: 1.0.0
- **Repository**: [Nishchay-0/file-date-sorter](https://github.com/Nishchay-0/file-date-sorter)
- **Purpose**: High-performance, multi-tool desktop GUI & CLI utility for organizing, deduplicating, batch renaming, converting, and indexing files and media across deep directory hierarchies.
- **Stack**: Python 3.8+, CustomTkinter, OpenCV (YuNet/SFace), ONNX Runtime, scikit-learn (DBSCAN), Pillow, Send2Trash, Watchdog, Pystray, PyInstaller, Inno Setup.

---

## 🚀 How to Run, Test, and Build

### Desktop GUI
```bash
python run_sorter.py
# or
python gui.py
```

### Command Line Interface (CLI)
```bash
# Basic sort by creation date
python cli.py --path "C:\Target\Path"

# Category sort with dry-run and exclusions
python cli.py --path "C:\Target\Path" --sort-category category --dry-run --exclude-folders ".git,node_modules"

# Standalone empty folder cleanup
python cli.py --path "C:\Target\Path" --clean-empty-only --exclude-folders ".git,node_modules"

# Undo the last operation
python cli.py --path "C:\Target\Path" --undo LATEST
```

### Test Suite Execution
```bash
# Master deployment verification (all 12 engines)
python test_deployment.py

# Core unit tests
python test_sorter.py
python test_super_duplicates.py
python test_people_sorter.py
```

### Production Build & Packaging
```bash
# 1. Compile PyInstaller standalone executable into dist/SmartFileOrganizer/
python build_exe.py

# 2. Compile Inno Setup Windows installer executable into installer_output/
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 🗺️ Module Map & Architectural Responsibilities

### Root Architecture & Entry Points
| File | Responsibility & Key Symbols |
| :--- | :--- |
| [`run_sorter.py`](file:///c:/file-date-sorter%20-%20Copy/run_sorter.py) | Dual-mode entry launcher; routes CLI arguments to `cli.main()` or launches GUI `gui.main()`. |
| [`gui.py`](file:///c:/file-date-sorter%20-%20Copy/gui.py) | Lightweight facade exporting `ModernFileDateSorterGUI`, `SmartFileOrganizerGUI`, and `main` from `gui_modules`. |
| [`cli.py`](file:///c:/file-date-sorter%20-%20Copy/cli.py) | Headless command line interface supporting all sorting modes, exclusions, dry-runs, undo, and cleaners. |
| [`version.py`](file:///c:/file-date-sorter%20-%20Copy/version.py) | Global constants: `APP_NAME`, `VERSION`, `APP_AUTHOR`, `APP_URL`. |
| [`settings_manager.py`](file:///c:/file-date-sorter%20-%20Copy/settings_manager.py) | JSON config manager (`%LOCALAPPDATA%/SmartFileOrganizer/settings.json`) for watcher preferences and UI defaults. |

### Core Processing Engines
| File | Responsibility & Key Symbols |
| :--- | :--- |
| [`sorter_core.py`](file:///c:/file-date-sorter%20-%20Copy/sorter_core.py) | Central engine: Date detection (EXIF/filename/stat), category mapping (`FILE_CATEGORIES`), directory flattening, junk cleaning, empty folder detection, zip vault safety, undo manifests (`generate_undo_manifest`, `undo_last_operation`), batch renamer (`batch_rename_files`). |
| [`hashing.py`](file:///c:/file-date-sorter%20-%20Copy/hashing.py) | Fast SHA-256 (`get_file_hash`), head/tail sampling (`get_file_fast_hash`), dHash perceptual image hashing (`get_image_perceptual_hash`), Hamming distance (`calculate_hamming_similarity`), string fuzzy match (`calculate_fuzzy_name_similarity`), cloud stub detection (`is_cloud_placeholder`). |
| [`face_sort.py`](file:///c:/file-date-sorter%20-%20Copy/face_sort.py) | Face recognition & clustering engine: OpenCV YuNet detector & SFace embedding models, video interval sampler, DBSCAN clustering, disk cache (`.people_cache.json`), index generation (`.people_index.json`), Windows `.url` shortcut creator. |
| [`watcher_service.py`](file:///c:/file-date-sorter%20-%20Copy/watcher_service.py) | Live folder watcher: `watchdog.observers.Observer` with debounce timer queue, background worker thread, system tray icon (`pystray`), and desktop toast alerts. |

### Modular GUI Layer ([`gui_modules/`](file:///c:/file-date-sorter%20-%20Copy/gui_modules))
| File | Responsibility |
| :--- | :--- |
| [`gui_modules/app.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/app.py) | Root CustomTkinter application window (`SmartFileOrganizerGUI`), tab navigation, theme manager, progress handling, async thread pool execution. |
| [`gui_modules/components.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/components.py) | Reusable UI components: `HeaderCard`, `MetricCard`, `ActionButton`, `StyledEntry`, `FolderPicker`, `StatusBadge`. |
| [`gui_modules/context_menu.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/context_menu.py) | Native right-click popups for file lists and preview items. |
| [`gui_modules/views/tab_sorter.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_sorter.py) | Organization & Date/Category/Extension sorting view. |
| [`gui_modules/views/tab_duplicates.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_duplicates.py) | Exact SHA-256 & Perceptual similarity duplicate finder and isolator. |
| [`gui_modules/views/tab_extractor.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_extractor.py) | Deep directory flattener and selective extension extractor. |
| [`gui_modules/views/tab_renamer.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_renamer.py) | Pattern tag batch renamer with live side-by-side preview. |
| [`gui_modules/views/tab_converter.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_converter.py) | Magic byte header inspector, extension fixer, audio/video/image converter. |
| [`gui_modules/views/tab_cleaner.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_cleaner.py) | OS junk file removal & standalone empty folder hierarchy cleaner. |
| [`gui_modules/views/tab_analytics.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_analytics.py) | Storage disk usage analyzer, category breakdown charts, and date span metrics. |
| [`gui_modules/views/tab_exclusions.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_exclusions.py) | Unified exclusion rules editor (folders, extensions, file patterns). |
| [`gui_modules/views/tab_people.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_people.py) | Face recognition manager, person tagging, face thumbnail viewer, shortcut generator. |
| [`gui_modules/views/tab_watcher.py`](file:///c:/file-date-sorter%20-%20Copy/gui_modules/views/tab_watcher.py) | Background folder monitoring controls and real-time event log viewer. |

### Build & Spec Artifacts
| File | Responsibility |
| :--- | :--- |
| [`build_exe.py`](file:///c:/file-date-sorter%20-%20Copy/build_exe.py) | PyInstaller automation script with asset bundling and optional code-signing hooks. |
| [`SmartFileOrganizer.spec`](file:///c:/file-date-sorter%20-%20Copy/SmartFileOrganizer.spec) | PyInstaller specification definition. |
| [`installer.iss`](file:///c:/file-date-sorter%20-%20Copy/installer.iss) | Inno Setup Windows installer compilation script. |
