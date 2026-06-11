#!/data/data/com.termux/files/usr/bin/bash

# VoidClaw Termux Launcher
# Optimized for Android

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    echo "Environment not found. Please run ./termux/install.sh first."
    exit 1
fi

source .venv/bin/activate
python core/agent.py
