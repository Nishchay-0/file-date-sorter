> Read this file fully before searching or scanning the codebase. Only search for something if it's not already documented here. If you do have to search, add what you found back into this file before finishing, so the next session doesn't have to search again.

# Smart File Organizer Suite Pro — Working Agreement & Project Guide

## 🚨 Critical Non-Negotiable Hard Constraints

1. **Continuous GitHub Sync & Automated Commits**: Always stage, commit with clear descriptive semantic messages, and push all verified changes and task outputs to GitHub (`origin/main`) upon task completion, ensuring secrets hygiene and test verification before pushing.
2. **Zero-Deletion / Zero Data Loss Guarantee**: Destructive operations (move, delete, overwrite, rename) MUST always generate an atomic Zip backup vault and `.undo_manifest.json` before modifying files, with 1-click restore functionality.
3. **Cloud Placeholder Safety**: Always inspect Windows sparse/reparse cloud stub attributes (`is_cloud_placeholder` in `hashing.py`) before reading files to prevent triggering unintentional gigabyte downloads on OneDrive, iCloud, or Dropbox synced directories.
4. **Secrets & Hygiene Pre-Push Check**: Scan git diffs for credentials, tokens, or API keys before pushing; exclude sensitive files in `.gitignore`.
5. **No Telemetry / Data Sharing**: Never transmit or share user data to external servers without explicit consent (Constraint 002).
6. **No Silent Fallbacks**: Always surface degradation visibly (e.g. missing face models, permission errors) (Constraint 004).
7. **Dry-Run Exact Match**: Preview mode must match real execution exactly before confirmation (Constraint 006).
8. **Windows Path Resilience**: All paths must pass through `fix_win_long_path` (`\\?\` prefix support) and sanitize invalid NTFS characters.

---

## 🧭 Project Header

```
PROJECT: Smart File Organizer Suite Pro
PURPOSE: High-performance desktop GUI & CLI utility for organizing, deduplicating, batch renaming, converting, and indexing files and media across deep directory hierarchies with face recognition and system vault backup/undo.
STACK: Python 3.11+, CustomTkinter, OpenCV (YuNet/SFace), ONNX Runtime, scikit-learn (DBSCAN), Pillow, Send2Trash, Watchdog, PyInstaller, Inno Setup
HOW TO RUN:
  - GUI: python run_sorter.py or python gui.py
  - CLI: python cli.py --help
  - Tests: $env:TCL_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tcl8.6"; $env:TK_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tk8.6"; py -3.14 -m pytest -v
  - Build exe: python build_exe.py
  - Build installer: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
HARD CONSTRAINTS: Always commit & push to GitHub; Zero data loss (System Vault undo); Cloud safe mode; Windows-first long paths; No telemetry; Exact dry-run match.
```

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
```powershell
$env:TCL_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tcl8.6"
$env:TK_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tk8.6"
py -3.14 -m pytest -v
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
| [`run_sorter.py`](file:///c:/file-date-sorter/run_sorter.py) | Dual-mode entry launcher; routes CLI arguments to `cli.main()` or launches GUI `gui.main()`. |
| [`gui.py`](file:///c:/file-date-sorter/gui.py) | Lightweight facade exporting `ModernFileDateSorterGUI`, `SmartFileOrganizerGUI`, and `main` from `gui_modules`. |
| [`cli.py`](file:///c:/file-date-sorter/cli.py) | Headless command line interface supporting all sorting modes, exclusions, dry-runs, undo, and cleaners. |
| [`version.py`](file:///c:/file-date-sorter/version.py) | Global constants: `APP_NAME`, `VERSION`, `APP_AUTHOR`, `APP_URL`. |
| [`settings_manager.py`](file:///c:/file-date-sorter/settings_manager.py) | JSON config manager (`%LOCALAPPDATA%/SmartFileOrganizer/settings.json`) for watcher preferences and UI defaults. |
| [`utils.py`](file:///c:/file-date-sorter/utils.py) | Path utility helper with Windows long-path prefixing (`fix_win_long_path`). |

### Core Processing Engines
| File | Responsibility & Key Symbols |
| :--- | :--- |
| [`sorter_core.py`](file:///c:/file-date-sorter/sorter_core.py) | Central engine: Date detection (EXIF/filename/stat), category mapping (`FILE_CATEGORIES`), directory flattening, junk cleaning, empty folder detection, zip vault safety, undo manifests (`generate_undo_manifest`, `undo_last_operation`), batch renamer (`batch_rename_files`, `build_renamed_filename`, `cleanup_filename_str`, `extract_file_metadata`), exclusion filtering (`is_path_excluded`, `DEFAULT_EXCLUDED_FOLDERS`). **Smart Name Sorting**: `extract_meaningful_group(filename)` — deterministic token scanning that normalizes separators, skips leading numeric counters, stops on date stamps, strips leading stopwords (`COMMON_STOPWORDS`), preserves abbreviations (`pvt`, `m`, `ser`), and routes gibberish/hashes to `_Random/`. `natural_sort_key(text)` — alphanumeric sort key (numbers sorted numerically). |
| [`hashing.py`](file:///c:/file-date-sorter/hashing.py) | Fast SHA-256 (`get_file_hash`), head/tail sampling (`get_file_fast_hash`), dHash perceptual image hashing (`get_image_perceptual_hash`), Hamming distance (`calculate_hamming_similarity`), string fuzzy match (`calculate_fuzzy_name_similarity`), cloud stub detection (`is_cloud_placeholder`). |
| [`face_sort.py`](file:///c:/file-date-sorter/face_sort.py) | Face recognition & clustering engine: OpenCV YuNet detector & SFace embedding models, video interval sampler, complete-linkage DBSCAN clustering, disk cache (`.people_cache.json`) with content-aware hashing (`_cache_key_for_file`), index generation (`.people_index.json`), Windows `.url` shortcut creator. |
| [`watcher_service.py`](file:///c:/file-date-sorter/watcher_service.py) | Live folder watcher: `watchdog.observers.Observer` with debounce timer queue, background worker thread, system tray icon (`pystray`), and desktop toast alerts. |

### Modular GUI Layer ([`gui_modules/`](file:///c:/file-date-sorter/gui_modules))
| File | Responsibility |
| :--- | :--- |
| [`gui_modules/app.py`](file:///c:/file-date-sorter/gui_modules/app.py) | Root CustomTkinter application window (`SmartFileOrganizerGUI`), tab navigation, theme manager, progress handling, atomic repaint coordinator. |
| [`gui_modules/theme_manager.py`](file:///c:/file-date-sorter/gui_modules/theme_manager.py) | Apple Glassmorphism design system: color palette tokens (`GLASS`), fonts (`FONTS`), glass panels (`glass_frame`), accent buttons (`accent_button`), status badges (`status_badge`), hover pulse micro-animations. |
| [`gui_modules/components.py`](file:///c:/file-date-sorter/gui_modules/components.py) | Reusable UI components: `HeaderCard`, `MetricCard`, `ActionButton`, `StyledEntry`, `FolderPicker`, `StatusBadge`, `GlassCard`. |
| [`gui_modules/context_menu.py`](file:///c:/file-date-sorter/gui_modules/context_menu.py) | Native right-click popups for file lists and preview items. |
| [`gui_modules/views/tab_sorter.py`](file:///c:/file-date-sorter/gui_modules/views/tab_sorter.py) | Organization & Date/Category/Extension sorting view. |
| [`gui_modules/views/tab_duplicates.py`](file:///c:/file-date-sorter/gui_modules/views/tab_duplicates.py) | Exact SHA-256 & Perceptual similarity duplicate finder and isolator. |
| [`gui_modules/views/tab_extractor.py`](file:///c:/file-date-sorter/gui_modules/views/tab_extractor.py) | Deep directory flattener and selective extension extractor. |
| [`gui_modules/views/tab_renamer.py`](file:///c:/file-date-sorter/gui_modules/views/tab_renamer.py) | Pattern tag batch renamer with live side-by-side preview. |
| [`gui_modules/views/tab_converter.py`](file:///c:/file-date-sorter/gui_modules/views/tab_converter.py) | Magic byte header inspector, extension fixer, audio/video/image converter. |
| [`gui_modules/views/tab_cleaner.py`](file:///c:/file-date-sorter/gui_modules/views/tab_cleaner.py) | OS junk file removal & standalone empty folder hierarchy cleaner. |
| [`gui_modules/views/tab_analytics.py`](file:///c:/file-date-sorter/gui_modules/views/tab_analytics.py) | Storage disk usage analyzer, category breakdown charts, and date span metrics. |
| [`gui_modules/views/tab_exclusions.py`](file:///c:/file-date-sorter/gui_modules/views/tab_exclusions.py) | Unified exclusion rules editor (folders, extensions, file patterns). |
| [`gui_modules/views/tab_people.py`](file:///c:/file-date-sorter/gui_modules/views/tab_people.py) | Face recognition manager, person tagging, face thumbnail viewer, shortcut generator. |
| [`gui_modules/views/tab_watcher.py`](file:///c:/file-date-sorter/gui_modules/views/tab_watcher.py) | Background folder monitoring controls and real-time event log viewer. |

### Build & Spec Artifacts
| File | Responsibility |
| :--- | :--- |
| [`build_exe.py`](file:///c:/file-date-sorter/build_exe.py) | PyInstaller automation script with asset bundling and optional code-signing hooks. |
| [`SmartFileOrganizer.spec`](file:///c:/file-date-sorter/SmartFileOrganizer.spec) | PyInstaller specification definition. |
| [`installer.iss`](file:///c:/file-date-sorter/installer.iss) | Inno Setup Windows installer compilation script. |

---

## Persistent Project Memory Pointer
- **Roadmap & Progress:** See [PLAN.md](file:///c:/file-date-sorter/PLAN.md)
- **Known Issues & Bugs:** See [docs/known-issues.md](file:///c:/file-date-sorter/docs/known-issues.md)
- **Hard Constraints & Policies:** See [docs/constraints.md](file:///c:/file-date-sorter/docs/constraints.md)
