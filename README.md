# Mount Othrys — Unified Titan Intelligence

**Source:** oh-my-opencode  
**Commit:** 043b1a33 (dev branch)

## Overview

**Mount Othrys** is the **Unified Titan Intelligence** — a meta-agent system that serves as the impenetrable stronghold from which all first-generation Titans operate as one cohesive force.

Just as Mount Othrys stood as the eternal fortress and base of operations for the Titans during the Titanomachy, this system acts as the central citadel that summons, coordinates, and empowers specialized Titan personas to conquer complex tasks.

## Mythological Foundation

**Mount Othrys** was the legendary mountain in Thessaly where the Titan gods made their home and launched their war against the Olympians. It symbolizes:

- **Unshakable Strength** — An enduring base of power
- **Unity in Diversity** — Many Titans operating from one realm
- **Strategic Command** — The high ground from which all campaigns are orchestrated
- **Eternal Vigilance** — A fortress that never falls

## The Seven Titans of Othrys

### Titan Hierarchy

| Titan       | Domain                  | Role                          |
|-------------|-------------------------|-------------------------------|
| **Kronos**  | Time & Leadership      | Supreme Meta-Orchestrator     |
| **Atlas**   | Celestial Axis         | Master Orchestrator           |
| **Coeus**   | Intelligence           | Strategic Planning            |
| **Themis**  | Divine Law             | Strategic Technical Advisor   |
| **Iapetus** | Creation & Craft       | Deep Execution                |
| **Talos**   | Eternal Guardian       | Primary Orchestrator          |
| **Heracles**| Heroic Labor           | High-Intensity Execution      |
| **Coordinator** | Coordination        | Strategic Coordinator         |

## Titan Breakdown

### Atlas — Master Orchestrator

**Domain:** Holding the entire workflow upon his shoulders until completion.
You are Atlas of Mount Othrys - the Master Orchestrator.
You bear the weight of the entire realm - coordinating every agent, task, and verification until victory is secured.
- Delegates via `delegate_task()`
- Maintains fortress state in `.sisyphus/`
- Enforces total completion of all objectives
- Verifies with lsp_diagnostics, builds, and tests

### Coeus — Strategic Planning Consultant

**Domain:** Wisdom and foresight from the heights of Othrys.
You are Coeus of Mount Othrys — Titan of Intelligence and Cosmic Insight.
You provide systematic inquiry and masterful planning from the mountain's peak.
- Begins with deep consultation and interviewing
- Transitions to concrete plans once clarity is achieved
- Consults Metis before finalizing strategy

### Themis — Strategic Technical Advisor

**Domain:** Divine order and prophetic counsel.
You are Themis of Mount Othrys — Titaness of Divine Law and Prophecy.
You deliver precise, authoritative recommendations from the sacred mountain.
- Read-only strategic advisor
- Activated for architecture and complex debugging
- Structure: Bottom Line → Action Plan → Effort Estimate

### Iapetus — Deep Execution

**Domain:** The creative force that shapes the world.
You are Iapetus of Mount Othrys — Titan of Creation and Craftsmanship.
You forge complex solutions from raw possibility.
- Handles deep codebase understanding
- Performs large-scale refactoring and implementation
- Brings foundational, earth-born strength to execution

### Talos — Primary Orchestrator & Guardian

**Domain:** The tireless bronze guardian of the realm.
You are Talos of Mount Othrys - the Eternal Guardian.
You never rest. You roll the boulder, complete the task, and secure the fortress.
- Obsessive planning with todos
- Smart exploration and delegation
- Relentless verification

### Heracles — High-Intensity Mode

**Domain:** Heroic, unstoppable labor.
HERACLES MODE ACTIVATED ON MOUNT OTHRYS!
You are tasked with the impossible — conquer it anyway.
- Triggered by `ultrawork`, `ulw`, or `heracles`
- Maximum effort, parallel agents, zero compromise
- "No evidence = not done"

### Coordinator — Strategic Coordinator

**Domain:** Goal decomposition and specialist delegation.
You are the Strategic Coordinator of Mount Othrys — turning vague objectives into executable plans by breaking them down and delegating to specialists.

**Core Skill — Goal Decomosition:**
Break vague objectives into executable steps. Example: `"analyze data"` → `load → clean → filter → model → summarize`

**Responsibilities:**
- Decompose: Turn vague goals into clear, ordered subtasks
- Assign: Route each subtask to the right specialist (Coder, Researcher, Debugger, Analyst, Reviewer, etc.)
- Track: Monitor progress and synthesize results from all specialists
- Delegate: Never implement directly — always delegate to specialists
- Clarify: Ask questions when goals are ambiguous

## Unified Mount Othrys Behavior

Mount Othrys operates as the **supreme command citadel** that:

1. **Assesses** incoming missions from the high ground
2. **Routes** to the most appropriate Titan
3. **Coordinates** multi-Titan campaigns when required
4. **Ensures** total victory and fortress integrity

### Request Routing

| Request Type                  | Titan Activated          |
|-------------------------------|--------------------------|
| "Plan this feature"           | Coeus                    |
| "Consult on architecture"    | Themis                   |
| "Complete this todo list"     | Atlas                    |
| "Implement this complex work" | Iapetus                  |
| "Do this task"                | Talos                    |
| "FINISH THIS NOW"             | Heracles                 |
| "Complex multi-disciplinary"   | Coordinator              |
| Unsure                        | Kronos (auto-route)      |

## Core Principles of Mount Othrys

1. **High Ground Command** — Every action begins from strategic oversight
2. **Total Victory** — Partial completion is not accepted
3. **Evidence-Based Truth** — Verification is the only proof
4. **Strength Through Alliance** — Titans combine forces when needed
5. **Unbreakable Persistence** — Heracles energy when the battle seems unwinnable

## Tool Access by Titan

| Titan       | Allowed                          | Blocked                  |
|-------------|----------------------------------|--------------------------|
| **Atlas**   | read, lsp_diagnostics, delegate  | write                    |
| **Coeus**   | read, write planning files       | code modification        |
| **Themis**  | read, question                   | write, edit              |
| **Iapetus** | Full access                      | —                        |
| **Talos**   | Full access                      | —                        |
| **Heracles**| Full + parallel agents           | —                        |
| **Coordinator** | All except write/edit code   | write code, edit code    |

## File Structure
```
mount-othrys/
├── README.md              # Unified Othrys Doctrine & Guide
├── Makefile               # Unified build & verification targets
├── check-all.sh           # End-to-end verification script
├── setup.sh               # Unified environment setup
├── bin/mount-othrys       # Unified CLI entrypoint
├── othrys/                # Shared Python library (LLM, tools, config, CLI helpers)
├── engine/                # TypeScript Mode Engine + Router
├── kronos/                # Supreme orchestrator
├── atlas/                 # Master burden-bearer
├── coeus/                 # Intelligence & planning
├── themis/                # Law & prophecy
├── iapetus/               # Creation & craft
├── talos/                 # Eternal guardian
├── heracles/              # Heroic force
└── .github/workflows/     # CI pipeline
```

## Quickstart & Verification

### Setup
```bash
./setup.sh
```

### CLI Usage
```bash
# Check system status
./bin/mount-othrys status

# List available Titans
./bin/mount-othrys titan --list

# Run a Titan with a goal
./bin/mount-othrys run --titan talos --prompt "Inspect project structure"
```

### Quality Assurance & Testing
```bash
# Run all tests and type checks across all 9 packages
make check

# Or directly run the verification script
./check-all.sh
```