# Mount Othrys — Remediation Report

**Repository:** `jeromeskiii/mount-othrys`
**Baseline:** `add1070` (`main`, as found — could not build or pass CI)
**Final:** `1aaae07` (`main`, merged and CI-green)
**Verdict carried forward:** ADAPT — Harness Readiness Score 50 → ~54

This is the consolidated report for the whole remediation effort. It covers the **two
Medium-severity findings** that were the original brief (MF-1, MF-2), the **three follow-on findings**
that the work surfaced or created (G-1 High, G-2 Medium, G-3 Medium), the test evidence for each, and
what remains. Per-finding depth lives in companion documents; this report is the index and summary:

- [`REMEDIATION.md`](REMEDIATION.md) — MF-1 and MF-2, full detail.
- [`CI-GUARDRAIL.md`](CI-GUARDRAIL.md) — G-1, G-2 and G-3, full detail.
- [`validation/`](validation/) — raw logs and reproducibility harnesses.

---

## Executive summary

The project's self-assessment was optimistic relative to what actually ran. Two premises in particular
did not hold:

1. **The engine's routing identity was inert.** A Titan's routed context was assembled, then dropped
   before it reached any worker. Every mode-specific prompt and phase was decorative.
2. **There was no single routing authority.** Three tables disagreed, and precedence depended on
   iteration order.

Fixing (2) then broke the engine's portability, and repairing the CI pipeline — which had never passed
— turned out to be a prerequisite for trusting any of the above. All five findings are now fixed and
verified, and `main`'s CI is green for the first time.

| ID | Severity | Finding | Status | Evidence |
|----|----------|---------|--------|----------|
| **MF-1** | Medium | The engine's routed context was discarded before reaching any worker | Fixed | 10 TS + Python tests; real-runner-chain e2e |
| **MF-2** | Medium | Three routing tables disagreed; precedence was order-dependent | Fixed | 9 TS + conformance tests; ~320-message cross-language diff |
| **G-1** | High | CI's `python-titans` matrix could not pass as written — the pipeline gave no signal | Fixed | 9/9 CI jobs green; per-package strict mypy clean |
| **G-2** | Medium | The local gate was weaker than CI while claiming "Production Ready" | Fixed | Gate proven to fail on an injected violation |
| **G-3** | Medium | The built engine required the monorepo layout to import (regression from MF-2) | Fixed | Relocated-engine import succeeds |

**No production runtime behaviour was changed by G-1/G-2/G-3**: 29 edits are type annotations, the
rest are manifests, a build step and a gate script. MF-1 and MF-2 do change behaviour, which is their
purpose.

---

## MF-1 — The engine's routed context was discarded before reaching any worker

- **Severity:** Medium · **Category:** correctness / silent no-op · **Status:** Fixed

### Impact

`WorkflowRunner` assembled the per-Titan routing decision — `{ systemPrompt, mode, phase }` — into
`TitanInput.context`, and `spawnPythonTitan` then **dropped it**; the bridge even carried a comment
saying so. The native adapters ignored it as well. The practical effect: the engine's per-Titan mode
identity had no effect on anything. A Titan was invoked with the same inputs regardless of which mode
and phase the router had selected for it. The mode's prompt text existed in two places that could
drift, and any diagnosis of "the agent ignored its mode instructions" would have been chasing a
phantom, because those instructions were never sent.

This was a *silent* failure: nothing errored, nothing logged, no test failed.

### Root cause

The context envelope was constructed on the engine side and consumed on the Python side with **no
defined contract between them**. The bridge accepted `context` as a parameter and never serialised it;
no shared type or test asserted that what the engine sent was what the child process received. A
cross-language boundary with no contract and no test *at* the boundary is exactly where this class of
defect hides.

### Remediation

- **`othrys/src/othrys/context.py`** *(new)* — `EngineContext` plus `load_context()`/`parse_context()`
  over a single JSON environment variable, `OTHRYS_CONTEXT`. Malformed or absent input yields an empty
  context and never raises, so a bad envelope degrades instead of breaking a run.
- **`othrys/src/othrys/llm.py`** — `BaseLLM.__init__` and `_system_block` accept and honour it.
- **`engine/src/adapters/engineContext.ts`** *(new)* — the TypeScript side of the contract.
- **`engine/src/adapters/python-bridge.ts`** — refactored so envelope construction is a pure,
  unit-testable function, `buildTitanInvocation()`, instead of being entangled with `spawn`.
