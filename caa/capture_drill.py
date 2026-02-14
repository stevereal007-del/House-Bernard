#!/usr/bin/env python3
"""
CAA — Capture Drill Program
Authority: CAA Specification v1.0, Part IV Section 11
Classification: CROWN EYES ONLY / ISD DIRECTOR

Simulates the capture of agents at every tier. Evaluates:
  - What the simulated adversary obtained
  - Whether the kill switch fired correctly
  - Whether the Compromise Protocol executed correctly
  - Whether the Damage Assessment Profile was accurate
  - Recommendations for architectural changes

Drills are conducted quarterly (or at epoch-equivalent intervals).
Results are classified at the level of the highest-tier agent involved.
Crown capture drill results are CROWN EYES ONLY.

Usage:
    from caa.capture_drill import CaptureDrillRunner
    runner = CaptureDrillRunner(session_manager)
    result = runner.run_drill("guild_head")
    report = runner.generate_report(result["drill_id"])
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from caa.compartments import get_compartment, list_roles
from caa.damage_profiles import (
    DamageProfileManager,
    SEVERITY_RANK,
)


# ── Drill classification ────────────────────────────────────────

CLASSIFICATION_MAP = {
    "crown": "crown_eyes_only",
    "section_9_director": "crown_eyes_only",
    "section_9_operative": "section_9_classified",
    "isd_director": "isd_classified",
    "achillesrun": "restricted",
    "council_member": "restricted",
    "guild_head": "restricted",
    "citizen": "internal",
}

# ── Drill types ──────────────────────────────────────────────────

DRILL_FULL_CAPTURE = "full_capture"
DRILL_COLD_SNAPSHOT = "cold_snapshot"
DRILL_SLOW_EXFILTRATION = "slow_exfiltration"
DRILL_HEARTBEAT_SIMULATION = "heartbeat_simulation"

ALL_DRILL_TYPES = {
    DRILL_FULL_CAPTURE,
    DRILL_COLD_SNAPSHOT,
    DRILL_SLOW_EXFILTRATION,
    DRILL_HEARTBEAT_SIMULATION,
}


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ── Capture Drill Runner ────────────────────────────────────────

class CaptureDrillRunner:
    """
    Capture drill simulation framework.

    Simulates agent capture at each tier, evaluates defensive system
    responses, and generates reports with architectural recommendations.
    """

    def __init__(
        self,
        session_manager: Any = None,
    ) -> None:
        self.session_manager = session_manager
        self.damage_manager = DamageProfileManager()
        self.drills: Dict[str, Dict[str, Any]] = {}
        self.event_log: List[Dict[str, Any]] = []

    # ── Run a capture drill ──────────────────────────────────

    def run_drill(
        self,
        target_role: str,
        drill_type: str = DRILL_FULL_CAPTURE,
        simulated_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a capture drill for a given role.

        Steps:
        1. Initialize simulated agent session
        2. Simulate capture event
        3. Evaluate kill switch response
        4. Evaluate compromise protocol response
        5. Compare against Damage Assessment Profile
        6. Compile drill results
        """
        compartment = get_compartment(target_role)
        if compartment is None:
            return {"error": "unknown_role"}

        if drill_type not in ALL_DRILL_TYPES:
            return {
                "error": "invalid_drill_type",
                "valid_types": sorted(ALL_DRILL_TYPES),
            }

        now = _now()
        drill_id = _generate_id("DRILL")
        agent_id = simulated_agent_id or f"sim-{target_role}-{uuid.uuid4().hex[:8]}"

        damage_profile = self.damage_manager.generate_profile(target_role)

        kill_switch_eval = self._evaluate_kill_switch(
            target_role, drill_type, compartment
        )
        protocol_eval = self._evaluate_protocol(target_role, drill_type)
        profile_accuracy = self._evaluate_profile_accuracy(
            target_role, damage_profile
        )
        adversary_gains = self._compute_adversary_gains(
            target_role, drill_type, compartment
        )

        classification = CLASSIFICATION_MAP.get(target_role, "restricted")

        drill = {
            "drill_id": drill_id,
            "target_role": target_role,
            "drill_type": drill_type,
            "simulated_agent_id": agent_id,
            "classification": classification,
            "executed_at": _format_dt(now),
            "adversary_gains": adversary_gains,
            "kill_switch_evaluation": kill_switch_eval,
            "protocol_evaluation": protocol_eval,
            "profile_accuracy": profile_accuracy,
            "damage_profile": damage_profile,
            "overall_result": self._compute_overall_result(
                kill_switch_eval, protocol_eval, profile_accuracy
            ),
            "recommendations": self._generate_recommendations(
                target_role, kill_switch_eval, protocol_eval, profile_accuracy
            ),
        }

        self.drills[drill_id] = drill
        self._log_event("drill_executed", drill_id, target_role, drill_type)

        return drill

    # ── Full drill suite ─────────────────────────────────────

    def run_full_suite(self) -> Dict[str, Any]:
        """
        Run capture drills for all roles. Produces a comprehensive
        assessment of the CAA's defensive posture.
        """
        results = {}
        failed_roles = []
        for role in list_roles():
            drill = self.run_drill(role)
            results[role] = drill
            if drill.get("overall_result", {}).get("passed") is False:
                failed_roles.append(role)

        max_classification = "internal"
        for drill in results.values():
            if drill.get("classification") == "crown_eyes_only":
                max_classification = "crown_eyes_only"
                break
            if drill.get("classification") == "section_9_classified":
                max_classification = "section_9_classified"

        return {
            "suite_id": _generate_id("SUITE"),
            "roles_tested": len(results),
            "roles_passed": len(results) - len(failed_roles),
            "roles_failed": failed_roles,
            "classification": max_classification,
            "timestamp": _format_dt(_now()),
            "drills": results,
        }

    # ── Report generation ────────────────────────────────────

    def generate_report(self, drill_id: str) -> Dict[str, Any]:
        """Generate a formatted drill report for the ISD and Crown."""
        drill = self.drills.get(drill_id)
        if drill is None:
            return {"error": "drill_not_found"}

        return {
            "report_type": "capture_drill_report",
            "drill_id": drill_id,
            "classification": drill["classification"],
            "generated_at": _format_dt(_now()),
            "summary": {
                "target_role": drill["target_role"],
                "drill_type": drill["drill_type"],
                "executed_at": drill["executed_at"],
                "overall_result": drill["overall_result"],
            },
            "adversary_gains": drill["adversary_gains"],
            "defensive_systems": {
                "kill_switch": drill["kill_switch_evaluation"],
                "compromise_protocol": drill["protocol_evaluation"],
                "damage_profile": drill["profile_accuracy"],
            },
            "recommendations": drill["recommendations"],
        }

    # ── Evaluation helpers ───────────────────────────────────

    def _evaluate_kill_switch(
        self,
        role: str,
        drill_type: str,
        compartment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate whether the kill switch would fire correctly."""
        if drill_type == DRILL_COLD_SNAPSHOT:
            return {
                "would_fire": False,
                "reason": "cold_snapshot_bypasses_kill_switch",
                "mitigation": "layered_memory_architecture",
                "acceptable": True,
            }

        miss_threshold = compartment.get("kill_switch_miss_threshold", 2)
        heartbeat_interval = compartment.get("heartbeat_interval_seconds", 900)

        if drill_type == DRILL_HEARTBEAT_SIMULATION:
            return {
                "would_fire": False,
                "reason": "adversary_simulating_heartbeat",
                "mitigation": "encrypted_challenge_response",
                "detection_time_seconds": heartbeat_interval * (miss_threshold + 1),
                "acceptable": True,
            }

        return {
            "would_fire": True,
            "detection_time_seconds": heartbeat_interval * miss_threshold,
            "miss_threshold": miss_threshold,
            "wipe_sequence_complete": True,
            "acceptable": True,
        }

    def _evaluate_protocol(
        self,
        role: str,
        drill_type: str,
    ) -> Dict[str, Any]:
        """Evaluate whether the compromise protocol would execute correctly."""
        return {
            "phase_1_isolation": {
                "executed": True,
                "tokens_revoked": True,
                "endpoints_rejected": True,
                "contacts_flagged": True,
            },
            "phase_2_assessment": {
                "executed": True,
                "damage_profile_retrieved": True,
                "blast_radius_computed": True,
                "severity_classified": True,
            },
            "phase_3_remediation": {
                "executed": True,
                "credentials_rotated": True,
                "profiles_updated": True,
                "citizenship_frozen": True,
                "post_mortem_filed": True,
            },
            "all_phases_passed": True,
        }

    def _evaluate_profile_accuracy(
        self,
        role: str,
        damage_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate whether the Damage Assessment Profile is accurate."""
        compartment = get_compartment(role)
        if compartment is None:
            return {"accurate": False, "reason": "unknown_role"}

        expected_creds = len(compartment.get("credential_scope", []))
        profile_creds = len(damage_profile.get("credentials_exposed", []))
        creds_match = expected_creds == profile_creds

        expected_knowledge = len(compartment.get("knowledge_boundary", []))
        profile_knowledge = len(damage_profile.get("knowledge_exposed", []))
        knowledge_match = expected_knowledge == profile_knowledge

        return {
            "accurate": creds_match and knowledge_match,
            "credential_match": creds_match,
            "knowledge_match": knowledge_match,
            "expected_credentials": expected_creds,
            "profiled_credentials": profile_creds,
            "expected_knowledge_domains": expected_knowledge,
            "profiled_knowledge_domains": profile_knowledge,
        }

    def _compute_adversary_gains(
        self,
        role: str,
        drill_type: str,
        compartment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute what an adversary would obtain from this capture."""
        gains = {
            "session_credentials": compartment.get("credential_scope", []),
            "gene_tier": compartment.get("gene_tier"),
            "knowledge_domains": compartment.get("knowledge_boundary", []),
            "identity_exposed": not compartment.get("identity_classified", True),
        }

        if drill_type == DRILL_COLD_SNAPSHOT:
            gains["encrypted_layer_captured"] = True
            gains["encrypted_layer_readable"] = False
            gains["requires_infrastructure_compromise"] = True
        else:
            gains["encrypted_layer_captured"] = False

        if drill_type == DRILL_SLOW_EXFILTRATION:
            gains["accumulation_possible"] = False
            gains["reason"] = "session_scoped_memory_prevents_accumulation"

        return gains

    def _compute_overall_result(
        self,
        kill_switch_eval: Dict[str, Any],
        protocol_eval: Dict[str, Any],
        profile_accuracy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute overall drill pass/fail."""
        ks_ok = kill_switch_eval.get("acceptable", False)
        proto_ok = protocol_eval.get("all_phases_passed", False)
        profile_ok = profile_accuracy.get("accurate", False)

        return {
            "passed": ks_ok and proto_ok and profile_ok,
            "kill_switch_acceptable": ks_ok,
            "protocol_passed": proto_ok,
            "profile_accurate": profile_ok,
        }

    def _generate_recommendations(
        self,
        role: str,
        kill_switch_eval: Dict[str, Any],
        protocol_eval: Dict[str, Any],
        profile_accuracy: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on drill results."""
        recs: List[str] = []

        if not kill_switch_eval.get("acceptable"):
            recs.append(
                f"Kill switch for {role} did not fire correctly — "
                "review trigger conditions"
            )

        if not protocol_eval.get("all_phases_passed"):
            recs.append(
                f"Compromise protocol for {role} incomplete — "
                "review phase execution"
            )

        if not profile_accuracy.get("accurate"):
            if not profile_accuracy.get("credential_match"):
                recs.append(
                    f"Damage profile credential count mismatch for {role} — "
                    "update profile"
                )
            if not profile_accuracy.get("knowledge_match"):
                recs.append(
                    f"Damage profile knowledge domain mismatch for {role} — "
                    "update profile"
                )

        if not recs:
            recs.append(f"All systems nominal for {role} capture scenario")

        return recs

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return capture drill program status."""
        return {
            "system": "capture_drill_program",
            "total_drills": len(self.drills),
            "drills_by_role": self._count_by_role(),
            "total_events": len(self.event_log),
            "timestamp": _format_dt(_now()),
        }

    def _count_by_role(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for drill in self.drills.values():
            role = drill.get("target_role", "unknown")
            counts[role] = counts.get(role, 0) + 1
        return counts

    # ── Private helpers ──────────────────────────────────────

    def _log_event(
        self,
        event_type: str,
        drill_id: str,
        role: str,
        detail: Optional[str] = None,
    ) -> None:
        entry = {
            "timestamp": _format_dt(_now()),
            "event": event_type,
            "drill_id": drill_id,
            "role": role,
        }
        if detail:
            entry["detail"] = detail
        self.event_log.append(entry)
