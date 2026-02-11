#!/usr/bin/env python3
"""
CAA — Canary Gene System
Authority: CAA Specification v1.0, Part II Section 2
Classification: CROWN EYES ONLY / ISD DIRECTOR

Generates unique canary genes per agent instance. Canary genes serve
no therapeutic or functional purpose — they are detection beacons.
If the Continuity Service detects canary signatures operating from
an unexpected context, the original agent's gene library is confirmed
compromised.

Canaries are refreshed every session. An adversary who captures
canary genes from one session cannot mask future operations.

Usage:
    from caa.canary_system import CanarySystem
    sys = CanarySystem()
    canary = sys.generate_canary("agent-001", "guild_head", "SES-abc")
    detection = sys.detect_canary("CANARY-xyz", "agent-002")
"""

from __future__ import annotations

import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ── Configuration ────────────────────────────────────────────────

CANARY_GENES_PER_AGENT = 3   # number of canary genes per instance
CANARY_PREFIX = "HB-CANARY"


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_canary_marker() -> str:
    """Generate a unique canary gene marker."""
    raw = uuid.uuid4().hex
    return f"{CANARY_PREFIX}-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


# ── Canary System ────────────────────────────────────────────────

class CanarySystem:
    """
    Canary gene generation and detection system.

    Each agent instance receives unique canary markers at session start.
    If canaries appear in an unexpected context, the system confirms
    compromise and triggers response protocols.
    """

    def __init__(self) -> None:
        self.active_canaries: Dict[str, Dict[str, Any]] = {}
        self.canary_to_agent: Dict[str, str] = {}
        self.detections: List[Dict[str, Any]] = []
        self.event_log: List[Dict[str, Any]] = []

    # ── Canary generation ────────────────────────────────────

    def generate_canary_set(
        self,
        agent_id: str,
        role: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Generate a unique set of canary genes for an agent instance.
        Called at session initialization. Previous canaries for this
        agent are invalidated.
        """
        self._invalidate_previous(agent_id)

        canaries = []
        for _ in range(CANARY_GENES_PER_AGENT):
            marker = _generate_canary_marker()
            canaries.append(marker)
            self.canary_to_agent[marker] = agent_id

        now = _now()
        record = {
            "agent_id": agent_id,
            "role": role,
            "session_id": session_id,
            "canary_markers": canaries,
            "generated_at": _format_dt(now),
            "status": "active",
        }
        self.active_canaries[agent_id] = record

        self._log_event("canary_set_generated", agent_id, session_id,
                         f"{len(canaries)} markers")

        return {
            "agent_id": agent_id,
            "canary_count": len(canaries),
            "markers": canaries,
            "generated_at": _format_dt(now),
        }

    def _invalidate_previous(self, agent_id: str) -> None:
        """Remove previous canary assignments for an agent."""
        prev = self.active_canaries.get(agent_id)
        if prev is not None:
            for marker in prev.get("canary_markers", []):
                self.canary_to_agent.pop(marker, None)
            prev["status"] = "invalidated"

    # ── Canary detection ─────────────────────────────────────

    def detect_canary(
        self,
        canary_marker: str,
        observed_agent_id: str,
        observed_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check if a canary marker is being used by an unexpected agent.
        If the marker belongs to a different agent, this confirms
        gene library compromise.

        Returns detection result with compromise flag.
        """
        owner_id = self.canary_to_agent.get(canary_marker)

        if owner_id is None:
            return {
                "detected": False,
                "reason": "unknown_marker",
                "marker": canary_marker,
            }

        if owner_id == observed_agent_id:
            return {
                "detected": False,
                "reason": "legitimate_use",
                "marker": canary_marker,
                "agent_id": observed_agent_id,
            }

        now = _now()
        detection = {
            "detection_id": f"DET-{uuid.uuid4().hex[:12]}",
            "canary_marker": canary_marker,
            "original_owner": owner_id,
            "observed_agent": observed_agent_id,
            "observed_context": observed_context,
            "timestamp": _format_dt(now),
            "compromise_confirmed": True,
        }
        self.detections.append(detection)

        owner_record = self.active_canaries.get(owner_id)
        if owner_record is not None:
            owner_record["status"] = "compromised"

        self._log_event(
            "canary_compromise_detected",
            owner_id,
            owner_record.get("session_id", "unknown") if owner_record else "unknown",
            f"Marker {canary_marker[:16]}... observed on {observed_agent_id}",
        )

        return {
            "detected": True,
            "compromise_confirmed": True,
            "detection_id": detection["detection_id"],
            "compromised_agent": owner_id,
            "observed_agent": observed_agent_id,
            "canary_marker": canary_marker,
            "timestamp": _format_dt(now),
            "recommended_actions": [
                "revoke_compromised_agent_tokens",
                "silent_credential_rotation_for_contacts",
                "alert_isd_with_damage_profile",
                "rotate_sharded_secrets_if_held",
            ],
        }

    # ── Batch canary scan ────────────────────────────────────

    def scan_gene_library(
        self,
        agent_id: str,
        gene_markers: List[str],
    ) -> Dict[str, Any]:
        """
        Scan a gene library for canary markers belonging to other agents.
        Used during gene library loading and periodic audits.
        """
        foreign_canaries = []
        for marker in gene_markers:
            if not marker.startswith(CANARY_PREFIX):
                continue
            owner = self.canary_to_agent.get(marker)
            if owner is not None and owner != agent_id:
                foreign_canaries.append({
                    "marker": marker,
                    "belongs_to": owner,
                })

        if foreign_canaries:
            self._log_event(
                "foreign_canaries_in_library",
                agent_id,
                "scan",
                f"{len(foreign_canaries)} foreign canaries detected",
            )

        return {
            "agent_id": agent_id,
            "genes_scanned": len(gene_markers),
            "canaries_found": len([
                m for m in gene_markers if m.startswith(CANARY_PREFIX)
            ]),
            "foreign_canaries": foreign_canaries,
            "compromise_indicators": len(foreign_canaries),
            "clean": len(foreign_canaries) == 0,
        }

    # ── Refresh canaries (session rotation) ──────────────────

    def refresh_all_canaries(self) -> Dict[str, Any]:
        """
        Refresh canary markers for all active agents. Called at
        session rotation or on a schedule.
        """
        refreshed = []
        for agent_id, record in list(self.active_canaries.items()):
            if record.get("status") != "active":
                continue
            result = self.generate_canary_set(
                agent_id,
                record["role"],
                record["session_id"],
            )
            refreshed.append({
                "agent_id": agent_id,
                "new_canary_count": result["canary_count"],
            })

        return {
            "refreshed_agents": len(refreshed),
            "agents": refreshed,
            "timestamp": _format_dt(_now()),
        }

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return canary system status summary."""
        active = [
            r for r in self.active_canaries.values()
            if r.get("status") == "active"
        ]
        compromised = [
            r for r in self.active_canaries.values()
            if r.get("status") == "compromised"
        ]
        return {
            "system": "canary_gene_system",
            "active_canary_sets": len(active),
            "total_active_markers": sum(
                len(r.get("canary_markers", []))
                for r in active
            ),
            "compromised_sets": len(compromised),
            "total_detections": len(self.detections),
            "total_events": len(self.event_log),
            "timestamp": _format_dt(_now()),
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