- **`themis` / `heracles` adapters** — honour the directive, and gained an injected `LLMProvider` seam
  so their behaviour is testable without network access.

**Deliberate scope decision:** the engine directive is **prepended** to the Titan's own system prompt,
never substituted for it — substituting would have silently deleted each Titan's identity. Token
budgets are **not** forwarded; that belongs to the still-open P1-4 (inert engine config) and was left
unimplemented rather than half-implemented.

### Verification

- `engine/tests/contextPropagation.test.ts` (10 tests) — the pure-function contract.
- `validation/verify-context-e2e.mjs` — drives the envelope through the **real** chain
  (`ModeEngine → WorkflowRunner → PythonTitanAdapter → spawnPythonTitan → child process`) with a
  stubbed Titan binary, and asserts the child received `systemPrompt`, `mode` and `phase`. The unit
  tests exercise `buildTitanInvocation` in isolation; this proves the wiring *around* it.

### Recommended follow-up

Move the envelope to a schema shared with MF-2's table rather than two hand-written parsers, so a
future field addition fails at build time instead of silently at runtime.

---

## MF-2 — Three routing tables disagreed; precedence was order-dependent

- **Severity:** Medium · **Category:** correctness / non-determinism · **Status:** Fixed

### Impact

Routing decided which Titan handled a request, and **three separate definitions** of that mapping
existed with no authority among them. They disagreed. Worse, precedence was **order-dependent** — the
selected Titan depended on dictionary iteration order rather than a stated rule — so the same message
could route differently between runs. A reviewer comparing any two of the tables could reasonably
conclude the system was correct while the running system agreed with neither.

### Root cause

Triggers and keywords were duplicated per consumer: each of seven mode files carried its own, and
Kronos and Talos each kept a private table. Nothing derived from anything else, and no test compared
the implementations, so divergence was invisible.

### Remediation

- **`othrys/src/othrys/routing.table.json`** *(new)* — **one** authority, shipping inside the wheel
  (verified present in the built artefact), because the wheel is the one artefact both languages
  install.
- **`othrys/src/othrys/routing.py`** *(new)* — Python loader/matcher over that table.
- **`engine/src/routing/table.ts`** *(new)* — zod-validated TypeScript loader over the same file, so a
  malformed table fails loudly rather than routing wrongly.
- **Mode files** — all seven dropped their private triggers/keywords for a shared `TitanModeSpec`;
  `registry` now **derives** triggers, keywords and `routingPriority` from the table.
- **Kronos and Talos** — private tables deleted; the shared table is the only source.

**Precedence is now explicit and deterministic:** highest weight wins → ties broken by earliest entry
in the table → otherwise fall through to Talos as the default.

### Verification

- `engine/tests/routingTable.test.ts` (9 tests) plus Python conformance tests
  (`othrys/tests/test_routing.py`, `kronos/tests/test_kronos_routing_conformance.py`,
  `talos/tests/test_talos_routing_conformance.py`) hold **both languages to the same table**.
- **Cross-language agreement, independently verified:** pass 1 checked the curated 23-example corpus;
  pass 2 generated messages from *every pattern* in the table plus decoys (~320) and diffed the
  TypeScript router against the Python matcher decision-for-decision — **0 mismatches**. The generator
  is archived as `validation/verify-routing-cross-language.py`.
- **Determinism:** repeated runs over the corpus return stable decisions.

### Recommended follow-up

Add a CI job that fails when the two language loaders disagree, rather than relying on a conformance
test a future contributor may not think to extend.

---

## Follow-on findings (G-1, G-2, G-3)

These were not in the original brief. G-1 and G-2 were found while trying to *verify* MF-1/MF-2; G-3
was **created** by the MF-2 fix and caught during independent re-verification. Full detail in
[`CI-GUARDRAIL.md`](CI-GUARDRAIL.md).

### G-1 (High) — CI's `python-titans` matrix could not pass as written

