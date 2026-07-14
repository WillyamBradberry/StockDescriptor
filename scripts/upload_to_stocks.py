#!/usr/bin/env python3
"""
StockDescriptor - upload_to_stocks.py
Parallel SFTP/FTP upload to stock platforms: Shutterstock, Adobe Stock, Pond5
Supports progress reporting via queue for GUI integration.
"""

import os
import sys
import json
import time
import threading
import paramiko
import ftplib
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from stat import S_ISDIR

# ================= CONFIG =================

# Default FTP config (can be overridden via user config file)
DEFAULT_UPLOAD_CONFIG = {
    "shutterstock": {
        "host": "ftps.shutterstock.com",
        "port": 21,
        "username": "",
        "password": "",
        "remote_path": "/"
    },
    "adobe": {
        "host": "sftp.contributor.adobestock.com",
        "port": 22,
        "username": "",
        "password": "",
        "remote_path": "/"
    },
    "pond5": {
        "host": "ftp.pond5.com",
        "port": 21,
        "username": "",
        "password": "",
        "remote_path": "/"
    }
}




# ================= SFTP UPLOAD HELPERS =================

def ensure_remote_dir(sftp, remote_path: str):
    """Recursively ensure remote directory exists."""
    parts = remote_path.strip("/").split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current += "/" + part
        try:
            sftp.stat(current)
        except FileNotFoundError:
            try:
                sftp.mkdir(current)
                print(f"  Created remote dir: {current}")
            except Exception as e:
                print(f"  Warning: could not create dir {current}: {e}")


