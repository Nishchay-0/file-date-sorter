# Smart File Organizer — Development Roadmap

## ✅ Done

### v1.0.0 Core Release
- **[Date: Multiple commits]** 10-tool suite (Sorter, Duplicates, Converter, Renamer, Extractor, Cleaner, Empty Folder Cleaner, Analytics, Exclusions, Watcher)
- **[Commit: 154951d]** Face-based People sorter with clustering and neural model auto-download
- **[Commit: 35195ef]** Watch-folder auto-organize mode + watchdog debouncing
- **[Commit: a01f282]** App icon, central version, Inno Setup installer, code-signing hook, CI workflow
- **[Commit: 35c6d8d]** GUI scrolling tab mapping fix
- **[Commit: 76ecead]** Zero-deletion banner positioning
- **[Commit: 74dce12]** ModernFileDateSorterGUI class definition fix
- **[Commit: be50538]** Installer artifact ignoring, Windows test cleanup
- **[Commit: a0fde0a]** OneDrive Safe Mode, truncation safety guards, face detection perf optimization
- **[Commit: fb415a7]** Face clustering mega-cluster fix, complete-linkage cosine, thumbnails, search/sort/filter, gallery modal
- **[Commit: 0d60ec1]** Checkbox desync fix across scrollable frames, atomic widget repaint engine, banner padding fix
- **[Commit: e08511c (this session)]** Reverted d53b773 (atomic checkbox builder) — moved to git history as intentional rollback

### Testing Infrastructure
- Pytest test suite with 15+ test files
- Regression tests for face clustering, scrolling, checkbox state sync
- CI workflow (GitHub Actions)

---

## 🚧 In Progress

- [ ] **Face model cache robustness** — `.people_cache.json` invalidation logic needs strengthening
- [ ] **Scrolling edge cases** — Some tab widgets may still have repaint sync issues (atomic engine just deployed)
- [ ] **Performance profiling** — Multi-threaded face scanning working; identify bottlenecks in other tools

---

## 📋 Planned (Priority Order)

### High Priority (Next Sprint)
1. **Verification testing** — Run full regression suite on Windows, test installer output
2. **Known issues audit** — Create `docs/known-issues.md` with confirmed bugs + status
3. **Cache strategy** — Document and harden face model + `.people_cache.json` cache invalidation
4. **Code coverage** — Target 75%+ coverage on core modules (sorter_core, face_engine, hashing)

### Medium Priority (Post-Sprint)
5. **Batch operation UX** — Add progress cancellation for long-running duplicates scan, face detection
6. **Exclusion engine audit** — Verify `.git`, `node_modules`, custom paths respected across all 10 tools
7. **CLI parity** — Ensure all GUI features available via CLI with equivalent options
8. **Model management UI** — Explicit face model download/update/delete in settings tab

### Lower Priority
9. Cross-platform testing (macOS, Linux) — low priority given Windows-first constraint
10. Performance: Parallel hashing across cores, incremental face encoding cache

---

## Decision Log

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| ??? | Windows-first platform focus | Installation & deployment complexity; most users on Windows | Locked |
| ??? | PyQt5 for GUI | Mature, cross-platform, good Windows native look | Locked |
| ??? | System Vault backup before destructive ops | HARD CONSTRAINT: No irreversible action without undo path | Locked |
| ??? | ONNX face models (not TensorFlow) | Smaller runtime footprint, no heavy ML framework deps | Locked |
| [This session] | Revert atomic checkbox builder (d53b773) | Builder complexity; simpler approach pending review | Pending review |

---

## Metrics & Acceptance Criteria

### Per-Feature Acceptance Bar
- **New tool (Sorter, Duplicates, etc.):** Dry-run matches actual execution, undo works, 90%+ category accuracy
- **Face clustering:** Silhouette score > 0.65, visual verification (gallery modal) mandatory
- **Performance:** Long operations (>5 sec) must show progress bar + cancel button
- **Installer:** Silent install works, uninstall cleans registry, no SmartScreen warning on code-signed build
- **Testing:** No regression test ships for a bug fix = fix not complete

---

## Handoff Notes (Current)

**From: This session (2026-08-18)**  
**What changed:**
- Reverted commit d53b773 (atomic checkbox builder) → revert commit e08511c pushed to main
- Created CLAUDE.md (project summary + module map)
- About to create PLAN.md, known-issues.md, constraints.md

**Tests run:** 
- Git revert executed successfully
- No regression tests run yet (next step)

**What's left:**
- Complete persistent documentation setup (known-issues.md, constraints.md, decisions.md)
- Verify checkbox desync fix (0d60ec1) with actual scrolling stress tests
- Clear up specs folder gap — restore or document why removed

**To-do for next session (priority order):**
1. Run `pytest -v` — verify no baseline failures
2. Read & update known-issues.md with any recent bugs found
3. Test face detection on low-memory system (edge case stress)
4. Audit exclusion engine (verify `.git`, `node_modules` skipped everywhere)
5. Create face model cache invalidation strategy doc

**Evidence:**  
- Commit: e08511c (revert successful)
- Git log: 0d60ec1 (latest on main after revert)
- Documentation: CLAUDE.md created with full module map
