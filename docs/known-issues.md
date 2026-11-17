# Known Issues

| Issue | Status | Evidence |
|-------|--------|----------|
| `Write-Progress` access‑denied warnings during `Compress-Archive` backup | Fixed (ignored – does not affect backup integrity) | Observed in backup step logs; archive created successfully |
| Missing `requirements.txt` and `installer.iss` paths during copy – files were renamed/moved earlier | Resolved | Updated copy script to use correct locations |
| `.git` permission errors prevent committing from this environment | Open | Need admin rights or run from a terminal with proper privileges |

*Add new issues here as they are discovered, and update the status accordingly.*