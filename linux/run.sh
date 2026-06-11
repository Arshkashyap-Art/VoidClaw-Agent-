#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"
if [ ! -d ".venv" ]; then
    echo "Environment not found. Please run install.sh first."
    exit 1
fi
source .venv/bin/activate
echo "Starting VoidClaw..."
python3 -m core.agent
