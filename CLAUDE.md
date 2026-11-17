> **This project uses `AGENTS.md` as its primary project-memory file.**
> Read `AGENTS.md` fully before searching or scanning the codebase.

# Smart File Organizer Suite Pro — CLAUDE.md

This file exists as a companion/redirect. All module maps, run commands, working rules, and constraints are in:

- **[AGENTS.md](AGENTS.md)** — full project guide, module map, working rules digest
- **[PLAN.md](PLAN.md)** — living roadmap (done / in-progress / planned)
- **[docs/known-issues.md](docs/known-issues.md)** — confirmed bugs and fixes with evidence
- **[docs/constraints.md](docs/constraints.md)** — hard rules and runtime decisions

---

## Runtime: Native (not Docker)

This project targets a Windows desktop GUI with OS-specific APIs (cloud-placeholder file attributes, Windows registry, Tkinter/CustomTkinter, Inno Setup installer). Per Part 11 of the working agreement, **Docker does not fit as the primary runtime** for this project. See `docs/constraints.md` for the full rationale.

**Native environment:**
```powershell
# Activate venv
& "C:\file-date-sorter\.venv\Scripts\Activate.ps1"

# Run GUI
python run_sorter.py

# Run tests
$env:TCL_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python315\tcl\tcl8.6"
$env:TK_LIBRARY="C:\Users\saini\AppData\Local\Programs\Python\Python315\tcl\tk8.6"
& "C:\file-date-sorter\.venv\Scripts\python.exe" -m pytest -v
```

## Docker (CI-only, not for GUI)

Docker is used **only** for the CI pipeline (secret scan, headless CLI tests). It cannot run the desktop GUI. If Docker is not installed, the CI workflow handles it; local development always uses the native `.venv`.

```powershell
# CI-equivalent local test (headless CLI tests only)
docker compose run --rm test
```
