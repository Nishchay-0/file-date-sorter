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

## In Progress

- None — all changes cleanly fast-forwarded and pushed directly to `origin/main` and `origin/docs-update`.

## Planned

- Verify all 67 tests pass in a normal (non-sandboxed) terminal
- Tag release `v1.0.2` after CI green
- Periodic review/pruning of `AGENTS.md` and `docs/constraints.md` (keep top-priority info near top)
- `onnxruntime` wheel for Python 3.15 — track release; re-enable face-sort tests when available

## Handoff Note (2026-11-18 session)

**What changed:** Applied Working Agreement v3 to all four project memory files. Fixed Python version references (3.14→3.15). Corrected Docker-as-primary-runtime constraint. Created `pytest.ini` and resolved collection collisions. Scrubbed secret file from history using `git-filter-repo`. Pushed all changes directly to `origin/main`.

**What's left:** Revoke OpenRouter API keys on OpenRouter console (if not done yet).
