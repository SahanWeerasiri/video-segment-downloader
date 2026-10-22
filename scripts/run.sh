#!/bin/bash
# Convenient runner using the virtual environment in ~/projects/headless_telebot
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_SCRIPT="$REPO_ROOT/src/video_sniffer_downloader.py"
VENV_PYTHON="/home/sahan-weerasiri/projects/headless_telebot/.venv/bin/python"

if [ -f "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "$PYTHON_SCRIPT" "$@"
else
    python3 "$PYTHON_SCRIPT" "$@"
fi
