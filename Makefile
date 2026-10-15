.PHONY: all test typecheck build check clean setup

PYTHONPATH := othrys/src:atlas/src:coeus/src:iapetus/src:talos/src:kronos/src

all: check

setup:
	./setup.sh

build:
	cd engine && npm run build
	cd themis && npm run build
	cd heracles && npm run build

typecheck-ts:
	cd engine && npx tsc --noEmit
	cd themis && npx tsc --noEmit
	cd heracles && npx tsc --noEmit

typecheck-py:
	PYTHONPATH=$(PYTHONPATH) python3 -m mypy othrys/src atlas/src coeus/src iapetus/src talos/src kronos/src

typecheck: typecheck-ts typecheck-py

test-ts:
	cd engine && npm test -- --run
	cd themis && npm test -- --run
	cd heracles && npm test -- --run

test-py:
	PYTHONPATH=$(PYTHONPATH) python3 -m pytest -q othrys/tests atlas/tests coeus/tests iapetus/tests talos/tests kronos/tests

test: test-ts test-py

check: typecheck test

clean:
	cd engine && npm run clean || true
	cd themis && npm run clean || true
	cd heracles && npm run clean || true
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
