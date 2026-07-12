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
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from stat import S_ISDIR

# ================= CONFIG =================

# Default FTP config (can be overridden via user config file)
DEFAULT_UPLOAD_CONFIG = {
    "shutterstock": {
        "host": "upload.shutterstock.com",
        "port": 22,
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
        "host": "upload.pond5.com",
        "port": 22,
        "username": "",
        "password": "",
        "remote_path": "/"
    }
}

CONFIG_DIR = Path.home() / ".stockdescriptor"
UPLOAD_CONFIG_FILE = CONFIG_DIR / "upload_config.json"


def load_upload_config() -> Dict[str, Any]:
    """Load FTP upload config from user file, merge with defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if UPLOAD_CONFIG_FILE.exists():
        try:
            with open(UPLOAD_CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            # Deep merge with defaults
            cfg = json.loads(json.dumps(DEFAULT_UPLOAD_CONFIG))  # deep copy
            for platform in cfg:
                if platform in user_cfg:
                    cfg[platform].update(user_cfg[platform])
            return cfg
        except Exception as e:
            print(f"Warning: could not load upload config ({e}), using defaults.")
    return json.loads(json.dumps(DEFAULT_UPLOAD_CONFIG))


def save_upload_config(cfg: Dict[str, Any]) -> bool:
    """Save FTP upload config to user file."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(UPLOAD_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving upload config: {e}")
        return False


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


# ================= PLATFORM-SPECIFIC UPLOADERS =================

def _get_upload_config(platform: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get upload config for a platform from main config or upload config."""
    # First check if there's an upload_config key in main config
    upload_cfg = config.get("upload_config", {})
    if platform in upload_cfg:
        return upload_cfg[platform]

    # Fall back to loading from file
    try:
        uc = load_upload_config()
        if platform in uc:
            return uc[platform]
    except Exception:
        pass

    # Return default
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
            progress_queue.put(("log", platform, msg, "warning"))
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
            progress_queue.put(("log", platform, msg, "info"))
        else:
            print(msg)
        return 0

    total_files = len(jpg_files)
    uploaded_count = 0
    uploaded_folder = folder / "_UPLOADED"

    if progress_queue:
        # Signal total file count
        progress_queue.put(("upload_start", platform, total_files))
        progress_queue.put(("log", platform, f"📤 Starting upload {total_files} files to {platform.upper()}...", "step"))

    # Connect via SFTP
    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
    except Exception as e:
        msg = f"❌ Connection failed for {platform}: {e}"
        if progress_queue:
            progress_queue.put(("log", platform, msg, "error"))
            progress_queue.put(("upload_error", platform, str(e)))
        else:
            print(msg)
        return 0

    try:
        # Ensure remote root dir exists
        try:
            ensure_remote_dir(sftp, remote_root)
        except Exception:
            pass  # root may already exist

        # Upload each file
        for idx, local_file in enumerate(jpg_files):
            filename = local_file.name
            remote_file = f"{remote_root.rstrip('/')}/{filename}"

            if progress_queue:
                progress_queue.put(("progress", platform, idx + 1, total_files, filename))

            try:
                success = upload_file_sftp(sftp, local_file, remote_file)
            except Exception as e:
                success = False
                if progress_queue:
                    progress_queue.put(("log", platform, f"❌ Error uploading {filename}: {e}", "error"))

            if success:
                uploaded_count += 1
                if progress_queue:
                    progress_queue.put(("log", platform, f"✅ {filename} uploaded successfully", "success"))
                else:
                    print(f"  ✅ {filename} uploaded")

                # Move to _UPLOADED if requested
                if move_uploaded:
                    try:
                        uploaded_folder.mkdir(exist_ok=True)
                        dest = uploaded_folder / filename
                        if dest.exists():
                            dest.unlink()  # remove if already exists
                        local_file.rename(dest)
                    except Exception as e:
                        if progress_queue:
                            progress_queue.put(("log", platform, f"⚠️ Could not move {filename}: {e}", "warning"))
            else:
                if progress_queue:
                    progress_queue.put(("log", platform, f"❌ Failed to upload {filename}", "error"))

        # Summary
        if progress_queue:
            progress_queue.put(("upload_done", platform, uploaded_count, total_files))
            if uploaded_count == total_files:
                progress_queue.put(("log", platform, f"✅ {platform.upper()}: All {uploaded_count}/{total_files} files uploaded!", "success"))
            else:
                progress_queue.put(("log", platform, f"⚠️ {platform.upper()}: {uploaded_count}/{total_files} files uploaded (some failed)", "warning"))

    except Exception as e:
        msg = f"❌ {platform} upload error: {e}"
        if progress_queue:
            progress_queue.put(("log", platform, msg, "error"))
            progress_queue.put(("upload_error", platform, str(e)))
        else:
            print(msg)
    finally:
        try:
            sftp.close()
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