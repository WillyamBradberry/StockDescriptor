#!/usr/bin/env python3
"""
StockDescriptor - Automatic JPG Uploader to Stock Platforms
Supports: Shutterstock (FTPS), Adobe Stock (SFTP), Pond5 (FTP)

Usage examples:
  python upload_to_stocks.py --platform shutterstock --folder ./my_photos
  python upload_to_stocks.py --platform adobe --folder ./my_photos --move-uploaded
  python upload_to_stocks.py --setup   # interactive credential setup

Requirements:
  pip install paramiko

Config file: ~/.stockdescriptor/upload_config.json (created automatically)
Never commit this file!
"""

import argparse
import ftplib
import getpass
import json
import os
import shutil
import queue
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import paramiko
except ImportError:
    paramiko = None
    print("Warning: paramiko not installed. Adobe SFTP upload will not work.")
    print("Install with: pip install paramiko")

CONFIG_DIR = Path.home() / ".stockdescriptor"
CONFIG_FILE = CONFIG_DIR / "upload_config.json"


def load_config() -> Dict[str, Any]:
    """Load upload credentials config."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config ({e})")
    return {}


def save_config(cfg: Dict[str, Any]) -> None:
    """Save config securely."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    # Set restrictive permissions on Unix-like systems
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except:
        pass


def get_credentials(platform: str, config: Dict[str, Any]) -> tuple:
    """Get or prompt for credentials."""
    key_user = f"{platform}_user"
    key_pass = f"{platform}_pass"

    user = config.get(key_user)
    passwd = config.get(key_pass)

    if not user:
        user = input(f"Enter {platform} username / email: ").strip()
        config[key_user] = user

    if not passwd:
        passwd = getpass.getpass(f"Enter {platform} password: ")
        config[key_pass] = passwd
        save_config(config)  # Save after first entry

    return user, passwd


def upload_shutterstock(folder: Path, config: Dict[str, Any], progress_queue: Optional[queue.Queue] = None, move_uploaded: bool = False) -> int:
    """Upload JPGs to Shutterstock via Explicit FTPS. Supports progress via queue."""
    import queue as q  # local import to avoid circular if needed
    host = "ftps.shutterstock.com"
    port = 21
    user, passwd = get_credentials("shutterstock", config)

    def report(msg_type, *args):
        if progress_queue:
            progress_queue.put((msg_type, "shutterstock", *args))
        else:
            if msg_type == "log":
                print(args[0])
            elif msg_type == "progress":
                print(f"shutterstock: {args[0]}/{args[1]} - {args[2]}")

    report("log", f"\n=== Connecting to Shutterstock FTPS ({host}) ===")
    ftp = ftplib.FTP_TLS()
    ftp.connect(host, port)
    ftp.login(user, passwd)
    ftp.prot_p()
    ftp.set_pasv(True)

    uploaded = 0
    jpg_files = sorted(list(folder.glob("*.jpg")) + list(folder.glob("*.JPG")))
    total = len(jpg_files)

    for file_path in jpg_files:
        try:
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {file_path.name}", f)
            uploaded += 1
            report("progress", uploaded, total, file_path.name)
            report("log", f"✓ Uploaded: {file_path.name}")

            if move_uploaded:
                uploaded_dir = folder / "uploaded"
                uploaded_dir.mkdir(exist_ok=True)
                shutil.move(str(file_path), uploaded_dir / file_path.name)
        except Exception as e:
            report("log", f"✗ Failed {file_path.name}: {e}")

    ftp.quit()
    report("log", f"\nShutterstock: {uploaded} files uploaded successfully.")
    return uploaded


def upload_adobe(folder: Path, config: Dict[str, Any], progress_queue: Optional[queue.Queue] = None, move_uploaded: bool = False) -> int:
    """Upload JPGs to Adobe Stock via SFTP. Supports progress via queue."""
    if paramiko is None:
        if progress_queue:
            progress_queue.put(("log", "adobe", "Error: paramiko is required. pip install paramiko"))
        else:
            print("Error: paramiko is required for Adobe SFTP. Run: pip install paramiko")
        return 0

    host = "sftp.contributor.adobestock.com"
    user, passwd = get_credentials("adobe", config)

    def report(msg_type, *args):
        if progress_queue:
            progress_queue.put((msg_type, "adobe", *args))
        else:
            if msg_type == "log":
                print(args[0])
            elif msg_type == "progress":
                print(f"adobe: {args[0]}/{args[1]} - {args[2]}")

    report("log", f"\n=== Connecting to Adobe Stock SFTP ({host}) ===")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=passwd)
    sftp = ssh.open_sftp()

    uploaded = 0
    jpg_files = sorted(list(folder.glob("*.jpg")) + list(folder.glob("*.JPG")))
    total = len(jpg_files)

    for file_path in jpg_files:
        try:
            remote_path = file_path.name
            sftp.put(str(file_path), remote_path)
            uploaded += 1
            report("progress", uploaded, total, file_path.name)
            report("log", f"✓ Uploaded: {file_path.name}")

            if move_uploaded:
                uploaded_dir = folder / "uploaded"
                uploaded_dir.mkdir(exist_ok=True)
                shutil.move(str(file_path), uploaded_dir / file_path.name)
        except Exception as e:
            report("log", f"✗ Failed {file_path.name}: {e}")

    sftp.close()
    ssh.close()
    report("log", f"\nAdobe Stock: {uploaded} files uploaded successfully.")
    return uploaded


