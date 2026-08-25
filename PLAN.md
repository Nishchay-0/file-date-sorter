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

---

## 📋 Session Handoff Notes (2026-08-25)

**What changed:**
- Completed Full Production-Readiness Bug Hunt, Stability & Performance Audit across all 9 audit phases.
- Fixed 8 critical, high, and medium severity bugs across GUI, CLI, Core Sorter, Converter, and Renamer modules.
- Created `test_audit_fixes.py` (6/6 passed) validating all bug fixes and edge cases.
- Validated master test suite: **31 passed, 2 skipped, 0 failed** across all pytest suites + **12/12 deployment tests passed (100%)**.

**Verification Evidence:**
- `test_audit_fixes.py`: 6 passed
- `test_deployment.py`: 12 passed
- Full pytest suite: 31 passed, 2 skipped
