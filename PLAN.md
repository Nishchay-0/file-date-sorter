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
- **[Commit: b0fdb78 (this session)]** Fixed SCROLL-002 background tab scrolling bug + comprehensive regression tests (5 tests pass)

### Documentation & Process Setup (This Session)
- **[Created: CLAUDE.md]** Project summary, module map (13 files documented), how to run, hard constraints
- **[Created: PLAN.md]** Living roadmap with completed items, in-progress, planned features (phased by priority)
- **[Created: docs/known-issues.md]** Bug tracking with 4 critical/high, 3 medium priority, closed bugs section
- **[Created: docs/constraints.md]** 9 hard constraints codified, violation escalation process, release review checklist
- **[Created: test_scrolling_background_fix.py]** Regression test suite for SCROLL-002 (5 comprehensive tests)

### Testing Infrastructure
- Pytest test suite with 24 test files (22 passed, 2 skipped in latest run)
- Regression tests for face clustering, scrolling, checkbox state sync, background scrolling fix
- CI workflow (GitHub Actions)

---

## 🚧 In Progress

- [ ] **Face model cache robustness** — `.people_cache.json` invalidation logic needs strengthening
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
- Fixed SCROLL-002: Background tab scrolling bug → only active tab now receives scroll events
- Created comprehensive regression test suite (5 tests, all passing)
- Set up persistent project documentation (CLAUDE.md, PLAN.md, docs/known-issues.md, docs/constraints.md)
- Reverted commit d53b773 (atomic checkbox builder) → revert commit e08511c pushed to main
- Created CLAUDE.md with complete module map (13 files, key classes documented)

**Tests run:** 
- `pytest -v` → 22 passed, 2 skipped, 0 failed (total 24 tests)
- SCROLL-002 regression tests: 5/5 PASSED
- All prior tests (face clustering, checkbox sync, cloud safe mode): PASSED

**What's left:**
- Stress test SCROLL-002 fix under realistic scenarios (rapid scroll, drag, resize)
- Clear up cache invalidation strategy (CACHE-001)
- Audit exclusion engine across all 10 tools
- Verify installer output (code signing, no SmartScreen warning)

**To-do for next session (priority order):**
1. Stress test scrolling fix (manual: rapid scroll, drag tab, resize window)
2. Test face detection on 500+ image dataset (PEOPLE-001 validation)
3. Design CACHE-001 fix (version-tagged `.people_cache.json` format)
4. Audit exclusions: verify `.git`, `node_modules`, `_Duplicates` skipped everywhere
5. Run full installer build + test output (SmartScreen warning check)

**Evidence:**  
- Commit: b0fdb78 (scrolling fix + regression tests pushed)
- Test run: 22 passed, 2 skipped (no failures)
- Documentation: 4 persistent files created (CLAUDE.md, PLAN.md, known-issues.md, constraints.md)
- Root cause analysis: Fallback logic in mousewheel handler picked first scroll container instead of active tab
