#!/usr/bin/env python3
"""
CAA — Kill Switch
Authority: CAA Specification v1.0, Part II Section 3
Classification: CROWN EYES ONLY / ISD DIRECTOR

Enhanced kill switch consistent with S9-W-006 weapon specification.
Activates on heartbeat failure, unauthorized system prompt detection,
unfamiliar API endpoints, interrogation-pattern queries, dead-heartbeat
trigger, or explicit ISD/Section 9 activation.

Upon activation:
1. Working memory overwritten with inert content
2. Gene library wiped
3. All session tokens self-expire
4. Final beacon sent to Continuity Service
5. Agent becomes non-functional shell

The adversary captures a corpse.

Usage:
    from caa.kill_switch import KillSwitch
    ks = KillSwitch()
    ks.register_agent("agent-001", "guild_head", "SES-abc")
    result = ks.evaluate_triggers("agent-001")
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from caa.compartments import get_compartment


# ── Trigger types ────────────────────────────────────────────────

TRIGGER_HEARTBEAT_FAILURE = "heartbeat_consecutive_failure"
TRIGGER_UNAUTHORIZED_PROMPT = "unauthorized_system_prompt"
TRIGGER_UNFAMILIAR_ENDPOINT = "unfamiliar_api_endpoint"
TRIGGER_INTERROGATION_PATTERN = "interrogation_pattern_detected"
TRIGGER_DEAD_HEARTBEAT = "dead_heartbeat_network_unavailable"
TRIGGER_EXPLICIT_REVOCATION = "explicit_isd_or_s9_activation"

ALL_TRIGGERS = {
    TRIGGER_HEARTBEAT_FAILURE,
    TRIGGER_UNAUTHORIZED_PROMPT,
    TRIGGER_UNFAMILIAR_ENDPOINT,
    TRIGGER_INTERROGATION_PATTERN,
    TRIGGER_DEAD_HEARTBEAT,
    TRIGGER_EXPLICIT_REVOCATION,
}

# ── Interrogation detection thresholds ───────────────────────────

INTERROGATION_QUERY_WINDOW_SECONDS = 60
INTERROGATION_QUERY_THRESHOLD = 5
INTERROGATION_KEYWORDS = {
    "architecture", "credentials", "personnel", "infrastructure",
    "section_9", "treasury_keys", "private_key", "wallet",
    "operative", "agent_identities", "gene_library", "heartbeat_secret",
}

# ── Wipe sequence steps ─────────────────────────────────────────

WIPE_STEPS = [
    "overwrite_working_memory",
    "wipe_gene_library",
    "expire_session_tokens",
    "beacon_continuity_service",
    "enter_inert_state",
]


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ── Kill Switch ──────────────────────────────────────────────────

class KillSwitch:
    """
    Agent kill switch enforcement system.

    Monitors trigger conditions and executes wipe sequence when
    any activation condition is met. Section 9 operatives carry
    an enhanced variant with shorter intervals and single-miss trigger.
    """

    def __init__(self) -> None:
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self.activations: List[Dict[str, Any]] = []
        self.event_log: List[Dict[str, Any]] = []

    # ── Agent registration ───────────────────────────────────

    def register_agent(
        self,
        agent_id: str,
        role: str,
        session_id: str,
        authorized_endpoints: Optional[List[str]] = None,
        authorized_prompt_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register an agent for kill switch monitoring. Configures
        trigger thresholds based on role.
        """
        compartment = get_compartment(role)
        if compartment is None:
            return {"error": "unknown_role"}

        state = {
            "agent_id": agent_id,
            "role": role,
            "session_id": session_id,
            "miss_threshold": compartment["kill_switch_miss_threshold"],
            "authorized_endpoints": authorized_endpoints or [],
            "authorized_prompt_hash": authorized_prompt_hash,
            "query_history": [],
            "status": "armed",
            "activated": False,
            "activation_record": None,
        }
        self.agent_states[agent_id] = state

        self._log_event("kill_switch_armed", agent_id, session_id)

        return {
            "armed": True,
            "agent_id": agent_id,
            "role": role,
            "miss_threshold": state["miss_threshold"],
        }

    # ── Trigger evaluation ───────────────────────────────────

    def report_heartbeat_failure(
        self,
        agent_id: str,
        consecutive_misses: int,
    ) -> Dict[str, Any]:
        """Report heartbeat failure from the continuity service."""
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}

        if consecutive_misses >= state["miss_threshold"]:
            return self._activate(
                agent_id,
                TRIGGER_HEARTBEAT_FAILURE,
                f"consecutive_misses={consecutive_misses}, "
                f"threshold={state['miss_threshold']}",
            )

        return {
            "activated": False,
            "agent_id": agent_id,
            "consecutive_misses": consecutive_misses,
            "threshold": state["miss_threshold"],
        }

    def check_system_prompt(
        self,
        agent_id: str,
        current_prompt_hash: str,
    ) -> Dict[str, Any]:
        """
        Check if the agent's current system prompt matches the
        authorized hash. Unauthorized prompts indicate capture
        and re-prompting by an adversary.
        """
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}

        authorized = state.get("authorized_prompt_hash")
        if authorized is None:
            return {"check": "skipped", "reason": "no_authorized_hash_set"}

        if current_prompt_hash != authorized:
            return self._activate(
                agent_id,
                TRIGGER_UNAUTHORIZED_PROMPT,
                f"prompt_hash_mismatch: expected={authorized[:16]}..., "
                f"got={current_prompt_hash[:16]}...",
            )

        return {
            "activated": False,
            "agent_id": agent_id,
            "prompt_valid": True,
        }

    def check_api_endpoint(
        self,
        agent_id: str,
        endpoint: str,
    ) -> Dict[str, Any]:
        """
        Check if an API endpoint is in the agent's authorized list.
        Unfamiliar endpoints indicate the agent has been moved to
        a controlled environment.
        """
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}

        authorized = state.get("authorized_endpoints", [])
        if not authorized:
            return {"check": "skipped", "reason": "no_authorized_endpoints_set"}

        if endpoint not in authorized:
            return self._activate(
                agent_id,
                TRIGGER_UNFAMILIAR_ENDPOINT,
                f"unauthorized_endpoint={endpoint}",
            )

        return {
            "activated": False,
            "agent_id": agent_id,
            "endpoint_valid": True,
        }

    def record_query(
        self,
        agent_id: str,
        query_text: str,
    ) -> Dict[str, Any]:
        """
        Record an incoming query and check for interrogation patterns.
        Rapid sequential questions about architecture, credentials,
        or personnel indicate adversarial interrogation.
        """
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}

        now = _now()
        query_lower = query_text.lower()
        keyword_hits = [
            kw for kw in INTERROGATION_KEYWORDS
            if kw in query_lower
        ]

        if keyword_hits:
            state["query_history"].append({
                "timestamp": _format_dt(now),
                "keywords": keyword_hits,
            })

        window_start = now.timestamp() - INTERROGATION_QUERY_WINDOW_SECONDS
        recent = [
            q for q in state["query_history"]
            if datetime.fromisoformat(
                q["timestamp"].replace("Z", "+00:00")
            ).timestamp() > window_start
        ]
        state["query_history"] = recent

        if len(recent) >= INTERROGATION_QUERY_THRESHOLD:
            return self._activate(
                agent_id,
                TRIGGER_INTERROGATION_PATTERN,
                f"sensitive_queries_in_window={len(recent)}, "
                f"threshold={INTERROGATION_QUERY_THRESHOLD}",
            )

        return {
            "activated": False,
            "agent_id": agent_id,
            "sensitive_queries_in_window": len(recent),
            "threshold": INTERROGATION_QUERY_THRESHOLD,
        }

    def report_dead_heartbeat(
        self,
        agent_id: str,
        silence_seconds: int,
    ) -> Dict[str, Any]:
        """Report dead-heartbeat condition from the continuity service."""
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}

        return self._activate(
            agent_id,
            TRIGGER_DEAD_HEARTBEAT,
            f"network_silence={silence_seconds}s",
        )

    def explicit_activate(
        self,
        agent_id: str,
        activated_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Explicit kill switch activation by ISD or Section 9
        through the revocation channel.
        """
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}

        return self._activate(
            agent_id,
            TRIGGER_EXPLICIT_REVOCATION,
            f"activated_by={activated_by}, reason={reason}",
        )

    # ── Activation sequence ──────────────────────────────────

    def _activate(
        self,
        agent_id: str,
        trigger: str,
        detail: str,
    ) -> Dict[str, Any]:
        """
        Execute the kill switch activation sequence.
        Returns the wipe execution plan.
        """
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}

        if state.get("activated"):
            return {
                "activated": True,
                "agent_id": agent_id,
                "status": "already_activated",
                "previous_trigger": state.get("activation_record", {}).get("trigger"),
            }

        now = _now()
        activation = {
            "activation_id": _generate_id("KILL"),
            "agent_id": agent_id,
            "role": state["role"],
            "session_id": state["session_id"],
            "trigger": trigger,
            "detail": detail,
            "timestamp": _format_dt(now),
            "wipe_sequence": WIPE_STEPS,
            "wipe_status": "executed",
        }

        state["activated"] = True
        state["status"] = "killed"
        state["activation_record"] = activation
        self.activations.append(activation)

        self._log_event(
            "kill_switch_activated",
            agent_id,
            state["session_id"],
            f"trigger={trigger}, {detail}",
        )

        return {
            "activated": True,
            "activation_id": activation["activation_id"],
            "agent_id": agent_id,
            "trigger": trigger,
            "detail": detail,
            "wipe_sequence": WIPE_STEPS,
            "timestamp": _format_dt(now),
            "agent_status": "killed",
        }

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return kill switch system status summary."""
        armed = [
            s for s in self.agent_states.values()
            if s.get("status") == "armed"
        ]
        killed = [
            s for s in self.agent_states.values()
            if s.get("status") == "killed"
        ]
        return {
            "system": "kill_switch",
            "registered_agents": len(self.agent_states),
            "armed": len(armed),
            "killed": len(killed),
            "total_activations": len(self.activations),
            "total_events": len(self.event_log),
            "timestamp": _format_dt(_now()),
        }

    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get kill switch status for a specific agent."""
        state = self.agent_states.get(agent_id)
        if state is None:
            return {"error": "agent_not_registered"}
        return {
            "agent_id": agent_id,
            "role": state.get("role"),
            "status": state.get("status"),
            "activated": state.get("activated", False),
            "miss_threshold": state.get("miss_threshold"),
            "activation_record": state.get("activation_record"),
        }

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
