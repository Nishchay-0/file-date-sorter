# 🐳 Docker Environment Guide — Smart File Organizer Suite Pro

This guide explains how to build and run **Smart File Organizer Suite Pro** inside a containerized Docker environment. It allows you to organize directories, run batch renames, deduplicate files, and execute the automated test suite without configuring Python or system dependencies on your host.

---

## 📋 Table of Contents

1. [Quickstart with Docker Compose](#quickstart-with-docker-compose)
2. [Building the Docker Image](#building-the-docker-image)
3. [Running File Organization Tasks](#running-file-organization-tasks)
   - [Dry-Run Mode (Safe Preview)](#1-dry-run-mode-safe-preview)
   - [Sort by Category](#2-sort-by-category-documents-images-etc)
   - [Sort by Date](#3-sort-by-date-yearmonth)
   - [Sort by Smart Name](#4-sort-by-smart-name-grouping)
   - [Clean Empty Folders](#5-clean-empty-folders)
   - [Undo Last Operation](#6-undo-last-operation)
4. [Running the Test Suite in Docker](#running-the-test-suite-in-docker)
5. [Interactive Shell](#interactive-shell)
6. [Mounting Host Directories on Windows / macOS / Linux](#mounting-host-directories-on-windows--macos--linux)
7. [GUI via Docker (Optional X11 Forwarding)](#gui-via-docker-optional-x11-forwarding)

---

## ⚡ Quickstart with Docker Compose

Ensure Docker (or Docker Desktop) is running, then use Docker Compose:

```bash
# 1. Build the Docker image
docker compose build

# 2. View CLI options and help
docker compose run --rm sorter

# 3. Run the automated pytest test suite inside the container
docker compose run --rm test
```

---

## 🔨 Building the Docker Image

To build the standalone Docker image using Docker CLI:

```bash
docker build -t smart-file-organizer .
```

Verify the image build and version:

```bash
docker run --rm smart-file-organizer --version
```

---

## 📂 Running File Organization Tasks

When using Docker, mount the directory containing your files to the `/data` directory inside the container using the `-v` (volume) flag.

### 1. Dry-Run Mode (Safe Preview)
Always preview sorting operations without moving any files:

```bash
# Windows PowerShell / CMD:
docker run --rm -v "C:\Users\YourUser\Downloads:/data" smart-file-organizer --path /data --sort-category category --dry-run

# Linux / macOS:
docker run --rm -v "/path/to/myfiles:/data" smart-file-organizer --path /data --sort-category category --dry-run
```

### 2. Sort by Category (Documents, Images, etc.)
Moves files into categorized folders (`Images`, `Documents`, `Audio`, `Videos`, `Archives`, etc.):

```bash
docker run --rm -v "C:\Target\Path:/data" smart-file-organizer --path /data --sort-category category
```

### 3. Sort by Date (Year/Month)
Organize files by creation date into `YYYY/MM` subfolders:

```bash
docker run --rm -v "C:\Target\Path:/data" smart-file-organizer --path /data --sort-category date --format "YYYY/MM"
```

### 4. Sort by Smart Name Grouping
Group files by meaningful title prefixes (stripping dates, stopwords, and routing random hashes to `_Random/`):

```bash
docker run --rm -v "C:\Target\Path:/data" smart-file-organizer --path /data --sort-category smart_name
```

### 5. Clean Empty Folders
Remove leftover empty directories recursively:

```bash
docker run --rm -v "C:\Target\Path:/data" smart-file-organizer --path /data --clean-empty-only
```

### 6. Undo Last Operation
Rollback the last move/sort action using the atomic undo manifest:

```bash
docker run --rm -v "C:\Target\Path:/data" smart-file-organizer --path /data --undo LATEST
```

---

## 🧪 Running the Test Suite in Docker

Run the entire suite of unit and integration tests inside the isolated container:

```bash
# Using Docker Compose:
docker compose run --rm test

# Or using Docker CLI:
docker run --rm smart-file-organizer test
```

You can also pass specific test files or flags to pytest:

```bash
docker run --rm smart-file-organizer test test_smart_name_sorter.py -k test_clean
```

---

## 🐚 Interactive Shell

To enter the container with a bash prompt for debugging or custom operations:

```bash
# Using Docker Compose:
docker compose run --rm shell

# Or using Docker CLI:
docker run --rm -it -v "C:\Target\Path:/data" smart-file-organizer bash
```

---

## 💻 Mounting Host Directories on Windows / macOS / Linux

| OS | Host Path Syntax | Docker Run Example |
| :--- | :--- | :--- |
| **Windows (PowerShell)** | `"C:\MyFolder:/data"` | `docker run --rm -v "C:\MyFolder:/data" smart-file-organizer --path /data --dry-run` |
| **Windows (Git Bash)** | `/c/MyFolder:/data` | `docker run --rm -v /c/MyFolder:/data smart-file-organizer --path /data --dry-run` |
| **macOS / Linux** | `$(pwd)/mydata:/data` | `docker run --rm -v "$(pwd)/mydata:/data" smart-file-organizer --path /data --dry-run` |

> [!TIP]
> **Zero Data Loss Guarantee**: Destructive actions (moving/deleting files) automatically create a `.undo_manifest.json` in the target folder so you can undo the operation at any time.

---

## 🖥️ GUI via Docker (Optional X11 Forwarding)

The container includes all Tkinter and CustomTkinter dependencies. To display the graphical UI from within the container:

### Linux:
```bash
xhost +local:root
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix smart-file-organizer gui
```

### Windows (with VcXsrv / Xming):
1. Start VcXsrv with "Disable access control" checked.
2. In PowerShell:
```powershell
docker run --rm -e DISPLAY=host.docker.internal:0.0 smart-file-organizer gui
```
