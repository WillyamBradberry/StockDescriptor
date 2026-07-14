# StockDescriptor — Task Board

## Legend

| Prefix | Meaning |
|--------|---------|
| ✅ Done | Implemented and working |
| 🔧 In Progress | Active development |
| 📋 Planned | Design complete, ready to implement |
| 💡 Proposed | Idea, needs spec |

---

## Priority P0 — Core Pipeline (all ✅ Done)

| ID | Task | Priority | Status | Key File |
|----|------|----------|--------|----------|
| SPEC-001 | GUI Application | P0 | ✅ Done | `gui_launcher.py` |
| SPEC-002 | AI Providers & Config Manager | P0 | ✅ Done | `config_manager.py` |
| SPEC-003 | Batch Metadata Pipeline | P0 | ✅ Done | `processing/batch_metadata.py` |
| SPEC-004 | EXIF Injection | P0 | ✅ Done | `processing/write_exif.ps1` |
| SPEC-005 | Stock Upload (SFTP) | P0 | ✅ Done | `scripts/upload_to_stocks.py` |

## Priority P1 — Important

| ID | Task | Priority | Status | Key File |
|----|------|----------|--------|----------|
| SPEC-006 | Resize & Navigation Scripts | P1 | ✅ Done | `processing/*.ps1` |
| SPEC-007 | Multilingual UI (EN/RU) | P1 | ✅ Done | `gui_launcher.py` |
| TASK-001 | GUI Refactoring (split ~1339 lines) | P1 | 🔧 Proposed | `gui_launcher.py` |
| TASK-003 | Response Parsing Robustness | P1 | 💡 Proposed | `processing/batch_metadata.py` |
| TASK-007 | Testing & Documentation | P1 | 📋 Planned | Project-wide |

## Priority P2 — Nice to Have

| ID | Task | Priority | Status | Key File |
|----|------|----------|--------|----------|
| TASK-002 | Config Manager — Security Review | P2 | 💡 Proposed | `config_manager.py` |
| TASK-004 | SFTP Upload — Retry & Resilience | P2 | 💡 Proposed | `scripts/upload_to_stocks.py` |
| TASK-005 | CLI Pipeline — Improvements | P2 | 💡 Proposed | `processing/batch_metadata.py` |
| TASK-006 | PowerShell Scripts — Portability | P2 | 💡 Proposed | `processing/*.ps1` |

---

## Spec Files

| File | Content |
|------|---------|
| `docs/specs/matrix.md` | Specification index |
| `docs/specs/SPEC-001-gui-application.md` | GUI Application |
| `docs/specs/SPEC-002-ai-providers-config.md` | AI Providers & Config Manager |
| `docs/specs/SPEC-003-batch-metadata-pipeline.md` | Batch Metadata Pipeline |
| `docs/specs/SPEC-004-exif-injection.md` | EXIF Injection |
| `docs/specs/SPEC-005-stock-upload-sftp.md` | Stock Upload (SFTP) |
| `docs/specs/SPEC-006-resize-navigation.md` | Resize & Navigation Scripts |
| `docs/specs/SPEC-007-multilingual-ui.md` | Multilingual UI (EN/RU) |

## Task Files

| File | Content |
|------|---------|
| `docs/tasks/TASK-001-gui-maintenance.md` | GUI code splitting |
| `docs/tasks/TASK-002-config-manager-review.md` | Config security review |
| `docs/tasks/TASK-003-response-parsing-robustness.md` | LLM response parser improvements |
| `docs/tasks/TASK-004-sftp-upload-retry.md` | Upload retry & resilience |
| `docs/tasks/TASK-005-cli-pipeline-improvements.md` | CLI polish & logging |
| `docs/tasks/TASK-006-ps-scripts-consolidation.md` | PS scripts maintenance |
| `docs/tasks/TASK-007-testing-documentation.md` | Tests & developer docs |

---

*Last updated: 2026-07-14*