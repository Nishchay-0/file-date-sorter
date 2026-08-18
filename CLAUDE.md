# Smart File Organizer — Project Summary

## Project Header

**PROJECT:** Smart File Organizer Suite  
**PURPOSE:** Desktop application and CLI utility for organizing, extracting, deduplicating, renaming, and cleaning files across directory trees with unified exclusion engine and system vault backup/undo.  
**STACK:** Python 3.11+, PyQt5 (GUI), PyInstaller (packaging), pytest (testing), OpenCV + ONNX (face detection)  
**HOW TO RUN:**
- **GUI:** `python gui.py` or `python run_sorter.py`
- **CLI:** `python cli.py --help`
- **Tests:** `pytest` or `python -m pytest tests/ -v`
- **Build exe:** `python build_exe.py`
- **Build installer:** `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

**HARD CONSTRAINTS:**
- No user data transmitted without explicit consent — audit all dependencies for telemetry
- Every destructive operation (delete, overwrite, rename) must have backup/undo capability via System Vault
- Long-running operations must show progress bar and allow cancellation without losing completed work
- No silent fallbacks — surface degradation visibly (e.g., missing models)
- Dry-run preview must be exact match to actual execution before confirmation
- Windows target platform; cross-platform compatibility secondary

---

## Module Map

### Core Sorting & Organization
| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `sorter_core.py` | Main sorting logic engine — handles recursion, category mapping, exclusions | `SmartFileDateSorter`, `organize_tree()`, `categorize_file()` |
| `face_sort.py` | Face-based People category sorter using ONNX models | `FaceSortEngine`, `detect_faces()`, `cluster_faces()` |
| `face_engine.py` | OpenCV/ONNX model loading and face detection primitives | `FaceDetector`, `load_model()`, `detect_and_encode()` |
| `cli.py` | Command-line interface with argument parsing and dry-run logic | `main()`, argument handlers |
| `hashing.py` | SHA-256 file hashing and duplicate detection | `compute_file_hash()`, `find_duplicates()` |

### GUI & UI
| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `gui_modules/app.py` | Main PyQt5 application, tabbed interface, state management | `ModernFileDateSorterGUI`, `show_tab()`, `apply_settings()` |
| `gui_modules/components.py` | Reusable UI components (buttons, sliders, checkboxes) | `ModernButton`, `ModernSlider`, `create_atomic_checkbox()` |
| `gui_modules/context_menu.py` | Right-click context menus for trees and lists | `ContextMenu`, `show_context_menu()` |
| `gui_modules/views/tab_*.py` | Individual tab implementations (10 tabs: sorter, duplicates, converter, etc.) | Tab-specific logic |

### Settings & State
| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `settings_manager.py` | Persistent config storage (JSON-based) | `SettingsManager`, `load()`, `save()`, `get()`, `set()` |
| `watcher_service.py` | File system watcher for auto-organize mode | `WatcherService`, `on_file_change()` |
| `version.py` | Central version constant | `__version__` |

### Testing
| File | Purpose |
|------|---------|
| `test_*.py` | Unit and integration tests (pytest) |
| `benchmark_*.py` | Performance benchmarking |
| `scratch/` | Ad-hoc test scripts and experiments |

### Build & Packaging
| File | Purpose |
|------|---------|
| `build_exe.py` | PyInstaller build + code-signing hook |
| `SmartFileOrganizer.spec` | PyInstaller spec file |
| `installer.iss` | Inno Setup installer configuration |

### Assets & Data
| File | Purpose |
|------|---------|
| `models/` | Face detection ONNX models (downloaded on first run) |
| `assets/` | Icons, images, themes |
| `.people_cache.json` | Cached face detection results |

---

## Recent History & Current State

**Latest commit (HEAD):** `0d60ec1` — "Fix checkbox desync sliver bug across scrollable frames, add atomic widget repaint engine, fix guarantee banner padding, and add regression test"

**Just completed (this session):** Reverted commit `d53b773` ("Add create_atomic_checkbox component builder...") — revert commit `e08511c` pushed to main.

**Active areas of work:**
- GUI state sync (checkboxes, scrolling) — atomic repaint engine
- Face clustering and People sorter
- Watch-folder auto-organize
- Performance optimization (face scanning, hashing)

**Known gaps/debt:**
- Specs folder removed (was in `specs/001-baseline-spec/`) — design docs not in repo
- No formal PLAN.md or known-issues.md yet
- `.people_cache.json` and model files need more robust cache invalidation

---

## How to Run & Test

### Development Setup
```bash
pip install -r requirements.txt
python gui.py           # Launch GUI
python cli.py --help    # CLI help
pytest -v              # Run all tests
```

### Dry-Run / Preview Mode
All destructive operations support `--dry-run` flag (CLI) or checkbox in GUI. Preview must show exact files that will be affected before confirmation.

### System Vault (Backup & Undo)
- Generated automatically before destructive operations
- Stored as zip in user's system backup location
- 1-click undo via manifest files (`.undo_manifest.json`)

---

## Key Dependencies & Constraints

| Dependency | Version | Role | Constraint |
|------------|---------|------|-----------|
| PyQt5 | 5.15+ | GUI framework | Windows primary; code path for other OS not heavily tested |
| OpenCV (cv2) | 4.5+ | Image processing | Face detection preprocessing |
| ONNX Runtime | 1.x | ML inference | Face detection & recognition models |
| PyInstaller | 5.x+ | Packaging | Must include models/ in bundle |
| pytest | 7.x+ | Testing | Requires fixtures for temp dirs & cleanup |

---

## Open Questions & Decisions Log

(To be filled as issues are discovered)

- [ ] Face model auto-download: How to handle offline scenarios?
- [ ] Cache invalidation: Current `.people_cache.json` logic — is mtime-based sufficient?
- [ ] Scrolling desync: Root cause was checkbox repaint during scroll — do all tab widgets have this risk?

---

## Session Handoff Template

When ending a session, log:
```markdown
### Session: [date]
**What changed:** [files modified, features added, bugs fixed]
**Tests run:** [pass/fail, coverage notes]
**What's left:** [blockers, incomplete features]
**To-do for next session:** [priority order]
**Evidence:** [commit hashes, test runs, screenshots]
```
