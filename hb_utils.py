"""
House Bernard — Shared Utilities
Common functions used across treasury, splicer, airlock, ledger, and guild.

Centralizes:
  - Datetime helpers (_now, _parse_dt, _format_dt, _months_between)
  - Atomic file I/O (atomic_save)

Existing code still uses local copies (not a breaking change).
New code should import from hb_utils.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _now():
    """Current UTC datetime."""
    return datetime.now(timezone.utc)


def _parse_dt(s):
    """Parse ISO 8601 datetime string, handling Z and +00:00 suffixes."""
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _format_dt(dt):
    """Format datetime as ISO 8601 with Z suffix."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _months_between(start, end):
    """Approximate months between two datetimes (30.44-day months)."""
    delta = end - start
    return max(0, delta.days / 30.44)


def atomic_save(data, path):
    """
    Atomic JSON write with backup.

    1. Creates backup (.bak) if file already exists
    2. Writes to tempfile in same directory
    3. Atomically replaces target via os.replace()

    Crash-safe: if interrupted mid-write, original file is intact.
    """
    path = Path(path)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp", prefix="hb_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
