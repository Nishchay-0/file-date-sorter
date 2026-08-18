# Known Issues & Bug Status

## Critical (Blocking Release)

| Bug ID | Description | Status | Evidence | Notes |
|--------|-------------|--------|----------|-------|
| — | None currently identified | ✅ Verified OK | — | Last check: 2026-08-18 |

---

## High Priority (Affects Core Features)

| Bug ID | Description | Status | Evidence | Last Activity |
|--------|-------------|--------|----------|----------------|
| **SCROLL-001** | Checkbox state desync during scrolling (scrollable frames) | ✅ **FIXED** in commit `0d60ec1` | Regression test added: `test_gui_atomic_checkbox_sync.py` | Deployed; needs stress testing |
| **SCROLL-002** | Background tab scrolling instead of active tab (mousewheel fallback) | ✅ **FIXED** in this session | Root cause: fallback loop picked first scroll container, not active tab; Regression test: `test_scrolling_background_fix.py` | All 5 regression tests pass (2026-08-18) |
| **PEOPLE-001** | Face clustering mega-cluster absorption (outlier merging) | ✅ **FIXED** in commit `fb415a7` | Gallery modal + threshold tuning; silhouette score > 0.65 | Needs validation on large datasets (500+ images) |
| **FACE-001** | OpenCV model concurrency crash (thread safety) | ✅ **FIXED** in commit `01496da` | Lock added around model inference; test_people_clustering_tune.py | Monitor for race conditions under heavy multi-thread load |

---

## Medium Priority (Affects UX, Not Blocking)

| Bug ID | Description | Status | Workaround | Next Steps |
|--------|-------------|--------|-----------|-----------|
| **CACHE-001** | `.people_cache.json` invalidation insufficient (mtime-only check) | 🟡 **OPEN** | Clear cache manually via settings or delete file | Implement content-hash or version-tagged cache format |
| **MODEL-001** | Face model auto-download fails silently on offline (no fallback) | 🟡 **OPEN** | User must pre-download manually or connect to internet | Add explicit offline mode detection + user prompt |
| **PERF-001** | Duplicate finding (SHA-256) slow on 100k+ files (single-threaded) | 🟡 **OPEN** | Run on smaller subsets, use dry-run for preview | Implement parallel hashing with thread pool |

---

## Low Priority (Minor / Cosmetic)

| Bug ID | Description | Status | Workaround |
|--------|-------------|--------|-----------|
| **UI-001** | Analytics chart labels cut off on small window | 🟢 **KNOWN** | Resize window; not urgent |
| **UI-002** | Right-click context menu sometimes overlaps with banner | 🟢 **KNOWN** | Click elsewhere to dismiss; use keyboard shortcut instead |

---

## Closed (Fixed & Verified)

| Bug ID | Description | Fixed In | Evidence |
|--------|-------------|----------|----------|
| **GUI-001** | ModernFileDateSorterGUI class definition error (missing methods) | `74dce12` | Commit message; no test regression |
| **BANNER-001** | Zero-deletion banner overlap with Treeview header | `76ecead` | Visual verification required on next run |
| **SYNC-001** | Tab mapping index off-by-one in GUI state | `35c6d8d` | test_full_app_gui_atomic_sync.py |

---

## Testing Status

| Test File | Pass/Fail | Coverage | Last Run | Notes |
|-----------|-----------|----------|----------|-------|
| `test_sorter.py` | — | — | Not run | Needs verification |
| `test_people_sorter.py` | — | — | Not run | Face detection tests; slow (~30s) |
| `test_gui_atomic_checkbox_sync.py` | — | — | Not run | Critical for SCROLL-001 validation |
| `test_full_app_gui_atomic_sync.py` | — | — | Not run | 10-tab atomic state sync (reverted in this session) |
| `test_full_duplicate_tool_verification.py` | — | — | Not run | Duplicates tool end-to-end |
| All others (`test_*.py`) | — | — | Not run | Batch run: `pytest -v` needed |

---

## Bug Report Template (When Adding New Issues)

```markdown
## BugID: [COMPONENT]-###

**Title:** [One-line summary]

**Reproduction Steps:**
1. ...
2. ...

**Expected Behavior:** 
[What should happen]

**Actual Behavior:** 
[What actually happens]

**Environment:**
- OS: [Windows version / other]
- Python: [version]
- PyQt5: [version]
- Commit: [git hash]

**Severity:** Critical | High | Medium | Low

**Evidence:** [Screenshot, log output, or code snippet]

**Root Cause (if known):** [Hypothesis or confirmed finding]

**Fix Strategy (if proposed):** [Outline of fix approach]
```

---

## Next Actions

- [ ] Run `pytest -v` and populate test pass/fail status in table above
- [ ] Verify SCROLL-001 fix (0d60ec1) with manual stress test (rapid scroll, drag, resize)
- [ ] Stress test PEOPLE-001 (mega-cluster fix) with 500+ image dataset
- [ ] Create offline mode handling strategy for MODEL-001
- [ ] Design cache versioning format for CACHE-001 fix
