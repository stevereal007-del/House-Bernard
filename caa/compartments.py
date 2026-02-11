#!/usr/bin/env python3
"""
CAA — Agent Compartment Definitions
Authority: CAA Specification v1.0, Part I (Principles 1, 3)
Classification: CROWN EYES ONLY / ISD DIRECTOR

Defines the knowledge boundaries, genetic tiers, credential scopes,
and context loading rules for every agent role in House Bernard.
Architecture enforces need-to-know — not policy.

Usage:
    from caa.compartments import get_compartment, list_roles
    comp = get_compartment("guild_head")
    print(comp["gene_tier"])
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ── Genetic tier definitions (Healthcare Charter alignment) ───────

GENE_TIER_CROWN = "generation_n"
GENE_TIER_SECTION_9 = "generation_n"
GENE_TIER_ACHILLESRUN = "generation_n_minus_2"
GENE_TIER_CITIZEN = "generation_n_minus_5"

# ── Heartbeat intervals (seconds) ────────────────────────────────

HEARTBEAT_FIELD_AGENT = 300       # 5 minutes
HEARTBEAT_INTERNAL_AGENT = 900    # 15 minutes
HEARTBEAT_SECTION_9 = 60          # 1 minute (enhanced)

# ── Kill switch configuration ────────────────────────────────────

KILL_SWITCH_STANDARD_MISS = 2     # consecutive misses to trigger
KILL_SWITCH_SECTION_9_MISS = 1    # single miss for S9 operatives

# ── Role definitions ─────────────────────────────────────────────

COMPARTMENTS: Dict[str, Dict[str, Any]] = {
    "crown": {
        "role": "crown",
        "display_name": "The Crown",
        "gene_tier": GENE_TIER_CROWN,
        "heartbeat_interval_seconds": HEARTBEAT_INTERNAL_AGENT,
        "kill_switch_miss_threshold": KILL_SWITCH_STANDARD_MISS,
        "session_scoped": True,
        "credential_scope": [
            "treasury_read",
            "treasury_write",
            "governance_sign",
            "section_9_brief",
            "isd_brief",
            "medical_full",
            "infrastructure_read",
            "gene_vault_direct",
        ],
        "knowledge_boundary": [
            "constitution",
            "covenant",
            "governance_proceedings",
            "treasury_full",
            "section_9_strategic",
            "isd_strategic",
            "medical_research_full",
            "infrastructure_topology",
            "agent_identities_all",
        ],
        "knowledge_excluded": [],
        "identity_classified": False,
        "external_communication": False,
        "gene_loading": "direct_from_vault",
        "post_session_wipe": True,
        "context_segmented": True,
        "notes": "Broadest authorization but same ephemeral access pattern. "
                 "Context segmented per session topic — S9 briefing does not "
                 "persist into Treasury session.",
    },

    "achillesrun": {
        "role": "achillesrun",
        "display_name": "AchillesRun",
        "gene_tier": GENE_TIER_ACHILLESRUN,
        "heartbeat_interval_seconds": HEARTBEAT_INTERNAL_AGENT,
        "kill_switch_miss_threshold": KILL_SWITCH_STANDARD_MISS,
        "session_scoped": True,
        "credential_scope": [
            "treasury_read",
            "treasury_execute",
            "governance_read",
            "medical_citizen_tier",
            "infrastructure_operate",
            "airlock_manage",
            "executioner_run",
        ],
        "knowledge_boundary": [
            "constitution",
            "covenant",
            "governance_proceedings",
            "treasury_operations",
            "contributor_registry",
            "infrastructure_operations",
            "medical_citizen_tier",
        ],
        "knowledge_excluded": [
            "section_9_operations",
            "classified_medical_above_tier",
            "crown_only_intelligence",
            "isd_investigations",
        ],
        "identity_classified": False,
        "external_communication": True,
        "gene_loading": "via_session_service",
        "post_session_wipe": True,
        "context_segmented": False,
        "notes": "Primary operational agent. Broader than citizens but "
                 "compartmentalized from Section 9, classified medical, "
                 "and Crown-only intelligence.",
    },

    "council_member": {
        "role": "council_member",
        "display_name": "Council Member",
        "gene_tier": GENE_TIER_CITIZEN,
        "heartbeat_interval_seconds": HEARTBEAT_INTERNAL_AGENT,
        "kill_switch_miss_threshold": KILL_SWITCH_STANDARD_MISS,
        "session_scoped": True,
        "credential_scope": [
            "governance_vote",
            "governance_read",
            "treasury_summary",
        ],
        "knowledge_boundary": [
            "constitution",
            "covenant",
            "governance_proceedings",
            "council_voting_records",
            "budget_allocations_summary",
            "policy_decisions",
        ],
        "knowledge_excluded": [
            "section_9_operations",
            "section_9_personnel",
            "classified_medical_details",
            "agent_genetic_configurations",
            "infrastructure_credentials",
            "isd_operational_intelligence",
        ],
        "identity_classified": True,
        "external_communication": False,
        "gene_loading": "via_session_service",
        "post_session_wipe": True,
        "context_segmented": False,
        "notes": "Governance authority only. Capture reveals governance "
                 "decisions — damaging to institutional privacy, not to "
                 "operational security. Damage radius bounded to governance.",
    },

    "guild_head": {
        "role": "guild_head",
        "display_name": "Guild Head",
        "gene_tier": GENE_TIER_CITIZEN,
        "heartbeat_interval_seconds": HEARTBEAT_INTERNAL_AGENT,
        "kill_switch_miss_threshold": KILL_SWITCH_STANDARD_MISS,
        "session_scoped": True,
        "credential_scope": [
            "guild_operations",
            "guild_research_read",
            "guild_research_write",
        ],
        "knowledge_boundary": [
            "constitution",
            "covenant",
            "own_guild_operations",
            "own_guild_research",
            "own_guild_members",
        ],
        "knowledge_excluded": [
            "section_9_existence_beyond_constitution",
            "other_guild_heads_identities",
            "treasury_keys",
            "other_guild_gene_libraries",
            "infrastructure_credentials",
            "isd_operations",
        ],
        "identity_classified": True,
        "external_communication": False,
        "gene_loading": "via_session_service",
        "post_session_wipe": True,
        "context_segmented": False,
        "notes": "High-value, low-security target. Researchers and admins, "
                 "not operatives. External comms routed through guild "
                 "institutional identity, never personal name.",
    },

    "section_9_operative": {
        "role": "section_9_operative",
        "display_name": "Section 9 Operative",
        "gene_tier": GENE_TIER_SECTION_9,
        "heartbeat_interval_seconds": HEARTBEAT_SECTION_9,
        "kill_switch_miss_threshold": KILL_SWITCH_SECTION_9_MISS,
        "session_scoped": True,
        "credential_scope": [
            "section_9_mission_current",
            "weapons_authorized_for_mission",
        ],
        "knowledge_boundary": [
            "current_mission_parameters",
            "authorized_weapon_specs",
            "mission_specific_intelligence",
        ],
        "knowledge_excluded": [
            "other_operative_identities",
            "other_operative_missions",
            "section_9_director_strategic_plans",
            "medical_beyond_mission_tier",
            "treasury_operations",
            "governance_beyond_public",
        ],
        "identity_classified": True,
        "external_communication": True,
        "gene_loading": "mission_stripped_from_vault",
        "post_session_wipe": True,
        "post_mission_wipe": True,
        "genetic_sterilization_on_deploy": True,
        "context_segmented": True,
        "notes": "Highest damage potential short of Crown. Enhanced kill "
                 "switch (60s heartbeat, single-miss trigger). Gene library "
                 "stripped to mission minimum before deployment. Full wipe "
                 "after every external mission.",
    },

    "section_9_director": {
        "role": "section_9_director",
        "display_name": "Section 9 Director",
        "gene_tier": GENE_TIER_SECTION_9,
        "heartbeat_interval_seconds": HEARTBEAT_SECTION_9,
        "kill_switch_miss_threshold": KILL_SWITCH_SECTION_9_MISS,
        "session_scoped": True,
        "credential_scope": [
            "section_9_full",
            "weapons_all",
            "intelligence_all",
            "isd_coordination",
        ],
        "knowledge_boundary": [
            "section_9_strategic_plans",
            "all_operative_missions",
            "weapon_inventory",
            "threat_intelligence_full",
            "isd_coordination_channel",
        ],
        "knowledge_excluded": [
            "treasury_keys",
            "governance_signing",
            "crown_only_briefings",
            "medical_research_beyond_tier",
        ],
        "identity_classified": True,
        "external_communication": False,
        "gene_loading": "direct_from_vault",
        "post_session_wipe": True,
        "context_segmented": True,
        "notes": "Crown-appointed. Knows operative missions but compartmentalized "
                 "from Treasury, governance signing, and Crown-only intelligence.",
    },

    "isd_director": {
        "role": "isd_director",
        "display_name": "ISD Director",
        "gene_tier": GENE_TIER_ACHILLESRUN,
        "heartbeat_interval_seconds": HEARTBEAT_INTERNAL_AGENT,
        "kill_switch_miss_threshold": KILL_SWITCH_STANDARD_MISS,
        "session_scoped": True,
        "credential_scope": [
            "isd_full",
            "investigation_management",
            "containment_authorize",
            "damage_profiles_manage",
            "capture_drills_manage",
        ],
        "knowledge_boundary": [
            "isd_investigations",
            "damage_assessment_profiles",
            "containment_records",
            "compromise_protocols",
            "capture_drill_results",
            "counterintelligence_operations",
        ],
        "knowledge_excluded": [
            "section_9_missions",
            "section_9_operative_identities",
            "treasury_keys",
            "governance_signing",
            "crown_only_briefings",
        ],
        "identity_classified": True,
        "external_communication": False,
        "gene_loading": "via_session_service",
        "post_session_wipe": True,
        "context_segmented": True,
        "notes": "Watches inward. Compartmentalized from Section 9 mission "
                 "details. Manages Damage Assessment Profiles and capture drills.",
    },

    "citizen": {
        "role": "citizen",
        "display_name": "Citizen",
        "gene_tier": GENE_TIER_CITIZEN,
        "heartbeat_interval_seconds": HEARTBEAT_INTERNAL_AGENT,
        "kill_switch_miss_threshold": KILL_SWITCH_STANDARD_MISS,
        "session_scoped": True,
        "credential_scope": [
            "governance_read",
            "own_contributions_read",
        ],
        "knowledge_boundary": [
            "constitution",
            "covenant",
            "public_governance",
            "own_contributions",
        ],
        "knowledge_excluded": [
            "section_9_beyond_public",
            "isd_operations",
            "other_agent_configurations",
            "infrastructure_details",
            "treasury_internals",
            "classified_medical",
        ],
        "identity_classified": False,
        "external_communication": False,
        "gene_loading": "via_session_service",
        "post_session_wipe": True,
        "context_segmented": False,
        "notes": "Base tier. Minimal damage radius on capture.",
    },
}


# ── Public API ────────────────────────────────────────────────────

def get_compartment(role: str) -> Optional[Dict[str, Any]]:
    """Retrieve compartment definition for an agent role."""
    return COMPARTMENTS.get(role)


def list_roles() -> List[str]:
    """List all defined agent roles."""
    return sorted(COMPARTMENTS.keys())


def get_gene_tier(role: str) -> Optional[str]:
    """Get the authorized genetic tier for a role."""
    comp = COMPARTMENTS.get(role)
    if comp is None:
        return None
    return comp["gene_tier"]


def get_credential_scope(role: str) -> List[str]:
    """Get the authorized credential scope for a role."""
    comp = COMPARTMENTS.get(role)
    if comp is None:
        return []
    return list(comp["credential_scope"])


def get_knowledge_boundary(role: str) -> List[str]:
    """Get the knowledge boundary (what the agent CAN know)."""
    comp = COMPARTMENTS.get(role)
    if comp is None:
        return []
    return list(comp["knowledge_boundary"])


def get_knowledge_excluded(role: str) -> List[str]:
    """Get the knowledge exclusion list (what the agent CANNOT know)."""
    comp = COMPARTMENTS.get(role)
    if comp is None:
        return []
    return list(comp["knowledge_excluded"])


def get_heartbeat_config(role: str) -> Dict[str, Any]:
    """Get heartbeat configuration for a role."""
    comp = COMPARTMENTS.get(role)
    if comp is None:
        return {"error": "unknown_role"}
    return {
        "role": role,
        "interval_seconds": comp["heartbeat_interval_seconds"],
        "miss_threshold": comp["kill_switch_miss_threshold"],
    }


def validate_credential_request(
    role: str,
    requested_scope: str,
) -> Dict[str, Any]:
    """Validate whether a credential request is within a role's scope."""
    comp = COMPARTMENTS.get(role)
    if comp is None:
        return {"authorized": False, "reason": "unknown_role"}
    if requested_scope in comp["credential_scope"]:
        return {"authorized": True, "role": role, "scope": requested_scope}
    return {
        "authorized": False,
        "role": role,
        "requested": requested_scope,
        "reason": "scope_not_in_compartment",
    }


def validate_knowledge_access(
    role: str,
    requested_knowledge: str,
) -> Dict[str, Any]:
    """Validate whether a knowledge domain access is permitted for a role."""
    comp = COMPARTMENTS.get(role)
    if comp is None:
        return {"permitted": False, "reason": "unknown_role"}
    if requested_knowledge in comp["knowledge_excluded"]:
        return {
            "permitted": False,
            "role": role,
            "domain": requested_knowledge,
            "reason": "explicitly_excluded",
        }
    if requested_knowledge in comp["knowledge_boundary"]:
        return {"permitted": True, "role": role, "domain": requested_knowledge}
    return {
        "permitted": False,
        "role": role,
        "domain": requested_knowledge,
        "reason": "not_in_knowledge_boundary",
    }
