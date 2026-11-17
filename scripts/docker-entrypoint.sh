#!/usr/bin/env bash
set -e

# Handle special subcommand keywords
if [ "$1" = "test" ]; then
    shift
    echo "Running Smart File Organizer Suite test suite..."
    exec pytest -v "$@"
elif [ "$1" = "gui" ]; then
    shift
    echo "Launching Smart File Organizer Suite GUI..."
    exec python run_sorter.py "$@"
elif [ "$1" = "cli" ]; then
    shift
    exec python cli.py "$@"
elif [ "$1" = "bash" ] || [ "$1" = "sh" ]; then
    exec "$@"
fi

# If arguments are passed starting with '-' or a path, pass them directly to cli.py
if [ $# -gt 0 ]; then
    exec python cli.py "$@"
else
    # Default: display CLI help
    exec python cli.py --help
fi
