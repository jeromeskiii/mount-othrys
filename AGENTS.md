# Mount Othrys — agent notes

Unified Titan router. TypeScript engine classifies a request and dispatches to a Titan (Python workers or TS adapters).

## Setup (run from this repo)

```bash
cd /Users/ohmskiii/mount-othrys
bash setup.sh
```

`setup.sh` installs `othrys` (shared Python lib), builds `engine/`, then creates a `.venv` in each Python Titan (`atlas`, `coeus`, `iapetus`, `talos`, `kronos`) and `npm install`s `themis` / `heracles`.

Needs Node 22+ and Python 3.11+. The script `cd`s back to the repo root after every Titan. Local packages (`atlas`, `othrys`, …) are installed from this repo (`--no-deps` for siblings) so pip does not fetch the unrelated PyPI `atlas` package. `npm install` uses `--no-audit` so setup does not stall for minutes on registry audit.

## How agents invoke it

CLI: `bin/mount-othrys` (or `npx tsx engine/src/cli.ts` from `engine/`).

```bash
./bin/mount-othrys help
./bin/mount-othrys status
./bin/mount-othrys titan --list
./bin/mount-othrys route "plan this feature"
./bin/mount-othrys ask "fix the auth bug" --workdir <project>
./bin/mount-othrys ask --titan themis "review this design"
```

Python workers (after venv exists):

```bash
./bin/mount-othrys coeus --help
./bin/mount-othrys atlas --help
./bin/mount-othrys iapetus --help
./bin/mount-othrys talos --help
./bin/mount-othrys kronos --help
```

Routing table (see README): plan → Coeus, architecture consult → Themis, todo list → Atlas, deep implement → Iapetus, default task → Talos, ultrawork → Heracles, unclear → Kronos.

## Env

- `ANTHROPIC_API_KEY` — Python Titans (`othrys.llm`)
- Engine default model: `claude-sonnet-4-5` (`engine/src/config.ts`)

Never commit keys. Never log tokens.

## Tests

```bash
cd engine && npm test
# per Titan, with its venv:
#   .venv/bin/python -m pytest
```

## Laws

- Engine routes; Titans execute. Do not import Titan internals into `engine/src/cli.ts`.
- Python Titans depend on the `othrys` package. Install `othrys` first (setup.sh does this).
- Directory names are lowercase (`coeus/`, not `Coeus/`).
- `ask` / `--execute` need the Titan venv at `<titan>/.venv/bin/python`.
