#!/usr/bin/env python3
"""
S9-W-006: Dead Man's Switch — Heartbeat Monitor
Classification: CROWN EYES ONLY
Class IV (Scorched Earth)

Checks the heartbeat file and counts missed heartbeats.
Alert thresholds:
  3 missed: WARNING  — log to operations/LOG.md
  5 missed: CRITICAL — write alert file
  6 missed: ACTIVATION — trigger lockdown sequence

Fails safely: any error = no activation. Never triggers
lockdown on error conditions.

Usage:
    python3 S9-W-006_monitor.py
    python3 S9-W-006_monitor.py --heartbeat-path /custom/path.json
    python3 S9-W-006_monitor.py --check-only
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


# Default paths
_WEAPONS_DIR = Path(__file__).resolve().parent
_SECTION_9_DIR = _WEAPONS_DIR.parent
_DEFAULT_HEARTBEAT = _SECTION_9_DIR / "operations" / "heartbeat.json"
_DEFAULT_LOG = _SECTION_9_DIR / "operations" / "LOG.md"
_DEFAULT_ALERT = _SECTION_9_DIR / "operations" / "ALERT_CRITICAL.json"

# Configuration
HEARTBEAT_INTERVAL_HOURS: int = 12
GRACE_HOURS: int = 1  # 13 hours total before counting a miss
WARNING_THRESHOLD: int = 3
CRITICAL_THRESHOLD: int = 5
ACTIVATION_THRESHOLD: int = 6


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    """Parse ISO 8601 timestamp. Returns None on failure."""
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def read_heartbeat(heartbeat_path: Optional[Path] = None) -> Optional[dict]:
    """Read and parse the heartbeat file. Returns None on any error."""
    if heartbeat_path is None:
        heartbeat_path = _DEFAULT_HEARTBEAT
    try:
        data = json.loads(heartbeat_path.read_text())
        if not isinstance(data, dict):
            return None
        if "timestamp" not in data:
            return None
        return data
    except (OSError, IOError, json.JSONDecodeError, TypeError):
        return None


def count_missed_heartbeats(
    heartbeat_data: Optional[dict],
    now: Optional[datetime] = None,
) -> int:
    """Count how many heartbeats have been missed.

    Returns 0 if heartbeat is current or missing (never started).
    Missing heartbeat = "never started", not "missed".
    """
    if heartbeat_data is None:
        # No heartbeat file = system never started. Not a miss.
        return 0

    if now is None:
        now = datetime.now(timezone.utc)

    ts = _parse_timestamp(heartbeat_data.get("timestamp", ""))
    if ts is None:
        # Malformed timestamp — not a miss, it's corruption
        return 0

    # Ensure timezone-aware comparison
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age = now - ts
    interval = timedelta(hours=HEARTBEAT_INTERVAL_HOURS + GRACE_HOURS)

    if age <= interval:
        return 0  # Heartbeat is current

    # Count missed intervals
    missed = int(age / timedelta(hours=HEARTBEAT_INTERVAL_HOURS))
    return missed


def check_status(
    heartbeat_path: Optional[Path] = None,
    now: Optional[datetime] = None,
) -> dict:
    """Check heartbeat status and return a status report."""
    heartbeat = read_heartbeat(heartbeat_path)
    missed = count_missed_heartbeats(heartbeat, now)

    if missed >= ACTIVATION_THRESHOLD:
        level = "ACTIVATION"
    elif missed >= CRITICAL_THRESHOLD:
        level = "CRITICAL"
    elif missed >= WARNING_THRESHOLD:
        level = "WARNING"
    elif missed > 0:
        level = "STALE"
    elif heartbeat is None:
        level = "NO_HEARTBEAT"
    else:
        level = "OK"

    return {
        "weapon": "S9-W-006",
        "component": "monitor",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "heartbeat_present": heartbeat is not None,
        "heartbeat_timestamp": heartbeat.get("timestamp") if heartbeat else None,
        "heartbeat_sequence": heartbeat.get("sequence") if heartbeat else None,
        "heartbeat_status": heartbeat.get("status") if heartbeat else None,
        "missed_heartbeats": missed,
        "level": level,
        "thresholds": {
            "warning": WARNING_THRESHOLD,
            "critical": CRITICAL_THRESHOLD,
            "activation": ACTIVATION_THRESHOLD,
        },
    }


def write_warning_log(
    status: dict,
    log_path: Optional[Path] = None,
) -> None:
    """Append a warning to the operations log."""
    if log_path is None:
        log_path = _DEFAULT_LOG
    try:
        entry = (
            "\n\n"
            "═══════════════════════════════════════════════════════════\n"
            f"AUTOMATED ALERT: Dead Man's Switch — {status['level']}\n"
            f"DATE: {status['timestamp']}\n"
            f"MISSED HEARTBEATS: {status['missed_heartbeats']}\n"
            f"LAST HEARTBEAT: {status.get('heartbeat_timestamp', 'NONE')}\n"
            f"SEQUENCE: {status.get('heartbeat_sequence', 'NONE')}\n"
            "ACTION: Monitoring continues. Crown should send heartbeat.\n"
            "═══════════════════════════════════════════════════════════\n"
        )
        with open(str(log_path), "a") as f:  # noqa: S104
            f.write(entry)
    except (OSError, IOError):
        pass  # Fail to passive


def write_critical_alert(
    status: dict,
    alert_path: Optional[Path] = None,
) -> None:
    """Write a critical alert file."""
    if alert_path is None:
        alert_path = _DEFAULT_ALERT
    try:
        alert_path.parent.mkdir(parents=True, exist_ok=True)
        alert_path.write_text(json.dumps(status, indent=2))
    except (OSError, IOError):
        pass  # Fail to passive


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    heartbeat_path: Optional[Path] = None
    check_only = False

    while args:
        flag = args.pop(0)
        if flag == "--heartbeat-path" and args:
            heartbeat_path = Path(args.pop(0))
        elif flag == "--check-only":
            check_only = True

    status = check_status(heartbeat_path)
    print(json.dumps(status, indent=2))

    if check_only:
        return

    level = status["level"]

    if level == "WARNING":
        write_warning_log(status)
        print("[MONITOR] WARNING logged to operations/LOG.md", file=sys.stderr)

    elif level == "CRITICAL":
        write_warning_log(status)
        write_critical_alert(status)
        print("[MONITOR] CRITICAL alert written", file=sys.stderr)

    elif level == "ACTIVATION":
        write_warning_log(status)
        write_critical_alert(status)
        print("[MONITOR] ACTIVATION threshold reached!", file=sys.stderr)
        print("[MONITOR] Lockdown sequence should be triggered.", file=sys.stderr)
        # In production, this would call S9-W-006_lockdown.py --live
        # For safety, we only report — the cron or supervisor handles activation


if __name__ == "__main__":
    main()
