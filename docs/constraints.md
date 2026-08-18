# Hard Constraints & Project Decisions

## Non-Negotiable Rules

### 🔒 Data Integrity & Safety

**CONSTRAINT-001: No Silent Destruction**
- Every destructive operation (delete, overwrite, rename, move) must:
  1. Show preview (exact list of affected files)
  2. Generate System Vault backup (zip + manifest)
  3. Require explicit confirmation (checkbox + button)
  4. Support undo via 1-click restore
- **Scope:** All tools (Sorter, Duplicates, Converter, Renamer, Cleaner)
- **Violation:** Fail build and reject PR until fixed
- **Evidence:** `test_full_duplicate_tool_verification.py`, dry-run mode in CLI/GUI

---

**CONSTRAINT-002: No Telemetry Without Consent**
- Application must NOT transmit user data (file lists, folder paths, OS info, usage stats) to any external server without:
  1. Explicit opt-in checkbox in Settings (visible on first launch)
  2. Clear disclosure of what data, where it's sent, and why
  3. Easy opt-out (persist choice in config)
- **Scope:** Entire application + all dependencies
- **Audit:** Code review for `import requests`, `urllib`, `analytics`, `telemetry`, `crash_reporter` patterns
- **Evidence:** Static analysis + network sniffing (Wireshark) on first run
- **Status:** ✅ Verified — no external calls found in core code (2026-08-18)

---

**CONSTRAINT-003: Cache Invalidation Strategy**
- Face detection results (`.people_cache.json`) must invalidate when:
  - Source image file modified (mtime changed)
  - Face model version changed (model file mtime or embedded version)
  - Cache format version changed (schema bump)
- **Current:** mtime-based only (insufficient) — see CACHE-001 in known-issues.md
- **Next:** Implement content-hash or version-tagged format
- **Scope:** `face_engine.py`, `face_sort.py`, cache loading/saving
- **Test:** `test_people_clustering_tune.py` — verify cache hit/miss on image edit

---

### 🎯 User Experience & Clarity

**CONSTRAINT-004: No Silent Fallbacks**
- If an operation cannot complete as designed, surface the degradation visibly:
  - Missing face models → show download prompt, not silent skip
  - Insufficient disk space → show error + required space, not partial write
  - Permission denied → show which folder + suggest admin mode, not skip silently
- **Scope:** All tools, especially Sorter and Converter (write-heavy)
- **Violation Example:** ❌ File write fails → skip to next file without user notice
- **Correct Example:** ✅ File write fails → show error dialog with retry/skip/abort options
- **Evidence:** Error paths in `sorter_core.py`, exception handlers

---

**CONSTRAINT-005: Long Operations Require Progress UI**
- Any operation taking > 5 seconds must show:
  1. Progress bar (% complete or items/total)
  2. Cancel button (non-blocking; must preserve completed work if cache exists)
  3. Time remaining estimate (optional; accuracy not required)
- **Scope:** Duplicate scanning, face detection, bulk conversions, hashing
- **Test:** `test_watcher_debounce.py`, manual test on 100k+ files
- **Evidence:** Progress bar implementation in `gui_modules/views/tab_duplicates.py`, `tab_people.py`

---

**CONSTRAINT-006: Dry-Run Must Be Exact Match**
- `--dry-run` preview in CLI and "Preview" in GUI must show exactly what will execute:
  - Same files, same counts, same categories/destinations
  - No approximations ("~100 files") — exact lists
  - If actual execution differs from preview, treat as bug (CONSTRAINT-001 violation)
- **Scope:** All 10 tools
- **Test:** Create paired tests (dry-run vs. actual) for each tool; assert identical results
- **Evidence:** `test_full_duplicate_tool_verification.py`, test_sorter.py

---

### 🔧 Platform & Dependencies

**CONSTRAINT-007: Windows-First, Cross-Platform Secondary**
- Primary development/testing target: Windows 10/11
- Cross-platform (macOS, Linux) support is lower priority; breakage on other OS acceptable if Windows works
- Build artifacts (installer, .exe) Windows-only
- **Scope:** CI/CD, GUI theming, file path handling, packaging
- **Exception:** Python standard library code must be platform-agnostic where trivial

---

**CONSTRAINT-008: No Heavy ML/Inference Framework Runtime Dependency**
- Face detection uses ONNX Runtime (lightweight, ~20 MB)
- No TensorFlow, PyTorch, Transformers, etc. bundled (excessive bloat)
- Models downloaded on-demand (lazy load, not bundled)
- **Scope:** `face_engine.py`, model loading
- **Rationale:** Installer must stay under 200 MB; ONNX achieves this
- **Evidence:** `build_exe.py` spec file; PyInstaller bundle size check

