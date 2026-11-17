# Project Constraints

## Hard Rules (non-negotiable)

- **No telemetry or data sharing** with any external service unless the user explicitly authorises it.
- **Zero-destructive-action without a reversible path**: every destructive operation (move, delete, rename) must first create an atomic zip backup and a `.undo_manifest.json` that can restore the previous state.
- **Windows long-path handling**: any file-system path must be passed through `utils.fix_win_long_path` before using OS APIs.
- **No secrets in the repository**: `.env`, credential files, private keys, and any token-like strings must be listed in `.gitignore` and never committed.
- **No external network calls** (downloading models, contacting APIs) without explicit user consent.
- **No irreversible changes without user confirmation**: large downloads, heavy compute, long-running jobs must be announced with estimated cost and await approval.
- **Public interface stability**: do not modify existing CLI arguments, function signatures, or GUI APIs without explicit instruction.
- **No silent degradation**: surface missing models, permission errors, and fallbacks visibly — never hide them.

## Runtime Decision (Part 11, decided 2026-11-18)

**Primary runtime: Native Windows (`.venv`) — Docker does NOT fit as primary.**

**Reasoning:** This project is a Windows desktop GUI application (`CustomTkinter`/`Tkinter`) that relies on:
- OS-specific APIs: Windows cloud-placeholder file attributes (`FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`), Windows registry paths, NTFS extended paths (`\\?\`)
- A host-OS installer (`Inno Setup`, `.exe` output targeting Windows)
- A display server (Tkinter requires a real or forwarded display — not available headlessly in Docker on Windows)

Per Part 11 Step 1 of the working agreement: *"Desktop GUI apps, OS-specific APIs, installers or executables targeting a host OS"* do **not** fit Docker as a primary runtime.

**Docker is used for CI only** (secret scan, headless CLI/core-logic tests). It cannot replace the native environment for GUI development or installer builds.

**Native environment requirements:**
- Python 3.15 at `C:\Users\saini\AppData\Local\Programs\Python\Python315\`
- `.venv` at `C:\file-date-sorter\.venv\` (created with Python 3.15)
- `onnxruntime` not yet available for Python 3.15 — face-sort tests are skipped until a compatible wheel ships

## Operational Guidelines

- **Backup before any file-system mutation** — `sorter_core.generate_undo_manifest` creates a zip and manifest; ensure it runs before moving/deleting files.
- **Secret-scan before push** — run a diff scan for strings matching typical secret patterns (`AKIA`, `-----BEGIN PRIVATE KEY-----`, etc.).
- **Testing discipline** — every bug fix must be accompanied by a regression test; run with the `.venv` python, not system python.
- **pytest.ini is authoritative** — `backup_before_sort/`, `.venv/`, `backup/`, `test_folder_advanced/`, `test_super_duplicates_temp/` are excluded via `norecursedirs`.
- **Documentation discipline** — any discrepancy between code and docs must be resolved by updating docs to reflect the code, not the other way around.
- **Context hygiene** — re-read `AGENTS.md`, `PLAN.md`, and this file before each new phase of work.

## Project-Specific Decisions

- **Model files** (`*.onnx` in `models/`) are large binary assets; excluded from the repo via `.gitignore`, downloaded on-demand. Never commit them.
- **Generated caches** (`.people_cache.json`, `.people_index.json`, `.undo_manifest.json`) are runtime artifacts; never commit them.
- **`backup_before_sort/`** is a snapshot directory containing duplicate test files from an earlier session. It is excluded from pytest collection via `pytest.ini`. Do not delete it without creating a fresh backup zip first.
- **Docker (CI use only)** — the container runs the full headless test suite in CI (`.github/workflows/ci.yml`). No GUI or installer tests run inside Docker. All local development uses the native `.venv`.

*This file is authoritative for constraints. Any change must be committed with a clear rationale.*
