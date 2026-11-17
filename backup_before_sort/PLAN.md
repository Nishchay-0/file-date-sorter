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
| 2026-08-25 | **Stopword-Aware Multi-Word Title Sorting** | Implemented `extract_meaningful_group()` in `sorter_core.py`. Strips leading stopwords (`the`, `a`, `my`, etc.) and preserves multi-word title prefixes before numeric/date patterns (e.g. `_the_june_pearl_...` -> `june_pearl/`, `the_silent_eyes_...` -> `silent_eyes/`). All non-word/hash files consolidated into single `_Random/` folder. 47/47 pytest + 12/12 deployment tests passing (100%). |
| 2026-08-25 | **Deterministic Prefix-Preserving Grouping Engine** | Overhauled `sorter_core.py` with deterministic token scanning that preserves useful prefixes (`pvt`, `m`, `ser`), skips leading index counters, stops on numeric date stamps, and unifies all random/hash files into a single `_Random/` folder. 14/14 super prompt scenarios + 12/12 deployment tests passing (100%). |
| 2026-09-04 / `39aa0ae` | **Production Docker Environment** | Added standalone container image (`Dockerfile`), multi-service orchestration (`docker-compose.yml`), smart entrypoint (`docker-entrypoint.sh`), build context ignore (`.dockerignore`), gitattributes LF enforcement, and comprehensive guide (`DOCKER.md`). |
| 2026-09-04 | **Architecture & Quality Overhaul** | Eliminated code duplication (`fix_win_long_path`, `config.py` constants), added Windows UNC path resilience, centralized logging (`logger.py`), explicit error handling, type annotations, untracked scratch artifacts, and added core unit tests (`test_core_units.py`). |

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
| Stopword-aware multi-word title grouping | Strips leading stopwords ('the', 'a', etc.) and takes title prefix before digits to avoid grouping everything under 'the' | ✅ LOCKED |
| Deterministic prefix preservation | Preserves 'pvt', 'm', 'ser' and handles multi-part names while dropping leading counter numbers | ✅ LOCKED |

---

## 📋 Session Handoff Notes (2026-08-25)

**What changed:**
- Overhauled `extract_meaningful_group()` in `sorter_core.py` with deterministic token scanning and separator normalization.
- Verified 14 target patterns (e.g. `_pvt.shaunak_...` -> `pvt_shaunak`, `13_deshwal-...` -> `deshwal`, `vanujawaliya.-...` -> `vanujawaliya`, `100ser_...` -> `ser`).
- Fixed compound extension handling in `strip_all_extensions()`.
- Validated all tests: **14/14 in test_sorter.py**, **8/8 in test_smart_name_sorter.py**, **12/12 in test_deployment.py (100%)**, and **47/47 in pytest (100%)**.

