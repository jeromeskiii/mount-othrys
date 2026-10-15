#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo " Mount Othrys: Production Verification "
echo "=========================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHONPATH_TITANS="othrys/src:atlas/src:coeus/src:iapetus/src:talos/src:kronos/src"

echo ""
echo "[1/4] TypeScript Type Checks..."
(cd engine && npx tsc --noEmit)
(cd themis && npx tsc --noEmit)
(cd heracles && npx tsc --noEmit)
echo "✓ TypeScript type checking passed!"

echo ""
echo "[2/4] Python Type Checks (mypy)..."
PYTHONPATH="$PYTHONPATH_TITANS" python3 -m mypy othrys/src atlas/src coeus/src iapetus/src talos/src kronos/src
echo "✓ Python type checking passed!"

echo ""
echo "[3/4] TypeScript Tests (vitest)..."
(cd engine && npm test -- --run)
(cd themis && npm test -- --run)
(cd heracles && npm test -- --run)
echo "✓ TypeScript tests passed!"

echo ""
echo "[4/4] Python Tests (pytest)..."
PYTHONPATH="$PYTHONPATH_TITANS" python3 -m pytest -q othrys/tests atlas/tests coeus/tests iapetus/tests talos/tests kronos/tests
echo "✓ Python tests passed!"

echo ""
echo "=========================================="
echo " ALL CHECKS PASSED (Production Ready) ✓"
echo "=========================================="