All five matrix jobs failed their typecheck step, from two pre-existing causes:
`atlas` declared no dev extra and `coeus`'s held only pytest, so `pip install -e ".[dev]"` **succeeded**,
the workflow's `||` fallback was unreachable, and the step died with `mypy: command not found` (exit
127); and `iapetus`/`talos`/`kronos` ran *strict* mypy over unannotated modules (29 errors).
`main`'s only prior CI run (`25420395652`) failed all six of its jobs, so the matrix had never passed.

**Fixed** with 29 annotations and the missing dev extras — deliberately **not** by narrowing
`[tool.mypy]`, which would have gone green while leaving the largest files in each package permanently
unchecked.

### G-2 (Medium) — the local gate was weaker than CI while claiming "Production Ready"

`./check-all.sh` printed `ALL CHECKS PASSED (Production Ready) ✓` with five of nine CI jobs red. It ran
mypy from the repository root, which never loads a package's `[tool.mypy] strict = true`, so it could
not observe what CI observed. `make check` had the same gap — every local verification in this project
had to be cross-checked by hand to be trusted.

**Fixed:** both gates now run the CI-identical per-package strict check, and the banner states what is
and is not covered. The gate was **proven able to fail** by injecting an unannotated function into a
throwaway copy (`mypy` exit 1), without writing that code to the repository.

### G-3 (Medium) — the built engine required the monorepo layout to import

A regression from MF-2. `engine/src/routing/table.ts` resolved the table only via
`../../../othrys/src/...`, and `modes/registry.ts` reads it during module initialisation, so relocating
`engine/dist` made an `import` throw `ENOENT`. The engine could not be bundled, relocated or deployed
standalone — and it had newly acquired import-time file I/O, a property the v2.0 review had recorded
as absent.

**Fixed:** `npm run build` now copies the table beside the compiled output
(`scripts/sync-routing-table.mjs`), and the resolver prefers that copy while falling back to the
sibling path for `src`/tsx/vitest. One source of truth is preserved — the table still lives only in
`othrys`, and the engine's copy is generated. Proven by relocating the built engine outside the
repository and importing it: 7 entries, 23 examples, `matchRoutingRule(...)` → `iapetus`.

---

## Test results

Environment: macOS arm64, Python 3.14.4, Node 24.14.1, npm 11.11.0, mypy 1.20.2, pytest 9.1.1.
CI independently exercises Linux for the typecheck and test jobs.

### Full suite — final state (`1aaae07`)

| Suite | Tests | Result |
|---|---|---|
| engine (vitest) | 42 | PASS |
| themis (vitest) | 15 | PASS |
| heracles (vitest) | 10 | PASS |
| othrys, atlas, coeus, iapetus, talos, kronos (pytest) | 106 | PASS |
| **Total** | **173** | **PASS** |

- **Passed:** 173
- **Failed:** 0
- **Skipped:** 0
- **Blocked:** the end-to-end agent path with a **real model** — no API credentials are available in
  this environment. These are not skipped tests that exist and decline to run; no such tests exist,
  and the harnesses that do cover the path stub the LLM. Every claim about model-visible behaviour is
  correspondingly absent from this report.

### Growth across the effort

| Stage | Tests | Note |
|---|---|---|
| Baseline (`add1070`) | 105 | |
| After MF-1 + MF-2 | 169 | +64, all the new behaviour |
| After G-1/G-2/G-3 | 173 | +4, the G-3 packaging contract |

### Targeted tests per finding

| Finding | Targeted coverage |
|---|---|
| MF-1 | `engine/tests/contextPropagation.test.ts` (10); `validation/verify-context-e2e.mjs` through the real runner chain |
| MF-2 | `engine/tests/routingTable.test.ts` (9); `othrys/tests/test_routing.py`; `kronos/tests/test_kronos_routing_conformance.py`; `talos/tests/test_talos_routing_conformance.py`; ~320-message cross-language diff |
| G-1 | per-package strict mypy: atlas 11, coeus 7, iapetus 8, talos 11, kronos 9 files — all clean |
| G-2 | gate exercised on an injected violation → `no-untyped-def`, **mypy exit 1** |
| G-3 | `engine/tests/routingTablePackaging.test.ts` (4); relocated-engine import |

### Regressions

**One was introduced by this work and caught by the second pass:** G-3, created by MF-2 and fixed
before delivery. No other regressions were observed: the 105 baseline tests all still pass, and the
delta in every previously-passing suite is additive.

