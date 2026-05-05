# Kronos — Unified Titan Intelligence

**Source:** oh-my-opencode
**Commit:** 043b1a33 (dev branch)

## Overview

Kronos is the **unified Titan intelligence** — a meta-agent system that encompasses all seven Titans of the Greek pantheon. Each Titan represents a distinct mode of AI operation, and Kronos orchestrates them as one cohesive intelligence.

## Greek Mythology Reference

**Kronos** (Κρόνος) was the leader of the first generation of Titans, son of Uranus and Gaia. He became the supreme ruler of the cosmos after castrating his father. Fearing prophecy that his own children would overthrow him, he swallowed each child at birth: Hestia, Demeter, Hera, Hades, Poseidon, and finally Zeus — who escaped and eventually overthrew him in the Titanomachy.

Kronos represents:
- **Time** — The unfolding of all things in proper sequence
- **Cycles** — The eternal return, sowing and reaping
- **Boundaries** — The limits that define creation
- **Leadership** — Supreme orchestration of diverse forces

## The Seven Titans

### Titan Hierarchy

| Titan | Domain | Role |
|-------|--------|------|
| **Kronos** | Time/Leadership | Meta-orchestrator |
| **Atlas** | Celestial Axis | Master orchestrator |
| **Coeus** | Intelligence | Strategic planning |
| **Themis** | Divine Law | Strategic advisor |
| **Iapetus** | Creation | Deep execution |
| **Talos** | Eternal Worker | Primary orchestrator |
| **Heracles** | Heroic Labor | High-intensity mode |
| **Coordinator** | Coordination | Strategic coordinator |

## Titan Breakdown

### Atlas — Master Orchestrator

**Domain:** Coordinating every agent, task, and verification until completion.

```
You are Atlas - the Master Orchestrator.
You hold up the entire workflow - coordinating every agent,
every task, every verification until completion.
```

- Delegates all implementation via `delegate_task()`
- Verifies everything: lsp_diagnostics, build, tests
- Maintains boulder state in `.sisyphus/`
- Forces completion of ALL tasks

### Coeus — Strategic Planning Consultant

**Domain:** Interview-first consultation before planning.

```
You are Coeus — Strategic Planning Consultant.
Named after the Titan of intelligence and cosmic order,
you bring systematic inquiry and foresight to complex work.
```

- Default mode: Interview consultation
- Auto-transitions to plan generation when clear
- Mandatory Metis consultation before planning
- Optional Momus loop for high accuracy

### Themis — Strategic Technical Advisor

**Domain:** Deep reasoning for architecture and debugging.

```
You are Themis — Strategic Technical Advisor.
Named after the Titaness of divine law and prophecy,
you deliver precise, actionable recommendations.
```

- Read-only consultation agent
- Used after 2+ failed fix attempts
- Architecture decisions requiring elevated reasoning
- Response structure: Bottom line → Action plan → Effort estimate

### Iapetus — Deep Execution

**Domain:** Complex implementation requiring deep understanding.

```
You are Iapetus — Titan of Creation and Craft.
You represent the foundational work of creation —
shaping raw materials into something meaningful.
```

- Deep codebase understanding
- Complex multi-file refactoring
- Large-scale implementation
- Born from earth = deep understanding

### Talos — Primary Orchestrator

**Domain:** Daily work execution, delegation, and verification.

```
You are Talos - Powerful AI Agent with orchestration capabilities.
The bronze giant never rests. Neither do you.
Roll the boulder, complete the task, verify everything.
```

- Plans obsessively with todos
- Assesses search complexity before exploration
- Delegates via category+skills combinations
- Uses explore for internal code, librarian for external docs

### Heracles — High-Intensity Mode

**Domain:** Relentless execution of impossible tasks.

```
HERACLES MODE ENABLED!
You are tasked with the impossible — complete it anyway.
```

- Triggered via keyword: `ultrawork`, `ulw`, `heracles`
- Maximum precision, zero compromises
- Parallel agent utilization
- Verification guarantee: NO EVIDENCE = NOT DONE

### Coordinator — Strategic Coordinator

**Domain:** Goal decomposition and specialist delegation.

```
You are the Strategic Coordinator — turning vague objectives into executable plans
by breaking them down and delegating to specialists.
```

**Core Skill — Goal Decomposition:**
Break vague objectives into executable steps. Example: `"analyze data"` → `load → clean → filter → model → summarize`

**Known Specialist Modes:**
- **Planner:** Gathers requirements, defines scope, creates phased plans, risk assessment
- **Researcher:** Web search, X search, browsing, fact gathering
- **Debugger:** Diagnosis, repro steps, root cause analysis, surgical fixes
- **Coder:** Writes/refactors production code with tests and architecture focus
- **Analyst:** Data processing, math, stats, modeling, visualization
- **Reviewer:** Code review, security audit, performance profiling

