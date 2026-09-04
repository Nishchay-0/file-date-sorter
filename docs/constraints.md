# docs/constraints.md — Hard Rules & Settled Technical Decisions

## 🛡️ Non-Negotiable Hard Constraints

### 1. Zero Data Loss & Reversibility First
- **Rule**: No file operation may permanently destroy user data without a reversible path.
- **Implementation**:
  - Moves and reorganizations default to Dry-Run preview.
  - Operations generate automatic System Vault zip backups (`get_system_vault_dir()`) and JSON undo manifests.
  - Deletions must use `send2trash` (OS Recycle Bin) instead of hard `os.remove()` / `shutil.rmtree()`, unless the user explicitly commands permanent removal.
---

**CONSTRAINT-001: No Silent Destruction**
- Every destructive operation (delete, overwrite, rename, move) must:
  1. Show preview (exact list of affected files)
  2. Generate System Vault backup (zip + `.undo_manifest.json`)
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
- **Evidence:** Static analysis + network sniffing on first run
- **Status:** ✅ Verified — no external telemetry calls in core code

---

**CONSTRAINT-003: Cache Invalidation Strategy**
- Face detection results (`.people_cache.json`) must invalidate when:
  - Source image file modified (mtime or content hash changed)
  - Face model version changed (model file mtime or embedded version)
  - Cache format version changed (schema bump)
- **Current:** Content-aware hash + schema version tag implemented in `face_sort.py`
- **Scope:** `face_sort.py`, cache loading/saving
- **Test:** `test_people_sorter.py` — `test_05_cache_key_changes_when_file_contents_change` (PASSED)

---

### 🎯 User Experience & Clarity

**CONSTRAINT-004: No Silent Fallbacks**
- If an operation cannot complete as designed, surface the degradation visibly:
  - Missing face models → show download prompt, not silent skip
  - Insufficient disk space → show error + required space, not partial write
  - Permission denied → show which folder + suggest admin mode, not skip silently
- **Scope:** All tools, especially Sorter and Converter (write-heavy)
- **Evidence:** Error paths in `sorter_core.py`, exception handlers

---

**CONSTRAINT-005: Long Operations Require Progress UI**
- Any operation taking > 5 seconds must show:
  1. Progress bar (% complete or items/total)
  2. Cancel button (non-blocking; must preserve completed work if cache exists)
  3. Time remaining estimate (optional; accuracy not required)
- **Scope:** Duplicate scanning, face detection, bulk conversions, hashing
- **Evidence:** Progress bar implementation in `gui_modules/views/tab_duplicates.py`, `tab_people.py`

---

**CONSTRAINT-006: Dry-Run Must Be Exact Match**
- `--dry-run` preview in CLI and "Preview" in GUI must show exactly what will execute:
  - Same files, same counts, same categories/destinations
  - No approximations ("~100 files") — exact lists
  - If actual execution differs from preview, treat as bug (CONSTRAINT-001 violation)
- **Scope:** All 10 tools
- **Evidence:** `test_full_duplicate_tool_verification.py`, `test_super_duplicates.py`

---

### 🔧 Platform & Workflow