### Acceptance criteria

| Finding | Criterion | Met |
|---|---|---|
| MF-1 | A Titan's routed `systemPrompt`/`mode`/`phase` reaches the child process | Yes — asserted in the child |
| MF-1 | Malformed/absent envelope degrades, never raises | Yes |
| MF-2 | Exactly one routing authority, shipped in the wheel | Yes — verified in the built artefact |
| MF-2 | Both languages agree, precedence explicit and order-independent | Yes — 0 mismatches over ~320 messages |
| G-1 | Every `python-titans` job passes | Yes — 9/9 CI jobs green |
| G-1 | Strictness raised, not lowered | Yes — no `[tool.mypy]` override or exclusion added |
| G-2 | Local gate matches CI and can fail | Yes — proven |
| G-3 | Built engine imports outside the monorepo | Yes |

---

## Validation evidence

Raw logs and harnesses: [`validation/`](validation/). Highlights:

```
CI, post-merge main run 38680480430 ............ 9/9 jobs success (first green pipeline in this repo)
CI, PR #1 run 38678703780 ...................... 5/9 red (baseline this work repaired)
make check, merged main ........................ exit 0 — includes per-package strict mypy
./check-all.sh, after G-2 ...................... exit 0 — 5 steps
per-package strict mypy ........................ atlas 11, coeus 7, iapetus 8, talos 11, kronos 9 — clean
negative control on the G-2 gate ............... mypy exit 1 on an injected violation
relocated engine import ........................ 7 entries, 23 examples, iapetus, 7 Titans
cross-language routing diff .................... ~320 messages, 0 mismatches
```

### Explicitly unconfirmed

- **No end-to-end run with a real model**, so no claim is made that a Titan now *behaves* differently
  with the restored context — only that the context reaches it.
- **The CI result was forecast before merging and then observed.** The forecast was 9/9 green; the
  observed run matched. Both are recorded; the numbers quoted above are the observed ones.
- **Behaviour outside macOS is unverified by me directly.** CI runs Linux for the typecheck and test
  jobs, so those are covered; interactive/agent paths are not exercised on any platform.
- **The Harness Readiness Score of ~54 is an estimate** carried from the prior evaluation, not a
  measured quantity.

---

## Recommended remediation steps

Ordered by risk-reduction per unit of change. None of these are fixed yet.

| # | Recommendation | Why it matters | Size |
|---|---|---|---|
| **1** | **Make auto-verification opt-in.** `ask` currently executes the target repository's build/test scripts automatically. | This is arbitrary code execution triggered by a request, with no consent step. Removing the blast radius is the single highest-value change left. | Small |
| **2** | **Enforce the capability model** by wiring `guardScope`, which today has **zero call sites**. | The README's Tool Access table does not describe reality: Atlas is documented read-only and is not. Until this lands, the permission model is decoration — and it is a security boundary, so it needs tests, not just wiring. | Large |
| **3** | **Add a CI job that diffs the two routing loaders** against the shared table. | MF-2's guarantee is enforced by a conformance test a future contributor may not extend; a CI job makes disagreement impossible to merge. | Small |
| **4** | **Declare `tsx`** in `engine/package.json` and actually ship/repair the `heracles` `dist` build. | `bin/mount-othrys` relies on an undeclared dependency, so it works only by accident of a global install; `heracles/dist` is not loadable. | Small |
| **5** | **Resolve the inert engine config** (`--set-model` does not persist) and forward the token budgets MF-1 deliberately left out. | Configuration that silently does nothing is worse than absent configuration. | Medium |
| **6** | **Raise `atlas` and `coeus` to `[tool.mypy] strict = true`** and add the agent-state directories to `.gitignore`. | They currently pass under mypy's defaults, i.e. weaker coverage than their siblings; and `.architect/`, `.sisyphus/` and `Icon\r` show up as untracked noise on every status. | Small |

---

## Remaining risks

**Carried from earlier passes, unresolved:**

