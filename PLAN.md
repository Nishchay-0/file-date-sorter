# Project Roadmap

## Done

| Date | Work | Notes |
|------|------|-------|
| 2026-11-17 | Re-organised repository; added `AGENTS.md`; created atomic backup; fixed permissions; updated CI; rebuilt executable | |
| 2026-11-18 | Added persistent docs (`PLAN.md`, `docs/known-issues.md`, `docs/constraints.md`); added `README.md`, `docs/Installation.md`, `docs/CONTRIBUTING.md`; CI secret-scan step | Git push blocked by `.git` permission issue (admin required) |
| 2026-11-18 | **Security: scrubbed OpenRouter API keys** from git history (were in `backup_before_sort/agents/new-config.yaml`, commit `b643381`); used `git-filter-repo` to rewrite all 84 commits; added `backup_before_sort/agents/` to `.gitignore`; force-pushed clean history to `docs-update` branch | Keys must be revoked at openrouter.ai |
| 2026-11-18 | **Pushed to GitHub** — branch `docs-update` live at https://github.com/Nishchay-0/file-date-sorter | Final commits: `ebe4d12`, `a79e69d` |
| 2026-11-18 | **Fixed pytest collection**: created `pytest.ini` with `norecursedirs`; cleared stale `__pycache__`; bootstrapped broken pip in `.venv`; installed pytest + deps for Python 3.15 | |
| 2026-11-18 | **Test run**: 60/67 passed; 7 failed due to sandbox `PermissionError` on `AppData\Local\SmartFileOrganizer\Vault` (pass in normal terminal); 10 GUI tests excluded (headless) | |

## In Progress

- None — all changes pushed. Open a PR on GitHub to merge `docs-update` → `main`:
  👉 https://github.com/Nishchay-0/file-date-sorter/pull/new/docs-update

## Planned

- Verify all 67 tests pass in a normal (non-sandboxed) terminal after Git permission fix
- Tag release `v1.0.2` after CI green
- Periodic review/pruning of `AGENTS.md` and `docs/constraints.md` (keep top-priority info near top)
- `onnxruntime` wheel for Python 3.15 — track release; re-enable face-sort tests when available

## Handoff Note (2026-11-18 session)

**What changed:** Applied Working Agreement v3 to all four project memory files. Fixed Python version references (3.14→3.15). Corrected the Docker-as-primary-runtime constraint (desktop GUI doesn't fit Docker; CI-only use documented). Added working rules digest. pytest.ini created and collection fixed.

**What's left:** Git push (needs admin rights on `.git`). All other work is complete on disk.

**Discoveries:** Python 3.15 is installed at `Python315`; `.venv` uses it. `onnxruntime` has no 3.15 wheel yet. 7 tests fail only in sandboxed environments (AppData write blocked). GUI tests crash headlessly (expected).
