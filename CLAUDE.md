## Running with Docker

The project can be built, tested, and run inside a Docker container to guarantee a reproducible environment.

**Typical workflow**
```powershell
# Build the image (run once or after Dockerfile changes)
docker compose build

# Start the container (detached)
docker compose up -d

# Run the GUI (or CLI) inside the container
# GUI (requires display forwarding on Windows; see Docker docs for X server setup)
docker compose exec app python gui.py

# Run the CLI
# Example: sort a folder

docker compose exec app python cli.py --path C:\\Target\\Path --sort-category date

# Run the test suite

docker compose exec app pytest -v

# Stop and clean up

docker compose down
```

**Notes**
- The source directory is mounted as a volume (`.:/app:cached`), so changes you make on the host are reflected inside the container without rebuilding.
- No ports are exposed by default because the application is a desktop GUI; if you add a web service later, expose it via the `ports:` section in `docker‑compose.yml`.
- All development commands (build, test, lint, etc.) should be executed via `docker compose exec app <cmd>` as enforced by `docs/constraints.md`.
- If Docker is not installed, see the Docker detection step in the startup script (to be added) which will prompt the user to install Docker before proceeding.
