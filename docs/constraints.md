# docs/constraints.md — Hard Rules & Settled Technical Decisions

## 🛡️ Non-Negotiable Hard Constraints

### 1. Zero Data Loss & Reversibility First
- **Rule**: No file operation may permanently destroy user data without a reversible path.
- **Implementation**:
  - Moves and reorganizations default to Dry-Run preview.
  - Operations generate automatic System Vault zip backups (`get_system_vault_dir()`) and JSON undo manifests.
  - Deletions must use `send2trash` (OS Recycle Bin) instead of hard `os.remove()` / `shutil.rmtree()`, unless the user explicitly commands permanent removal.

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
