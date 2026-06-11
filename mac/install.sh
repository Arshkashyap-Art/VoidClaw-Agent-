#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[*] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python 3 is not installed. Please install it.${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Python found!${NC}"

python3 -m venv .venv
source .venv/bin/activate
echo -e "${CYAN}[*] Installing dependencies...${NC}"
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo -e "${GREEN}[+] Dependencies installed!${NC}"

echo -e "${CYAN}[*] Starting Configuration Wizard...${NC}"
python3 core/setup.py

