# ==============================================================================
# Smart File Organizer Suite Pro - Container Image
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install required system packages for OpenCV, ONNX Runtime, and Tkinter
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    tk \
    tcl \
    python3-tk \
    libx11-6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first for optimal Docker layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt pytest

# Copy project source code and assets
COPY . /app/

# Create non-root user and setup directories with permissions
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /data /output && \
    chmod +x /app/docker-entrypoint.sh && \
    chown -R appuser:appuser /app /data /output

# Switch to non-root user
USER appuser

# Set volume mount points
VOLUME ["/data", "/output"]

# Entrypoint script routes commands to cli.py, pytest, or bash
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default argument displays CLI help
CMD ["--help"]
