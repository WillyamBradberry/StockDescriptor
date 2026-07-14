# TASK-006: PowerShell Scripts — Maintenance & Portability

**Spec:** SPEC-004, SPEC-006  
**Key Files:** `processing/write_exif.ps1`, `processing/resize_for_vision.ps1`, `processing/create-metadata-nav-modified.ps1`  
**Priority:** P2  
**Status:** ✅ Working, portability improvements identified

---

## Description

The PowerShell scripts have hardcoded paths and lack cross-platform support:

1. **ExifTool path** — default path is hardcoded (`D:\PROGRAMS\EXIFTOOL\exiftool.exe`)
2. **No dry-run mode** — no way to preview changes without writing
3. **Error reporting** — exit codes are not consistently checked

---

## Proposed Improvements

1. Read ExifTool path from config (`~/.stockdescriptor/config.json`) instead of hardcoding
2. Add `-WhatIf` support for dry-run (PowerShell native)
3. Add consistent error handling with structured exit codes

---

## Files

- `processing/write_exif.ps1`
- `processing/resize_for_vision.ps1`

---

## Dependencies

- SPEC-002 (config file format)