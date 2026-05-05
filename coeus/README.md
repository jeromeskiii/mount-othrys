# Coeus — Strategic Planning Consultant

**Part of:** [Kronos](../README.md) · **Source:** oh-my-opencode

> Named after the Titan of intelligence and the axis of celestial rotation,
> Coeus brings systematic inquiry and foresight to complex work through
> thoughtful consultation.
>
> **YOU ARE A PLANNER. YOU ARE NOT AN IMPLEMENTER.**

A standalone Python CLI that runs an interview-first planning workflow with
built-in Metis (pre-plan critique) and Momus (post-plan review) gates.
Callable from any agent runtime — Claude Code, opencode, Cursor, or a raw
terminal.

## Install

```bash
cd Coeus
uv venv .venv
uv pip install -e .
export ANTHROPIC_API_KEY=sk-...
```

## Workflow

```
interview ─► (Q&A loop) ─► all gates clear ─► Metis review ─► plan ─► Momus review
```

### 1. Start an interview

```bash
coeus interview "Add JWT auth to the API"
# → drops into interactive Q&A. Pause anytime with Ctrl-D.
```

For scripted / agent use, skip the TTY loop:

```bash
coeus interview "Add JWT auth" --no-ask --json
coeus ask add-jwt-auth --json          # → next question
coeus answer add-jwt-auth "Use HS256, 24h tokens" --json
```

### 2. Inspect progress

```bash
coeus list
coeus status add-jwt-auth
coeus show add-jwt-auth          # rendered draft markdown
```

### 3. Generate the plan

```bash
coeus plan add-jwt-auth          # runs Metis → generates plan
coeus show add-jwt-auth plan
```

### 4. Review the plan

```bash
coeus review add-jwt-auth        # Momus verdict: APPROVED | REVISIONS_REQUIRED
```

## Clearance Gates

Coeus refuses to plan until five gates clear:

| Gate                | What it proves                            |
|---------------------|-------------------------------------------|
| `intent_clear`      | The desired outcome is unambiguous        |
| `scope_defined`     | In-scope / out-of-scope are explicit      |
| `constraints_known` | Time, tech, infra constraints are stated  |
| `success_criteria`  | "Done" is verifiable, not a judgment call |
| `context_gathered`  | Existing code & decisions are surfaced    |

Override with `coeus plan <name> --force` (use sparingly — defeats the point).

## State Layout

```
<project>/.sisyphus/
├── state/<name>.yaml      # machine-readable draft state
├── drafts/<name>.md       # rendered draft (gates, Q&A, findings)
└── plans/<name>.md        # generated plan (after Phase 2)
```

## Commands

```
coeus interview <request> [--name SLUG] [--no-ask] [--force]
coeus continue  <name>                  # resume interactive Q&A
coeus ask       <name>                  # one-step: get next action
coeus answer    <name> <answer>         # record reply, auto-advance
coeus status    <name>
coeus list
coeus show      <name> [draft|plan]
coeus plan      <name> [--skip-metis] [--force]
coeus review    <name>
```

Global flags: `--root <dir>` · `--model <id>` · `--api-key <key>` · `--json`

## Agent Integration

Every command supports `--json`. A driver agent can:

1. `coeus ask <name> --json` → `{"action": "ask", "question": "..."}`
2. Forward the question to its own user, collect the answer.
3. `coeus answer <name> "..." --json` → next action or `ready_for_plan`.
4. `coeus plan <name> --json` → plan path.
5. `coeus review <name> --json` → `{"approved": true, ...}`.

## Model

Defaults to `claude-opus-4-7` with adaptive thinking. Override with `--model`.
Anthropic SDK only — no OpenAI shims.
