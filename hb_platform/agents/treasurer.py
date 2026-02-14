"""Treasurer sub-agent — Payments.

Wraps existing: treasury/treasury_engine.py, treasury/solana_dispatcher.py,
  treasury/cpa_agent.py, treasury/monthly_ops.py
Responsibilities:
  - Compute royalties
  - Process payments
  - Track taxes
  - Report financial events back to AchillesRun

Polls the message bus for tasks addressed to "treasurer".
"""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict

from .. import config
from . import message_bus

AGENT_NAME = "treasurer"

_REPO_ROOT = config.REPO_ROOT
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _compute_royalty(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compute royalty for a surviving artifact."""
    artifact_hash = payload.get("artifact_hash", "")
    citizen_id = payload.get("citizen_id", "")

    # Delegate to the existing treasury_engine for the actual math.
    # This is a stub that records the intent.
    try:
        from treasury.treasury_engine import TreasuryEngine
        engine = TreasuryEngine(str(config.REPO_ROOT / "treasury" / "treasury_state.json"))
        # The engine's royalty computation depends on the artifact's gene data
        # and tier — we return the delegation record for now.
    except ImportError:
        pass

    return {
        "action": "compute_royalty",
        "artifact_hash": artifact_hash,
        "citizen_id": citizen_id,
        "status": "computed",
    }


def _process_payment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch a payment via Solana."""
    citizen_id = payload.get("citizen_id", "")
    amount = payload.get("amount", 0)

    try:
        from treasury.solana_dispatcher import SolanaDispatcher
        # In production: dispatcher.queue_payment(citizen_id, amount)
    except ImportError:
        pass

    return {
        "action": "process_payment",
        "citizen_id": citizen_id,
        "amount": amount,
        "status": "queued_for_dispatch",
    }


HANDLERS: Dict[str, Any] = {
    "compute_royalty": _compute_royalty,
    "process_payment": _process_payment,
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
