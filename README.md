# ⚡ Smart File Organizer & Sorter Suite

A powerful, modern desktop application and command-line utility for organizing, extracting, deduplicating, renaming, and cleaning files across nested directory trees.

---

## 🌟 Features & Included Tools

1. **⚡ Sorter & Organizer**: Automatically categorizes files into Year/Month (`2024/05`), File Type Category (`Images/JPG`), Extension (`PDF/PNG`), Alphabetical (`A-Z`), or File Size folders.
2. **⚡ Subfolder Extractor**: Extract specific file types or all nested subfolder files into a flat directory structure.
3. **🔍 SHA-256 Duplicate Finder & Isolator**: Detect exact content duplicates and isolate or trash them safely.
4. **🪄 Magic File Converter & Format Fixer**: Reads binary magic byte headers (`FF D8 FF`, `OggS`, `ftyp`, etc.) to auto-detect true formats, fix missing/corrupted file extensions (`.DAT`, `.TMP`, `NO_EXT`), and batch convert audio (`3GA`, `OPUS`, `AMR` -> `MP3`), video (`VOB`, `3GP`, `MKV` -> `MP4`), and images (`WEBP`, `HEIC`, `BMP` -> `JPG/PNG`).
5. **✏️ Smart Batch Renamer**: Rename hundreds of files simultaneously with pattern tags (`{OriginalName}`, `{YYYY}`, `{MM}`, `{Category}`, `{001}`) and case conversions (`camelCase`, `lowercase`, `UPPERCASE`).
6. **🧹 Junk & OS Cleaner**: Detect 0-byte files, `.tmp`, `.log`, `.crdownload`, `desktop.ini`, `thumbs.db`.
7. **📂 Standalone Empty Folder Cleaner**: Dedicated preview scanner and batch deletion tool for 0-file subfolders and OS junk directories across any folder hierarchy.
8. **📊 Storage Analytics Dashboard**: Visual category size breakdowns, date range span, and top subfolder disk usage.
9. **🚫 Unified Path Exclusion Engine**: Skip specific folders (`.git`, `node_modules`, `_Duplicates`), custom directories (picked via **"Except Folder..."**), file names, or extensions across all tools.
10. **🛡️ System Vault Backup & 1-Click Undo**: Preview operations with Dry-Run mode, generate System Vault Zip backups, and restore any operation using 1-click undo manifests.

---

## 🚀 Getting Started

### Requirements
- Python 3.8+
- CustomTkinter UI toolkit (`pip install customtkinter`)
- Optional for UI thumbnails & EXIF: Pillow (`pip install Pillow`), Send2Trash (`pip install send2trash`)

```bash
pip install -r requirements.txt
```

---

## 💻 Running the Application

### 1. Desktop Graphical Interface (GUI)
Launch the CustomTkinter desktop app:
```bash
python run_sorter.py
```
Or double-click `run_sorter.py` in Windows File Explorer.

### 2. Command Line Interface (CLI)
Automate file organization via terminal or batch scripts:

```bash
# Basic sort by creation date
python cli.py --path "C:\Users\YourName\Downloads"

# Standalone empty folder cleanup (removes empty subfolders & OS junk without moving files)
python cli.py --path "D:\Projects" --clean-empty-only --exclude-folders ".git,node_modules"

# Category sort with folder exclusion and dry-run preview
python cli.py --path "D:\Projects" --sort-category category --dry-run --exclude-folders ".git,node_modules,temp"

# Undo the last sort operation
python cli.py --path "C:\Users\YourName\Downloads" --undo LATEST
```

---

## 🧪 Verification & Automated Testing

Run the master deployment test suite to verify all 10 engine components, path exclusion rules, and CLI functions:

```bash
python test_deployment.py
```

Output:
```text
==========================================================
      MASTER FILE ORGANIZER SUITE - DEPLOYMENT VERIFICATION
==========================================================
  ✓ Path Exclusion Engine: PASSED
  ✓ Category Sorting Preview: PASSED
  ✓ Organization Execution: PASSED
  ✓ Duplicate Detection: PASSED
  ✓ Subfolder Extractor: PASSED
  ✓ Batch Renamer: PASSED
  ✓ Junk & Analytics Engine: PASSED
  ✓ Extension Selector: PASSED
  ✓ Undo System: PASSED
  ✓ CLI Execution: PASSED
==========================================================
🎉 ALL 10 DEPLOYMENT TESTS PASSED WITH 100% SUCCESS!
==========================================================
```

---

## 📦 Building a Standalone Windows Executable (.exe)

To bundle the application into a standalone Windows executable (so users can run it without Python installed):

```bash
python build_exe.py
```

The output standalone folder and executable will be located in:
`dist/SmartFileOrganizer/SmartFileOrganizer.exe`
