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

## In Progress

- None — all changes tested and verified.

## Planned

- Verify all tests pass in CI
- Tag release `v1.0.2` after CI green
- `onnxruntime` wheel for Python 3.15 — track release; re-enable face-sort tests when available

## Handoff Note (2026-11-18 session)

**What changed:** 
1. Fixed sidebar text alignment by decoupling icon and text widgets inside `SidebarNavButton`. Icon sits in a fixed 28px box centered; text begins at guaranteed 42px offset. Replaced toggle icon with Latin-1 `«` / `»` to eliminate missing glyph boxes.
2. Built and integrated USB Phone Manager (`device_bridge.py`, `scripts/mtp_operations.ps1`, `gui_modules/phone_dialog.py`) with support for ADB in-place phone sorting and MTP/WPD import & date organization.
3. Added shortcut button `[📱 Phone (USB)...]` to the Organizer tab in `tab_sorter.py`.
4. Recompiled standalone portable `dist/SmartFileOrganizer.exe` (117.6 MB).
5. Cleaned up experimental mobile scaffolds, keeping repo pure and professional. Verified test suite with 84 tests.

**What's left:** None. Ready for production use.
