"""AchillesRun — Steward / Delegation Engine.

AchillesRun is the sovereign agent.  He receives all incoming requests
and delegates to the right sub-agent.  He does NOT do the work himself.

Delegation rules (from spec):
  Event                      → Delegated To      → Escalate If
  New artifact submitted     → Warden             → Warden unresponsive > 5 min
  Artifact survives T4       → Treasurer           → Payment > 1% of supply
  Guild dispute filed        → Magistrate          → Constitutional question
  Security alert             → Warden             → Severity >= HIGH
  Royalty payment due        → Treasurer           → Insufficient treasury balance
  Brief claimed              → AchillesRun (self) → —
  Forum moderation           → Magistrate          → Citizen appeals
  Heartbeat timeout          → Crown              → Any agent down > 15 min
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict

from .. import config
from ..database import get_db
from . import heartbeat as heartbeat_mod
from . import message_bus

AGENT_NAME = "achillesrun"

# ── Delegation map ─────────────────────────────────

DELEGATION: Dict[str, str] = {
    "evaluate_artifact":  "warden",
    "security_alert":     "warden",
    "revoke_access":      "warden",
    "compute_royalty":    "treasurer",
    "process_payment":    "treasurer",
    "resolve_dispute":    "magistrate",
    "moderate_post":      "magistrate",
    "ban_citizen":        "magistrate",
}


def delegate(action: str, payload: Dict[str, Any],
             priority: str = "normal") -> int | None:
    """Route a task to the appropriate sub-agent.  Returns message id."""
    target = DELEGATION.get(action)
    if not target:
        return None
    payload["action"] = action
    return message_bus.send(AGENT_NAME, target, "task", payload, priority)


def on_artifact_submitted(artifact_hash: str, citizen_id: str,
                          brief_id: str | None = None) -> int:
    """A new artifact has entered the inbox.  Delegate to Warden."""
    return delegate("evaluate_artifact", {
        "artifact_hash": artifact_hash,
        "citizen_id": citizen_id,
        "brief_id": brief_id,
    })


def on_artifact_survived(artifact_hash: str, citizen_id: str) -> int:
    """An artifact survived T4.  Delegate royalty computation to Treasurer."""
    return delegate("compute_royalty", {
        "artifact_hash": artifact_hash,
        "citizen_id": citizen_id,
    })


def on_dispute_filed(dispute_id: str, guild_id: str) -> int:
    """A guild dispute has been filed.  Delegate to Magistrate."""
    return delegate("resolve_dispute", {
        "dispute_id": dispute_id,
        "guild_id": guild_id,
    })


def _process_response(msg: Dict[str, Any]) -> None:
    """Handle a response from a sub-agent."""
    payload = json.loads(msg["payload"]) if isinstance(msg["payload"], str) else msg["payload"]
    action = payload.get("action", "")

    # If an artifact was evaluated, check the result
    if action == "evaluate_artifact" and payload.get("status") == "survived":
        on_artifact_survived(payload["artifact_hash"], payload["citizen_id"])

    # Post status updates to the Announcements forum topic
    _post_agent_update(action, payload)


def _post_agent_update(action: str, payload: Dict[str, Any]) -> None:
    """Post a status update to the forum (Announcements topic, id=2)."""
    summary = f"[{AGENT_NAME}] {action}: {json.dumps(payload, default=str)}"
    now = datetime.now(timezone.utc).isoformat()
    try:
        with get_db() as conn:
            # Find or create the status thread
            thread = conn.execute(
                "SELECT id FROM forum_threads "
                "WHERE topic_id = 2 AND title = 'Agent Status Updates' LIMIT 1"
            ).fetchone()
            if not thread:
                cur = conn.execute(
                    "INSERT INTO forum_threads (topic_id, title, author_id, created_at) "
                    "VALUES (2, 'Agent Status Updates', 'SYSTEM', ?)", (now,)
                )
                # Ensure SYSTEM citizen exists
                conn.execute(
                    "INSERT OR IGNORE INTO citizens (id, alias, tier, joined_at) "
                    "VALUES ('SYSTEM', 'AchillesRun', 'invariant', ?)", (now,)
                )
                thread_id = cur.lastrowid
            else:
                thread_id = thread["id"]
            conn.execute(
                "INSERT INTO forum_posts (thread_id, author_id, body, created_at, is_agent) "
                "VALUES (?, 'SYSTEM', ?, ?, 1)",
                (thread_id, summary, now),
            )
    except Exception:
        pass  # Forum updates are best-effort


def run_loop() -> None:
    """Main steward loop.

    1. Heartbeat
    2. Check sub-agent health
    3. Process incoming messages (responses, alerts)
    4. Monitor inbox for new submissions (filesystem)
    5. Sleep
    """
    while True:
        message_bus.heartbeat(AGENT_NAME)

        # Check sub-agent health
        heartbeat_mod.check_health()

        # Process messages addressed to achillesrun
        messages = message_bus.poll(AGENT_NAME)
        for msg in messages:
            msg_type = msg.get("message_type", "")
            if msg_type == "response":
                _process_response(msg)
            elif msg_type == "alert":
                payload = json.loads(msg["payload"]) if isinstance(msg["payload"], str) else msg["payload"]
                severity = payload.get("severity", "low")
                if severity in ("high", "emergency"):
                    delegate("security_alert", payload, priority="high")
            # heartbeat messages from sub-agents are just informational
            message_bus.ack(msg["id"])

        time.sleep(5)
