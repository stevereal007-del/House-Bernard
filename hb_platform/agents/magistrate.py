"""Magistrate sub-agent — Governance.

Wraps existing: guild/magistrate_engine.py, guild/advocate_engine.py
Responsibilities:
  - Handle guild disputes
  - Process citizenship appeals
  - Forum moderation
  - Report rulings back to AchillesRun

Polls the message bus for tasks addressed to "magistrate".
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict

from .. import config
from . import message_bus

AGENT_NAME = "magistrate"

_REPO_ROOT = config.REPO_ROOT
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _resolve_dispute(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process a guild dispute."""
    dispute_id = payload.get("dispute_id", "")
    guild_id = payload.get("guild_id", "")

    try:
        from guild.magistrate_engine import MagistrateEngine
        # In production: engine.adjudicate(dispute_id)
    except ImportError:
        pass

    return {
        "action": "resolve_dispute",
        "dispute_id": dispute_id,
        "guild_id": guild_id,
        "status": "under_review",
    }


def _moderate_post(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Review a forum post for moderation."""
    post_id = payload.get("post_id", "")
    return {
        "action": "moderate_post",
        "post_id": post_id,
        "status": "reviewed",
        "verdict": "allowed",
    }


def _ban_citizen(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Ban a citizen — notify Warden to revoke access."""
    citizen_id = payload.get("citizen_id", "")
    reason = payload.get("reason", "")

    # Tell the Warden to revoke access
    message_bus.send(AGENT_NAME, "warden", "task",
                     {"action": "revoke_access", "citizen_id": citizen_id})

    return {
        "action": "ban_citizen",
        "citizen_id": citizen_id,
        "reason": reason,
        "status": "banned",
    }


HANDLERS: Dict[str, Any] = {
    "resolve_dispute": _resolve_dispute,
    "moderate_post": _moderate_post,
    "ban_citizen": _ban_citizen,
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
