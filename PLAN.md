# PLAN.md — Living Roadmap & Progress

## 🏁 Completed Milestones

| Date / Commit | Milestone | Details |
| :--- | :--- | :--- |
| `154951d` | **Face Sorter & Hashing Extraction** | Added ONNX + OpenCV face sorting pipeline (`face_sort.py`), extracted modular hashing utilities (`hashing.py`), and fixed initial scroll desync issues. |
| `a0fde0a` | **OneDrive & Cloud Safe Mode** | Implemented cloud placeholder stub detection (`is_cloud_placeholder`), attribute parsing, and safety guards preventing unintended file hydration. |
| `fb415a7` | **Face Clustering Optimization & UI** | Implemented complete-linkage cosine thresholding to prevent mega-cluster absorption, thumbnail strips, search/sort/filter bar, date ranges, and gallery modal. |
| `0d60ec1` | **Atomic Widget Repaint & Scroll Fix** | Resolved checkbox desync sliver bug across CustomTkinter scrollable frames with atomic state repaint engines. |
| `d53b773` | **10-Tab Atomic Checkbox Sync Suite** | Added `create_atomic_checkbox` component builder and full-application 10-tab atomic state verification suite. |
| 2026-08-25 | **Persistent Memory & GitHub Auto-Sync** | Initialized `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `docs/known-issues.md`, and `docs/constraints.md` with continuous GitHub sync rule. |
| 2026-08-25 | **Full Bug Hunt, Stability & Audit** | Audited all 9 phases: fixed GUI converter execution arguments (`CONV-001`), CLI missing arg crash (`CLI-001`), empty folder default exclusions (`EXC-003`, `EXC-004`), duplicate move collisions (`DUP-001`), single file converter same-extension output (`CONV-002`), batch renamer camelCase tokenization (`RENAME-001`), and dead code (`DEAD-001`). Added comprehensive regression test suite `test_audit_fixes.py` (6/6 passing). |
| 2026-08-25 | **Word-Based Sorting & Single Random Catch-All** | Implemented `extract_word_base()` extracting first meaningful alphabetical word (3+ letters, >= 1 vowel) per filename and routing to unique word folders (`amazon/`, `guru/`). All non-word / hash / gibberish files route to ONE shared `_Random/` folder. Added pre-execution plan modal, ISO date prefix renaming, and Unsorted subdivision options. 47/47 pytest + 12/12 deployment tests passing (100%). |
| 2026-08-25 | **Native Smooth Scrolling Engine** | Removed monkey-patched scrolling engine and individual widget bindings in `gui_modules/app.py`. Enabled native CustomTkinter `CTkScrollableFrame` mouse wheel handling across all tool tabs and modal dialogs, eliminating hover focus hijacking. |

---

## 🚧 In Progress

- [ ] **Multi-threaded Hashing Pool (PERF-001)** — Scale duplicate scanner to 100k+ files smoothly
- [ ] **Offline Face Model Management (MODEL-001)** — Local model file browser and graceful offline UX

---

## 📋 Planned Enhancements

### Phase 1: Performance & Offline Resiliency
1. Implement worker pool for parallel duplicate hashing (`hashing.py`)
2. Add manual model import / offline prompt in `PeopleTab` (`tab_people.py`)

### Phase 2: Packaging & CI Verification
3. Verify Inno Setup installer compilation with code signing hooks
4. Automate GitHub Actions CI release workflow

---

## 📝 Decision Log

| Decision | Rationale | Status |
|----------|-----------|--------|
| Git commit & push rule | Keep remote GitHub repository synchronized after every verified task | ✅ LOCKED (Constraint 010) |
| Content-aware cache key | Prevents stale cache hit when timestamp is preserved | ✅ LOCKED (Constraint 003) |
| System Vault backup | Protects against accidental data loss with 1-click restore | ✅ LOCKED (Constraint 001) |
| CustomTkinter UI | Fast native desktop styling with dark/light mode support | ✅ LOCKED |
| Word-based folder grouping | Groups by first meaningful alphabetical word and consolidates all non-word files into one `_Random/` folder | ✅ LOCKED |
| Native CTkScrollableFrame scrolling | Clean native wheel handling without monkey-patches or hover event blocking | ✅ LOCKED |

---

## 📋 Session Handoff Notes (2026-08-25)

**What changed:**
- Removed custom monkey-patching scroll engine (`_setup_global_smooth_scrolling`, `bind_mousewheel_to_widget`, `bind_mousewheel_to_container`) in `gui_modules/app.py`.
- Replaced with clean native `CTkScrollableFrame` mousewheel event propagation, eliminating hover focus hijacking.
- Updated `test_scrolling_background_fix.py` and `test_gui_scrolling_sync.py`.
- All test suites passing: **45 passed in pytest** and **12/12 deployment tests passed (100%)**.

