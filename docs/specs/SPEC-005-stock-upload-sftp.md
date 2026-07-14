# SPEC-005: Stock Upload (SFTP)

**Status:** ✅ Done  
**Priority:** P0  
**Key File:** `scripts/upload_to_stocks.py`  
**Dependencies:** SPEC-002 (Config), SPEC-004 (EXIF Injection)

---

## 1. Purpose

Upload processed JPG files directly to stock contributor accounts via SFTP. Supports three platforms: **Shutterstock**, **Adobe Stock**, and **Pond5**. Runs in parallel threads with per-platform progress tracking.

---

## 2. Supported Platforms

| Platform | Default Host | Default Port | Protocol |
|----------|-------------|-------------|----------|
| Shutterstock | `ftps.shutterstock.com` | 21 | FTP/S |
| Adobe Stock | `sftp.contributor.adobestock.com` | 22 | SFTP |
| Pond5 | `ftp.pond5.com` | 21 | FTP/S |

---

## 3. Configuration

### 3.1 Per-Platform Credentials

| Field | Description |
|-------|-------------|
| `host` | SFTP/FTP server hostname |
| `port` | Port number (default 22 or 21) |
| `username` | Contributor username |
| `password` | Contributor password (encrypted in secrets.enc) |
| `remote_path` | Remote directory path (default `/`) |

### 3.2 Storage

- Credentials stored in `~/.stockdescriptor/config.json` (passwords encrypted)
- Configured via GUI: Upload FTP Settings window (see SPEC-001 §2.3)

---

## 4. Upload Algorithm

### 4.1 Single Platform Upload

```
function upload_platform(folder, config, progress_queue, move_uploaded=False):
  1. Connect to {host}:{port} via SFTP/FTP
  2. Authenticate with {username}/{password}
  3. List all *.jpg files in {folder} (excluding _UPLOADED/ subfolder)
  4. For each file:
     a. Upload to {remote_path}/{filename}
     b. Push progress to queue: (platform, current, total, filename)
     c. If move_uploaded: move file to _UPLOADED/
  5. Disconnect
  6. Push "upload_done" to queue
```

### 4.2 Parallel Upload (GUI)

1. User selects platforms via checkboxes
2. Click "📤 Upload Selected"
3. Each platform starts in its own thread
4. Progress bars update in real-time via queue
5. Files moved to `_UPLOADED/` only after ALL selected platforms finish (race condition prevention)

### 4.3 Auto-Upload

- Optional checkbox: "Auto-upload to stocks after EXIF injection"
- Triggers automatically when pipeline completes
- Uses same parallel upload logic

---

## 5. Progress Tracking

### 5.1 Queue Messages

| Type | Payload | Description |
|------|---------|-------------|
| `upload_start` | (platform, total) | Initialize progress bar |
| `progress` | (platform, current, total, filename) | Update progress |
| `upload_done` | (platform, uploaded, total) | Mark platform complete |
| `upload_error` | (platform, error_msg) | Mark platform failed |
| `uploaded_file` | (platform, filename) | Track successful uploads |
| `upload_thread_done` | (platform) | Signal thread completion |

### 5.2 File Movement Logic

- Files are NOT moved during parallel upload (prevents race conditions)
- After ALL selected platform threads finish:
  1. Check which files were uploaded to ALL selected platforms
  2. Move only those files to `_UPLOADED/`
  3. Files that failed on any platform remain in source folder

---

## 6. Error Handling

- **Connection failure** → per-platform error shown on progress bar
- **Authentication failure** → error logged, platform marked as failed
- **Upload failure (single file)** → continue with remaining files
- **All files failed** → platform marked as error
- **Partial success** → only fully-uploaded files moved to `_UPLOADED/`

---

## 7. Dependencies

- `paramiko` — SFTP client library
- `ftplib` — FTP/S support (stdlib)

---

*Last updated: 2026-07-14*