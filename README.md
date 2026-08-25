# ⚡ Smart File Organizer Suite Pro

[![CI Status](https://github.com/Nishchay-0/file-date-sorter/actions/workflows/ci.yml/badge.svg)](https://github.com/Nishchay-0/file-date-sorter/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

A powerful, modern desktop application and CLI utility for organizing, extracting, deduplicating, renaming, and cleaning files across deep directory hierarchies — with face recognition, Apple Glassmorphism UI, and a zero-data-loss guarantee.

---

## 🎨 Modern Apple Glassmorphism UI

The GUI features a premium **Apple-inspired Glassmorphism** design with:

- **Left-Side Collapsible Toolbar** — Vertical icon+label sidebar; one-click `⏮️ Collapse` to icon-only (`☰`) mode, giving more space to the active tool panel.
- **Top Action Bar** — Quick-access `↩️ Undo`, `🛡️ Vault`, and `🌙 Dark / ☀️ Light` segmented theme toggle always visible.
- **Glass Cards** — Semi-transparent panels with `corner_radius=16`, `border_width=1`, soft shadows. Light: `#F2F2F7` / `#FFFFFF`. Dark: `#1C1C1E` / `#2C2C2E`.
- **iOS Accent Blue** — `#007AFF` (light) / `#0A84FF` (dark) for primary actions and active nav highlight.
- **Micro-animations** — Hover pulse on sidebar buttons and action cards.
- **Segoe UI Typography** — 13pt body · 15pt section headers · 19pt title.

### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Smart File Organizer Suite Pro  v1.0.0    ↩️ Undo  🛡️ Vault  🌙 Dark/☀️ Light │
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
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🌟 Features & Tools

| # | Tool | Description |
|---|------|-------------|
| 1 | 📅 **File Organizer** | Sort by Date (`2024/05`), Meaningful Title Group, Category, Extension, Alphabetical, or File Size. Dry-run preview with exact target paths. |
| 2 | 🎯 **Smart Name Grouping** | Stopword-aware extraction (`the`, `a`, `an`, `my`, …). Pure hashes / UUIDs → single `_Random/` folder. |
| 3 | 📦 **Subfolder Extractor** | Flatten nested directories or extract specific extensions into a single output folder. |
| 4 | 🔍 **Duplicate Finder** | SHA-256 exact + perceptual image hash. Isolate or trash duplicates with full undo support. |
| 5 | 🪄 **Magic Converter** | Magic-byte detection, extension repair, batch convert: `3GA/OPUS/AMR→MP3`, `VOB/MKV→MP4`, `WEBP/HEIC→JPG`. |
| 6 | 🏷️ **Smart Batch Renamer Pro** | Pattern tags `{YYYY}` `{Width}` `{SizeMB}` `{Artist}` · Regex with capture groups · 6 case modes · Custom numbering · Live diff preview · 1-click undo · Built-in presets |
| 7 | 🧹 **Storage Cleaner** | Remove 0-byte files, `.tmp/.log/.crdownload/Thumbs.db`; standalone empty-folder cleaner. |
| 8 | 📊 **Analytics Dashboard** | Category size breakdowns, date-range spans, top subfolder disk usage. |
| 9 | 👥 **People / Face Sorter** | OpenCV YuNet detection + SFace embeddings + DBSCAN clustering — group photos by recognized person. |
| 10 | 👁️ **Auto Watcher** | `watchdog` background service: monitors a folder, auto-organizes new files with desktop toasts + tray icon. |
| 11 | 🚫 **Exclusions Rules** | Skip folders, extensions, or file patterns app-wide across all 10 tools. |
| 12 | 🛡️ **System Vault & Undo** | Zip vault + `undo_manifest.json` before every move. Restore with 1 click or `cli.py --undo LATEST`. |

---

## 🚀 Getting Started

### Requirements
- Python 3.8+
- `pip install -r requirements.txt`

Key packages: `customtkinter`, `Pillow`, `Send2Trash`, `watchdog`, `pystray`, `mutagen`, `onnxruntime`

---

## 💻 Running

### Desktop GUI
```bash
python run_sorter.py
# or
python gui.py
```

### CLI
```bash
# Sort by creation date
python cli.py --path "C:\Target\Path"

# Category sort, dry-run, with exclusions
python cli.py --path "C:\Target\Path" --sort-category category --dry-run --exclude-folders ".git,node_modules"

# Remove empty folders only
python cli.py --path "C:\Target\Path" --clean-empty-only

# Undo the last operation
python cli.py --path "C:\Target\Path" --undo LATEST
```

---

## 🧪 Testing

```powershell
# Full pytest suite (Windows)
$env:TCL_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tcl8.6"
$env:TK_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python314\tcl\tk8.6"
py -3.14 -m pytest -v
```

```bash
# Master deployment verification
python test_deployment.py
```

---

## 📦 Build & Package

```bash
# Standalone exe (PyInstaller)
python build_exe.py
# → dist/SmartFileOrganizer/SmartFileOrganizer.exe

# Windows installer (Inno Setup)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
# → installer_output/SmartFileOrganizer_Setup_v1.0.0.exe
```

---

## 🛡️ Safety Guarantees

| Guarantee | Mechanism |
|:---|:---|
| **Zero data loss** | Zip vault + `undo_manifest.json` before every destructive op |
| **Cloud placeholder safety** | `is_cloud_placeholder()` check prevents OneDrive/iCloud gigabyte downloads |
| **Windows long paths** | All paths pass through `fix_win_long_path()` (`\\?\` prefix) |
| **No telemetry** | All processing is fully local — no external network calls |
| **Exact dry-run match** | Preview and real execution use identical code paths |