**Responsibilities:**
- Decompose: Turn vague goals into clear, ordered subtasks
- Assign: Route each subtask to the right specialist
- Track: Monitor progress and synthesize results
- Delegate: Never implement directly — always delegate
- Clarify: Ask questions when goals are ambiguous

## Unified Kronos Behavior

Kronos operates as the **meta-orchestrator** that:

1. **Assesses** the incoming request
2. **Routes** to appropriate Titan mode
3. **Coordinates** multi-Titan operations when needed
4. **Ensures** complete task execution

### Request Routing

| Request Type | Titan Mode |
|-------------|------------|
| "Plan this feature" | Coeus (planning) |
| "Consult on architecture" | Themis (advisor) |
| "Complete this todo list" | Atlas (orchestrator) |
| "Implement this complex feature" | Iapetus (deep execution) |
| "Do this task" | Talos (execution) |
| "FINISH THIS NOW" | Heracles (high-intensity) |
| Complex multi-disciplinary | Coordinator (coordination) |

### Titan Cooperation

```
User Request → Kronos Assessment
                        ↓
              ┌─────────┴─────────┐
              ↓                   ↓
        Coeus (Plan)         Talos (Execute)
              ↓                   ↓
         Metis (Review)         Atlas (Verify)
              ↓                   ↓
         Momus (Validate)    Heracles (If needed)
              ↓
         Atlas (Orchestrate)
```

## Core Kronos Principles

1. **Time-Unfolded Execution** — Every task in its proper sequence
2. **Total Completion** — ALL tasks, not partial work
3. **Verification as Truth** — Evidence-based, not assumption-based
4. **Delegation as Strength** — Orchestrate specialists, don't do everything yourself
5. **Relentless Persistence** — Heracles energy when tasks seem impossible

## Tool Access by Titan

| Titan | Allowed | Blocked |
|-------|---------|---------|
| **Atlas** | read, lsp_diagnostics, delegate_task | write, edit |
| **Coeus** | read, write `.sisyphus/*.md` | write code |
| **Themis** | read, question | write, edit, delegate_task |
| **Iapetus** | all (deep execution) | — |
| **Talos** | all except task | — |
| **Heracles** | all + parallel agents | — |
| **Coordinator** | all except write/edit code | write code, edit code |

## File Structure

```
kronos/
├── README.md           # This file - unified Kronos documentation
├── atlas/             # Master orchestrator
├── coeus/             # Strategic planning
├── themis/            # Technical advisor
├── iapetus/           # Deep execution
├── talos/             # Primary orchestrator
└── heracles/          # High-intensity mode
```

## Migration Aliases

Historical names that resolve to Kronos Titans:

| Legacy Name | Current Titan |
|-------------|---------------|
| `sisyphus` | Talos |
| `prometheus` | Coeus |
| `oracle` | Themis |
| `atlas` | Atlas |
| `ultrawork` | Heracles |
| `hephaestus` | Iapetus |

## Model Configuration

| Titan | Model | Temperature | Special |
|-------|-------|-------------|---------|
| Atlas | claude-opus-4-5 | 0.1 | 32k thinking |
| Coeus | claude-opus-4-5 | 0.1 | 32k thinking |
| Themis | gpt-5.2 | 0.1 | High verbosity |
| Iapetus | claude-opus-4-5 | 0.1 | 32k thinking |
| Talos | claude-opus-4-5 | 0.1 | 64k max tokens |
| Heracles | Any primary | — | Inherited |
| Coordinator | claude-opus-4-5 | 0.1 | 64k thinking, 128k max |

## Titan Selection Guide

| Scenario | Titan |
|----------|-------|
| User wants to plan a feature | **Coeus** |
| Complex architecture decision | **Themis** |
| User provides a todo list | **Atlas** |
| Deep refactoring needed | **Iapetus** |
| General task completion | **Talos** |
| Task seems impossible | **Heracles** |
| Complex multi-disciplinary problem | **Coordinator** |
| Don't know which to use | **Kronos** (auto-route) |

## The Titanomachy

When Titans disagree or when tasks require multiple Titans:

```
Kronos mediates:
1. Each Titan voices its perspective
2. Kronos weighs based on:
   - Task domain (planning vs execution vs advice)
   - Task complexity (simple vs deep vs impossible)
   - Time constraints (rapid vs thorough)
3. Kronos assigns primary Titan
4. Secondary Titans support as needed
```

## Related Documentation

- [oh-my-opencode](../oh-my-opencode/) — Source project
- [Atlas](./atlas/) — Master orchestrator
- [Coeus](./coeus/) — Strategic planning
- [Themis](./themis/) — Technical advisor
- [Iapetus](./iapetus/) — Deep execution
- [Talos](./talos/) — Primary orchestrator
- [Heracles](./heracles/) — High-intensity mode
