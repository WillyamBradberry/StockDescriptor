# Refactoring-Specific Requirement

For every refactoring task:

* Preserve existing functionality unless explicitly specified.
* Document all architectural changes.
* Record migration steps.
* Record affected modules.
* Record breaking changes.
* Record reasons for the change.

When modifying files over 600 lines:

Evaluate whether responsibilities can be separated.

Possible extraction targets:

- services
- utilities
- adapters
- handlers
- components
- state management

Refactor only if it reduces complexity.

Avoid micro-modules.

Do not split files only to satisfy line limits.

Each extracted module must have a clear responsibility.

Additional Rules:
- code-organization.md