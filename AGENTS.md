> Read this file fully before searching or scanning the codebase. Only search for something if it's not already documented here. If you do have to search, add what you found back into this file before finishing, so the next session doesn't have to search again.

# Smart File Organizer Suite Pro — Working Agreement & Project Guide

## Project Header

**PROJECT:** Smart File Organizer Suite Pro  
**PURPOSE:** Desktop application and CLI utility for organizing, extracting, deduplicating, renaming, and cleaning files across directory trees with unified exclusion engine, face-based sorting, and system vault backup/undo.  
**STACK:** Python 3.11+, CustomTkinter / Tkinter (GUI), PyInstaller (packaging), pytest (testing), OpenCV + ONNX / SciPy (face detection & clustering)  
**HOW TO RUN:**
- **GUI:** `python gui.py` or `python run_sorter.py`
- **CLI:** `python cli.py --help`
- **Tests:** `$env:TCL_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tcl8.6"; $env:TK_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tk8.6"; py -3.14 -m pytest -v`
- **Build exe:** `python build_exe.py`
- **Build installer:** `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

**HARD CONSTRAINTS (CRITICAL & NON-NEGOTIABLE):**
1. **Always Commit & Push to GitHub:** At the end of every task or session, verify all changes, run tests, commit with clear messages, and push to `origin/main` on GitHub.
2. **Zero Telemetry / Data Sharing:** Never transmit or share user data to external servers without explicit consent (Constraint 002).
3. **No Irreversible Destructive Actions:** Every destructive action (delete, overwrite, rename, move) must create a System Vault backup (`.undo_manifest.json`) and support 1-click restore (Constraint 001).
4. **Secrets & Hygiene Pre-Push Check:** Scan git diffs for credentials, tokens, or API keys before pushing; exclude sensitive files in `.gitignore`.
5. **No Silent Fallbacks:** Always surface degradation visibly (e.g. missing face models, permission errors) (Constraint 004).
6. **Dry-Run Exact Match:** Preview mode must match real execution exactly (Constraint 006).
7. **Progress UI & Cancellation:** Any operation > 5 seconds must provide progress tracking and safe cancellation without discarding cached progress (Constraint 005).
8. **Windows-First Target:** Primary target is Windows 10/11; preserve long-path support (`\\?\` prefix) and Windows-safe temp dir handling (Constraint 007).

---

## Module Map

### Core Logic & Engines
| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `sorter_core.py` | Primary organizing engine: directory recursion, category rules, exclusions, deduplication, safe cleaning | `SmartFileDateSorter`, `organize_tree()`, `gather_files()`, `find_duplicates()`, `clean_empty_dirs()`, `is_path_excluded()` |
| `face_sort.py` | Face-based People sorter with complete-linkage cosine thresholding & content-aware caching | `FaceSortEngine`, `detect_faces()`, `cluster_faces()`, `_cache_key_for_file()` |
| `hashing.py` | SHA-256 / Blake2 hashing, quick size filters, binary comparison for duplicate detection | `compute_file_hash()`, `find_duplicates_fast()`, `compare_files()` |
| `watcher_service.py` | Real-time directory monitoring with watchdog debouncing | `FolderWatcherService`, `DirectoryChangeHandler` |
| `settings_manager.py` | JSON configuration persistence with default fallbacks | `SettingsManager`, `load()`, `save()`, `get()`, `set()` |
| `utils.py` | Cross-platform & Windows long-path prefix helper | `fix_win_long_path()` |
| `version.py` | Single source of truth for semantic application version | `__version__ = "1.0.0"` |
| `cli.py` | Command-line interface with arg parsing, progress reporting, and dry-run execution | `main()`, `parse_args()`, CLI dispatchers |

### GUI Application (`gui_modules/`)
| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `gui.py` / `run_sorter.py` | Clean facade entry points into GUI package | `main()` |
| `gui_modules/__init__.py` | Package exports for GUI classes | `SmartFileOrganizerGUI`, `ModernFileDateSorterGUI` |
| `gui_modules/app.py` | Main CustomTkinter window, tab orchestrator, theme manager, atomic repaint coordinator | `SmartFileOrganizerGUI`, `_switch_tab()`, `_atomic_repaint_tab_widgets()` |
| `gui_modules/components.py` | Reusable custom UI components (buttons, headers, banners, cards) | `ModernButton`, `BannerWidget`, `ProgressCard` |
| `gui_modules/context_menu.py` | Right-click context menus for file lists and treeviews | `ContextMenuHelper`, `show_menu()` |
| `gui_modules/views/tab_sorter.py` | Date/Category organizer tab | `SorterTab` |
| `gui_modules/views/tab_duplicates.py` | Duplicate finder and resolver tab | `DuplicatesTab` |
| `gui_modules/views/tab_people.py` | Face recognition & People clustering tab with gallery modal | `PeopleTab`, `FaceGalleryModal` |
| `gui_modules/views/tab_converter.py` | Media / document conversion tab | `ConverterTab` |
| `gui_modules/views/tab_renamer.py` | Batch regex / template renamer tab | `RenamerTab` |
| `gui_modules/views/tab_extractor.py` | Archive extraction tab | `ExtractorTab` |
| `gui_modules/views/tab_cleaner.py` | Empty folder / junk cleaner tab | `CleanerTab` |
| `gui_modules/views/tab_exclusions.py` | Global exclusion rule management tab | `ExclusionsTab` |
| `gui_modules/views/tab_watcher.py` | Background folder monitoring tab | `WatcherTab` |
| `gui_modules/views/tab_analytics.py` | Storage & organization analytics dashboard tab | `AnalyticsTab` |

### Packaging & Distribution
| File | Purpose |
|------|---------|
| `build_exe.py` | PyInstaller build script with code signing integration |
| `SmartFileOrganizer.spec` | PyInstaller specification configuration |
| `installer.iss` | Inno Setup Windows installer script |
| `requirements.txt` | Python runtime dependencies |

---

## Persistent Project Memory Pointer
- **Roadmap & Progress:** See [PLAN.md](file:///c:/file-date-sorter/PLAN.md)
- **Known Issues & Bugs:** See [docs/known-issues.md](file:///c:/file-date-sorter/docs/known-issues.md)
- **Hard Constraints & Policies:** See [docs/constraints.md](file:///c:/file-date-sorter/docs/constraints.md)
