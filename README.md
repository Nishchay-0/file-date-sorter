# ⚡ Smart File Organizer Suite Pro

[![CI Status](https://github.com/Nishchay-0/file-date-sorter/actions/workflows/ci.yml/badge.svg)](https://github.com/Nishchay-0/file-date-sorter/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A high-performance desktop application and CLI utility for organizing, extracting, deduplicating, renaming, converting, and cleaning files across deep directory hierarchies — featuring face recognition, Apple Glassmorphism UI, and a zero-data-loss guarantee.

---

## 🎨 Modern Apple Glassmorphism UI

The GUI features a premium **Apple-inspired Glassmorphism** design:

- **Collapsible Navigation Toolbar** — Vertical icon+label sidebar; one-click `⏮️ Collapse` to icon-only (`☰`) mode for maximum working canvas.
- **Top Action Bar** — Quick-access `↩️ Undo`, `🛡️ Vault`, and `🌙 Dark / ☀️ Light` segmented theme toggle.
- **Glass Cards** — Semi-transparent panels with soft shadows and rounded corners (`#F2F2F7` light / `#1C1C1E` dark).
- **iOS Accent Blue** — `#007AFF` (light) / `#0A84FF` (dark) for primary actions and active navigation highlights.
- **Micro-animations** — Smooth hover pulse on sidebar buttons and interactive action cards.
- **Typography** — Optimized Segoe UI typography across all panels.

### UI Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Smart File Organizer Suite Pro  v1.0.1    ↩️ Undo  🛡️ Vault  🌙 Dark/☀️ Light │
├──────────────┬──────────────────────────────────────────────────────────────┤
│  ⏮️ Collapse  │                                                              │
│  📅 Organizer │                                                              │
│  🔍 Duplicates│              Active Tool Content Panel                       │
│  👥 People    │         (Glass cards · scrollable · theme-aware)             │
│  📦 Extractor │                                                              │
│  🪄 Converter │                                                              │
│  🏷️ Renamer   │                                                              │
│  🧹 Cleaner   │                                                              │
│  📊 Analytics │                                                              │
│  👁️ Watcher   │                                                              │
│  🚫 Exclusions│                                                              │
├──────────────┴──────────────────────────────────────────────────────────────┤
│  ● Ready — select a target folder or pick files to begin.                   │
│  Total: 0 files | Selected: 0 | Vault: Armed                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🌟 Features & Capabilities

| # | Tool | Description |
|---|------|-------------|
| 1 | 📅 **File Organizer** | Sort by Date (`YYYY/MM`), Meaningful Title Group, Category, Extension, Alphabetical, or Size. Real-time dry-run preview with exact target paths. |
| 2 | 🎯 **Smart Name Grouping** | Deterministic token scanning with stopword removal (`the`, `a`, `my`, ...). Gibberish, UUIDs, and pure hex hashes route to `_Random/`. |
| 3 | 📦 **Subfolder Extractor** | Flatten deep directory trees or selectively pull out specific file extensions into a destination directory. |
| 4 | 🔍 **Duplicate Finder** | Tiered hashing: Fast head/tail sampling, full SHA-256 exact match, and dHash perceptual image similarity. Isolate or trash duplicates with full undo history. |
| 5 | 🪄 **Magic Converter** | Magic-byte header inspection, damaged extension repair, and batch audio/video/image conversion (`WEBP/HEIC→JPG`, `MKV→MP4`, `OPUS→MP3`). |
| 6 | 🏷️ **Batch Renamer Pro** | Metadata pattern tags (`{YYYY}`, `{Width}`, `{SizeMB}`, `{Artist}`), regex capture groups, 6 letter-case presets, live side-by-side preview, and 1-click restore. |
| 7 | 🧹 **Storage Cleaner** | Remove 0-byte orphan files, `.tmp`, `.log`, `.crdownload`, and `Thumbs.db`; standalone recursive empty-folder cleaner. |
| 8 | 📊 **Disk Analytics** | Interactive storage breakdown by category, date span analysis, and largest subfolder consumption charts. |
| 9 | 👥 **Face & People Sorter** | OpenCV YuNet detector + SFace neural embeddings + complete-linkage DBSCAN clustering to cluster photos by person with cached embeddings. |
| 10 | 👁️ **Folder Watcher** | Background `watchdog` daemon that automatically organizes newly created or downloaded files, complete with system tray controls and desktop notifications. |
| 11 | 🚫 **Unified Exclusions** | App-wide exclusion engine: ignore protected folders (`.git`, `node_modules`, `AppData`), extensions, or custom glob patterns. |
| 12 | 🛡️ **System Vault & Undo** | Pre-flight atomic ZIP archive and `.undo_manifest.json` generated before every file operation. 1-click restore via GUI or `cli.py --undo LATEST`. |

---

## 🚀 Getting Started

### Installation

Clone the repository and set up a virtual environment:

```powershell
# 1. Clone repository
git clone https://github.com/Nishchay-0/file-date-sorter.git
cd file-date-sorter

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 💻 Running the App

### Desktop GUI
```powershell
python run_sorter.py
# or
python gui.py
```

### Command Line Interface (CLI)
```powershell
# Sort by creation date
python cli.py --path "C:\Target\Path"

# Organize by category with dry-run preview and exclusions
python cli.py --path "C:\Target\Path" --sort-category category --dry-run --exclude-folders ".git,node_modules"

# Standalone empty folder hierarchy cleanup
python cli.py --path "C:\Target\Path" --clean-empty-only --exclude-folders ".git,node_modules"

# Undo the last operation
python cli.py --path "C:\Target\Path" --undo LATEST
```

---

## 🐳 Docker (CI & Headless CLI)

For running the CLI in an isolated container or verifying headless tests, see [docs/DOCKER.md](docs/DOCKER.md).

```bash
# Build image
docker compose build

# Run CLI dry-run preview on mounted directory
docker run --rm -v "C:\Target\Path:/data" smart-file-organizer --path /data --sort-category category --dry-run

# Run full test suite in container
docker compose run --rm test
```

---

## 🧪 Running Tests

Tests are isolated inside the `tests/` directory and managed via `pytest`:

```powershell
# Run all unit and integration tests
& ".\.venv\Scripts\python.exe" -m pytest -v

# Run specific test suite
& ".\.venv\Scripts\python.exe" -m pytest tests/test_core_units.py -v
```

---

## 📦 Production Build & Packaging

Compile a standalone Windows executable or setup installer:

```powershell
# 1. Compile standalone executable with PyInstaller (outputs to dist/SmartFileOrganizer/)
python build_exe.py

# 2. Compile Inno Setup Windows installer (outputs to installer_output/)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

---

## 🛡️ Safety Guarantees

| Guarantee | Implementation |
|:---|:---|
| **Zero Data Loss** | Atomic ZIP vault and `.undo_manifest.json` generated before modifying any file. |
| **Cloud Placeholder Safe** | Inspects NTFS reparse/sparse attributes (`is_cloud_placeholder()`) to avoid hydrating OneDrive / iCloud / Dropbox cloud stubs. |
| **Windows Long Paths** | Normalizes all paths through `fix_win_long_path()` supporting `\\?\` and UNC network shares up to 32,767 characters. |
| **Zero Telemetry** | 100% local execution — no external analytics or network calls. |
| **Exact Dry-Run Match** | Preview simulation follows the exact production resolution logic. |

---

## 📄 License & Contributing

- Distributed under the [MIT License](LICENSE).
- For contributor guidelines and development standards, please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).
