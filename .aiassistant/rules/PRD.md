---
apply: always
---

Product Requirements Document (PRD)

Product: Mount Othrys Engine
Type: AI Mode-Orchestration System (Planner + Executor Framework)
Version: v0.1 (MVP → Dev Tool)

1. Executive Summary

Mount Othrys Engine is a developer-focused AI orchestration system that converts natural language prompts into structured, reliable execution workflows using mode-based behavior (Planner, Advisor, Executor). The system routes user intent into specialized “Titan modes” like Heracles (strict execution) or Themis (advisory), enabling predictable, high-quality outputs instead of generic AI responses. The core value is deterministic AI behavior with enforced workflows (plan → execute → verify). The MVP will ship as a CLI tool with a modular TypeScript engine, designed to scale into multi-agent pipelines and IDE integrations.

2. Problem Statement
   Current Issues with AI Dev Tools
   Outputs are inconsistent and non-deterministic
   No separation between planning and execution
   No verification → “looks correct” ≠ “actually works”
   Hard to control behavior (tone ≠ capability)
   Unsafe execution (no constraints on file/system access)
   Opportunity

Developers need:

Predictable AI behavior
Enforced workflows (plan before build)
Execution with validation (tests, builds)
Mode-based control (like /commands but smarter)
3. Goals & Non-Goals
   Goals
   Provide mode-based AI execution system
   Enforce plan → execute → verify workflow
   Enable safe, controlled tool usage
   Deliver CLI-first developer experience
   Support extensible architecture (new modes easily added)
   Non-Goals (MVP)
   Full GUI/web app
   Autonomous long-running agents
   Multi-user collaboration
   Cloud orchestration (local-first)
4. Target Users
   Primary
   Software engineers
   Indie hackers
   AI tool builders
   Secondary
   DevOps engineers
   Technical product builders
5. Core Features
   5.1 Mode Routing System

Automatically detects intent or uses explicit command

Examples

mount-othrys "heracles fix auth bug"
mount-othrys "plan database schema"

Behavior

Keyword detection (Heracles, plan, review, etc.)
Fallback intelligent routing
5.2 Titan Modes (Core System)
Mode	Role	Behavior
Heracles	Executor	Strict, verified execution
Coeus	Planner	Creates structured plans
Themis	Advisor	Reviews, critiques, guides
Talos	Default Executor	Fast implementation
Atlas	System Design	Architecture-level thinking
Iapetus	Risk Analysis	Edge cases, failure modes
5.3 Planner Phase (.sisyphus)
Generates structured plan files:
.sisyphus/plans/<task>.md

Plan includes

Goal
Steps
Dependencies
Risks
5.4 Execution Phase
Applies changes using tools:
File edits
Code generation
Shell commands
5.5 Verification System

Critical feature:

Runs:
Tests
Type checks
Linting
Produces:
{
"passed": true,
"checks": [...]
}
5.6 Tool Guard (Safety Layer)

Restricts:

File system access
Command execution
Scope of changes
5.7 CLI Interface (MVP)
mount-othrys "<prompt>"

Outputs structured JSON result

6. User Flow
   Flow A: Execution (Heracles)
   User Prompt
   ↓
   Router detects "heracles"
   ↓
   Planner (if required)
   ↓
   Executor runs task
   ↓
   Verifier checks output
   ↓
   Return result
   Flow B: Planning Only
   User Prompt → "plan X"
   ↓
   Planner mode
   ↓
   Generate .sisyphus plan
   ↓
   Return path
   Flow C: Advisory
   User Prompt → "review architecture"
   ↓
   Themis mode
   ↓
   Return structured advice
7. Functional Requirements
   FR1: Prompt Routing
   Must detect mode via:
   Explicit keyword
   NLP fallback rules
   FR2: Mode Execution
   Each mode must define:
   Allowed tools
   Behavior rules
   Output format
   FR3: Plan Generation
   Must create markdown plan files
   Must be deterministic and structured
   FR4: Execution Engine
   Must support:
   File operations
   Code generation
   Command execution
   FR5: Verification
   Must run at least one validation step
   Must return structured result
   FR6: Tool Safety
   Must block unauthorized actions
   Must restrict write scope
   FR7: CLI Interface
   Must accept prompt string
   Must output structured result
8. Non-Functional Requirements
   Performance
   < 2s routing time
   Execution dependent on task
   Reliability
   Deterministic routing
   Clear failure states
   Security
   Sandboxed execution
   File path restrictions
   Maintainability
   Modular mode system
   Clean TypeScript interfaces
   Extensibility
   Add new modes without engine rewrite
9. Success Metrics
   MVP Metrics
   % of prompts correctly routed
   % of executions passing verification
   Avg execution success rate
   Developer adoption (CLI usage)
   Quality Metrics
   Reduction in broken code output
   Increase in task completion rate
10. Risks & Mitigations
    Risk	Impact	Mitigation
    Wrong mode routing	Bad outputs	Add confidence scoring + fallback
    Unsafe execution	System damage	Strict ToolGuard
    No real verification	False success	Enforce checks
    Over-complex UX	Low adoption	CLI-first simplicity
    AI inconsistency	Unreliable results	Strict prompts + constraints
11. Open Questions
    Which LLM provider(s) to support first?
    Should execution be:
    local-only?
    sandboxed container?
    How strict should verification be for MVP?
    Do we allow auto-execution or require confirmation?
12. Future Roadmap
    Phase 2
    IDE plugin (VS Code)
    Interactive plan approval
    Persistent session memory
    Phase 3
    Multi-agent workflows
    Parallel execution
    Visual workflow graph
    Phase 4
    Web dashboard
    Team collaboration
    Cloud execution