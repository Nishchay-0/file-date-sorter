# Known Issues

| Issue | Status | Evidence |
|-------|--------|----------|
| `Write-Progress` access‑denied warnings during `Compress-Archive` backup | Fixed (ignored – does not affect backup integrity) | Observed in backup step logs; archive created successfully |
| Missing `requirements.txt` and `installer.iss` paths during copy – files were renamed/moved earlier | Resolved | Updated copy script to use correct locations |
| `.git` permission errors prevent committing from this environment | Open | Need admin rights or run from a terminal with proper privileges |
| Stale `__pycache__` from Python 3.14 caused pytest module-import collisions with `backup_before_sort/` duplicates | Fixed | Added `pytest.ini` with `norecursedirs` to exclude backup dirs; cleared all `__pycache__` |
| Python upgraded from 3.14 to 3.15; `onnxruntime` has no wheel for 3.15 yet | Open | `pip install onnxruntime` fails; face-sort features require ONNX. Use venv at `.venv/` |
| 7 tests fail in sandboxed environments due to `PermissionError` on `AppData\Local\SmartFileOrganizer\Vault` | Open (environment-specific) | Tests pass in a normal terminal; sandbox blocks `AppData\Local` writes |

*Add new issues here as they are discovered, and update the status accordingly.*