<<<<<<< HEAD
# Smart File Organizer — Development Roadmap & Working Plan
=======
# PLAN.md — Living Roadmap
>>>>>>> origin/main

## 🏁 Completed Milestones

<<<<<<< HEAD
### Core Capabilities & Stability
- **[Release 1.0.0]** 10-tool suite (Sorter, Duplicates, Converter, Renamer, Extractor, Cleaner, Empty Folder Cleaner, Analytics, Exclusions, Watcher)
- **[Face Sorting Engine]** Face-based People sorter with complete-linkage cosine thresholding & auto-download
- **[Cloud Safety]** OneDrive / iCloud / Dropbox Safe Mode with placeholder protection
- **[GUI Stability]** Background tab scrolling fix (`SCROLL-002`) & atomic checkbox state sync (`SCROLL-001`)
- **[Cache Hardening]** Content-aware cache key hashing (`CACHE-001`) in `face_sort.py`
- **[Exclusion Engine]** Default exclusion protection for `.git`, `node_modules`, `_Duplicates`, etc. (`EXC-001`, `EXC-002`)
- **[Working Agreement & Documentation]** Initialized and aligned self-enforcing working agreement files (`CLAUDE.md`, `AGENTS.md`, `PLAN.md`, `docs/known-issues.md`, `docs/constraints.md`)
=======
| Date / Commit | Milestone | Details |
| :--- | :--- | :--- |
| `154951d` | **Face Sorter & Hashing Extraction** | Added ONNX + OpenCV face sorting pipeline (`face_sort.py`), extracted modular hashing utilities (`hashing.py`), and fixed initial scroll desync issues. |
| `a0fde0a` | **OneDrive & Cloud Safe Mode** | Implemented cloud placeholder stub detection (`is_cloud_placeholder`), attribute parsing, and safety guards preventing unintended file hydration. |
| `fb415a7` | **Face Clustering Optimization & UI** | Implemented complete-linkage cosine thresholding to prevent mega-cluster absorption, thumbnail strips, search/sort/filter bar, date ranges, and gallery modal. |
| `0d60ec1` | **Atomic Widget Repaint & Scroll Fix** | Resolved checkbox desync sliver bug across CustomTkinter scrollable frames with atomic state repaint engines. |
| `d53b773` | **10-Tab Atomic Checkbox Sync Suite** | Added `create_atomic_checkbox` component builder and full-application 10-tab atomic state verification suite. |
| 2026-08-25 | **Persistent Memory & GitHub Auto-Sync** | Initialized `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `docs/known-issues.md`, and `docs/constraints.md` with continuous GitHub sync rule. |
>>>>>>> origin/main

---

## 🚧 In Progress

<<<<<<< HEAD
- [ ] **Multi-threaded Hashing Pool (PERF-001)** — Scale duplicate scanner to 100k+ files smoothly
- [ ] **Offline Face Model Management (MODEL-001)** — Local model file browser and graceful offline UX
=======
- **System Memory & Baseline Maintenance**: Continuously updating persistent documentation and monitoring regression baselines across all 12 test engines.
>>>>>>> origin/main

---

## 📋 Planned Enhancements

<<<<<<< HEAD
### Phase 1: Performance & Offline Resiliency
1. Implement worker pool for parallel duplicate hashing (`hashing.py`)
2. Add manual model import / offline prompt in `PeopleTab` (`tab_people.py`)

### Phase 2: Packaging & CI Verification
3. Verify Inno Setup installer compilation with code signing hooks
4. Automate GitHub Actions CI release workflow
=======
- [ ] **Performance Benchmarking on Massive Media Libraries**: Extend `benchmark_face_sort.py` for 50k+ image/video datasets.
- [ ] **Additional Archive Format Transcoding**: Expand `tab_converter.py` magic-byte extraction to support modern archive tarballs (e.g. zstd, xz).
- [ ] **Enhanced EXIF Geolocation Filtering**: Add optional country/city location grouping in date sorter if GPS tags exist.
>>>>>>> origin/main

---

## 📝 Session Handoff Notes

<<<<<<< HEAD
| Decision | Rationale | Status |
|----------|-----------|--------|
| Git commit & push rule | Keep remote GitHub repository synchronized after every verified task | ✅ LOCKED (Constraint 010) |
| Content-aware cache key | Prevents stale cache hit when timestamp is preserved | ✅ LOCKED (Constraint 003) |
| System Vault backup | Protects against accidental data loss with 1-click restore | ✅ LOCKED (Constraint 001) |
| CustomTkinter UI | Fast native desktop styling with dark/light mode support | ✅ LOCKED |

---

## Session Handoff Note (2026-08-25)

**What changed:**
- Established Universal Project Setup & Self-Enforcing Working Agreement
- Created and synchronized `CLAUDE.md`, `AGENTS.md`, `docs/constraints.md`, `docs/known-issues.md`, and `PLAN.md`
- Embedded mandatory instruction at the top of `CLAUDE.md`/`AGENTS.md` to prevent repetitive full codebase scans
- Codified `CONSTRAINT-010`: Always commit and push verified changes to GitHub on task completion
- Verified full test suite across GUI, Face Sorter, Exclusion Engine, and Cloud Safe Mode (18/18 tests passed)

**Tests run:**
- `test_scrolling_background_fix.py`: 5 passed
- `test_gui_atomic_checkbox_sync.py`: 3 passed
- `test_people_sorter.py`: 6 passed
- `test_full_duplicate_tool_verification.py`: 1 passed
- `test_super_duplicates.py`: 1 passed
- `test_cloud_safe_mode.py`: 5 passed
- Total: 18 passed, 0 failed

**Next steps:**
- Continue development per roadmap, verifying and committing/pushing after each task.
=======
- **Current Status**: All 12 automated deployment tests (`test_deployment.py`) pass with 100% success.
- **Git Sync**: Automatic staging, committing, and pushing to `origin/main` active for every task.
>>>>>>> origin/main
