# Smart File Organizer — Development Roadmap & Working Plan

## ✅ Done

### Core Capabilities & Stability
- **[Release 1.0.0]** 10-tool suite (Sorter, Duplicates, Converter, Renamer, Extractor, Cleaner, Empty Folder Cleaner, Analytics, Exclusions, Watcher)
- **[Face Sorting Engine]** Face-based People sorter with complete-linkage cosine thresholding & auto-download
- **[Cloud Safety]** OneDrive / iCloud / Dropbox Safe Mode with placeholder protection
- **[GUI Stability]** Background tab scrolling fix (`SCROLL-002`) & atomic checkbox state sync (`SCROLL-001`)
- **[Cache Hardening]** Content-aware cache key hashing (`CACHE-001`) in `face_sort.py`
- **[Exclusion Engine]** Default exclusion protection for `.git`, `node_modules`, `_Duplicates`, etc. (`EXC-001`, `EXC-002`)
- **[Working Agreement & Documentation]** Initialized and aligned self-enforcing working agreement files (`CLAUDE.md`, `AGENTS.md`, `PLAN.md`, `docs/known-issues.md`, `docs/constraints.md`)

---

## 🚧 In Progress

- [ ] **Multi-threaded Hashing Pool (PERF-001)** — Scale duplicate scanner to 100k+ files smoothly
- [ ] **Offline Face Model Management (MODEL-001)** — Local model file browser and graceful offline UX

---

## 📋 Planned (Priority Order)

### Phase 1: Performance & Offline Resiliency
1. Implement worker pool for parallel duplicate hashing (`hashing.py`)
2. Add manual model import / offline prompt in `PeopleTab` (`tab_people.py`)

### Phase 2: Packaging & CI Verification
3. Verify Inno Setup installer compilation with code signing hooks
4. Automate GitHub Actions CI release workflow

---

## Decision Log

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