def upload_pond5(folder: Path, config: Dict[str, Any], progress_queue: Optional[queue.Queue] = None, move_uploaded: bool = False) -> int:
    """Upload JPGs to Pond5 via plain FTP. Supports progress via queue."""
    host = "ftp.pond5.com"
    user, passwd = get_credentials("pond5", config)

    def report(msg_type, *args):
        if progress_queue:
            progress_queue.put((msg_type, "pond5", *args))
        else:
            if msg_type == "log":
                print(args[0])
            elif msg_type == "progress":
                print(f"pond5: {args[0]}/{args[1]} - {args[2]}")

    report("log", f"\n=== Connecting to Pond5 FTP ({host}) ===")
    ftp = ftplib.FTP()
    ftp.connect(host)
    ftp.login(user, passwd)
    ftp.set_pasv(True)

    uploaded = 0
    jpg_files = sorted(list(folder.glob("*.jpg")) + list(folder.glob("*.JPG")))
    total = len(jpg_files)

    for file_path in jpg_files:
        try:
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {file_path.name}", f)
            uploaded += 1
            report("progress", uploaded, total, file_path.name)
            report("log", f"✓ Uploaded: {file_path.name}")

            if move_uploaded:
                uploaded_dir = folder / "uploaded"
                uploaded_dir.mkdir(exist_ok=True)
                shutil.move(str(file_path), uploaded_dir / file_path.name)
        except Exception as e:
            report("log", f"✗ Failed {file_path.name}: {e}")

    ftp.quit()
    report("log", f"\nPond5: {uploaded} files uploaded successfully.")
    return uploaded


def setup_credentials():
    """Interactive setup for all platforms."""
    print("=== Stock Uploader Credential Setup ===")
    config = load_config()

    platforms = ["shutterstock", "adobe", "pond5"]
    for p in platforms:
        print(f"\n--- {p.upper()} ---")
        user = input(f"Username / Email for {p} (or press Enter to skip): ").strip()
        if user:
            config[f"{p}_user"] = user
            passwd = getpass.getpass(f"Password for {p}: ")
            config[f"{p}_pass"] = passwd

    save_config(config)
    print("\n✅ Credentials saved to:", CONFIG_FILE)
    print("You can now run uploads without entering passwords every time.")


def main():
    parser = argparse.ArgumentParser(
        description="Automatic JPG uploader to Shutterstock, Adobe Stock, and Pond5"
    )
    parser.add_argument("--platform", choices=["shutterstock", "adobe", "pond5"],
                        help="Target platform")
    parser.add_argument("--folder", type=str, default=".",
                        help="Folder with JPG files (default: current directory)")
    parser.add_argument("--move-uploaded", action="store_true",
                        help="Move successfully uploaded files to 'uploaded/' subfolder")
    parser.add_argument("--setup", action="store_true",
                        help="Interactive setup of credentials (saves to config)")

    args = parser.parse_args()

    if args.setup:
        setup_credentials()
        return

    if not args.platform:
        parser.error("--platform is required (or use --setup)")

    folder = Path(args.folder).resolve()
    if not folder.exists() or not folder.is_dir():
        print(f"Error: Folder not found: {folder}")
        return

    config = load_config()

    print(f"Scanning folder: {folder}")
    jpg_count = len(list(folder.glob("*.jpg"))) + len(list(folder.glob("*.JPG")))
    print(f"Found {jpg_count} JPG files")

    if jpg_count == 0:
        print("No JPG files found. Exiting.")
        return

    if args.platform == "shutterstock":
        upload_shutterstock(folder, config, args.move_uploaded)
    elif args.platform == "adobe":
        upload_adobe(folder, config, args.move_uploaded)
    elif args.platform == "pond5":
        upload_pond5(folder, config, args.move_uploaded)

    print("\n✅ Done! Check your contributor portal for uploaded files.")


if __name__ == "__main__":
    main()
