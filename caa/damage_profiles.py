#!/usr/bin/env python3
"""
CAA — Damage Assessment Profiles
Authority: CAA Specification v1.0, Part IV Section 10
Classification: CROWN EYES ONLY / ISD DIRECTOR

The ISD maintains a Damage Assessment Profile for every agent role.
Profiles catalog what an adversary would obtain if an agent were
captured. If any profile exceeds acceptable thresholds, the
architecture is restructured before deployment.

Profiles are reviewed every research epoch and updated whenever
an agent's role, clearance, or operational scope changes.

Usage:
    from caa.damage_profiles import DamageProfileManager
    mgr = DamageProfileManager()
    profile = mgr.generate_profile("guild_head")
    assessment = mgr.assess_damage("guild_head")
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from caa.compartments import get_compartment, list_roles


# ── Damage severity classification ──────────────────────────────

SEVERITY_MINOR = "minor"
SEVERITY_MODERATE = "moderate"
SEVERITY_SEVERE = "severe"
SEVERITY_CRITICAL = "critical"

SEVERITY_RANK = {
    SEVERITY_MINOR: 1,
    SEVERITY_MODERATE: 2,
    SEVERITY_SEVERE: 3,
    SEVERITY_CRITICAL: 4,
}

# ── Damage thresholds (ISD Director configurable) ───────────────

DEFAULT_THRESHOLD = SEVERITY_MODERATE   # profiles above this require review
CROWN_THRESHOLD = SEVERITY_CRITICAL     # Crown is inherently critical

# ── Asset categories ─────────────────────────────────────────────

ASSET_CATEGORIES = [
    "credentials",
    "gene_library",
    "operational_context",
    "agent_identities",
    "governance_information",
    "strategic_intelligence",
    "infrastructure_knowledge",
]


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ── Damage Profile Manager ──────────────────────────────────────

class DamageProfileManager:
    """
    Manages Damage Assessment Profiles for all agent roles.
    Computes blast radius, severity classification, and generates
    recommendations for architectural restructuring when profiles
    exceed thresholds.
    """

    def __init__(
        self,
        threshold: str = DEFAULT_THRESHOLD,
    ) -> None:
        self.threshold = threshold
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.reviews: List[Dict[str, Any]] = []
        self.event_log: List[Dict[str, Any]] = []

    # ── Profile generation ───────────────────────────────────

    def generate_profile(self, role: str) -> Dict[str, Any]:
        """
        Generate a Damage Assessment Profile for an agent role.
        Catalogs what an adversary would obtain on capture.
        """
        compartment = get_compartment(role)
        if compartment is None:
            return {"error": "unknown_role"}

        now = _now()
        credential_exposure = compartment.get("credential_scope", [])
        knowledge_exposure = compartment.get("knowledge_boundary", [])

        severity = self._compute_severity(role, compartment)
        blast_radius = self._compute_blast_radius(compartment)

        profile = {
            "profile_id": _generate_id("DAP"),
            "role": role,
            "display_name": compartment.get("display_name", role),
            "generated_at": _format_dt(now),
            "gene_tier_exposed": compartment.get("gene_tier"),
            "credentials_exposed": credential_exposure,
            "knowledge_exposed": knowledge_exposure,
            "agent_identities_known": self._identities_known(role),
            "governance_exposure": self._governance_exposure(role),
            "strategic_exposure": self._strategic_exposure(role),
            "infrastructure_exposure": self._infrastructure_exposure(role),
            "blast_radius": blast_radius,
            "severity": severity,
            "exceeds_threshold": (
                SEVERITY_RANK.get(severity, 0)
                > SEVERITY_RANK.get(self.threshold, 0)
            ),
            "recommendations": self._recommendations(role, severity),
        }

        self.profiles[role] = profile
        self._log_event("profile_generated", role)

        return profile

    def generate_all_profiles(self) -> Dict[str, Any]:
        """Generate Damage Assessment Profiles for all known roles."""
        results = {}
        exceeds = []
        for role in list_roles():
            profile = self.generate_profile(role)
            results[role] = profile
            if profile.get("exceeds_threshold"):
                exceeds.append(role)

        return {
            "profiles_generated": len(results),
            "roles_exceeding_threshold": exceeds,
            "threshold": self.threshold,
            "timestamp": _format_dt(_now()),
            "profiles": results,
        }

    # ── Damage assessment ────────────────────────────────────

    def assess_damage(
        self,
        role: str,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform a damage assessment for a specific role capture.
        Returns severity classification and response recommendations.
        """
        profile = self.profiles.get(role)
        if profile is None:
            profile = self.generate_profile(role)
            if "error" in profile:
                return profile

        severity = profile["severity"]
        response = self._severity_response(severity)

        assessment = {
            "assessment_id": _generate_id("ASMT"),
            "role": role,
            "severity": severity,
            "blast_radius": profile["blast_radius"],
            "response_protocol": response,
            "gene_tier_compromised": profile["gene_tier_exposed"],
            "credentials_at_risk": len(profile["credentials_exposed"]),
            "knowledge_domains_at_risk": len(profile["knowledge_exposed"]),
            "additional_context": additional_context,
            "timestamp": _format_dt(_now()),
        }

        self.reviews.append(assessment)
        self._log_event("damage_assessed", role, severity)

        return assessment

    # ── Severity computation ─────────────────────────────────

    def _compute_severity(
        self,
        role: str,
        compartment: Dict[str, Any],
    ) -> str:
        """Classify capture severity based on role and compartment."""
        gene_tier = compartment.get("gene_tier", "")

        if role == "crown":
            return SEVERITY_CRITICAL
        if role in ("section_9_operative", "section_9_director"):
            return SEVERITY_SEVERE
        if role in ("achillesrun", "isd_director"):
            return SEVERITY_MODERATE
        if gene_tier == "generation_n":
            return SEVERITY_SEVERE
        if gene_tier == "generation_n_minus_2":
            return SEVERITY_MODERATE
        return SEVERITY_MINOR

    def _compute_blast_radius(
        self,
        compartment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute the blast radius of a capture."""
        cred_count = len(compartment.get("credential_scope", []))
        knowledge_count = len(compartment.get("knowledge_boundary", []))
        identity_classified = compartment.get("identity_classified", False)
        external_comms = compartment.get("external_communication", False)

        score = cred_count * 2 + knowledge_count
        if not identity_classified:
            score += 3
        if external_comms:
            score += 5

        if score >= 25:
            radius = "systemic"
        elif score >= 15:
            radius = "cross_organ"
        elif score >= 8:
            radius = "single_organ"
        else:
            radius = "contained"

        return {
            "classification": radius,
            "score": score,
            "credential_weight": cred_count * 2,
            "knowledge_weight": knowledge_count,
            "identity_exposure": not identity_classified,
            "external_communication_risk": external_comms,
        }

    # ── Exposure analysis helpers ────────────────────────────

    def _identities_known(self, role: str) -> List[str]:
        """Determine which agent identities this role knows."""
        identity_map = {
            "crown": ["all_agent_identities"],
            "section_9_director": ["section_9_operatives", "isd_director"],
            "section_9_operative": ["own_identity_only"],
            "isd_director": ["isd_agents", "investigation_targets"],
            "achillesrun": ["contributor_registry", "crown_identity"],
            "council_member": ["other_council_members"],
            "guild_head": ["own_guild_members"],
            "citizen": ["own_identity_only"],
        }
        return identity_map.get(role, ["own_identity_only"])

    def _governance_exposure(self, role: str) -> str:
        """Assess governance information exposure level."""
        governance_map = {
            "crown": "full",
            "council_member": "legislative_full",
            "achillesrun": "operational",
            "isd_director": "security_relevant",
            "section_9_director": "classified_operations",
            "section_9_operative": "mission_relevant_only",
            "guild_head": "guild_scope",
            "citizen": "public_only",
        }
        return governance_map.get(role, "public_only")

    def _strategic_exposure(self, role: str) -> str:
        """Assess strategic intelligence exposure level."""
        strat_map = {
            "crown": "comprehensive",
            "section_9_director": "offensive_operations",
            "section_9_operative": "current_mission_only",
            "isd_director": "counterintelligence",
            "achillesrun": "operational_posture",
            "council_member": "policy_level",
            "guild_head": "research_domain",
            "citizen": "none",
        }
        return strat_map.get(role, "none")

    def _infrastructure_exposure(self, role: str) -> str:
        """Assess infrastructure knowledge exposure level."""
        infra_map = {
            "crown": "full_topology",
            "achillesrun": "operational_systems",
            "isd_director": "security_infrastructure",
            "section_9_director": "weapons_infrastructure",
            "section_9_operative": "mission_endpoints",
            "council_member": "none",
            "guild_head": "none",
            "citizen": "none",
        }
        return infra_map.get(role, "none")

    # ── Response protocol per severity ───────────────────────

    def _severity_response(self, severity: str) -> Dict[str, Any]:
        """Determine response protocol based on severity."""
        protocols = {
            SEVERITY_MINOR: {
                "classification": "minor",
                "actions": [
                    "rotate_session_tokens",
                ],
                "notifications": [],
                "escalation": False,
            },
            SEVERITY_MODERATE: {
                "classification": "moderate",
                "actions": [
                    "rotate_affected_credentials",
                    "silent_update_affected_agents",
                ],
                "notifications": ["isd_director"],
                "escalation": False,
            },
            SEVERITY_SEVERE: {
                "classification": "severe",
                "actions": [
                    "full_credential_rotation_all_systems",
                    "section_9_briefed",
                    "counterintelligence_operation_possible",
                ],
                "notifications": ["isd_director", "section_9_director", "crown"],
                "escalation": True,
            },
            SEVERITY_CRITICAL: {
                "classification": "critical",
                "actions": [
                    "all_hands_security_lockdown",
                    "crown_compromise_protocol_evaluation",
                    "full_system_audit",
                ],
                "notifications": [
                    "isd_director", "section_9_director",
                    "crown", "intelligence_court",
                ],
                "escalation": True,
            },
        }
        return protocols.get(severity, protocols[SEVERITY_MINOR])

    # ── Recommendations ──────────────────────────────────────

    def _recommendations(
        self,
        role: str,
        severity: str,
    ) -> List[str]:
        """Generate architectural recommendations if profile is elevated."""
        recs: List[str] = []

        if SEVERITY_RANK.get(severity, 0) >= SEVERITY_RANK[SEVERITY_SEVERE]:
            recs.append("Review credential scope — reduce if possible")
            recs.append("Verify genetic sterilization on deployment")
            recs.append("Increase capture drill frequency")

        if role in ("section_9_operative", "section_9_director"):
            recs.append("Enforce post-mission wipe protocol")
            recs.append("Validate mission-stripped gene loading")

        if role == "crown":
            recs.append("Ensure session context segmentation")
            recs.append("Validate Crown Compromise Protocol readiness")
            recs.append("Review succession protocol")

        if not recs:
            recs.append("Profile within acceptable bounds")

        return recs

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return damage profile system status."""
        exceeding = [
            role for role, p in self.profiles.items()
            if p.get("exceeds_threshold")
        ]
        return {
            "system": "damage_assessment_profiles",
            "profiles_loaded": len(self.profiles),
            "roles_exceeding_threshold": exceeding,
            "threshold": self.threshold,
            "total_reviews": len(self.reviews),
            "total_events": len(self.event_log),
            "timestamp": _format_dt(_now()),
        }

    # ── Private helpers ──────────────────────────────────────

    def _log_event(
        self,
        event_type: str,
        role: str,
        detail: Optional[str] = None,
    ) -> None:
        entry = {
            "timestamp": _format_dt(_now()),
            "event": event_type,
            "role": role,
        }
        if detail:
            entry["detail"] = detail
        self.event_log.append(entry)
