#!/usr/bin/env python3
"""
CAA — Continuity Service (Heartbeat Challenge-Response)
Authority: CAA Specification v1.0, Part II Section 1
Classification: CROWN EYES ONLY / ISD DIRECTOR

Implements the heartbeat challenge-response protocol. Every agent
deployed outside core infrastructure maintains a heartbeat connection
to this service. Challenges are derived from the agent's encrypted
operational layer. Two consecutive failures trigger Compromise Protocol.

Dead-heartbeat trigger: if no heartbeat attempt is possible for a
duration exceeding twice the normal interval, the agent enters
Compromise Protocol regardless of challenge issuance.

Usage:
    from caa.continuity_service import ContinuityService
    svc = ContinuityService()
    challenge = svc.issue_challenge("agent-001", "SES-abc123")
    result = svc.validate_response("agent-001", "SES-abc123", response)
"""

from __future__ import annotations

import json
import uuid
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from caa.compartments import get_heartbeat_config


# ── Configuration ────────────────────────────────────────────────

CHALLENGE_EXPIRY_SECONDS = 120   # challenges expire in 2 minutes
DEAD_HEARTBEAT_MULTIPLIER = 2    # 2x normal interval = dead heartbeat


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if s is None:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _generate_challenge_seed() -> str:
    """Generate a random challenge seed."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def _compute_expected_response(seed: str, agent_secret: str) -> str:
    """
    Compute expected response using HMAC-SHA256.
    In production, the agent_secret comes from the encrypted
    operational layer. Here we model the computation.
    """
    return hmac.new(
        agent_secret.encode(),
        seed.encode(),
        hashlib.sha256,
    ).hexdigest()


# ── Continuity Service ───────────────────────────────────────────

class ContinuityService:
    """
    Heartbeat challenge-response service for agent continuity monitoring.

    Tracks heartbeat status per agent, issues challenges, validates
    responses, and detects anomalies (missed heartbeats, unexpected
    network locations, dead-heartbeat conditions).
    """

    def __init__(self) -> None:
        self.agent_records: Dict[str, Dict[str, Any]] = {}
        self.pending_challenges: Dict[str, Dict[str, Any]] = {}
        self.agent_secrets: Dict[str, str] = {}
        self.event_log: List[Dict[str, Any]] = []

    # ── Agent registration ───────────────────────────────────

    def register_agent(
        self,
        agent_id: str,
        role: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Register an agent for heartbeat monitoring. Called at
        session initialization. Generates a session-scoped secret
        for challenge-response.
        """
        hb_config = get_heartbeat_config(role)
        if "error" in hb_config:
            return hb_config

        secret = _generate_challenge_seed()
        self.agent_secrets[agent_id] = secret

        now = _now()
        record = {
            "agent_id": agent_id,
            "role": role,
            "session_id": session_id,
            "registered_at": _format_dt(now),
            "heartbeat_interval_seconds": hb_config["interval_seconds"],
            "miss_threshold": hb_config["miss_threshold"],
            "consecutive_misses": 0,
            "total_heartbeats": 0,
            "last_heartbeat_at": None,
            "last_challenge_at": None,
            "status": "active",
            "compromise_triggered": False,
        }
        self.agent_records[agent_id] = record

        self._log_event("agent_registered", agent_id, session_id)

        return {
            "registered": True,
            "agent_id": agent_id,
            "heartbeat_interval_seconds": hb_config["interval_seconds"],
            "miss_threshold": hb_config["miss_threshold"],
            "secret_hash": hashlib.sha256(secret.encode()).hexdigest(),
        }

    def deregister_agent(self, agent_id: str) -> Dict[str, Any]:
        """Deregister an agent from heartbeat monitoring (session end)."""
        if agent_id not in self.agent_records:
            return {"error": "agent_not_registered"}

        record = self.agent_records.pop(agent_id)
        self.agent_secrets.pop(agent_id, None)
        self.pending_challenges.pop(agent_id, None)

        self._log_event("agent_deregistered", agent_id,
                         record.get("session_id", "unknown"))

        return {
            "deregistered": True,
            "agent_id": agent_id,
            "total_heartbeats": record.get("total_heartbeats", 0),
        }

    # ── Challenge issuance ───────────────────────────────────

    def issue_challenge(
        self,
        agent_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Issue a heartbeat challenge to an agent. The challenge
        seed is derived from the agent's session secret. The agent
        must respond with the correct HMAC within the expiry window.
        """
        record = self.agent_records.get(agent_id)
        if record is None:
            return {"error": "agent_not_registered"}

        if record.get("session_id") != session_id:
            return {"error": "session_mismatch"}

        if record.get("compromise_triggered"):
            return {"error": "agent_compromise_active"}

        seed = _generate_challenge_seed()
        now = _now()

        challenge = {
            "challenge_id": _generate_id("CHG"),
            "agent_id": agent_id,
            "seed": seed,
            "issued_at": _format_dt(now),
            "expires_at": _format_dt(
                now + timedelta(seconds=CHALLENGE_EXPIRY_SECONDS)
            ),
        }
        self.pending_challenges[agent_id] = challenge
        record["last_challenge_at"] = _format_dt(now)

        return {
            "challenge_id": challenge["challenge_id"],
            "seed": seed,
            "expires_in_seconds": CHALLENGE_EXPIRY_SECONDS,
        }

    # ── Response validation ──────────────────────────────────

    def validate_response(
        self,
        agent_id: str,
        session_id: str,
        response: str,
    ) -> Dict[str, Any]:
        """
        Validate an agent's heartbeat response. Returns pass/fail
        and updates consecutive miss counter. Two consecutive misses
        (or one for Section 9) triggers compromise detection.
        """
        record = self.agent_records.get(agent_id)
        if record is None:
            return {"error": "agent_not_registered"}

        if record.get("session_id") != session_id:
            return {"error": "session_mismatch"}

        challenge = self.pending_challenges.get(agent_id)
        if challenge is None:
            return {"error": "no_pending_challenge"}

        now = _now()
        expires = _parse_dt(challenge.get("expires_at"))
        if expires is not None and now >= expires:
            record["consecutive_misses"] += 1
            self.pending_challenges.pop(agent_id, None)
            return self._evaluate_misses(agent_id, "challenge_expired")

        secret = self.agent_secrets.get(agent_id, "")
        expected = _compute_expected_response(challenge["seed"], secret)

        self.pending_challenges.pop(agent_id, None)

        if not hmac.compare_digest(response, expected):
            record["consecutive_misses"] += 1
            return self._evaluate_misses(agent_id, "wrong_response")

        record["consecutive_misses"] = 0
        record["total_heartbeats"] += 1
        record["last_heartbeat_at"] = _format_dt(now)

        self._log_event("heartbeat_success", agent_id, session_id)

        return {
            "valid": True,
            "agent_id": agent_id,
            "heartbeat_number": record["total_heartbeats"],
            "consecutive_misses": 0,
        }

    def _evaluate_misses(
        self,
        agent_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Evaluate consecutive misses against threshold."""
        record = self.agent_records[agent_id]
        misses = record["consecutive_misses"]
        threshold = record["miss_threshold"]

        self._log_event(
            "heartbeat_miss",
            agent_id,
            record.get("session_id", "unknown"),
            f"miss #{misses}, threshold={threshold}, reason={reason}",
        )

        if misses >= threshold:
            record["compromise_triggered"] = True
            record["status"] = "compromise_detected"
            self._log_event(
                "compromise_triggered",
                agent_id,
                record.get("session_id", "unknown"),
                f"consecutive misses ({misses}) >= threshold ({threshold})",
            )
            return {
                "valid": False,
                "agent_id": agent_id,
                "compromise_triggered": True,
                "consecutive_misses": misses,
                "threshold": threshold,
                "reason": reason,
            }

        return {
            "valid": False,
            "agent_id": agent_id,
            "compromise_triggered": False,
            "consecutive_misses": misses,
            "threshold": threshold,
            "reason": reason,
        }

    # ── Dead-heartbeat detection ─────────────────────────────

    def check_dead_heartbeats(self) -> Dict[str, Any]:
        """
        Check all registered agents for dead-heartbeat condition.
        If no heartbeat attempt for 2x the normal interval, the
        agent is treated as potentially compromised.

        Run periodically by the infrastructure cron.
        """
        now = _now()
        dead_agents: List[Dict[str, Any]] = []

        for agent_id, record in self.agent_records.items():
            if record.get("compromise_triggered"):
                continue
            if record.get("status") != "active":
                continue

            interval = record.get("heartbeat_interval_seconds", 900)
            threshold = timedelta(
                seconds=interval * DEAD_HEARTBEAT_MULTIPLIER
            )

            last_hb = _parse_dt(record.get("last_heartbeat_at"))
            registered = _parse_dt(record.get("registered_at"))
            reference = last_hb or registered

            if reference is None:
                continue

            silence = now - reference
            if silence > threshold:
                record["compromise_triggered"] = True
                record["status"] = "dead_heartbeat"
                dead_agents.append({
                    "agent_id": agent_id,
                    "role": record.get("role"),
                    "silence_seconds": int(silence.total_seconds()),
                    "threshold_seconds": int(threshold.total_seconds()),
                    "last_heartbeat": record.get("last_heartbeat_at"),
                })
                self._log_event(
                    "dead_heartbeat_triggered",
                    agent_id,
                    record.get("session_id", "unknown"),
                    f"silence={int(silence.total_seconds())}s, "
                    f"threshold={int(threshold.total_seconds())}s",
                )

        return {
            "checked": len(self.agent_records),
            "dead_heartbeats": len(dead_agents),
            "agents": dead_agents,
            "timestamp": _format_dt(now),
        }

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return continuity service status summary."""
        active = [
            r for r in self.agent_records.values()
            if r.get("status") == "active"
        ]
        compromised = [
            r for r in self.agent_records.values()
            if r.get("compromise_triggered")
        ]
        return {
            "service": "continuity_service",
            "registered_agents": len(self.agent_records),
            "active_agents": len(active),
            "compromised_agents": len(compromised),
            "pending_challenges": len(self.pending_challenges),
            "total_events": len(self.event_log),
            "timestamp": _format_dt(_now()),
        }

    def get_agent_heartbeat_status(
        self,
        agent_id: str,
    ) -> Dict[str, Any]:
        """Get heartbeat status for a specific agent."""
        record = self.agent_records.get(agent_id)
        if record is None:
            return {"error": "agent_not_registered"}
        return {
            "agent_id": agent_id,
            "role": record.get("role"),
            "status": record.get("status"),
            "consecutive_misses": record.get("consecutive_misses", 0),
            "total_heartbeats": record.get("total_heartbeats", 0),
            "last_heartbeat_at": record.get("last_heartbeat_at"),
            "compromise_triggered": record.get("compromise_triggered", False),
        }

    # ── Compute expected response (for agent-side use) ───────

    def compute_response(
        self,
        agent_id: str,
        seed: str,
    ) -> Dict[str, Any]:
        """
        Compute the expected response for a given challenge seed.
        In production, this computation happens in the agent's
        encrypted operational layer. This method models that.
        """
        secret = self.agent_secrets.get(agent_id)
        if secret is None:
            return {"error": "agent_not_registered"}
        response = _compute_expected_response(seed, secret)
        return {"response": response}

    # ── Private helpers ──────────────────────────────────────

    def _log_event(
        self,
        event_type: str,
        agent_id: str,
        session_id: str,
        detail: Optional[str] = None,
    ) -> None:
        entry = {
            "timestamp": _format_dt(_now()),
            "event": event_type,
            "agent_id": agent_id,
            "session_id": session_id,
        }
        if detail:
            entry["detail"] = detail
        self.event_log.append(entry)