---

**CONSTRAINT-009: Code Signing & SmartScreen Warning Removal**
- Distributed executable (.exe, installer) must be code-signed with EV or OV certificate
- Signing must be automatic if environment variables set:
  - `CODE_SIGNING_CERT_PATH` (path to .pfx file)
  - `CODE_SIGNING_CERT_PASS` (certificate password)
- **Scope:** `build_exe.py` (code-signing hook), CI workflow
- **Rationale:** Prevent Windows SmartScreen "Unrecognized Publisher" warning
- **Evidence:** `build_exe.py` has `sign_executable()` function; CI workflow sets env vars

---

## Settled Technical Decisions

### Architecture

| Decision | Alternative(s) Rejected | Why | Owner | Date |
|----------|-------------------------|-----|-------|------|
| PyQt5 for GUI | Tkinter, PySimpleGUI, web-based (Electron) | Tkinter: outdated look; PySimpleGUI: limited styling; Electron: bloated (~200 MB); PyQt5: native look, mature, ~30 MB footprint | — | Pre-1.0 |
| ONNX for face models | TensorFlow, PyTorch | ONNX: inference-only (smaller); TF/PT: full framework (100+ MB overhead) | — | Pre-1.0 |
| Watchdog for file monitoring | Manual polling, OS-specific APIs | Watchdog: cross-platform, mature; polling: CPU waste; OS APIs: fragmentation | — | Pre-1.0 |
| JSON for settings storage | SQLite, YAML, INI | JSON: human-readable, no extra deps; SQLite: overkill; YAML: dependency; INI: limited types | — | Pre-1.0 |

### Data & Caching

| Decision | Why | Status | Test |
|----------|-----|--------|------|
| mtime-based cache invalidation | Simple, fast; covers most cases | 🟡 INSUFFICIENT — needs version tag | CACHE-001 in known-issues |
| SHA-256 for duplicate detection | Collision probability negligible (~1e-77 for 2^64 files); no false positives in practice | ✅ LOCKED | test_sorter.py |
| System Vault as folder + manifest file (not database) | Human-readable recovery; no dependency on DB library | ✅ LOCKED | Manual undo tests |

### UI/UX

| Decision | Why | Status |
|----------|-----|--------|
| Tabbed interface (10 tools in one app) | Single-window UX; tool switching without app overhead | ✅ LOCKED |
| Right-click context menus for folders/files | Familiar; reduces toolbar clutter | ✅ LOCKED |
| Dry-run checkbox (not separate mode) | Single UI path; easier to discover | ✅ LOCKED |
| Atomic checkbox repaint engine (scrollable frames) | Prevent state desync during scroll; fixed in 0d60ec1 | 🟡 TESTING — needs validation |

---

## Violation & Escalation Process

### If a Constraint is Violated

1. **Stop work** on that feature (do not commit to main)
2. **File issue** referencing the constraint number (e.g., "Violates CONSTRAINT-001")
3. **Root-cause analysis:** Which constraint? Why not caught earlier?
4. **Choose one:**
   - **A) Fix it** — revert change, fix root cause, re-submit (preferred)
   - **B) Propose exception** — document in this file with explicit trade-off + approval from [owner TBD]
5. **Update this file** if constraint wording was unclear or needs tightening

### Escalation Path

- **Constraints 001–003 (data safety):** Release-blocking; no exceptions without explicit sign-off
- **Constraints 004–006 (UX):** Release-blocking for public builds; internal testing may skip temporarily
- **Constraints 007–009 (platform/build):** Non-blocking for development; blocking for release builds

---

## Review Checklist (Before Shipping Release)

- [ ] No telemetry found in code or dependencies (audit: `pip list`, grep for requests/analytics)
- [ ] Dry-run tests pass (paired actual vs. preview tests)
- [ ] All destructive operations have backup + undo path
- [ ] No operation > 5 sec without progress UI
- [ ] Face cache invalidation strategy documented and implemented (if CACHE-001 fix included)
- [ ] Installer code-signed (no SmartScreen warning)
- [ ] Windows target verified (run on Windows 10 VM minimum)
- [ ] Constraint violations log empty (or documented exceptions only)

---

## Update Log

| Date | Change | Rationale |
|------|--------|-----------|
| 2026-08-18 | Created this document (constraints.md) | Formalize hard rules; prevent silent relitigations |
| — | To be updated as constraints evolve | — |
