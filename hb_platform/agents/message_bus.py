"""SQLite-backed message bus for inter-agent communication.

Every agent polls this bus for tasks addressed to it, processes them,
and posts responses.  AchillesRun monitors all messages read-only for
situational awareness but does not bottleneck the flow.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..database import get_db


def send(from_agent: str, to_agent: str, message_type: str,
         payload: Dict[str, Any], priority: str = "normal") -> int:
    """Post a message onto the bus.  Returns the message id."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO agent_messages "
            "(from_agent, to_agent, message_type, payload, priority, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
            (from_agent, to_agent, message_type, json.dumps(payload), priority, now),
        )
        return cur.lastrowid


def poll(agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch pending messages for *agent_name*, oldest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_messages "
            "WHERE to_agent = ? AND status = 'pending' "
            "ORDER BY "
            "  CASE priority "
            "    WHEN 'emergency' THEN 0 "
            "    WHEN 'high'      THEN 1 "
            "    WHEN 'normal'    THEN 2 "
            "    WHEN 'low'       THEN 3 "
            "  END, created_at "
            "LIMIT ?",
            (agent_name, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def ack(message_id: int, status: str = "completed") -> None:
    """Mark a message as processed."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "UPDATE agent_messages SET status = ?, processed_at = ? WHERE id = ?",
            (status, now, message_id),
        )


def respond(original_id: int, from_agent: str, payload: Dict[str, Any]) -> int:
    """Send a response to the sender of *original_id*."""
    with get_db() as conn:
        orig = conn.execute(
            "SELECT from_agent FROM agent_messages WHERE id = ?", (original_id,)
        ).fetchone()
    if not orig:
        raise ValueError(f"No message with id {original_id}")
    return send(from_agent, orig["from_agent"], "response", payload)


def heartbeat(agent_name: str) -> int:
    """Record a heartbeat for an agent."""
    return send(agent_name, "achillesrun", "heartbeat",
                {"agent": agent_name, "status": "alive"})


def recent(limit: int = 50) -> List[Dict[str, Any]]:
    """Return the most recent messages (for monitoring)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM agent_messages ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
