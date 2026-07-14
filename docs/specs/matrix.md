# StockDescriptor — Specification Matrix

## Project Overview

**StockDescriptor** — batch describer for photo stocks. Automated pipeline:
1. Resize images for Vision API
2. AI-generated Title / Description / Keywords (LM Studio or Google Gemini)
3. EXIF metadata injection into original JPGs
4. Obsidian navigation page (METADATA-NAV.md)
5. Parallel SFTP upload to stock platforms (Shutterstock, Adobe Stock, Pond5)

## Specification Index

| ID        | Name                              | Key Files                          | Priority | Status |
|-----------|-----------------------------------|------------------------------------|----------|--------|
| SPEC-001  | GUI Application                   | `gui_launcher.py`                  | P0       | ✅ Done |
| SPEC-002  | AI Providers & Config Manager     | `config_manager.py`, Settings UI   | P0       | ✅ Done |
| SPEC-003  | Batch Metadata Pipeline           | `processing/batch_metadata.py`     | P0       | ✅ Done |
| SPEC-004  | EXIF Injection                    | `processing/write_exif.ps1`        | P0       | ✅ Done |
| SPEC-005  | Stock Upload (SFTP)               | `scripts/upload_to_stocks.py`      | P0       | ✅ Done |
| SPEC-006  | Resize & Navigation Scripts       | `processing/*.ps1`                 | P1       | ✅ Done |
| SPEC-007  | Multilingual UI (EN/RU)           | Embedded in `gui_launcher.py`      | P1       | ✅ Done |

## Legend

- **P0**: Core functionality — must work for pipeline to complete
- **P1**: Important but non-blocking
- **P2**: Nice to have

## Status Meanings

- ✅ **Done** — Implemented and working
- 🔧 **In Progress** — Active development
- 📋 **Planned** — Spec written, not implemented
- ❌ **Broken** — Known issues exist

---

*Last updated: 2026-07-14*