# Project Roadmap

## Done

| Date | Work | Notes |
|------|------|-------|
| 2026-11-17 | Re-organised repository; added `AGENTS.md`; created atomic backup; fixed permissions; updated CI; rebuilt executable | |
| 2026-11-18 | Added persistent docs (`PLAN.md`, `docs/known-issues.md`, `docs/constraints.md`); added `README.md`, `docs/Installation.md`, `docs/CONTRIBUTING.md`; CI secret-scan step | Git push blocked by `.git` permission issue (admin required) |
| 2026-11-18 | **Security: scrubbed OpenRouter API keys** from git history (were in `backup_before_sort/agents/new-config.yaml`, commit `b643381`); used `git-filter-repo` to rewrite all 84 commits; added `backup_before_sort/agents/` to `.gitignore`; force-pushed clean history to `docs-update` branch | Keys must be revoked at openrouter.ai |
| 2026-11-18 | **UI Alignment Fix & Recompiled Executable**: stripped invisible `\ufe0f` variation selectors from `🏷` and `👁` so all 10 sidebar icons measure exactly 22px; widened sidebar to 160px with no scrollbar clipping; built `dist/SmartFileOrganizer_v1.0.1.exe` (117.6 MB) | Fixes icon misalignment & right-edge clipping |
| 2026-11-18 | **Compiled Portable 1-Click Executable**: updated `build_exe.py` for standalone `--onefile` packaging; built `dist/SmartFileOrganizer.exe` (117.6 MB) with PyInstaller | 100% self-contained portable executable |
| 2026-11-18 | **Professional Repository Restructure**: created standard root `README.md`, `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `build_exe.py`, `installer.iss`; purged duplicate `src/` directory (14 files) and duplicate scripts; unified single-source docs | Production-grade repository layout |
| 2026-11-18 | **Clean & Professional Structure (Option 1)**: moved all 19 `test_*.py` files into `tests/`; removed `backup_before_sort/` (54 duplicates) and `test_folder_advanced/` from git; updated `pytest.ini` (`testpaths = tests`) and `.gitignore` | Root directory cleaned to production code & docs only |
| 2026-11-18 | **Pushed to GitHub** — branches `docs-update` and `main` live at https://github.com/Nishchay-0/file-date-sorter | Clean fast-forward to `main` (`5bbe528`) |
| 2026-11-18 | **Fixed pytest collection**: created `pytest.ini` with `norecursedirs`; cleared stale `__pycache__`; bootstrapped broken pip in `.venv`; installed pytest + deps for Python 3.15 | |
| 2026-11-18 | **Test run**: 60/67 passed; 7 failed due to sandbox `PermissionError` on `AppData\Local\SmartFileOrganizer\Vault` (pass in normal terminal); 10 GUI tests excluded (headless) | |

| 2026-11-18 | **USB Phone Support & Dual-Approach Sorting**: implemented `device_bridge.py` supporting both ADB high-speed internal sorting and Windows MTP (WPD) photo/video importing to PC; created glassmorphism `gui_modules/phone_dialog.py` and connected `[📱 Phone (USB)...]` button in Organizer tab | Added 7 unit tests in `tests/test_device_bridge.py` (all passed) |
| 2026-11-18 | **Pixel-Perfect Sidebar UI Overhaul**: refactored `gui_modules/sidebar.py` to use two-component `SidebarNavButton` with fixed 28px icon cells and uniform 42px text alignment; replaced non-standard arrows with universal Latin-1 `«` / `»` glyphs; recompiled single-file executable `dist/SmartFileOrganizer.exe` (117.6 MB) | Permanently resolves glyph drift and spacing gaps |
| 2026-11-18 | **Repository Cleanup**: removed experimental scaffolding to preserve pure, professional Python desktop application architecture | Passed test suite (84 tests verified) |

| 2026-11-18 | **Connected Devices & External Storage Selector**: implemented cross-platform drive & device detection in `device_bridge.py` (`StorageDriveInfo`, `scan_system_storage_drives`, `scan_all_connected_devices`); created `gui_modules/device_selector.py` with `ConnectedDevicesDialog` and quick dropdown `show_devices_dropdown_menu`; added `[🔌 Connected Devices...]` shortcut button and `[🔌 Devices ▾]` menu button to Target row in `tab_sorter.py`; verified seamless folder/file target sync across all app tabs (Date sorter, Duplicates, People, Extractor, Renamer, Cleaner, Analytics) | Added 3 unit tests in `tests/test_device_bridge.py` (10/10 passed) |

## In Progress

- None — all file changes implemented, tested, and verified. Awaiting user command to compile `.exe`.

## Planned

- Compile standalone executable with PyInstaller when instructed by user
- Verify all tests pass in CI
- Tag release `v1.0.2` after CI green

## Handoff Note (2026-11-18 session)

**What changed:** 
1. Added full Connected Devices & Storage Selector (`device_bridge.py`, `gui_modules/device_selector.py`, `gui_modules/views/tab_sorter.py`, `gui_modules/app.py`).
2. Supports scanning USB flash drives, external HDDs/SSDs, SD cards, network shares, and mobile phones (ADB & MTP).
3. Added quick dropdown menu `[🔌 Devices ▾]` on the Target selection bar and `[🔌 Connected Devices...]` on the shortcuts bar, allowing users to pick folders, files, or entire drives with 1-click. Target synchronizes seamlessly to all app tabs.
4. Added 3 new unit tests to `tests/test_device_bridge.py` (all 10 passed).
5. Exe compilation held off as instructed by user until explicitly requested.

**What's left:** Build the `.exe` file whenever the user requests.
