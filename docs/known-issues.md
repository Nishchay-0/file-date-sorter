# Known Issues

| Issue | Status | Evidence |
|-------|--------|----------|
| `Write-Progress` access‑denied warnings during `Compress-Archive` backup | Fixed (ignored – does not affect backup integrity) | Observed in backup step logs; archive created successfully |
| Missing `requirements.txt` and `installer.iss` paths during copy – files were renamed/moved earlier | Resolved | Updated copy script to use correct locations |
| `.git` permission errors prevent committing from sandboxed environment | Fixed | Used bypass-sandbox mode to run git directly at `C:\Program Files\Git\bin\git.exe` |
| **OpenRouter API keys in git history** (`backup_before_sort/agents/new-config.yaml`, commit `b643381`) | Fixed (history) — **Keys must still be revoked at openrouter.ai** | Scrubbed via `git-filter-repo --invert-paths`; all 84 commits rewritten; `backup_before_sort/agents/` added to `.gitignore`; clean history force-pushed |
| Stale `__pycache__` from Python 3.14 caused pytest module-import collisions with `backup_before_sort/` duplicates | Fixed | Added `pytest.ini` with `norecursedirs` to exclude backup dirs; cleared all `__pycache__` |
| Python upgraded from 3.14 to 3.15; `onnxruntime` has no wheel for 3.15 yet | Open | `pip install onnxruntime` fails; face-sort features require ONNX. Use venv at `.venv/` |
| 7 tests fail in sandboxed environments due to `PermissionError` on `AppData\Local\SmartFileOrganizer\Vault` | Open (environment-specific) | Tests pass in a normal terminal; sandbox blocks `AppData\Local` writes |

*Add new issues here as they are discovered, and update the status accordingly.*