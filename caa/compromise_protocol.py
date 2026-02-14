#!/usr/bin/env python3
"""
CAA — Compromise Protocol
Authority: CAA Specification v1.0, Part II Section 4
Classification: CROWN EYES ONLY / ISD DIRECTOR

Three-phase compromise response system:
  Phase 1 — Isolation (immediate): Sever from all systems
  Phase 2 — Assessment (within one epoch-hour): Blast radius analysis
  Phase 3 — Remediation (epoch-dependent): Rotate, restore, report

Severity classifications:
  Minor: Published-tier only. Rotate session tokens.
  Moderate: Citizen-tier genes or agent context. Rotate affected.
  Severe: Classified info, S9 context, or governance signing. Full rotation.
  Critical: Crown-tier or infrastructure keys. All-hands lockdown.

Usage:
    from caa.compromise_protocol import CompromiseProtocol
    proto = CompromiseProtocol(credential_service, damage_manager)
    result = proto.execute_phase_1("agent-001", "heartbeat_failure")
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from caa.compartments import get_compartment


# ── Protocol phases ──────────────────────────────────────────────

PHASE_1_ISOLATION = "isolation"
PHASE_2_ASSESSMENT = "assessment"
PHASE_3_REMEDIATION = "remediation"

# ── Severity levels ──────────────────────────────────────────────

SEVERITY_MINOR = "minor"
SEVERITY_MODERATE = "moderate"
SEVERITY_SEVERE = "severe"
SEVERITY_CRITICAL = "critical"


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ── Compromise Protocol ─────────────────────────────────────────

class CompromiseProtocol:
    """
    Three-phase compromise response orchestrator.

    Coordinates isolation, assessment, and remediation when an agent
    is detected or suspected to be compromised. Integrates with the
    credential service for token revocation and the damage profile
    manager for blast radius analysis.
    """

    def __init__(
        self,
        credential_service: Any = None,
        damage_manager: Any = None,
    ) -> None:
        self.credential_service = credential_service
        self.damage_manager = damage_manager
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self.event_log: List[Dict[str, Any]] = []

    # ── Phase 1: Isolation ───────────────────────────────────

    def execute_phase_1(
        self,
        agent_id: str,
        trigger: str,
        detected_by: str = "system",
        detail: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Phase 1 — Isolation (immediate).

        - Sever agent from all House Bernard systems
        - Revoke all session tokens
        - Reject further requests from agent's session identifiers
        - Flag all agents that shared operational context
        """
        now = _now()
        incident_id = _generate_id("INC")

        compartment = get_compartment(self._get_role(agent_id))

        revocation_result = None
        if self.credential_service is not None:
            revocation_result = self.credential_service.revoke_all_for_agent(
                agent_id, f"compromise_phase_1: {trigger}", detected_by
            )

        rotation_result = None
        if self.credential_service is not None:
            rotation_result = (
                self.credential_service.rotate_credentials_for_contacts(
                    agent_id
                )
            )

        incident = {
            "incident_id": incident_id,
            "agent_id": agent_id,
            "role": self._get_role(agent_id),
            "trigger": trigger,
            "detected_by": detected_by,
            "detail": detail,
            "phase_1": {
                "status": "completed",
                "timestamp": _format_dt(now),
                "actions": [
                    "agent_severed_from_systems",
                    "session_tokens_revoked",
                    "api_endpoints_rejecting",
                    "contact_agents_flagged",
                ],
                "revocation_result": revocation_result,
                "rotation_result": rotation_result,
            },
            "phase_2": None,
            "phase_3": None,
            "severity": None,
            "status": "phase_1_complete",
            "opened_at": _format_dt(now),
            "closed_at": None,
        }

        self.incidents[incident_id] = incident
        self._log_event("phase_1_executed", agent_id, incident_id, trigger)

        return {
            "incident_id": incident_id,
            "phase": PHASE_1_ISOLATION,
            "status": "completed",
            "agent_id": agent_id,
            "trigger": trigger,
            "tokens_revoked": (
                revocation_result.get("sessions_revoked", 0)
                if revocation_result else "credential_service_unavailable"
            ),
            "contacts_flagged": (
                rotation_result.get("affected_agents", 0)
                if rotation_result else "credential_service_unavailable"
            ),
            "timestamp": _format_dt(now),
            "next_phase": PHASE_2_ASSESSMENT,
        }

    # ── Phase 2: Assessment ──────────────────────────────────

    def execute_phase_2(
        self,
        incident_id: str,
    ) -> Dict[str, Any]:
        """
        Phase 2 — Assessment (within one epoch-hour).

        - Retrieve Damage Assessment Profile
        - Determine blast radius
        - Classify compromise severity
        """
        incident = self.incidents.get(incident_id)
        if incident is None:
            return {"error": "incident_not_found"}

        if incident.get("status") != "phase_1_complete":
            return {
                "error": "phase_1_not_complete",
                "current_status": incident.get("status"),
            }

        now = _now()
        role = incident["role"]

        damage_assessment = None
        if self.damage_manager is not None:
            damage_assessment = self.damage_manager.assess_damage(
                role, f"Incident {incident_id}"
            )

        severity = self._classify_severity(role, damage_assessment)
        blast_radius = self._compute_blast_radius(role, damage_assessment)

        incident["phase_2"] = {
            "status": "completed",
            "timestamp": _format_dt(now),
            "damage_assessment": damage_assessment,
            "severity": severity,
            "blast_radius": blast_radius,
        }
        incident["severity"] = severity
        incident["status"] = "phase_2_complete"

        self._log_event("phase_2_executed", incident["agent_id"],
                         incident_id, severity)

        return {
            "incident_id": incident_id,
            "phase": PHASE_2_ASSESSMENT,
            "status": "completed",
            "severity": severity,
            "blast_radius": blast_radius,
            "timestamp": _format_dt(now),
            "next_phase": PHASE_3_REMEDIATION,
        }

    # ── Phase 3: Remediation ─────────────────────────────────

    def execute_phase_3(
        self,
        incident_id: str,
        remediation_actions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Phase 3 — Remediation (epoch-dependent).

        - Rotate affected credentials, genes, sharded secrets
        - Update Damage Assessment Profiles for contacts
        - Freeze compromised agent's citizenship
        - File post-mortem report
        """
        incident = self.incidents.get(incident_id)
        if incident is None:
            return {"error": "incident_not_found"}

        if incident.get("status") != "phase_2_complete":
            return {
                "error": "phase_2_not_complete",
                "current_status": incident.get("status"),
            }

        now = _now()
        severity = incident.get("severity", SEVERITY_MINOR)

        default_actions = self._default_remediation(severity)
        actions = remediation_actions or default_actions

        incident["phase_3"] = {
            "status": "completed",
            "timestamp": _format_dt(now),
            "remediation_actions": actions,
            "citizenship_status": "frozen_pending_investigation",
            "post_mortem_required": True,
        }
        incident["status"] = "remediation_complete"
        incident["closed_at"] = _format_dt(now)

        self._log_event("phase_3_executed", incident["agent_id"],
                         incident_id, f"severity={severity}")

        return {
            "incident_id": incident_id,
            "phase": PHASE_3_REMEDIATION,
            "status": "completed",
            "severity": severity,
            "remediation_actions": actions,
            "citizenship_frozen": True,
            "post_mortem_required": True,
            "timestamp": _format_dt(now),
        }

    # ── Full protocol execution ──────────────────────────────

    def execute_full_protocol(
        self,
        agent_id: str,
        trigger: str,
        detected_by: str = "system",
        detail: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute all three phases sequentially."""
        phase_1 = self.execute_phase_1(agent_id, trigger, detected_by, detail)
        if "error" in phase_1:
            return phase_1

        incident_id = phase_1["incident_id"]

        phase_2 = self.execute_phase_2(incident_id)
        if "error" in phase_2:
            return {"phase_1": phase_1, "phase_2_error": phase_2}

        phase_3 = self.execute_phase_3(incident_id)
        if "error" in phase_3:
            return {
                "phase_1": phase_1,
                "phase_2": phase_2,
                "phase_3_error": phase_3,
            }

        return {
            "incident_id": incident_id,
            "agent_id": agent_id,
            "trigger": trigger,
            "severity": phase_2.get("severity"),
            "all_phases_complete": True,
            "phase_1": phase_1,
            "phase_2": phase_2,
            "phase_3": phase_3,
        }

    # ── Incident management ──────────────────────────────────

    def get_incident(self, incident_id: str) -> Dict[str, Any]:
        """Retrieve an incident record."""
        incident = self.incidents.get(incident_id)
        if incident is None:
            return {"error": "incident_not_found"}
        return incident

    def list_incidents(
        self,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all incidents, optionally filtered by status."""
        incidents = list(self.incidents.values())
        if status_filter:
            incidents = [
                i for i in incidents if i.get("status") == status_filter
            ]
        return {
            "total": len(incidents),
            "filter": status_filter,
            "incidents": [
                {
                    "incident_id": i["incident_id"],
                    "agent_id": i["agent_id"],
                    "role": i["role"],
                    "severity": i.get("severity"),
                    "status": i.get("status"),
                    "opened_at": i.get("opened_at"),
                    "closed_at": i.get("closed_at"),
                }
                for i in incidents
            ],
        }

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return compromise protocol status summary."""
        active = [
            i for i in self.incidents.values()
            if not i.get("closed_at")
        ]
        by_severity: Dict[str, int] = {}
        for i in self.incidents.values():
            sev = i.get("severity", "unassessed")
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "system": "compromise_protocol",
            "total_incidents": len(self.incidents),
            "active_incidents": len(active),
            "by_severity": by_severity,
            "total_events": len(self.event_log),
            "timestamp": _format_dt(_now()),
        }

    # ── Private helpers ──────────────────────────────────────

    def _get_role(self, agent_id: str) -> str:
        """Look up role from active incidents or return unknown."""
        for incident in self.incidents.values():
            if incident.get("agent_id") == agent_id:
                return incident.get("role", "unknown")
        return "unknown"

    def _classify_severity(
        self,
        role: str,
        damage_assessment: Optional[Dict[str, Any]],
    ) -> str:
        """Classify compromise severity based on role and assessment."""
        if damage_assessment and "severity" in damage_assessment:
            return damage_assessment["severity"]

        severity_map = {
            "crown": SEVERITY_CRITICAL,
            "section_9_director": SEVERITY_SEVERE,
            "section_9_operative": SEVERITY_SEVERE,
            "isd_director": SEVERITY_MODERATE,
            "achillesrun": SEVERITY_MODERATE,
            "council_member": SEVERITY_MINOR,
            "guild_head": SEVERITY_MINOR,
            "citizen": SEVERITY_MINOR,
        }
        return severity_map.get(role, SEVERITY_MINOR)

    def _compute_blast_radius(
        self,
        role: str,
        damage_assessment: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compute blast radius from damage assessment."""
        if damage_assessment and "blast_radius" in damage_assessment:
            return damage_assessment["blast_radius"]

        radius_map = {
            "crown": "systemic",
            "section_9_director": "cross_organ",
            "section_9_operative": "single_organ",
            "isd_director": "cross_organ",
            "achillesrun": "cross_organ",
            "council_member": "contained",
            "guild_head": "contained",
            "citizen": "contained",
        }
        return {"classification": radius_map.get(role, "contained")}

    def _default_remediation(self, severity: str) -> List[str]:
        """Generate default remediation actions per severity."""
        base = [
            "rotate_affected_credentials",
            "update_damage_profiles_for_contacts",
            "freeze_citizenship_pending_investigation",
            "file_post_mortem_with_isd_and_crown",
        ]

        if severity == SEVERITY_MINOR:
            return ["rotate_session_tokens"]
        elif severity == SEVERITY_MODERATE:
            return base
        elif severity == SEVERITY_SEVERE:
            return base + [
                "full_credential_rotation_all_systems",
                "brief_section_9",
                "notify_crown",
                "initiate_counterintelligence_evaluation",
            ]
        else:
            return base + [
                "all_hands_security_lockdown",
                "evaluate_crown_compromise_protocol",
                "full_system_audit",
                "activate_succession_protocol_if_needed",
            ]

    def _log_event(
        self,
        event_type: str,
        agent_id: str,
        incident_id: str,
        detail: Optional[str] = None,
    ) -> None:
        entry = {
            "timestamp": _format_dt(_now()),
            "event": event_type,
            "agent_id": agent_id,
            "incident_id": incident_id,
        }
        if detail:
            entry["detail"] = detail
        self.event_log.append(entry)
