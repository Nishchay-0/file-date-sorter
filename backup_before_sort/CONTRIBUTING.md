# Contributing to Smart File Organizer Suite Pro

Thank you for your interest in contributing to **Smart File Organizer Suite Pro**! This guide outlines our architecture, coding conventions, testing protocols, and working agreements.

---

## 🧭 Architecture & Code Layout

- [`sorter_core.py`](sorter_core.py): Central engine handling date extraction, file moves, categorizations, smart name groupings, and directory flattening.
- [`hashing.py`](hashing.py): Tiered file hashing (SHA-256, head/tail fast sampling, perceptual dHash) and cloud placeholder checks.
- [`utils.py`](utils.py): Path normalization (`fix_win_long_path`), extended-length prefixes (`\\?\` and `\\?\UNC\`), and filesystem helpers.
- [`config.py`](config.py): Named constants (`FILE_CHUNK_SIZE`, `WIN_LONG_PATH_THRESHOLD`), file category maps, and stopwords.
- [`logger.py`](logger.py): Centralized logging provider (`get_logger`, `setup_logging`).
- [`face_sort.py`](face_sort.py): OpenCV YuNet + SFace face detection and DBSCAN clustering.
- [`cli.py`](cli.py): Headless command-line interface.
- [`gui_modules/`](gui_modules/): Apple Glassmorphism desktop GUI views and components.

---

## 🚨 Non-Negotiable Hard Constraints

1. **Zero Personal Data (PII) Policy**: Never commit real user data, credentials, real photos, or database files. Use synthetic fixtures only.
2. **Zero Data Loss Guarantee**: All destructive operations (moving, deleting, overwriting) must create a System Vault zip backup and an atomic `.undo_manifest.json`.
3. **Cloud Safe Mode**: Always check `is_cloud_placeholder()` before reading files to prevent hydrating cloud-only files on OneDrive, iCloud, or Dropbox.
4. **Windows Path Resilience**: Always use `fix_win_long_path()` when opening files or checking paths to support Windows paths $\ge 240$ characters and UNC network shares.
5. **No Telemetry**: The application runs 100% locally. Do not add external network reporting, telemetry, or analytics.

---

## 🛠️ Development Setup

### Local Python Environment

```powershell
# 1. Clone repository
git clone https://github.com/Nishchay-0/file-date-sorter.git
cd file-date-sorter

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt pytest
```

### Docker Environment

```bash
# Build container image
docker compose build

# Run automated tests in container
docker compose run --rm test

# Run interactive container shell
docker compose run --rm shell
```

---

## 🧪 Running Tests

Always run the full test suite before committing:

```powershell
# Run core unit tests
py -3.14 -m pytest test_core_units.py -v

# Run full regression suite
py -3.14 -m pytest -v
```

---

## 📐 Coding Conventions

1. **Type Hints**: Annotate public function parameters and return types (`def func(path: str) -> Optional[str]:`).
2. **Centralized Constants**: Never hardcode magic numbers (chunk sizes, path length limits, attribute masks). Define or import them from `config.py` or `utils.py`.
3. **Logging Over Print**: Use `logger = get_logger("SubsystemName")` with appropriate levels (`debug`, `info`, `warning`, `error`) instead of bare `print()`.
4. **DRY Principle**: Reuse existing helpers in `utils.py` and `hashing.py` rather than duplicating logic.
