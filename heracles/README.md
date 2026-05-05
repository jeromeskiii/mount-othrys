# Heracles — High-Intensity Mode

**Source:** oh-my-opencode
**Part of:** [Kronos](../README.md)

## Overview

Heracles is a **high-intensity work mode** in the Kronos Titan system, not an agent. Triggered via keyword, it enforces maximum precision and agent utilization.

## Greek Mythology

**Heracles** (Hercules) was the greatest Greek hero, famed for his incredible strength and endurance. His Twelve Labors represent impossible tasks completed through relentless persistence:

1. Slay the Nemean Lion
2. Slay the nine-headed Lernaean Hydra
3. Capture the Golden Hind of Artemis
4. And 9 more impossible feats...

Heracles embodies **relentless execution** and **completing the impossible**.

## Trigger

```bash
heracles do something
ultrawork implement this
ulw finish the task
```

**Pattern:** `/\b(ultrawork|ulw|heracles)\b/i`

## Core Principles

### NO EXCUSES. NO COMPROMISES.

| Violation | Consequence |
|-----------|-------------|
| "I couldn't because..." | **UNACCEPTABLE.** Find a way or ask for help. |
| "This is simplified..." | **UNACCEPTABLE.** Deliver FULL implementation. |
| "You can extend later..." | **UNACCEPTABLE.** Finish it NOW. |

## Zero Tolerance

- **NO Scope Reduction** — Never make "demo" versions
- **NO MockUp Work** — Port A = Port A, 100%
- **NO Partial Completion** — Never stop at 60-80%
- **NO Test Deletion** — Never delete failing tests

## Verification Guarantee

**NOTHING is "done" without PROOF it works.**

| Phase | Evidence |
|-------|----------|
| Build | Exit code 0 |
| Test | All tests pass |
| Manual | Demonstrate it works |
| Regression | Nothing broke |

## Agent Utilization

```
1. EXPLORES + LIBRARIANS (background)
2. GATHER → delegate_task(subagent_type="plan", ...)
3. WORK BY DELEGATING TO CATEGORY + SKILLS AGENTS
```
