# TASK-007: Testing & Documentation

**Spec:** All SPECs  
**Key Files:** Project-wide  
**Priority:** P1  
**Status:** 📋 Planned

---

## Description

The project lacks automated tests and developer documentation. This task covers:

1. **Unit tests** — Core modules: `config_manager.py`, `batch_metadata.py` (parsing functions)
2. **Integration test** — Full pipeline with `--mock` mode
3. **Developer guide** — How to set up, extend, and debug
4. **CONTRIBUTING.md** — Contribution guidelines

---

## Proposed Deliverables

### 1. Unit Tests (`tests/`)

| Test File | Covers |
|-----------|--------|
| `test_config_manager.py` | `load_config()`, `save_config()`, encryption round-trip |
| `test_metadata_parser.py` | `extract_metadata_block()`, `_extract_field()`, `_split_into_sections()` |
| `test_upload_module.py` | `_get_upload_config()`, `upload_file_sftp()` mock |

### 2. Integration Test

- Mock pipeline run using `--mock` flag
- Verify METADATA.md output format
- Verify error handling paths

### 3. Documentation

| File | Purpose |
|------|---------|
| `docs/guides/developer-setup.md` | Setup from scratch, venv, dependencies |
| `docs/guides/extending-providers.md` | How to add a new AI provider |
| `CONTRIBUTING.md` | PR workflow, code style, testing |

---

## Dependencies

- pytest installed
- All other tasks should be stable first