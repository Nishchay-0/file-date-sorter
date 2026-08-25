# PLAN.md — Living Roadmap

## 🏁 Completed Milestones

| Date / Commit | Milestone | Details |
| :--- | :--- | :--- |
| `154951d` | **Face Sorter & Hashing Extraction** | Added ONNX + OpenCV face sorting pipeline (`face_sort.py`), extracted modular hashing utilities (`hashing.py`), and fixed initial scroll desync issues. |
| `a0fde0a` | **OneDrive & Cloud Safe Mode** | Implemented cloud placeholder stub detection (`is_cloud_placeholder`), attribute parsing, and safety guards preventing unintended file hydration. |
| `fb415a7` | **Face Clustering Optimization & UI** | Implemented complete-linkage cosine thresholding to prevent mega-cluster absorption, thumbnail strips, search/sort/filter bar, date ranges, and gallery modal. |
| `0d60ec1` | **Atomic Widget Repaint & Scroll Fix** | Resolved checkbox desync sliver bug across CustomTkinter scrollable frames with atomic state repaint engines. |
| `d53b773` | **10-Tab Atomic Checkbox Sync Suite** | Added `create_atomic_checkbox` component builder and full-application 10-tab atomic state verification suite. |
| 2026-08-25 | **Persistent Memory & GitHub Auto-Sync** | Initialized `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `docs/known-issues.md`, and `docs/constraints.md` with continuous GitHub sync rule. |

---

## 🚧 In Progress

- **System Memory & Baseline Maintenance**: Continuously updating persistent documentation and monitoring regression baselines across all 12 test engines.

---

## 📋 Planned Enhancements

- [ ] **Performance Benchmarking on Massive Media Libraries**: Extend `benchmark_face_sort.py` for 50k+ image/video datasets.
- [ ] **Additional Archive Format Transcoding**: Expand `tab_converter.py` magic-byte extraction to support modern archive tarballs (e.g. zstd, xz).
- [ ] **Enhanced EXIF Geolocation Filtering**: Add optional country/city location grouping in date sorter if GPS tags exist.

---

## 📝 Session Handoff Notes

- **Current Status**: All 12 automated deployment tests (`test_deployment.py`) pass with 100% success.
- **Git Sync**: Automatic staging, committing, and pushing to `origin/main` active for every task.
