# Project Constraints

## Hard Rules (non‑negotiable)
- **No telemetry or data sharing** with any external service unless the user explicitly authorises it.
- **Zero‑destructive‑action without a reversible path**: every destructive operation (move, delete, rename) must first create an atomic zip backup and a `.undo_manifest.json` that can restore the previous state.
- **Windows long‑path handling**: any file‑system path must be passed through `utils.fix_win_long_path` before using OS APIs.
- **No secrets in the repository**: `.env`, credential files, private keys, and any token‑like strings must be listed in `.gitignore` and never committed.
- **All development & build commands must run inside Docker** once the Docker environment is set up (see Docker auto‑setup section in `CLAUDE.md`). Host‑side installations are prohibited unless explicitly approved.
- **No external network calls** (e.g., downloading models, contacting APIs) without explicit user consent. The code should check `docs/constraints.md` before performing such actions.
- **No irreversible changes without user confirmation**: large downloads, heavy compute, long‑running jobs must be announced with estimated cost and await user approval.
- **Public interface stability**: Do not modify existing CLI arguments, function signatures, or GUI APIs without explicit instruction.

## Operational Guidelines
- **Backup before any file‑system mutation** – `sorter_core.generate_undo_manifest` creates a zip and manifest; ensure it runs before moving/deleting files.
- **Secret‑scan before push** – run a diff scan for strings matching typical secret patterns (e.g., `AKIA`, `-----BEGIN PRIVATE KEY-----`).
- **Docker presence check** – at session start, run `docker version` and `docker compose version`. If missing, prompt the user to install Docker before proceeding.
- **Testing discipline** – every bug fix must be accompanied by a regression test placed under `tests/`.
- **Documentation discipline** – any discrepancy between code and docs (`CLAUDE.md`, `PLAN.md`, `docs/known-issues.md`) must be resolved by updating the docs to reflect the code.
- **Context hygiene** – re‑read `CLAUDE.md`, `PLAN.md`, and `docs/constraints.md` before each new phase of work.

## Project‑Specific Decisions
- **Model files** (`*.onnx` in `models/`) are considered large binary assets; they are excluded from the repo and downloaded on‑demand. They are listed in `.gitignore`.
- **Generated caches** (`.people_cache.json`, `.people_index.json`, `.undo_manifest.json`) are runtime artifacts and must not be committed.
- **Docker default** – the container runs as `app` service exposing port `8000` (if needed). All commands should be executed via `docker compose exec app <cmd>`.

*This file is authoritative for constraints; any change must be reviewed and committed with a clear rationale.*