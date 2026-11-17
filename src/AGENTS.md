AGENT DIRECTIVE: Read this file fully before searching or scanning the codebase. Only search for something if it is not documented here. If you search for and discover new codebase structures, add what you found back into this file before finishing the task so future sessions do not need to repeat the search.

# Smart File Organizer Suite Pro — Working Agreement & Project Guide

## 🚨 Critical Non-Negotiable Hard Constraints

1. **Personal Data Protection & Zero-PII Leakage Policy (STRICT)**: Never commit or push personal data (PII) including real names, emails, credentials, user databases, or personal media. Use synthetic or anonymized fixtures only.
2. **Continuous GitHub Sync & Automated Commits**: Always stage, commit with clear descriptive semantic messages, and push all verified changes and task outputs to GitHub (`origin/main` / active branch) upon task completion, ensuring secrets hygiene and test verification before pushing.
3. **Zero-Deletion / Zero Data Loss Guarantee**: Destructive operations (move, delete, overwrite, rename) MUST always generate an atomic Zip backup vault and `.undo_manifest.json` before modifying files, with 1-click restore functionality.
4. **Cloud Placeholder Safety**: Always inspect Windows sparse/reparse cloud stub attributes (`is_cloud_placeholder` in `hashing.py`) before reading files to prevent triggering unintentional gigabyte downloads on OneDrive, iCloud, or Dropbox synced directories.
5. **Secrets & Hygiene Pre-Push Check**: Scan git diffs for credentials, tokens, or API keys before pushing; exclude sensitive files in `.gitignore`.
6. **No Telemetry / Data Sharing**: Never transmit or share user data to external servers without explicit consent (Constraint 002).
7. **No Silent Fallbacks**: Always surface degradation visibly (e.g. missing face models, permission errors) (Constraint 004).
8. **Dry-Run Exact Match**: Preview mode must match real execution exactly before confirmation (Constraint 006).
9. **Windows Path Resilience**: All paths must pass through `fix_win_long_path` (`\\?\` prefix support) and sanitize invalid NTFS characters.

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

### Docker Environment
```bash
# Build image
docker compose build

# Run CLI sorting with mounted target directory
docker run --rm -v "C:\Target\Path:/data" smart-file-organizer --path /data --sort-category category --dry-run

# Run full test suite in container
docker compose run --rm test
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
| [`config.py`](file:///c:/file-date-sorter/config.py) | Centralized constants: `FILE_CATEGORIES`, `COMMON_STOPWORDS`, `WIN_LONG_PATH_THRESHOLD`, `FILE_CHUNK_SIZE`, attribute bitmasks. |
| [`logger.py`](file:///c:/file-date-sorter/logger.py) | Centralized logging subsystem provider (`get_logger`, `setup_logging`) with level filtering and formatting. |
| [`settings_manager.py`](file:///c:/file-date-sorter/settings_manager.py) | JSON config manager (`%LOCALAPPDATA%/SmartFileOrganizer/settings.json`) for watcher preferences and UI defaults. |
| [`utils.py`](file:///c:/file-date-sorter/utils.py) | Cross-platform path normalization with Windows extended-length prefixing (`fix_win_long_path`) supporting standard and UNC network shares. |

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
| [`gui_modules/sidebar.py`](file:///c:/file-date-sorter/gui_modules/sidebar.py) | Right-side collapsible toolbar navigation (`RightSidebarToolbar`), icon+text buttons, active tool highlighting, glass styling. |
| [`gui_modules/theme_manager.py`](file:///c:/file-date-sorter/gui_modules/theme_manager.py) | Apple Glassmorphism design system: color palette tokens (`GLASS`, `LIGHT_THEME`, `DARK_THEME`), fonts (`FONTS`), glass panels (`glass_frame`), accent buttons (`accent_button`), status badges (`status_badge`), hover pulse micro-animations. |
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
| [`Dockerfile`](file:///c:/file-date-sorter/Dockerfile) | Production container specification based on Python 3.11-slim with OpenCV, ONNX, and Tkinter runtime. |
| [`docker-compose.yml`](file:///c:/file-date-sorter/docker-compose.yml) | Multi-service compose config for `sorter` (CLI), `test` (pytest), and `shell` (interactive). |
| [`docker-entrypoint.sh`](file:///c:/file-date-sorter/docker-entrypoint.sh) | Container entrypoint script routing CLI flags, test runner, and shell commands. |
| [`.dockerignore`](file:///c:/file-date-sorter/.dockerignore) | Docker build context exclusions for lightweight image generation. |
| [`DOCKER.md`](file:///c:/file-date-sorter/DOCKER.md) | Comprehensive usage guide for running, testing, and mounting volumes in Docker. |
| [`build_exe.py`](file:///c:/file-date-sorter/build_exe.py) | PyInstaller automation script with asset bundling and optional code-signing hooks. |
| [`SmartFileOrganizer.spec`](file:///c:/file-date-sorter/SmartFileOrganizer.spec) | PyInstaller specification definition. |
| [`installer.iss`](file:///c:/file-date-sorter/installer.iss) | Inno Setup Windows installer compilation script. |

---

## Persistent Project Memory Pointer
- **Roadmap & Progress:** See [PLAN.md](file:///c:/file-date-sorter/PLAN.md)
- **Known Issues & Bugs:** See [docs/known-issues.md](file:///c:/file-date-sorter/docs/known-issues.md)
- **Hard Constraints & Policies:** See [docs/constraints.md](file:///c:/file-date-sorter/docs/constraints.md)