def upload_file_sftp(
    sftp,
    local_path: Path,
    remote_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Upload a single file via SFTP with optional progress callback.
    progress_callback(current_bytes, total_bytes)
    """
    total_size = local_path.stat().st_size
    uploaded = 0

    # We use a custom progress callback for paramiko's put
    def callback(transferred, total):
        nonlocal uploaded
        uploaded = transferred
        if progress_callback:
            progress_callback(transferred, total_size)

    try:
        sftp.put(
            str(local_path),
            remote_path,
            callback=callback,
            confirm=True
        )
        return True
    except Exception as e:
        print(f"  Upload error: {e}")
        return False


def upload_file_ftp(
    ftp,
    local_path: Path,
    remote_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    Upload a single file via FTPS (FTP_TLS) with optional progress callback.
    progress_callback(current_bytes, total_bytes)
    """
    total_size = local_path.stat().st_size
    uploaded = 0

    def callback(block: bytes):
        nonlocal uploaded
        uploaded += len(block)
        if progress_callback:
            progress_callback(uploaded, total_size)

    try:
        with open(local_path, "rb") as f:
            ftp.storbinary(f"STOR {remote_path}", f, callback=callback)
        return True
    except Exception as e:
        print(f"  Upload error: {e}")
        return False


def ensure_ftp_dir(ftp, remote_path: str):
    """Recursively ensure remote directory exists on an FTP/FTPS server."""
    parts = remote_path.strip("/").split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current += "/" + part
        try:
            ftp.cwd(current)
        except Exception:
            try:
                ftp.mkd(current)
                ftp.cwd(current)
            except Exception:
                pass
    # Restore to root so subsequent STOR paths are interpreted from root
    try:
        ftp.cwd("/")
    except Exception:
        pass


# ================= PLATFORM-SPECIFIC UPLOADERS =================

def _get_upload_config(platform: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get upload config for a platform from main config (with decrypted secrets)."""
    upload_cfg = config.get("upload_config", {})
    if platform in upload_cfg:
        return upload_cfg[platform]
    return DEFAULT_UPLOAD_CONFIG.get(platform, {})


def upload_to_platform(
    platform: str,
    folder: Path,
    config: Dict[str, Any],
    progress_queue=None,
    move_uploaded: bool = True,
    file_filter: Optional[Callable[[Path], bool]] = None
) -> int:
    """
    Upload JPG files from folder to a stock platform via SFTP.

    Args:
        platform: "shutterstock", "adobe", or "pond5"
        folder: Local folder with JPG files
        config: Main app config dict
        progress_queue: Optional queue.Queue for GUI progress reporting
        move_uploaded: Move uploaded files to _UPLOADED/ subfolder
        file_filter: Optional function to filter files (e.g. by name)

    Returns:
        Number of successfully uploaded files
    """
    # Get platform config
    plat_cfg = _get_upload_config(platform, config)

    host = plat_cfg.get("host", "")
    port = plat_cfg.get("port", 22)
    username = plat_cfg.get("username", "")
    password = plat_cfg.get("password", "")
    remote_root = plat_cfg.get("remote_path", "/")

    if not host or not username:
        msg = f"⚠️ FTP config for {platform} is incomplete. Set credentials in Settings → Upload."
        if progress_queue:
            progress_queue.put(("log", f"[{platform.upper()}] {msg}", "warning"))
        else:
            print(msg)
        return 0

    # Find JPG files
    jpg_files = sorted([
        f for f in folder.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg") and f.is_file()
        and not f.name.startswith(".")
        and (file_filter is None or file_filter(f))
    ])

    if not jpg_files:
        msg = f"ℹ️ No JPG files found in {folder} for {platform}"
        if progress_queue:
            progress_queue.put(("log", f"[{platform.upper()}] {msg}", "info"))
        else:
            print(msg)
        return 0

    total_files = len(jpg_files)
    uploaded_count = 0
    uploaded_folder = folder / "_UPLOADED"

    if progress_queue:
        # Signal total file count
        progress_queue.put(("upload_start", platform, total_files))
        progress_queue.put(("log", f"[{platform.upper()}] 📤 Starting upload {total_files} files...", "step"))

    # Decide protocol: port 22 => SFTP (paramiko), otherwise FTPS (ftplib)
    use_sftp = (int(port) == 22)

    # ---- Connect ----
    sftp = None
    ftp = None
    transport = None
    try:
        if use_sftp:
            transport = paramiko.Transport((host, int(port)))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        else:
            # Try secure FTPS first with an explicit connection timeout.
            try:
                ftp = ftplib.FTP_TLS()
                ftp.connect(host, int(port), timeout=30)
                ftp.login(username, password)
                try:
                    # Some servers require set_pasv(True) AFTER login and
                    # BEFORE prot_p(), otherwise they reset the TLS session
                    # or time out on the data channel.
                    ftp.set_pasv(True)
                    ftp.prot_p()  # secure the data channel
                except Exception as tls_err:
                    # Server may not support securing the data channel
                    # (or drops TLS in passive mode). Continue without it
                    # rather than aborting the whole upload.
                    print(f"Warning: Could not secure data channel: {tls_err}")
            except Exception as e:
                # FTPS failed entirely (timeout, SSL handshake error, socket
                # error, etc.). Fall back to plain (unencrypted) FTP.
                print(f"FTPS connection failed, trying plain FTP... Error: {e}")
                try:
                    if ftp is not None:
                        try:
                            ftp.close()
                        except Exception:
                            pass
                except Exception:
                    pass
                ftp = ftplib.FTP()
                ftp.connect(host, int(port), timeout=30)
                ftp.login(username, password)
                ftp.set_pasv(True)
    except Exception as e:
        msg = f"❌ Connection failed for {platform}: {e}"
        if progress_queue:
            progress_queue.put(("log", f"[{platform.upper()}] {msg}", "error"))
            progress_queue.put(("upload_error", platform, str(e)))
        else:
            print(msg)
        return 0

    try:
        # Ensure remote root dir exists
        try:
            if use_sftp:
                ensure_remote_dir(sftp, remote_root)
            else:
                ensure_ftp_dir(ftp, remote_root)
        except Exception:
            pass  # root may already exist

        # Upload each file
        for idx, local_file in enumerate(jpg_files):
            filename = local_file.name
            remote_file = f"{remote_root.rstrip('/')}/{filename}"

            if progress_queue:
                progress_queue.put(("progress", platform, idx + 1, total_files, filename))

            try:
                if use_sftp:
                    success = upload_file_sftp(sftp, local_file, remote_file)
                else:
                    success = upload_file_ftp(ftp, local_file, remote_file)
            except Exception as e:
                success = False
                if progress_queue:
                    progress_queue.put(("log", f"[{platform.upper()}] ❌ Error uploading {filename}: {e}", "error"))

            if success:
                uploaded_count += 1
                if progress_queue:
                    progress_queue.put(("log", f"[{platform.upper()}] ✅ {filename} uploaded successfully", "success"))
                    # Report the successfully uploaded file so the GUI can
                    # safely move it to _UPLOADED only after ALL platforms finish
                    # (avoids a race when multiple platforms upload the same folder in parallel)
                    progress_queue.put(("uploaded_file", platform, filename))
                else:
                    print(f"  ✅ {filename} uploaded")

                # Move to _UPLOADED if requested (used by CLI / single-platform runs).
                # In parallel GUI runs the caller passes move_uploaded=False and moves
                # files itself once every platform thread has completed.
                if move_uploaded:
                    try:
                        uploaded_folder.mkdir(exist_ok=True)
                        dest = uploaded_folder / filename
                        if dest.exists():
                            dest.unlink()  # remove if already exists
                        local_file.rename(dest)
                    except Exception as e:
                        if progress_queue:
                            progress_queue.put(("log", f"[{platform.upper()}] ⚠️ Could not move {filename}: {e}", "warning"))
            else:
                if progress_queue:
                    progress_queue.put(("log", f"[{platform.upper()}] ❌ Failed to upload {filename}", "error"))

        # Summary
        if progress_queue:
            progress_queue.put(("upload_done", platform, uploaded_count, total_files))
            if uploaded_count == total_files:
                progress_queue.put(("log", f"[{platform.upper()}] ✅ All {uploaded_count}/{total_files} files uploaded!", "success"))
            else:
                progress_queue.put(("log", f"[{platform.upper()}] ⚠️ {uploaded_count}/{total_files} files uploaded (some failed)", "warning"))

    except Exception as e:
        msg = f"❌ {platform} upload error: {e}"
        if progress_queue:
            progress_queue.put(("log", f"[{platform.upper()}] {msg}", "error"))
            progress_queue.put(("upload_error", platform, str(e)))
        else:
            print(msg)
    finally:
        try:
            if sftp is not None:
                sftp.close()
        except Exception:
            pass
        try:
            if ftp is not None:
                ftp.quit()
        except Exception:
            pass
        try:
            if transport is not None:
                transport.close()
        except Exception:
            pass

    return uploaded_count


def upload_shutterstock(
    folder: Path,
    config: Dict[str, Any],
    progress_queue=None,
    move_uploaded: bool = True
) -> int:
    """Upload files to Shutterstock."""
    return upload_to_platform("shutterstock", folder, config, progress_queue, move_uploaded)


def upload_adobe(
    folder: Path,
    config: Dict[str, Any],
    progress_queue=None,
    move_uploaded: bool = True
) -> int:
    """Upload files to Adobe Stock."""
    return upload_to_platform("adobe", folder, config, progress_queue, move_uploaded)


def upload_pond5(
    folder: Path,
    config: Dict[str, Any],
    progress_queue=None,
    move_uploaded: bool = True
) -> int:
    """Upload files to Pond5."""
    return upload_to_platform("pond5", folder, config, progress_queue, move_uploaded)


# ================= CLI ENTRY POINT =================

def main():
    """CLI interface for testing uploads."""
    import argparse

    parser = argparse.ArgumentParser(description="Upload JPG files to stock platforms via SFTP")
    parser.add_argument("folder", type=str, help="Folder with JPG files")
    parser.add_argument("--platform", "-p", choices=["shutterstock", "adobe", "pond5", "all"],
                        default="all", help="Platform to upload to (default: all)")
    parser.add_argument("--no-move", action="store_true", help="Don't move uploaded files to _UPLOADED")

    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"Error: folder not found: {folder}")
        sys.exit(1)

    platforms = ["shutterstock", "adobe", "pond5"] if args.platform == "all" else [args.platform]

    for platform in platforms:
        print(f"\n{'='*50}")
        print(f"📤 Uploading to {platform.upper()}...")
        print(f"{'='*50}")
        count = upload_to_platform(
            platform,
            folder,
            config={},  # Use defaults / file config
            move_uploaded=not args.no_move
        )
        print(f"Result: {count} files uploaded")

    print("\n✅ All uploads complete!")


if __name__ == "__main__":
    main()