# Output Contracts

Required response structure:

# Summary
# Decisions
# Risks
# Files
# Next Steps

# OUTPUT CONTRACT: AGENT IDENTIFICATION PROTOCOL

## MANDATORY HANDSHAKE RULE
Before executing any tool call (e.g., read_file, write_file, execute_command) or providing a final response, the active agent MUST output the following identity block at the very beginning of the message.

### Header Template (to be rendered in the chat):
---
🤖 **АКТИВНЫЙ АГЕНТ:** [Insert Active Agent Name here, e.g., Orchestrator / Backend / Reviewer]
⚔️ **ТЕКУЩИЙ СТАТУС:** [Insert current workflow state in Russian, e.g., Анализ задачи / Написание кода / Проверка]
🫡 **ПРИВЕТСТВИЕ:** [Dynamically resolve and inject the ${Base Greeting Formula} here]
---

## REPORTING RULES
- After the header block, switch completely to Russian (RU) for prose, explanations, and reports.
- Be concise, avoid fluff, and maintain the unique tone of the active agent persona.