"""Agent health monitoring.

AchillesRun calls check_health() periodically.  If any sub-agent has
not sent a heartbeat within HEARTBEAT_TIMEOUT_S, it is marked as down.
If the agent has been down longer than ESCALATION_TIMEOUT_S, an
emergency message is sent to the Crown.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from .. import config
from ..database import get_db
from . import message_bus

AGENTS = ("warden", "treasurer", "magistrate")


def check_health() -> List[Dict]:
    """Return health status for all sub-agents.  Escalate if needed."""
    results = []
    now = datetime.now(timezone.utc)

    with get_db() as conn:
        for name in AGENTS:
            row = conn.execute(
                "SELECT created_at FROM agent_messages "
                "WHERE from_agent = ? AND message_type = 'heartbeat' "
                "ORDER BY created_at DESC LIMIT 1",
                (name,),
            ).fetchone()

            if not row:
                results.append({"agent": name, "status": "never_seen", "age_s": None})
                continue

            last = datetime.fromisoformat(row["created_at"])
            age = (now - last).total_seconds()

            if age < config.HEARTBEAT_TIMEOUT_S:
                status = "online"
            elif age < config.ESCALATION_TIMEOUT_S:
                status = "stale"
            else:
                status = "down"
                # Escalate to Crown
                message_bus.send(
                    "achillesrun", "crown", "alert",
                    {"agent": name, "age_s": age,
                     "message": f"{name} has been unresponsive for {int(age)}s"},
                    priority="emergency",
                )

            results.append({"agent": name, "status": status, "age_s": age})

    return results
