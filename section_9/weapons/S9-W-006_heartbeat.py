#!/usr/bin/env python3
"""
S9-W-006: Dead Man's Switch — Heartbeat Sender
Classification: CROWN EYES ONLY
Class IV (Scorched Earth)

Sends a heartbeat signal (proof-of-life) by writing a
timestamped, hashed record to the heartbeat file.

Usage:
    python3 S9-W-006_heartbeat.py
    python3 S9-W-006_heartbeat.py --heartbeat-path /custom/path.json
    python3 S9-W-006_heartbeat.py --threats-path /custom/THREATS.md
"""

from __future__ import annotations

import json
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Default paths relative to this file's location
_WEAPONS_DIR = Path(__file__).resolve().parent
_SECTION_9_DIR = _WEAPONS_DIR.parent
_DEFAULT_HEARTBEAT = _SECTION_9_DIR / "operations" / "heartbeat.json"
_DEFAULT_THREATS = _SECTION_9_DIR / "intelligence" / "THREATS.md"
_BACKUP_HEARTBEAT = Path("/tmp/hb_sec9_heartbeat.json")


def _hash_file(filepath: Path) -> str:
    """SHA256 hash of a file's contents. Returns empty hash on error."""
    try:
        content = filepath.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except (OSError, IOError):
        return hashlib.sha256(b"").hexdigest()


def _read_current_sequence(heartbeat_path: Path) -> int:
    """Read the current sequence number from existing heartbeat. Returns 0 if none."""
    try:
        data = json.loads(heartbeat_path.read_text())
        return int(data.get("sequence", 0))
    except (OSError, IOError, json.JSONDecodeError, ValueError, TypeError):
        return 0


def send_heartbeat(
    heartbeat_path: Optional[Path] = None,
    threats_path: Optional[Path] = None,
    backup_path: Optional[Path] = None,
) -> dict:
    """Write a heartbeat record. Returns the heartbeat data."""
    if heartbeat_path is None:
        heartbeat_path = _DEFAULT_HEARTBEAT
    if threats_path is None:
        threats_path = _DEFAULT_THREATS
    if backup_path is None:
        backup_path = _BACKUP_HEARTBEAT

    current_seq = _read_current_sequence(heartbeat_path)

    heartbeat = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threats_hash": _hash_file(threats_path),
        "status": "alive",
        "sequence": current_seq + 1,
    }

    heartbeat_json = json.dumps(heartbeat, indent=2)

    # Write primary
    try:
        heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        heartbeat_path.write_text(heartbeat_json)
    except (OSError, IOError) as e:
        print(f"[HEARTBEAT] WARNING: Failed to write primary: {e}", file=sys.stderr)

    # Write backup
    try:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(heartbeat_json)
    except (OSError, IOError):
        pass  # Backup failure is not critical

    return heartbeat


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    heartbeat_path: Optional[Path] = None
    threats_path: Optional[Path] = None

    while args:
        flag = args.pop(0)
        if flag == "--heartbeat-path" and args:
            heartbeat_path = Path(args.pop(0))
        elif flag == "--threats-path" and args:
            threats_path = Path(args.pop(0))

    heartbeat = send_heartbeat(heartbeat_path, threats_path)
    print(json.dumps(heartbeat, indent=2))


if __name__ == "__main__":
    main()
