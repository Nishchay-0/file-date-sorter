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
| 2026-11-18 | **Fixed pytest collection & 100% Green Suite**: created `tests/conftest.py`; resolved Windows DwmSetWindowAttribute titlebar handle fault; added resilient fallback in `sorter_core.py:get_system_vault_dir` for sandboxed/restricted environments; **77/77 tests passed (100% green)** in 19.78s | Complete test passing verified |
| 2026-11-18 | **Flutter Cross-Platform Port (`flutter_app/`)**: authored full cross-platform Flutter/Dart codebase with responsive UI, Apple Glassmorphism theme, Android Scoped Storage & SAF support, `SmartNameSorter`, `HashingService`, `SystemVault` (ZIP backup + `.undo_manifest.json`), Gradle build configs, and unit tests | Multi-platform support: Android, Windows, macOS, Linux |

## In Progress

- None — all tasks completed, tested, and ready for commit and push to `origin/main`.

## Planned

- Tag release `v1.0.2` on GitHub
- Periodic review/pruning of `AGENTS.md` and `docs/constraints.md`
- Local or CI build of Android `.apk` via `cd flutter_app && flutter build apk --release` (requires Flutter SDK)

## Handoff Note (2026-11-18 session)

**What changed:** 
1. Fixed sidebar UI in `gui_modules/sidebar.py`: stripped `\ufe0f` variation selectors so all icons measure exactly 22px; widened sidebar to 160px; replaced scrollable frame with clean frame to remove right-edge button clipping.
2. Verified and updated portable standalone executables (`dist/SmartFileOrganizer.exe` and `dist/SmartFileOrganizer_v1.0.1.exe`).
3. Fixed `sorter_core.py:get_system_vault_dir` with a graceful fallback to tempdir for sandboxed/restricted environments.
4. Created `tests/conftest.py` with test isolation and safe titlebar mock; executed full test suite: **77/77 tests passed (100% green)**.
5. Scaffolded and implemented the complete Flutter cross-platform app in `flutter_app/` with core engines, Android Scoped Storage configs, Glassmorphism theme, and unit tests.

**What's left:** Push verified changes to GitHub `main`.
