#!/usr/bin/env python3
"""
S9-W-006: Dead Man's Switch — Lockdown Sequence
Classification: CROWN EYES ONLY
Class IV (Scorched Earth)

Executes the lockdown sequence when the Dead Man's Switch
activates. Requires --live flag for real execution.
Without --live, runs in simulation mode (prints actions
without executing them).

Usage:
    python3 S9-W-006_lockdown.py                   # simulation
    python3 S9-W-006_lockdown.py --live             # REAL lockdown
    python3 S9-W-006_lockdown.py --repo-path /path  # custom repo
"""

from __future__ import annotations

import json
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Default paths
_WEAPONS_DIR = Path(__file__).resolve().parent
_SECTION_9_DIR = _WEAPONS_DIR.parent
_REPO_ROOT = _SECTION_9_DIR.parent
_DEFAULT_HEARTBEAT = _SECTION_9_DIR / "operations" / "heartbeat.json"
_DEFAULT_LOG = _SECTION_9_DIR / "operations" / "LOG.md"


def _sim_print(msg: str, live: bool) -> None:
    """Print a message with simulation/live prefix."""
    prefix = "[LOCKDOWN]" if live else "[LOCKDOWN-SIM]"
    print(f"{prefix} {msg}")


def write_lockdown_status(
    heartbeat_path: Path,
    live: bool = False,
) -> None:
    """Write LOCKDOWN status to heartbeat file."""
    _sim_print("Writing LOCKDOWN status to heartbeat.json", live)
    if not live:
        return
    try:
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "threats_hash": "",
            "status": "LOCKDOWN",
            "sequence": -1,
        }
        heartbeat_path.write_text(json.dumps(status, indent=2))
    except (OSError, IOError) as e:
        _sim_print(f"WARNING: Failed to write lockdown status: {e}", live)


def create_snapshot_hash(
    repo_path: Path,
    live: bool = False,
) -> str:
    """Create a SHA256 hash of all tracked files in the repo.

    Does NOT create an actual tar archive (too slow and large
    for emergency lockdown). Instead, hashes the concatenation
    of all file hashes for a fast cryptographic proof of state.
    """
    _sim_print(f"Computing cryptographic snapshot of {repo_path}", live)

    file_hashes: list[str] = []
    try:
        for fpath in sorted(repo_path.rglob("*")):
            if fpath.is_file() and ".git" not in fpath.parts:
                try:
                    content = fpath.read_bytes()
                    h = hashlib.sha256(content).hexdigest()
                    rel = str(fpath.relative_to(repo_path))
                    file_hashes.append(f"{rel}:{h}")
                except (OSError, IOError):
                    continue
    except (OSError, IOError):
        pass

    combined = "\n".join(file_hashes)
    snapshot_hash = hashlib.sha256(combined.encode()).hexdigest()

    _sim_print(f"Snapshot hash: {snapshot_hash}", live)
    _sim_print(f"Files hashed: {len(file_hashes)}", live)
    return snapshot_hash


def log_lockdown(
    snapshot_hash: str,
    log_path: Path,
    live: bool = False,
) -> None:
    """Append lockdown entry to operations log."""
    _sim_print("Logging lockdown to operations/LOG.md", live)
    if not live:
        return
    try:
        entry = (
            "\n\n"
            "═══════════════════════════════════════════════════════════\n"
            "AUTOMATED ACTION: DEAD MAN'S SWITCH ACTIVATION\n"
            f"DATE: {datetime.now(timezone.utc).isoformat()}\n"
            "TRIGGER: 6+ missed heartbeats (72+ hours silence)\n"
            f"SNAPSHOT HASH: {snapshot_hash}\n"
            "ACTION: System lockdown initiated\n"
            "RECOVERY: Crown or Director must authenticate to stand down\n"
            "STATUS: ACTIVE\n"
            "═══════════════════════════════════════════════════════════\n"
        )
        with open(str(log_path), "a") as f:  # noqa: S104
            f.write(entry)
    except (OSError, IOError) as e:
        _sim_print(f"WARNING: Failed to log lockdown: {e}", live)


def write_lockdown_notice(
    snapshot_hash: str,
    repo_path: Path,
    live: bool = False,
) -> None:
    """Write a lockdown notice file to the repo root."""
    notice_path = repo_path / "LOCKDOWN_NOTICE.json"
    _sim_print(f"Writing lockdown notice to {notice_path}", live)
    if not live:
        return
    try:
        notice = {
            "status": "LOCKDOWN",
            "activated": datetime.now(timezone.utc).isoformat(),
            "trigger": "Dead Man's Switch — Crown/Director unreachable",
            "snapshot_hash": snapshot_hash,
            "recovery": "Crown or Director must authenticate to stand down",
            "weapon": "S9-W-006",
        }
        notice_path.write_text(json.dumps(notice, indent=2))
    except (OSError, IOError) as e:
        _sim_print(f"WARNING: Failed to write notice: {e}", live)


def execute_lockdown(
    repo_path: Optional[Path] = None,
    heartbeat_path: Optional[Path] = None,
    log_path: Optional[Path] = None,
    live: bool = False,
) -> dict:
    """Execute the full lockdown sequence.

    Returns a summary of actions taken (or simulated).
    """
    if repo_path is None:
        repo_path = _REPO_ROOT
    if heartbeat_path is None:
        heartbeat_path = _DEFAULT_HEARTBEAT
    if log_path is None:
        log_path = _DEFAULT_LOG

    mode = "LIVE" if live else "SIMULATION"
    _sim_print(f"=== LOCKDOWN SEQUENCE — {mode} ===", live)

    # Step 1: Write LOCKDOWN status
    write_lockdown_status(heartbeat_path, live)

    # Step 2: Create cryptographic snapshot
    snapshot_hash = create_snapshot_hash(repo_path, live)

    # Step 3: Log the lockdown
    log_lockdown(snapshot_hash, log_path, live)

    # Step 4: Write lockdown notice
    write_lockdown_notice(snapshot_hash, repo_path, live)

    _sim_print(f"=== LOCKDOWN SEQUENCE {mode} COMPLETE ===", live)

    return {
        "weapon": "S9-W-006",
        "component": "lockdown",
        "mode": mode.lower(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "snapshot_hash": snapshot_hash,
        "actions": [
            "write_lockdown_status",
            "create_snapshot_hash",
            "log_lockdown",
            "write_lockdown_notice",
        ],
        "live": live,
    }


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    live = False
    repo_path: Optional[Path] = None

    while args:
        flag = args.pop(0)
        if flag == "--live":
            live = True
        elif flag == "--repo-path" and args:
            repo_path = Path(args.pop(0))

    result = execute_lockdown(repo_path=repo_path, live=live)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
