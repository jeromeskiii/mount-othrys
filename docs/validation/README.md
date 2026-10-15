# Validation evidence archive

Raw artifacts behind the two remediation passes. These are **evidence, not tests** — nothing here
runs in CI, and no test imports these files. They exist so a later reader can check the claims in
[`../REMEDIATION-REPORT.md`](../REMEDIATION-REPORT.md) without re-deriving them, and so the two
non-obvious verification harnesses survive.

> **Note on extensions:** these are plain text. They are named `*.log.txt` rather than `*.log`
> because `.gitignore` ignores `*.log` globally — a `*.log` archive would have been silently dropped
> by `git add` and the evidence would have vanished on the next clone.

## What to trust, and how much

| Artifact | What it shows | How it was produced |
|---|---|---|
| `01-make-check.branch.log.txt` | All gates green on the pass-3 branch, including the new per-package strict mypy (atlas 11, coeus 7, iapetus 8, talos 11, kronos 9 files). 42 + 15 + 10 TS tests, 106 Python tests. | `make check`, branch `fix/ci-guardrail-and-engine-portability`, exit 0 |
| `02-check-all.after-g2.log.txt` | The documented gate after G-2, now 5 steps and CI-equivalent, with an honest banner. | `./check-all.sh`, exit 0 |
| `03-make-check.merged-main.log.txt` | The same gates pass on merged `main` (`1aaae07`), i.e. the fix survives the merge. | `make check` on `main`, exit 0 |
| `04-check-all.before-g2.log.txt` | **Evidence of the G-2 defect.** The old 4-step gate exited 0 with a "Production Verification" banner while 5 of 9 CI jobs were red. | `./check-all.sh` in pass 2, before the fix |
| `05-ci.pr-1.log.txt` | **Baseline.** PR #1's CI failed (5 of 9 jobs red). | `gh run` polls of run `38678703780` |
| `06-ci.pr-2.log.txt` | **Result.** All 9 jobs green for PR #2, then green again on the post-merge `main` push. | `gh run view` job conclusions, runs `38680356868` / `38680480430` |
| `verify-context-e2e.mjs` | Drives the MF-1 envelope through the **real** runner chain (`ModeEngine → WorkflowRunner → PythonTitanAdapter → spawn → child process`), not `buildTitanInvocation` in isolation. | Pass-2 verification |
| `verify-routing-cross-language.py` | Generates messages from every pattern in the routing table plus decoys and diffs the TypeScript router against the Python matcher decision-for-decision (~320 messages, 0 mismatches). | Pass-2 verification |
| `verify-remediation.sh` | Pass-1 verification of MF-1/MF-2 against the curated 23-example corpus. | Pass-1 verification |

## Reproducing

The archived logs are outputs; re-run the commands rather than trusting them:

```bash
make check        # logs 01 / 03
./check-all.sh    # logs 02
```

The two harnesses are archival and **path-dependent** — they hardcode
`/Users/ohmskiii/mount-othrys` and, in the shell script's case, `talos/.venv/bin/python`:

```bash
node docs/validation/verify-context-e2e.mjs          # needs engine/dist built first
python3 docs/validation/verify-routing-cross-language.py
bash docs/validation/verify-remediation.sh
```

Both need `cd engine && npm run build` beforehand, since they import `engine/dist/index.js`.

## Known limits of this evidence

- It is a record of **one machine** (macOS arm64, Python 3.14.4, Node 24.14.1). The CI logs cover
  Linux for the typecheck and test jobs, but no job runs the end-to-end agent path.
- No end-to-end run with a real model is archived, because none was performed: the harnesses stub
  the LLM and there are no API credentials in this environment. Claims about model behaviour are
  correspondingly absent from the report.
- The CI logs record **conclusions**, not full job output. Where a per-job breakdown is quoted, it
  came from the `gh run view` calls recorded in the report and in `docs/REMEDIATION.md`.