1. **`guardScope` has 0 call sites** — the capability/permission model is not enforced (see #2 above).
2. **`ask` auto-runs a target repository's build/test scripts** — arbitrary code execution (#1 above).
3. **`heracles/dist` is not loadable** (#4 above).
4. **Engine config is inert** — `--set-model` does not persist; token budgets are still not forwarded
   to Titans (#5 above).
5. **P0-3:** a sandbox was removed from the flow; this is **disclosed** in commit `a265e41`, which means
   it is documented but not remediated.
6. **`.sisyphus/`, `.architect/`, `Icon\r` are not in `.gitignore`** (#6 above).

**Introduced or newly visible in this effort:**

7. **G-3's class of bug is fixed, but the engine still has import-time file I/O.** The read is now
   portable, not lazy. A missing table remains a module-init failure rather than a routed error.
8. **`atlas`/`coeus` lack a `[tool.mypy]` section**, so CI checks them under mypy defaults.
9. **The engine package has no `files` field and `dist/` is git-ignored**, so `npm publish` would ship
   a package without its compiled output. Latent — nothing publishes it today.
10. **`engine/scripts/` is not type-checked** (it is JavaScript, covered by a test that executes it).
11. **`make check` is now slower** (five extra mypy invocations, a few seconds) — accepted in exchange
    for the gate meaning something.
12. **No real-model end-to-end validation exists**, so nothing here speaks to model behaviour.

---

## Delivery record

### Commits

| Commit | Contents |
|---|---|
| `a265e41` | Pre-existing uncommitted work landed so the branch was buildable at all (`main` at `add1070` declared an out-of-tree `@core/exec-core` dependency and was missing `modes/kronos.ts`). Discloses P0-3. |
| `a3272b1` | **MF-1 + MF-2 remediation.** |
| `11e978c` | Documentation correction: records observed CI results and corrects the `atlas`/`coeus` assessment. |
| `502ef61` | **G-1 + G-2 + G-3.** First green pipeline in the repository. |
| *(this pass)* | Consolidated report + evidence archive + README pointer. |

`main`'s history is otherwise preserved — the remediation was integrated by merge commits, not rewrites.

### Pull requests

| PR | Title | Merge | Result |
|---|---|---|---|
| [#1](https://github.com/jeromeskiii/mount-othrys/pull/1) | `fix(mount-othrys): remediate medium-severity findings MF-1 and MF-2` | `b096350` (`add1070` + `11e978c`) | Merged; CI red **before** the fix (5/9), which is why PR #2 exists |
| [#2](https://github.com/jeromeskiii/mount-othrys/pull/2) | `fix(ci): repair the pipeline gate and make the built engine portable` | `1aaae07` | Merged; CI **9/9 green** |

### CI

| Run | Branch | Result |
|---|---|---|
| `25420395652` | `main`, 2026-05-06 (pre-existing) | 6/6 jobs **failed** |
| `38678703780` | PR #1 | 5/9 **failed** — baseline |
| `38680356868` | PR #2 | **9/9 succeeded** |
| `38680480430` | `main` post-merge | **9/9 succeeded** — first green main build |

### Cleanup performed

- Remote and local feature branches deleted after each merge.
- `git worktree prune`, `git remote prune origin`, `git gc` run.
- Temporary validation artifacts removed from `/tmp`; the evidence worth keeping was **archived into
  `docs/validation/`** first.
- No secrets committed; the diff was scanned before each commit.

---

## Final repository state

```
branch            main
HEAD              1aaae07  (== origin/main, ahead 0 / behind 0)
local branches    main only (no leftover feature branch)
tracked changes   0
untracked         .architect/  .sisyphus/  Icon\r   (agent state + OS junk, intentionally uncommitted)
main CI           success (9/9)
docs              REMEDIATION-REPORT.md  REMEDIATION.md  CI-GUARDRAIL.md  validation/
```

---

## Status of this report

- **Verified by execution:** all 173 tests; both local gates; the CI-identical per-package strict
  mypy; the negative control on the G-2 gate; the relocated-engine import; the merged-tree contents;
  the CI runs and their job-level conclusions; branch and remote cleanup.
- **Not done / out of scope:** the six recommended steps above; real-model end-to-end validation;
  direct verification of behaviour outside macOS and Linux.
- **Withdrawn claim worth noting:** the v2.0 evaluation recorded "no import-time I/O in the engine".
  MF-2 invalidated that; G-3 restored portability but not the no-I/O property. The claim should not be
  restated.