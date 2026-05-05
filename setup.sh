#!/bin/bash

# Mount Othrys Unified Setup Script
# Automatically configures Node.js and Python environments for all Titans

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Mount Othrys Unified Setup ===${NC}"

# Check for Node.js
if ! command -v node >/dev/null 2>&1; then
    echo -e "${RED}Error: Node.js is not installed.${NC}"
    exit 1
fi

# Check for Python
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: Python3 is not installed.${NC}"
    exit 1
fi

ROOT_DIR=$(pwd)

setup_node() {
    local dir=$1
    echo -e "${GREEN}Configuring Node.js in ${dir}...${NC}"
    cd "$ROOT_DIR/$dir"
    if [ -f "package-lock.json" ]; then
        npm install
    elif [ -f "pnpm-lock.yaml" ]; then
        pnpm install
    elif [ -f "bun.lockb" ] || [ -f "bun.lock" ]; then
        if command -v bun >/dev/null 2>&1; then
            bun install
        else
            npm install
        fi
    else
        npm install
    fi
}

setup_python() {
    local dir=$1
    echo -e "${GREEN}Configuring Python in ${dir}...${NC}"
    cd "$ROOT_DIR/$dir"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip -q
    if [ -f "pyproject.toml" ]; then
        pip install -e . -q
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
    fi
    if [ -d "$ROOT_DIR/othrys" ]; then
        pip install -e "$ROOT_DIR/othrys" -q
    fi
    deactivate
}

# Setup shared library first
if [ -d "othrys" ]; then
    echo -e "${GREEN}Installing shared library othrys...${NC}"
    cd "$ROOT_DIR/othrys"
    python3 -m pip install -e . -q
fi

# Setup Engine
if [ -d "engine" ]; then
    setup_node "engine"
    cd "$ROOT_DIR/engine"
    npm run build
fi

# Setup Titans
for dir in kronos atlas coeus iapetus talos themis heracles; do
    if [ -d "$dir" ]; then
        if [ -f "$dir/package.json" ]; then
            setup_node "$dir"
        fi
        if [ -f "$dir/pyproject.toml" ] || [ -f "$dir/requirements.txt" ]; then
            setup_python "$dir"
        fi
    fi
done

echo -e "${BLUE}=== Setup Complete ===${NC}"
echo -e "You can now run the system using the engine CLI."