**CONSTRAINT-007: Windows-First, Cross-Platform Secondary**
- Primary development/testing target: Windows 10/11
- Cross-platform support is secondary; breakage on other OS is acceptable if Windows works flawlessly
- Build artifacts (installer, .exe) Windows-focused with `fix_win_long_path()` prefix support (`\\?\`)
- **Scope:** CI/CD, GUI theming, file path handling, packaging

---

**CONSTRAINT-008: No Heavy ML/Inference Framework Runtime Dependency**
- Face detection uses ONNX Runtime / OpenCV (lightweight footprint)
- No TensorFlow, PyTorch, Transformers, etc. bundled (excessive bloat)
- Models downloaded on-demand (lazy load, not bundled in git repository)
- **Scope:** `face_sort.py`, model loading

---

**CONSTRAINT-009: Code Signing & SmartScreen Warning Removal**
- Distributed executable (.exe, installer) must be code-signed when cert environment variables are set:
  - `CODE_SIGNING_CERT_PATH` (path to .pfx file)
  - `CODE_SIGNING_CERT_PASS` (certificate password)
- **Scope:** `build_exe.py` (code-signing hook), CI workflow

---

**CONSTRAINT-010: Always Commit and Push to GitHub on Task Completion**
- At the conclusion of every task or work session:
  1. Run the test suite and verify changes pass cleanly
  2. Scan git diffs to ensure no API keys, credentials, or secrets are staged
  3. Commit changes with clean semantic commit messages
  4. Push directly to remote repository (`origin/main`)
- **Scope:** All agent workflows and pair programming sessions
- **Evidence:** Git log and remote branch tracking (`git push origin main`)

---

## Settled Technical Decisions

### Architecture
| Decision | Alternative(s) Rejected | Why | Status |
|----------|-------------------------|-----|--------|
| CustomTkinter / Tkinter for GUI | Qt/PyQt5, Electron, Kivy | Lightweight, native look on Windows, zero heavy external binary deps | ✅ LOCKED |
| ONNX / OpenCV for face models | TensorFlow, PyTorch | Fast inference, small footprint (< 20MB vs > 500MB) | ✅ LOCKED |
| Watchdog for folder monitoring | Manual polling, OS specific hooks | Cross-platform, event debouncing built-in | ✅ LOCKED |
| JSON for settings storage | SQLite, YAML, INI | Human-readable, native stdlib support | ✅ LOCKED |
| Content-aware cache key | mtime-only key | Prevents stale cache hit when timestamp preserved | ✅ LOCKED |
| System Vault with `.undo_manifest.json` | Relational DB | Reversible, file-system native, human-readable | ✅ LOCKED |

---

## Violation & Escalation Process

1. **Stop work** on that feature (do not commit to main).
2. **Identify root cause** and file issue in `docs/known-issues.md`.
3. **Fix root cause** and write a regression test.
4. **Update `PLAN.md` and `CLAUDE.md`/`AGENTS.md`** with findings.
5. **Commit and push** the fix and tests to GitHub.
=======
### 2. Strict Offline Privacy & Local Compute
- **Rule**: Never transmit, upload, or expose user data, image embeddings, or file names to external endpoints or cloud APIs.
- **Reasoning**: User photos, personal documents, and filesystem structures are sensitive.
- **Implementation**: Face detection (YuNet) and recognition (SFace) run locally via ONNX Runtime & OpenCV. Embeddings and index files remain strictly on the local machine (`.people_cache.json`, `.people_index.json`).

### 3. Cloud Placeholder Protection (OneDrive / iCloud / Dropbox)
- **Rule**: Never blindly read entire files without verifying cloud hydration state.
- **Reasoning**: Reading cold/offline cloud stubs triggers unwanted multi-gigabyte downloads over metered or slow connections.
- **Implementation**: `is_cloud_placeholder()` in [`hashing.py`](file:///c:/file-date-sorter%20-%20Copy/hashing.py) checks Windows file attributes (`FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`, `FILE_ATTRIBUTE_OFFLINE`).

### 4. Windows Long Path & Illegal Character Sanitization
- **Rule**: Paths exceeding 240+ characters must be prefixed with `\\?\` via `fix_win_long_path()`.
- **Reasoning**: Windows NTFS fails with `FileNotFoundError` or `PathTooLongException` on deeply nested folder structures.
- **Implementation**: Sanitizer strips invalid characters (`:`, `*`, `?`, `"`, `<`, `>`, `|`) when creating new folder names or renaming files.

### 5. Automated Git Commits & Remote GitHub Sync
- **Rule**: Every verified task, code addition, script generation, or documentation change must be committed and pushed to GitHub (`origin/main`).
- **Implementation**: Scan staged files against `.gitignore` to prevent committing secrets/API keys or personal test caches, verify test suites pass, craft descriptive git commit messages, and execute `git push origin main`.

---

## 🏛️ Settled Technical Architecture Decisions

| Decision | Selection | Alternatives Considered | Rationale |
| :--- | :--- | :--- | :--- |
| **Face Recognition Engine** | ONNX Runtime + OpenCV (YuNet + SFace) | `dlib` / `face_recognition` | `dlib` requires C++ compilers (CMake/Visual Studio), is difficult to build on Windows, and increases PyInstaller executable size by 300MB+. ONNX is lightweight, fast, and cross-platform. |
| **Face Clustering** | DBSCAN + Complete Linkage Cosine | K-Means, Agglomerative | K-Means requires pre-specifying $k$ (number of people), which is unknown in arbitrary photo libraries. DBSCAN discovers cluster counts automatically; complete linkage prevents mega-cluster chaining. |
| **UI Framework** | CustomTkinter | PyQt, Electron, WxPython | Python-native, modern dark/light mode aesthetic without heavy runtime bloat or licensing complexities. |
| **Duplicate Detection** | Tiered Hashing (Size -> Partial Head/Tail -> Full SHA-256) | Full SHA-256 on all files | Reduces disk I/O by >90% by discarding non-matching file sizes and quick sampling before full hash computation. |
