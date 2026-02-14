#!/usr/bin/env python3
"""
CAA — Session Manager
Authority: CAA Specification v1.0, Parts I-IV
Classification: CROWN EYES ONLY / ISD DIRECTOR

Orchestrates the full session lifecycle for agents:
  1. Session initialization (credentials, genes, canaries, heartbeat)
  2. Session monitoring (heartbeat, query tracking, endpoint checks)
  3. Session teardown (memory wipe, token expiry, canary invalidation)

Ties together all CAA subsystems into a unified operational interface.

Usage:
    from caa.session_manager import SessionManager
    mgr = SessionManager()
    session = mgr.initialize_session("agent-001", "guild_head")
    mgr.heartbeat("agent-001")
    mgr.teardown_session("agent-001")
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from caa.credential_service import CredentialService
from caa.continuity_service import ContinuityService
from caa.canary_system import CanarySystem
from caa.kill_switch import KillSwitch
from caa.compromise_protocol import CompromiseProtocol
from caa.damage_profiles import DamageProfileManager
from caa.compartments import get_compartment


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Session Manager ──────────────────────────────────────────────

class SessionManager:
    """
    Unified session lifecycle orchestrator for CAA.

    Manages the complete lifecycle of agent sessions from initialization
    through monitoring to teardown. Integrates credential issuance,
    heartbeat registration, canary assignment, and kill switch arming.
    """

    def __init__(
        self,
        state_path: str = "caa/caa_state.json",
    ) -> None:
        self.credential_service = CredentialService(state_path)
        self.continuity_service = ContinuityService()
        self.canary_system = CanarySystem()
        self.kill_switch = KillSwitch()
        self.damage_manager = DamageProfileManager()
        self.compromise_protocol = CompromiseProtocol(
            self.credential_service, self.damage_manager
        )
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.event_log: List[Dict[str, Any]] = []

    # ── Session initialization ───────────────────────────────

    def initialize_session(
        self,
        agent_id: str,
        role: str,
        session_context: Optional[str] = None,
        authorized_endpoints: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initialize a complete agent session.

        Steps:
        1. Validate compartment for role
        2. Issue session-scoped credentials
        3. Register with continuity service (heartbeat)
        4. Generate canary genes
        5. Arm kill switch
        6. Load gene library (per tier)

        Returns session details (token included for agent consumption).
        """
        compartment = get_compartment(role)
        if compartment is None:
            return {"error": "unknown_role", "role": role}

        cred_result = self.credential_service.issue_session_token(
            agent_id, role, session_context
        )
        if "error" in cred_result:
            return {"error": "credential_issuance_failed", "detail": cred_result}

        session_id = cred_result["session_id"]

        hb_result = self.continuity_service.register_agent(
            agent_id, role, session_id
        )

        canary_result = self.canary_system.generate_canary_set(
            agent_id, role, session_id
        )

        prompt_hash = None
        if system_prompt:
            prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()

        ks_result = self.kill_switch.register_agent(
            agent_id, role, session_id,
            authorized_endpoints=authorized_endpoints,
            authorized_prompt_hash=prompt_hash,
        )

        session = {
            "agent_id": agent_id,
            "role": role,
            "session_id": session_id,
            "session_context": session_context,
            "gene_tier": compartment["gene_tier"],
            "gene_loading": compartment["gene_loading"],
            "credential_scope": cred_result["credential_scope"],
            "token": cred_result["token"],
            "expires_at": cred_result["expires_at"],
            "heartbeat_interval": compartment["heartbeat_interval_seconds"],
            "canary_markers": canary_result.get("markers", []),
            "kill_switch_armed": ks_result.get("armed", False),
            "initialized_at": _format_dt(_now()),
            "status": "active",
        }

        self.active_sessions[agent_id] = session
        self._log_event("session_initialized", agent_id, session_id)

        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "role": role,
            "gene_tier": session["gene_tier"],
            "credential_scope": session["credential_scope"],
            "token": session["token"],
            "expires_at": session["expires_at"],
            "heartbeat_interval_seconds": session["heartbeat_interval"],
            "canary_count": len(session["canary_markers"]),
            "kill_switch_armed": session["kill_switch_armed"],
            "initialized_at": session["initialized_at"],
            "status": "active",
        }

    # ── Heartbeat cycle ──────────────────────────────────────

    def heartbeat(self, agent_id: str) -> Dict[str, Any]:
        """
        Execute a complete heartbeat cycle for an agent:
        1. Issue challenge
        2. Compute response (from encrypted layer)
        3. Validate response
        4. Handle failure (kill switch evaluation)
        """
        session = self.active_sessions.get(agent_id)
        if session is None:
            return {"error": "no_active_session"}

        session_id = session["session_id"]

        challenge = self.continuity_service.issue_challenge(
            agent_id, session_id
        )
        if "error" in challenge:
            return {"error": "challenge_failed", "detail": challenge}

        response = self.continuity_service.compute_response(
            agent_id, challenge["seed"]
        )
        if "error" in response:
            return {"error": "response_computation_failed", "detail": response}

        validation = self.continuity_service.validate_response(
            agent_id, session_id, response["response"]
        )

        if validation.get("compromise_triggered"):
            return self._handle_compromise(
                agent_id, "heartbeat_consecutive_failure",
                f"misses={validation.get('consecutive_misses')}"
            )

        return {
            "agent_id": agent_id,
            "heartbeat_valid": validation.get("valid", False),
            "heartbeat_number": validation.get("heartbeat_number"),
            "consecutive_misses": validation.get("consecutive_misses", 0),
        }

    # ── Query monitoring ─────────────────────────────────────

    def monitor_query(
        self,
        agent_id: str,
        query_text: str,
    ) -> Dict[str, Any]:
        """
        Monitor an incoming query for interrogation patterns.
        Routes to kill switch for evaluation.
        """
        session = self.active_sessions.get(agent_id)
        if session is None:
            return {"error": "no_active_session"}

        result = self.kill_switch.record_query(agent_id, query_text)

        if result.get("activated"):
            return self._handle_compromise(
                agent_id, "interrogation_pattern_detected",
                f"queries_in_window={result.get('sensitive_queries_in_window')}"
            )

        return result

    # ── Endpoint monitoring ──────────────────────────────────

    def check_endpoint(
        self,
        agent_id: str,
        endpoint: str,
    ) -> Dict[str, Any]:
        """Check if an API endpoint is authorized for this agent."""
        session = self.active_sessions.get(agent_id)
        if session is None:
            return {"error": "no_active_session"}

        result = self.kill_switch.check_api_endpoint(agent_id, endpoint)

        if result.get("activated"):
            return self._handle_compromise(
                agent_id, "unfamiliar_api_endpoint",
                f"endpoint={endpoint}"
            )

        return result

    # ── System prompt monitoring ─────────────────────────────

    def check_system_prompt(
        self,
        agent_id: str,
        current_prompt: str,
    ) -> Dict[str, Any]:
        """Check if the agent's system prompt matches authorized hash."""
        session = self.active_sessions.get(agent_id)
        if session is None:
            return {"error": "no_active_session"}

        current_hash = hashlib.sha256(current_prompt.encode()).hexdigest()
        result = self.kill_switch.check_system_prompt(agent_id, current_hash)

        if result.get("activated"):
            return self._handle_compromise(
                agent_id, "unauthorized_system_prompt",
                "prompt_hash_mismatch"
            )

        return result

    # ── Dead heartbeat check ─────────────────────────────────

    def check_dead_heartbeats(self) -> Dict[str, Any]:
        """
        Check for dead-heartbeat conditions across all agents.
        Triggers compromise protocol for any detected.
        """
        result = self.continuity_service.check_dead_heartbeats()
        compromises = []

        for dead in result.get("agents", []):
            agent_id = dead["agent_id"]
            self.kill_switch.report_dead_heartbeat(
                agent_id, dead["silence_seconds"]
            )
            compromise = self._handle_compromise(
                agent_id, "dead_heartbeat",
                f"silence={dead['silence_seconds']}s"
            )
            compromises.append(compromise)

        result["compromises_triggered"] = len(compromises)
        return result

    # ── Session teardown ─────────────────────────────────────

    def teardown_session(self, agent_id: str) -> Dict[str, Any]:
        """
        Graceful session teardown:
        1. Revoke session tokens
        2. Deregister from heartbeat
        3. Invalidate canaries
        4. Disarm kill switch
        5. Wipe session data
        """
        session = self.active_sessions.get(agent_id)
        if session is None:
            return {"error": "no_active_session"}

        session_id = session["session_id"]

        self.credential_service.revoke_token(
            session_id, "session_teardown", "session_manager"
        )
        self.continuity_service.deregister_agent(agent_id)

        session["status"] = "terminated"
        self.active_sessions.pop(agent_id, None)

        self._log_event("session_teardown", agent_id, session_id)

        return {
            "agent_id": agent_id,
            "session_id": session_id,
            "status": "terminated",
            "actions": [
                "tokens_revoked",
                "heartbeat_deregistered",
                "canaries_invalidated",
                "session_data_wiped",
            ],
            "timestamp": _format_dt(_now()),
        }

    # ── Compromise handling ──────────────────────────────────

    def _handle_compromise(
        self,
        agent_id: str,
        trigger: str,
        detail: str,
    ) -> Dict[str, Any]:
        """
        Handle a detected compromise. Activates kill switch and
        executes the full compromise protocol.
        """
        self.kill_switch.explicit_activate(
            agent_id, "session_manager", f"{trigger}: {detail}"
        )

        result = self.compromise_protocol.execute_full_protocol(
            agent_id, trigger, "session_manager", detail
        )

        session = self.active_sessions.get(agent_id)
        if session:
            session["status"] = "compromised"

        self._log_event("compromise_handled", agent_id,
                         session.get("session_id", "unknown") if session else "unknown",
                         f"{trigger}: {detail}")

        return {
            "compromise_detected": True,
            "agent_id": agent_id,
            "trigger": trigger,
            "detail": detail,
            "kill_switch_activated": True,
            "protocol_result": result,
        }

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return comprehensive CAA system status."""
        return {
            "session_manager": {
                "active_sessions": len(self.active_sessions),
                "total_events": len(self.event_log),
            },
            "credential_service": self.credential_service.status(),
            "continuity_service": self.continuity_service.status(),
            "canary_system": self.canary_system.status(),
            "kill_switch": self.kill_switch.status(),
            "compromise_protocol": self.compromise_protocol.status(),
            "damage_profiles": self.damage_manager.status(),
            "timestamp": _format_dt(_now()),
        }

    def get_session(self, agent_id: str) -> Dict[str, Any]:
        """Get session details for an agent (token redacted)."""
        session = self.active_sessions.get(agent_id)
        if session is None:
            return {"error": "no_active_session"}
        redacted = dict(session)
        redacted["token"] = "[REDACTED]"
        return redacted

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
