"""Warden sub-agent — Security.

Wraps existing: airlock/airlock_monitor.py
Responsibilities:
  - Process artifact submissions end-to-end
  - Run security scanning
  - Report verdicts back to AchillesRun

Polls the message bus for tasks addressed to "warden".
"""
from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

from .. import config
from . import message_bus

AGENT_NAME = "warden"

# Add repo root to path so we can import the airlock module
_REPO_ROOT = config.REPO_ROOT
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _evaluate_artifact(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run security checks on an artifact.  Returns verdict payload."""
    artifact_hash = payload.get("artifact_hash", "")
    citizen_id = payload.get("citizen_id", "")

    # The airlock_monitor handles the real scanning pipeline.
    # Here we record the attempt and delegate.
    from ..database import get_db
    with get_db() as conn:
        conn.execute(
            "UPDATE submissions SET status = 'testing' "
            "WHERE artifact_hash = ? AND citizen_id = ? AND status = 'queued'",
            (artifact_hash, citizen_id),
        )

    # In production, the airlock_monitor.py watches the inbox dir and
    # triggers the executioner.  This stub records the delegation.
    return {
        "action": "evaluate_artifact",
        "artifact_hash": artifact_hash,
        "citizen_id": citizen_id,
        "status": "delegated_to_airlock",
    }


def _revoke_access(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Revoke a citizen's access (e.g. after ban from Magistrate)."""
    citizen_id = payload.get("citizen_id", "")
    from ..database import get_db
    with get_db() as conn:
        conn.execute(
            "DELETE FROM citizen_secrets WHERE citizen_id = ?", (citizen_id,)
        )
    return {"action": "revoke_access", "citizen_id": citizen_id, "status": "revoked"}


HANDLERS: Dict[str, Any] = {
    "evaluate_artifact": _evaluate_artifact,
    "revoke_access": _revoke_access,
}


def process_one(msg: Dict[str, Any]) -> None:
    """Process a single message from the bus."""
    payload = json.loads(msg["payload"]) if isinstance(msg["payload"], str) else msg["payload"]
    action = payload.get("action", "")
    handler = HANDLERS.get(action)

    if handler:
        result = handler(payload)
        message_bus.respond(msg["id"], AGENT_NAME, result)
        message_bus.ack(msg["id"], "completed")
    else:
        message_bus.ack(msg["id"], "failed")
        message_bus.respond(msg["id"], AGENT_NAME,
                            {"error": f"unknown action: {action}"})


def run_loop() -> None:
    """Main agent loop — poll, process, heartbeat."""
    while True:
        message_bus.heartbeat(AGENT_NAME)
        messages = message_bus.poll(AGENT_NAME)
        for msg in messages:
            process_one(msg)
        time.sleep(5)
