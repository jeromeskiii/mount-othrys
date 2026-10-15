#!/usr/bin/env bash
set -euo pipefail

echo "=========================================="
echo " Mount Othrys: Verification "
echo "=========================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHONPATH_TITANS="othrys/src:atlas/src:coeus/src:iapetus/src:talos/src:kronos/src"
PY_TITANS="atlas coeus iapetus talos kronos"

# Runs the same command as CI's `python-titans` job: mypy from inside each
# package directory, which picks up that package's own [tool.mypy] settings
# (several set `strict = true`). The root-level check below does NOT use those
# settings, so without this step the local gate was quietly weaker than CI.
typecheck_python_strict() {
    local titan
    for titan in $PY_TITANS; do
        echo "  > mypy $titan"
        (cd "$titan" && PYTHONPATH="src:../othrys/src:../atlas/src:../coeus/src:../iapetus/src:../talos/src:../kronos/src" \
            python3 -m mypy src)
    done
}

echo ""
echo "[1/5] TypeScript Type Checks..."
(cd engine && npx tsc --noEmit)
(cd themis && npx tsc --noEmit)
(cd heracles && npx tsc --noEmit)
echo "✓ TypeScript type checking passed!"

echo ""
echo "[2/5] Python Type Checks (mypy, repo aggregate)..."
PYTHONPATH="$PYTHONPATH_TITANS" python3 -m mypy othrys/src atlas/src coeus/src iapetus/src talos/src kronos/src
echo "✓ Python type checking passed!"

echo ""
echo "[3/5] Python Type Checks (mypy, per-package strict — mirrors CI)..."
typecheck_python_strict
echo "✓ Python strict type checking passed!"

echo ""
echo "[4/5] TypeScript Tests (vitest)..."
(cd engine && npm test -- --run)
(cd themis && npm test -- --run)
(cd heracles && npm test -- --run)
echo "✓ TypeScript tests passed!"

echo ""
echo "[5/5] Python Tests (pytest)..."
PYTHONPATH="$PYTHONPATH_TITANS" python3 -m pytest -q othrys/tests atlas/tests coeus/tests iapetus/tests talos/tests kronos/tests
echo "✓ Python tests passed!"

echo ""
echo "=========================================="
echo " ALL CHECKS PASSED ✓"
echo "=========================================="
echo "Covered: TypeScript typecheck + tests (engine, themis, heracles);"
echo "         Python typecheck (aggregate + per-package strict) + tests."
echo "Not covered: end-to-end agent runs (these need ANTHROPIC_API_KEY);"
echo "             behaviour outside macOS/Linux; see docs/REMEDIATION.md."
