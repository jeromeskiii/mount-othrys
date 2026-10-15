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
    cd "$ROOT_DIR/$dir" || return 1
    # --include=dev: the user's global npmrc may set omit=dev, which would
    # strip typescript/@types/node/vitest and break `npm run build`.
    # --no-audit: npm audit against the registry can stall for minutes and
    # looks like a hung agent setup. Re-run with audit only when debugging.
    if [ -f "package-lock.json" ]; then
        npm install --include=dev --no-audit --no-fund
    elif [ -f "pnpm-lock.yaml" ]; then
        pnpm install
    elif [ -f "bun.lockb" ] || [ -f "bun.lock" ]; then
        if command -v bun >/dev/null 2>&1; then
            bun install --dev
        else
            npm install --include=dev --no-audit --no-fund
        fi
    else
        npm install --include=dev --no-audit --no-fund
    fi
    cd "$ROOT_DIR"
}

# Local Titan packages are not on PyPI (`atlas` on PyPI is a different
# project). Install the shared lib first, then sibling Titans from this
# repo, then the package itself so pip never hits PyPI for those names.
install_local_python_deps() {
    local dir=$1
    pip install -e "$ROOT_DIR/othrys" -q
    case "$dir" in
        iapetus)
            pip install -e "$ROOT_DIR/atlas" --no-deps -q
            ;;
        talos)
            pip install -e "$ROOT_DIR/atlas" --no-deps -q
            pip install -e "$ROOT_DIR/iapetus" --no-deps -q
            ;;
        kronos)
            pip install -e "$ROOT_DIR/atlas" --no-deps -q
            pip install -e "$ROOT_DIR/coeus" --no-deps -q
            pip install -e "$ROOT_DIR/iapetus" --no-deps -q
            pip install -e "$ROOT_DIR/talos" --no-deps -q
            ;;
    esac
}

setup_python() {
    local dir=$1
    echo -e "${GREEN}Configuring Python in ${dir}...${NC}"
    cd "$ROOT_DIR/$dir"
    python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install --upgrade pip -q
    install_local_python_deps "$dir"
    if [ -f "pyproject.toml" ]; then
        pip install -e . --no-deps -q
    elif [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -q
    fi
    deactivate
    cd "$ROOT_DIR"
}

# Setup shared library first
if [ -d "othrys" ]; then
    echo -e "${GREEN}Installing shared library othrys...${NC}"
    cd "$ROOT_DIR/othrys"
    python3 -m pip install -e . -q
    cd "$ROOT_DIR"
fi

# Setup Engine
if [ -d "engine" ]; then
    setup_node "engine"
    cd "$ROOT_DIR/engine"
    npm run build
    cd "$ROOT_DIR"
fi

# Setup Titans (Python DAG: atlas/coeus → iapetus → talos → kronos)
for dir in atlas coeus iapetus talos kronos themis heracles; do
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
