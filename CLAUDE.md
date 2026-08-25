# CLAUDE.md

> Read this file fully before searching or scanning the codebase. Only search for something if it's not already documented here. If you do have to search, add what you found back into this file before finishing, so the next session doesn't have to search again.

See [`AGENTS.md`](file:///c:/file-date-sorter%20-%20Copy/AGENTS.md) for the complete primary documentation, module map, critical directives, and run commands.

---

## ⚡ Critical Directives Quick Reference
1. **Zero Data Loss**: Always default to non-destructive operations (dry-run, safety zip backup, undo manifests, `send2trash`).
2. **Offline & Private**: 100% local execution for AI face sorting, hashing, and media transcoding. No external network traffic.
3. **Cloud Placeholder Safety**: Check `is_cloud_placeholder` before scanning/reading file bodies to avoid force-hydrating cloud files.
4. **Windows Path Resilience**: Support `\\?\` long paths via `fix_win_long_path`.
5. **Baseline Verification**: Run `python test_deployment.py` to ensure all 12 test engines pass.
6. **Continuous GitHub Sync**: Always stage, commit with clear messages, and push verified changes to GitHub (`origin/main`) upon task completion.

## 🚀 Quick Commands
- **Launch GUI**: `python run_sorter.py`
- **Run CLI**: `python cli.py --path "<path>"`
- **Run Deployment Test Suite**: `python test_deployment.py`
- **Build Standalone Exe**: `python build_exe.py`
