#!/usr/bin/env python3
"""Initialize the sanctum event ledger and workspace memory files."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

SANCTUM = Path(os.path.expanduser("~/.openclaw/agents/achillesrun/workspace/sanctum"))


def init_sanctum() -> None:
    """Create initial sanctum files if they don't exist."""
    SANCTUM.mkdir(parents=True, exist_ok=True)

    ledger = SANCTUM / "EVENT_LEDGER.jsonl"
    if not ledger.exists():
        entry = {
            "event": "sanctum_initialized",
            "agent": "AchillesRun",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Append-only event ledger created. Department of Continuity active.",
        }
        ledger.write_text(json.dumps(entry) + "\n")
        print(f"  Created: {ledger}")
    else:
        print(f"  Exists: {ledger}")

    decisions = SANCTUM / "DECISIONS.md"
    if not decisions.exists():
        decisions.write_text(
            "# AchillesRun Decision Log\n\n"
            "Append-only. One entry per decision that affects state.\n\n"
            "---\n"
        )
        print(f"  Created: {decisions}")
    else:
        print(f"  Exists: {decisions}")


if __name__ == "__main__":
    init_sanctum()
    print("Sanctum initialized.")
