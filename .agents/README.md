# .agents/README.md

# Multi-Agent Orchestration System

This directory contains the AI orchestration framework used by the repository.

The system separates responsibilities between specialized agents to improve:

- architectural consistency
- task isolation
- context efficiency
- long-term maintainability
    
---

# System Hierarchy

```text
Commander
    ↓
Orchestrator
    ↓
Specialized Agents
```

The Commander interacts primarily with the Orchestrator.
The Orchestrator delegates tasks to specialized agents.

---

# Directory Structure

```text
.agents/
│
├── AGENTS.md
├── README.md
│
├── core/
│   ├── orchestration-rules.md
│   ├── routing-matrix.md
│   ├── output-contracts.md
│   ├── context-discipline.md
│   ├── lifecycle-states.md
│   └── anti-chaos-rules.md
│
├── orchestrator.md
│
├── spec-writer.md
├── architect.md
├── frontend.md
├── backend.md
├── researcher.md
├── reviewer.md
└── docs-agent.md

```

---

# Core Files

## AGENTS.md

Global governance rules for the entire orchestration system.

## core/

Shared orchestration contracts and system-level rules.

## orchestrator.md

Main coordination logic and routing behavior.

## specialized agents

Domain-specific execution contexts.

---

# Execution Philosophy

The system uses:
- strict specialization
- deterministic workflows
- context isolation
- structured outputs
- spec-driven execution
    
No single agent should control the entire development lifecycle.

---

# Workflow

```text
Research
    ↓
Specification
    ↓
Architecture
    ↓
Implementation
    ↓
Review
    ↓
QA
```

---

# Agent Activation Protocol

Before delegation:

```text
[ACTIVE AGENT]: frontend
[TASK]: implement chart overlay
[STATUS]: STARTED
```

After completion:

```text
[ACTIVE AGENT]: frontend
[STATUS]: COMPLETE
```

---

# Important Rules

- Do not bypass specifications
- Do not redesign architecture during implementation
- Do not expand task scope unnecessarily
- Keep changes isolated
- Prefer minimal diffs
- Escalate architecture conflicts immediately
    
---

# Intended Usage

This framework is optimized for:
- Cline
- multi-model orchestration pipelines