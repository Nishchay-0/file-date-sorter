FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgtk-3-0 \
 && rm -rf /var/lib/apt/lists/*

# Copy only required source files
COPY CLAUDE.md requirements.txt requirements-dev.txt run_sorter.py cli.py gui.py sorter_core.py config.py utils.py settings_manager.py logger.py version.py face_sort.py hashing.py build_exe.py installer.iss . /app/

# Install Python dependencies (offline wheels could be added later)
RUN pip install --no-cache-dir -r requirements.txt

# Expose a port if the app provides a web service (none currently, placeholder)
# EXPOSE 8000

# Default command – launch the GUI (or CLI) when container runs
CMD ["python", "gui.py"]
