# Memory Bank Rules (Screener Refactoring)

Before starting ANY implementation, refactoring, debugging, or architectural task, you MUST load and review the Memory Bank.

## Execution Rules

- Do not make changes in the workspace root unless explicitly asked.
# Project Root

The ONLY project root is:

./

Never create:

./memory-bank/
./memory_bank/
./docs/
./reports/

outside project root.


### Active Development Context

5. `memory-bank/activeContext.md`

   * Current refactoring objective
   * Current session progress
   * Open questions
   * Temporary decisions
   * Current implementation status

6. `memory-bank/progress.md`

   * Completed milestones
   * Remaining tasks
   * Current roadmap
   * Refactoring progress tracking

---

### Long-Term Knowledge

7. `memory-bank/decisions.md`

   * Architectural Decision Records (ADR)
   * Refactoring decisions
   * Reasons behind major changes
   * Rejected alternatives

8. `memory-bank/knownIssues.md`

   * Known bugs
   * Technical debt
   * Legacy code constraints
   * Areas requiring future attention

9. `memory-bank/lessonsLearned.md`

   * Discoveries made during refactoring
   * Common mistakes
   * Framework quirks
   * Useful implementation notes

---

### Specifications & Reports

10. `docs/specs/`

    * Refactoring specifications
    * Design documents
    * Requirements

11. `docs/logs/`

    * Refactoring reports
    * Session reports
    * Progress summaries

---

# Mandatory Workflow

Before starting any significant task:

1. Read:

   * `memory-bank/projectBrief.md`
   * `memory-bank/systemPatterns.md`
   * `memory-bank/activeContext.md`
   * `memory-bank/progress.md`

2. Read all relevant specifications from:

   * `docs/specs/`

3. Read the latest reports from:

   * `docs/logs/`

4. Identify:

   * Existing architecture
   * Previous decisions
   * Current refactoring status
   * Known constraints

5. Only then begin implementation.

---

# Memory Maintenance Rules

Whenever any of the following occurs:

* Architecture changes
* Folder structure changes
* New design patterns appear
* Important discoveries are made
* Refactoring decisions are taken
* Technical limitations are found
* Major tasks are completed

You MUST update the appropriate Memory Bank files.

---

# Context Window Protection

When the conversation becomes long or context usage exceeds safe limits:

1. Summarize current progress.

2. Update:

   * `activeContext.md`
   * `progress.md`
   * `decisions.md`
   * `knownIssues.md`
   * `lessonsLearned.md`

3. Ensure the next session can continue without losing important project knowledge.

---

# Refactoring-Specific Requirement

For every refactoring task:

* Preserve existing functionality unless explicitly specified.
* Document all architectural changes.
* Record migration steps.
* Record affected modules.
* Record breaking changes.
* Record reasons for the change.


# Bug Investigation Priority

Priority order:

1. Recent git diff
2. Recent modified files
3. Recent refactoring reports
4. Relevant module
5. Full project scan

Never start with full project scan.

Every completed refactoring phase must leave the Memory Bank in a state where another AI agent can continue the project without additional explanation.

The Memory Bank is the source of truth. If documentation and code disagree, investigate and update the Memory Bank accordingly.
