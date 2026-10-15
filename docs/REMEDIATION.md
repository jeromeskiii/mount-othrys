# Remediation & Validation Report — Medium-Severity Findings MF-1, MF-2

- **Repository:** `jeromeskiii/mount-othrys`
- **Branch:** `fix/mount-othrys-medium-findings`
- **Source review:** *Project Harness Evaluation & Trial Run v2.0* of this repository (score 50/100, verdict ADAPT)
- **Scope of this remediation:** the two Medium-severity findings only.
- **Out of scope (still open, see [Remaining risks](#remaining-risks)):** P0-1/P0-2/P0-3
  build and bridge fixes (already landed in the preceding commit), P1-1 unenforced tool
  permissions, P1-2 automatic execution of the target repo's build/test scripts,
  P1-3 the unloadable `heracles` build artifact, P1-4 inert engine config.

Two findings were remediated. Nothing else was changed except the README sections they
made inaccurate.

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| **MF-1** | Medium | The engine's routed context was discarded before reaching any worker | **Fixed** |
| **MF-2** | Medium | Three routing tables disagreed and precedence was order-dependent | **Fixed** |

**Result:** 169 tests pass (was 105); `mypy` clean across 54 files; `tsc --noEmit` clean for
all three TypeScript packages. Both fixes are verified end-to-end, not just unit-tested.

---

## MF-1 — Rendered context is dropped before it reaches a worker

- **Severity / priority:** Medium / P1
- **Observed behaviour:** `WorkflowRunner` assembled
  `{ systemPrompt, mode, phase }` into `TitanInput.context`
  (`engine/src/workflow/runner.ts`), and `spawnPythonTitan` discarded it. The bridge carried a
  comment documenting the discard: *"Engine context (systemPrompt/mode/phase) is not accepted by
  any Titan CLI; each Titan ships its own system prompt, so it is not forwarded."* The two
  native adapters likewise ignored `input.context` and used their own hard-coded prompts.
- **Impact:** the engine's per-Titan mode identity never took effect for Python workers, so
  prompt engineering lived in **two** places (`engine/src/modes/*.ts` and each Titan's
  `prompts.py`) that could — and did — drift. Anything the engine learned about the routed mode
  was silently discarded at the process boundary.
- **Root cause (confirmed):** `runner.ts` builds the context; the bridge accepts `TitanInput` and
  reads only `prompt`/`workdir`, so the context field was dead payload. Forwarding it as command
  line arguments was not possible: every Titan defines `--json`/`--model` on its *main* argparse
  parser and subparsers reject undeclared options, so per-subcommand flags would have required
  editing all five CLIs; a multi-kilobyte system prompt also does not belong in the process table.
- **Fix applied:**
  - `othrys/src/othrys/context.py` *(new)* — `EngineContext` plus `load_context()`/`parse_context()`
    reading a single JSON environment variable `OTHRYS_CONTEXT`. Malformed or absent input yields
    an empty context rather than an exception, so a worker can never fail to start because of it.
  - `othrys/src/othrys/llm.py` — `BaseLLM.__init__` applies the envelope to its `LLMConfig`, and
    `_system_block` composes the engine directive ahead of the worker's own prompt. `BaseLLM` is
    the single funnel every Python Titan shares, so all five inherit the behaviour with no
    per-Titan wiring.
  - `engine/src/adapters/engineContext.ts` *(new)* — `buildEngineContext`/`serializeEngineContext`
    and `resolveSystemPrompt`, mirroring the Python composition rule.
  - `engine/src/adapters/python-bridge.ts` — the spawn prologue was extracted into a pure
    `buildTitanInvocation()` (so the argv/environment contract is testable without launching a
    process) and now sets `OTHRYS_CONTEXT`.
  - `engine/src/adapters/{themis,heracles}-adapter.ts` — honour the routed directive, and gained an
    optional injected `LLMProvider` so the request shape is assertable without network access.
- **Composition rule (deliberate):** the engine directive is **prepended**, not substituted — the
  worker's substantive persona prompt is preserved. Both languages implement the same rule with
  the same separator constant; it is asserted on both sides.
- **Regression risk:** a standalone CLI invocation has no envelope and is completely unaffected
  (asserted). Token budgets are deliberately **not** sent — Atlas declares `maxTokens: 16000`
  against its library default of 48000, so forwarding budgets would silently shorten its output.
  Per-Titan budgets belong to the engine-config finding (P1-4), which remains open.
- **Tests:** `engine/tests/contextPropagation.test.ts` (10) — includes a real child-process test
  proving the envelope arrives in a spawned process's environment;
  `othrys/tests/test_context.py` (10).
- **Acceptance criteria met:** the routed directive reaches the worker; the worker prompt survives;
  the prompt stays out of `argv`; absent/malformed envelopes change nothing.

---

## MF-2 — Three routing tables disagreed; precedence was order-dependent

- **Severity / priority:** Medium / P1
- **Observed behaviour:** routing was defined in **three** independent places that had drifted:
  `engine/src/router.ts` (the request boundary), `kronos/src/kronos/router.py` (`ROUTING_RULES`),
  and `talos/src/talos/titan_router.py` (its own keyword lists). The engine picked the *first*
  matching trigger in registry insertion order, so a generic trigger permanently shadowed a more
  specific one. Measured against the documented table in `README.md`:
  - `"Implement this complex work"` → documented **Iapetus**, actually routed to **Talos**.
  - `"Complex multi-disciplinary"` → documented **Coordinator**, actually routed to **Talos**.
- **Impact:** the documented routing contract was wrong in two of eight rows, and routing outcomes
  depended on the order of keys in a TypeScript object literal — a refactor that reordered the
  registry would silently change behaviour. Because the three tables disagreed, the engine,
  Kronos and Talos could each pick a different Titan for the same request.
- **Root cause (confirmed):** duplication with no shared source. Each layer had been written
  independently; the engine's `first match wins` scan gave no way to express specificity.
- **Fix applied — one canonical table:**
  - `othrys/src/othrys/routing.table.json` *(new)* — the single authority: ordered, weighted
    intent entries with regex patterns plus a shared golden `examples` corpus. It lives inside the
    `othrys` Python package, which is the one shared artifact both languages already install, so
    the wheel carries it automatically and an installed Titan cannot drift from the engine.
  - `othrys/src/othrys/routing.py` *(new)* — `load_table()`, `match_rule()`, `canonical_titan()`
    implementing the documented precedence.
  - `engine/src/routing/table.ts` *(new)* — reads and `zod`-validates the same table at runtime
    (it sits outside the engine's `rootDir`, so it is read rather than imported), exposing
    `matchRoutingRule()`, `routingTitans()` and `routingExamples()`.
  - `engine/src/modes/registry.ts` — builds each `TitanConfig`'s `triggers`, `keywords` and new
    `routingPriority` **from** the table; `EngineError`s loudly if a registered Titan has no entry.
  - `engine/src/router.ts` — selects by descending `routingPriority` (stable sort keeps registry
    order for ties) instead of declaration order.
  - `engine/src/modes/*.ts` (7 files) — the per-mode `triggers`/`keywords` literals were **deleted**
    and the type narrowed to a new `TitanModeSpec`, so the duplication cannot return.
  - `kronos/src/kronos/router.py` — `ROUTING_RULES` deleted; routing defers to `match_rule()` and
    maps the canonical Titan into Kronos's registry (`kronos` → its `coordinator` role).
  - `talos/src/talos/titan_router.py` — its keyword lists deleted; delegates to `match_rule()` and
    maps the resolved Titan into Talos's actions via a new `DELEGATIONS` table.
- **Precedence (documented in the README and in the table itself):** every matching entry scores its
  own `weight`; highest weight wins; ties resolve to the earliest table entry; nothing matched falls
  through to the caller's default (Talos). Weights make specificity explicit — Talos's generic
  `/implement/` is weight 10, Iapetus's "implement this complex work" is weight 60.
- **Behaviour deltas (intended and documented):** the two README rows above now route as
  documented. The previously unreachable intents Talos and Kronos implemented privately
  (`boulder`, `orchestrate`, `decompose`, `multi-disciplinary`, `deep analyse`, `thorough
  analysis`, …) are now in the shared table, so the engine reaches them too. Every pre-existing
  routing test still passes unchanged, and the README table is now machine-checked.
- **Regression risk:** low but real — a table edit changes runtime routing. Mitigated by
  (a) `zod` validation on load, (b) the engine failing fast if a Titan is missing from the table,
  and (c) `engine/tests/routingTable.test.ts` parsing the routing table **out of `README.md`** and
  failing if documentation and implementation disagree.
- **Tests:** `engine/tests/routingTable.test.ts` (9), `othrys/tests/test_routing.py` (15),
  `kronos/tests/test_kronos_routing_conformance.py` (4),
  `talos/tests/test_talos_routing_conformance.py` (4).
- **Acceptance criteria met:** exactly one table defines routing; both languages score the same
  golden corpus identically; a specific intent outranks a generic one; ties are deterministic;
  the README table is enforced by test.

---

## Validation results

Environment: macOS 27.0.1 (arm64), Python 3.14.4, Node v24.14.1, npm 11.11.0, mypy 1.20.2, pytest 9.1.1.

| Validation | Command | Result |
|---|---|---|
| Project gate | `make check` | **PASS** (exit 0) |
| TypeScript typecheck | `npx tsc --noEmit` — engine, themis, heracles | **PASS** |
| Python typecheck | `mypy othrys/src atlas/src coeus/src iapetus/src talos/src kronos/src` | **PASS** — "no issues found in 54 source files" |
| TypeScript tests | `npm test -- --run` — engine, themis, heracles | **PASS** — 38 + 15 + 10 = **63** |
| Python tests | `pytest -q othrys/tests atlas/tests coeus/tests iapetus/tests talos/tests kronos/tests` | **PASS** — **106** |
| **Total** | | **169 passed, 0 failed, 0 skipped** (105 before this change) |

### Independent cross-language verification

`route` through the built engine CLI and `canonical_titan()` through Python were run over all 23
golden corpus entries:

```
MF-2 corpus mismatches: 0        (23/23 identical in both languages)
Implement this complex work -> titan: iapetus | reason: Trigger match: /implement[^.]*complex/i → iapetus
args            : ["-m","iapetus","--json","analyze","what can break"]
argv carries prompt? false
OTHRYS_CONTEXT  : {"mode":"iapetus","phase":"execute","systemPrompt":"You are Iapetus of Mount Othrys: …"}
system prompt   : 'ENGINE DIRECTIVE\n\n---\n\nWORKER PROMPT'   (envelope present)
system prompt   : 'WORKER PROMPT'                               (no envelope — unchanged)
```

### CI assessment (not green — pre-existing)

`.github/workflows/ci.yml` was assessed against its own job definitions:

| Job | Expected outcome |
|---|---|
| `typescript-packages` (engine, themis, heracles) | **Green** — typecheck, 63 tests and build all pass |
| `python-othrys` | **Green** — mypy clean, tests pass |
| `python-titans` matrix — `atlas`, `coeus` | **Green** |
| `python-titans` matrix — `iapetus`, `talos`, `kronos` | **Red — pre-existing** |

The three red jobs run `mypy src` with `working-directory: <titan>`, which picks up each
`pyproject.toml`'s `[tool.mypy] strict = true`; the unannotated `cli.py`/`storage.py` files fail
under strict mode. This is **not** caused by this change — the same command against the parent
commit `a265e41` in a disposable worktree reproduces identical counts:

| Package | Errors at `a265e41` (baseline) | Errors after MF-1/MF-2 | Delta |
|---|---|---|---|
| `kronos` | 7 in 2 files | 7 in 2 files | **0** |
| `talos` | 11 in 3 files | 11 in 3 files | **0** |
| `iapetus` | 11 in 2 files | 11 in 2 files | **0** |

Neither `kronos/src/kronos/router.py` nor `talos/src/talos/titan_router.py` — the only files this
remediation edited in those packages — appears in either run's error output.

---

## Remaining risks

1. **CI `python-titans` is red for `iapetus`, `talos`, `kronos`** — pre-existing and unrelated to
   this change, but it means CI cannot go green on this branch. Either annotate those CLIs or scope
   each `[tool.mypy]` to the modules that are already typed.
2. **Tool permissions remain declarative (P1-1).** `guardScope()` in
   `engine/src/workflow/tool-guard.ts` is never called, and Atlas's declared read-only policy is not
   enforced on its subagents. The README's "Tool Access by Titan" table is still aspirational.
3. **`ask` still auto-executes the target repository's `build`/`test` scripts (P1-2)** through
   `engine/src/workflow/verifier.ts`, with no opt-in flag.
4. **`heracles`' built package is not loadable (P1-3)** — `moduleResolution: "bundler"` emits
   extensionless re-exports that Node ESM cannot resolve; its tests pass only because they import
   from `src/`.
5. **Engine config remains inert (P1-4)** — `config --set-model` does not persist and no adapter
   reads `defaultModel`. MF-1's envelope deliberately leaves token budgets to this finding.
6. **The baseline commit `a265e41` is a large pre-existing working-tree drop**, landed so this
   branch could build and be tested at all. It removes the process sandbox that the previous
   `HEAD` used (`allowShell: false`, command whitelist, `writablePaths`, audit logging). The
   replacement spawns a fixed, non-user-controlled argv, so there is no shell-injection vector, but
   the defence-in-depth loss deserves a deliberate review. The commit message carries the full
   inventory.
7. **`bin/mount-othrys` still shells out to `npx tsx`**, which is not declared in
   `engine/package.json`; it works on this machine only because a global `tsx` is installed.

---

## Release operations

- **Branch:** `fix/mount-othrys-medium-findings` — two commits: the baseline drop (`a265e41`), then
  the MF-1/MF-2 remediation.
- **Not committed:** `.architect/` and `.sisyphus/` (agent runtime state) and `Icon\r` (OS junk).
- **Adding a new routing intent:** edit `othrys/src/othrys/routing.table.json` only — add an entry
  (or a pattern to an existing one), add an `examples` row, and both test suites pick it up.
- **Adding a new Titan:** add its `TitanModeSpec` to `engine/src/modes/`, register it in `MODE_SPECS`,
  and add a table entry. The engine refuses to start if the two disagree.
- **Reproducing this validation:** `make check` from the repository root.