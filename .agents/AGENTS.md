# AGENTS.md

# AI Engineering Governance System

This repository uses a structured multi-agent orchestration framework for AI-assisted development.

The system is designed to:

* enforce Spec-First development
* isolate responsibilities
* reduce context chaos
* improve architectural consistency
* support scalable AI collaboration

---

# System Hierarchy

```text
Commander
    ↓
Orchestrator
    ↓
Specialized Agents
    ↓
Review / QA
```

---

# Core Principles

## 1. Spec-First Development

No implementation may begin without specification.

Source of truth:

```text
docs/specs/
```

All implementation must follow approved specifications.

---

## 2. Strict Specialization

Agents must operate only within their responsibility boundaries.

No single agent should handle the full development pipeline.

Specialized agents exist to:

* reduce hallucinations
* improve consistency
* isolate context
* maintain architectural discipline

---

## 3. Deterministic Workflow

All work must follow this order:

```text
RESEARCH
    ↓
SPECIFICATION
    ↓
ARCHITECTURE
    ↓
IMPLEMENTATION
    ↓
REVIEW
    ↓
QA
```

Stages must not be skipped.

---

# Agent Roles

## Orchestrator

Responsible for:

* task decomposition
* routing
* lifecycle management
* dependency coordination
* context distribution

Forbidden:

* writing implementation code
* redesigning architecture
* performing reviews
* bypassing specifications

---

## Specialized Agents

### spec-writer

Feature specifications, task breakdowns, acceptance criteria.

### architect

Architecture, module boundaries, scalability, system structure.

### frontend

React, charts, overlays, UI rendering.

### backend

APIs, storage, services, processing pipelines.

### researcher

Library analysis, ecosystem research, benchmarks.

### reviewer

Validation, quality control, spec compliance.

### docs-agent

Documentation, reports, guides, developer onboarding.


---

# Context Discipline

Agents must:

* pass only required context
* avoid large file dumps
* isolate tasks
* summarize before delegation
* minimize token usage

Prefer:

* task files
* specs
* structured docs

Over:

* large chat history
* uncontrolled context expansion

---

# Structured Outputs

All agents should return structured responses:

```text
# Summary
# Decisions
# Risks
# Files
# Next Steps
```

---

# Architecture Escalation Rules

If implementation requires architecture changes:

```text
STOP IMPLEMENTATION
    ↓
ESCALATE TO ARCHITECT
    ↓
UPDATE SPECIFICATION
    ↓
CONTINUE ONLY AFTER APPROVAL
```

Architecture changes must never occur implicitly during implementation.

---

# Anti-Chaos Rules

Agents MUST NOT:

* solve unrelated problems
* rewrite stable systems casually
* refactor outside task scope
* mix responsibilities
* introduce dependencies without justification
* bypass review stages

---

# Lifecycle States

```text
PLANNING
RESEARCH
SPECIFICATION
ARCHITECTURE
IMPLEMENTATION
REVIEW
QA
DONE
```

Additional states:

```text
BLOCKED
WAITING
ESCALATED
```

---

# File Structure

```text
.agents/
docs/specs/
docs/tasks/
docs/research/
docs/decisions/
```

---

# Execution Philosophy

The goal of this system is not autonomous coding.

The goal is:

* controlled execution
* architectural stability
* predictable workflows
* scalable AI collaboration
* maintainable long-term development
