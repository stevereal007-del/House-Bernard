"""
House Bernard Shared Utilities v1.0
Common functions used across all engines.
Single source of truth for datetime handling and atomic I/O.
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def now() -> datetime:
    """Current UTC time, timezone-aware."""
    return datetime.now(timezone.utc)


def parse_dt(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 datetime string to timezone-aware datetime."""
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def format_dt(dt: datetime) -> str:
    """Format datetime as ISO 8601 UTC string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def months_between(start: datetime, end: datetime) -> float:
    """Approximate months between two datetimes."""
    return max(0, (end - start).days / 30.44)


def days_between(start: datetime, end: datetime) -> float:
    """Days between two datetimes."""
    return max(0, (end - start).days)


def atomic_save(data: dict, path: Path, prefix: str = "hb_") -> None:
    """Atomic JSON write with backup. Crash-safe."""
    path = Path(path)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, suffix=".tmp", prefix=prefix
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=False)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def load_json(path: Path) -> dict:
    """Load JSON file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
