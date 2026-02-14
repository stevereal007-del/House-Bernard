#!/usr/bin/env python3
"""
House Bernard Intelligence Fusion Protocol Engine v1.0
Authority: Internal Security & Intelligence Court Act, Section III

The Fusion Protocol breaks the stovepipe between Section 9 (external),
the ISD (internal), and the Wardens (enforcement). Intelligence flows
through structured channels without contaminating judicial proceedings
or violating citizen rights.

The engine computes referral routing, deadline compliance, and fusion
health metrics. It does not route intelligence — it computes.

Usage:
    from isd.fusion_protocol import FusionProtocolEngine
    fusion = FusionProtocolEngine("isd/isd_state.json")
    result = fusion.create_threat_referral(source, target_organ, data)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Organs participating in fusion ───────────────────────────────

SECURITY_ORGANS = {"section_9", "isd", "wardens"}

# ── Fusion flows (Act Section III) ───────────────────────────────

FLOW_TYPES = {
    "flow_1": {
        "name": "External to Internal",
        "source": "section_9",
        "destination": "isd",
        "route_via": "crown",
        "description": "External threat becomes internal — "
                       "Section 9 tips, ISD builds",
    },
    "flow_2": {
        "name": "Surfacing for Prosecution",
        "source": "isd",
        "destination": "wardens",
        "route_via": "intelligence_court",
        "description": "ISD evidence surfaced to Wardens via "
                       "Clean Brief for open prosecution",
    },
    "flow_3": {
        "name": "Routine to Deeper Threat",
        "source": "wardens",
        "destination": "isd",
        "route_via": "crown",
        "description": "Warden investigation reveals deeper "
                       "internal security threat",
    },
    "flow_4": {
        "name": "Joint Threat Picture",
        "source": "section_9",
        "destination": "isd",
        "route_via": "crown",
        "description": "Bilateral analytical product — not "
                       "investigative action, no warrant needed",
    },
}

# ── Deadline configuration (Act Section III) ─────────────────────

REFERRAL_DEADLINE_HOURS = 48
CROWN_ACKNOWLEDGMENT_HOURS = 24
CROWN_ROUTING_HOURS = 72

# ── Fusion Coordinator configuration (Act Section III) ───────────

COORDINATOR_TERM_DAYS = 90
COORDINATOR_ACCESS_LEVEL = "referral_metadata_only"

# ── Jurisdictional default (Act Section III) ─────────────────────

JURISDICTIONAL_DEFAULT = "isd"
JURISDICTIONAL_OVERRIDE_HOURS = 72


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    """Current UTC time."""
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    """Format datetime to ISO 8601 string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 timestamp. Returns None on failure."""
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ── Engine ───────────────────────────────────────────────────────

class FusionProtocolEngine:
    """
    Intelligence Fusion Protocol computation engine.

    Manages threat referrals between Section 9, ISD, and Wardens.
    Tracks compliance with anti-stovepipe deadlines. Monitors
    fusion health. Read-only computation layer.
    """

    def __init__(self, state_path: str = "isd/isd_state.json") -> None:
        """Load state from JSON file."""
        self.state_path = Path(state_path)
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)
        self.fusion = self.state.get("fusion", {})

    # ── Threat referral creation ─────────────────────────────

    def create_threat_referral(
        self,
        source_organ: str,
        threat_category: str,
        threat_summary: str,
        urgency: str = "routine",
    ) -> Dict[str, Any]:
        """
        Create a threat referral from one security organ to another.
        Referrals are routed through the Crown (Flows 1, 3, 4) or
        through the Intelligence Court (Flow 2 — surfacing).

        The referral is a 'tip' only — the receiving organ builds
        its own independent case. Source methods are never revealed.
        """
        if source_organ not in SECURITY_ORGANS:
            return {
                "error": "invalid_source_organ",
                "valid_organs": sorted(SECURITY_ORGANS),
            }

        if urgency not in ("routine", "priority", "flash"):
            return {
                "error": "invalid_urgency",
                "valid_urgency": ["routine", "priority", "flash"],
            }

        if not threat_summary:
            return {"error": "threat_summary_required"}

        # Determine flow type and destination
        flow = self._determine_flow(source_organ, threat_category)

        now = _now()
        referral = {
            "referral_id": _generate_id("REF"),
            "source_organ": source_organ,
            "destination_organ": flow["destination"],
            "flow_type": flow["flow_id"],
            "flow_name": flow["name"],
            "route_via": flow["route_via"],
            "threat_category": threat_category,
            "threat_summary": threat_summary,
            "urgency": urgency,
            "created": _format_dt(now),
            "transmission_deadline": _format_dt(
                now + timedelta(hours=REFERRAL_DEADLINE_HOURS)
            ),
            "crown_ack_deadline": _format_dt(
                now + timedelta(hours=CROWN_ACKNOWLEDGMENT_HOURS)
            ),
            "crown_routing_deadline": _format_dt(
                now + timedelta(hours=CROWN_ROUTING_HOURS)
            ),
            "status": "pending_transmission",
            "crown_acknowledged": False,
            "crown_routed": False,
        }

        return {"referral": referral}

    # ── Clean Brief production (Flow 2) ──────────────────────

    def produce_clean_brief(
        self,
        investigation_id: str,
        actionable_intelligence: str,
        methods_stripped: bool = True,
    ) -> Dict[str, Any]:
        """
        Produce a Clean Brief for Warden activation. The Clean Brief
        provides enough actionable intelligence for Wardens to begin
        their own open investigation, without revealing ISD methods
        or the existence of the classified investigation.

        The Clean Brief is NEVER introduced in Judiciary proceedings.
        Only the Wardens' independent evidence is admissible.
        """
        if not actionable_intelligence:
            return {"error": "actionable_intelligence_required"}

        if not methods_stripped:
            return {
                "error": "methods_must_be_stripped",
                "detail": "Clean Brief must not contain classified "
                          "sources or methods",
            }

        now = _now()
        return {
            "brief_id": _generate_id("CB"),
            "type": "clean_brief",
            "investigation_id": investigation_id,
            "actionable_intelligence": actionable_intelligence,
            "methods_stripped": True,
            "produced": _format_dt(now),
            "recipient": "wardens",
            "admissible_in_proceedings": False,
            "note": "Clean Brief is never introduced in Judiciary "
                    "proceedings. Wardens build independent case.",
        }

    def produce_flash_clean_brief(
        self,
        investigation_id: str,
        actionable_intelligence: str,
        imminent_threat: bool = True,
    ) -> Dict[str, Any]:
        """
        Produce a flash Clean Brief for imminent threat response.
        Stripped of classified methods but containing enough
        actionable intelligence for Wardens to act immediately.
        """
        if not imminent_threat:
            return {
                "error": "flash_brief_requires_imminent_threat",
                "detail": "Use standard Clean Brief for non-imminent matters",
            }

        brief = self.produce_clean_brief(
            investigation_id, actionable_intelligence
        )
        if "error" in brief:
            return brief

        brief["type"] = "flash_clean_brief"
        brief["urgency"] = "flash"
        brief["note"] = (
            "Flash Clean Brief — imminent threat. Wardens may "
            "exercise 72-hour emergency authority."
        )
        return brief

    # ── Joint Threat Briefing (Flow 4) ───────────────────────

    def create_joint_threat_briefing(
        self,
        section_9_assessment: str,
        isd_assessment: str,
        combined_threat_picture: str,
    ) -> Dict[str, Any]:
        """
        Create a Joint Threat Briefing combining Section 9
        (external) and ISD (internal) intelligence for the Crown.
        This is an analytical product, not an investigative action —
        no warrant required.
        """
        if not section_9_assessment or not isd_assessment:
            return {"error": "both_assessments_required"}

        now = _now()
        return {
            "briefing_id": _generate_id("JTB"),
            "type": "joint_threat_briefing",
            "recipient": "crown",
            "section_9_assessment": section_9_assessment,
            "isd_assessment": isd_assessment,
            "combined_threat_picture": combined_threat_picture,
            "classification": "highest_of_either_contribution",
            "produced": _format_dt(now),
            "warrant_required": False,
            "note": "Analytical product only. May not be used to "
                    "circumvent warrant requirement.",
        }

    # ── Referral compliance tracking ─────────────────────────

    def check_referral_compliance(
        self, referral_id: str
    ) -> Dict[str, Any]:
        """
        Check whether a referral is meeting its deadlines:
        - 48-hour transmission deadline
        - 24-hour Crown acknowledgment deadline
        - 72-hour Crown routing deadline
        """
        referral = self._get_referral(referral_id)
        if referral is None:
            return {"error": "referral_not_found"}

        now = _now()
        violations = []

        # Check transmission deadline
        tx_deadline = _parse_dt(referral.get("transmission_deadline"))
        if tx_deadline and now > tx_deadline:
            if referral.get("status") == "pending_transmission":
                violations.append({
                    "type": "transmission_overdue",
                    "deadline": referral.get("transmission_deadline"),
                    "hours_overdue": round(
                        (now - tx_deadline).total_seconds() / 3600, 2
                    ),
                })

        # Check Crown acknowledgment
        ack_deadline = _parse_dt(referral.get("crown_ack_deadline"))
        if ack_deadline and now > ack_deadline:
            if not referral.get("crown_acknowledged", False):
                violations.append({
                    "type": "crown_acknowledgment_overdue",
                    "deadline": referral.get("crown_ack_deadline"),
                    "hours_overdue": round(
                        (now - ack_deadline).total_seconds() / 3600, 2
                    ),
                    "auto_alert": "intelligence_court",
                })

        # Check Crown routing
        route_deadline = _parse_dt(referral.get("crown_routing_deadline"))
        if route_deadline and now > route_deadline:
            if not referral.get("crown_routed", False):
                violations.append({
                    "type": "crown_routing_overdue",
                    "deadline": referral.get("crown_routing_deadline"),
                    "hours_overdue": round(
                        (now - route_deadline).total_seconds() / 3600, 2
                    ),
                })

        return {
            "referral_id": referral_id,
            "compliant": len(violations) == 0,
            "violations": violations,
            "checked": _format_dt(now),
        }

    # ── Jurisdictional resolution (Act Section III) ──────────

    def resolve_jurisdiction(
        self,
        threat_description: str,
        section_9_claim: bool,
        isd_claim: bool,
        crown_override: Optional[str] = None,
        crown_override_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve jurisdictional conflict when a threat spans the
        external-internal boundary. Default: ISD has primary
        jurisdiction for investigative action targeting a citizen.
        Crown may override with written determination.
        """
        now = _now()

        if crown_override and crown_override_reason:
            return {
                "resolution_id": _generate_id("JRES"),
                "jurisdiction": crown_override,
                "method": "crown_override",
                "reason": crown_override_reason,
                "override_filed_with": "intelligence_court",
                "resolved": _format_dt(now),
                "deadline_met": True,
            }

        if section_9_claim and isd_claim:
            return {
                "resolution_id": _generate_id("JRES"),
                "jurisdiction": JURISDICTIONAL_DEFAULT,
                "method": "default_rule",
                "detail": "ISD has primary jurisdiction for any "
                          "investigative action targeting a House Bernard "
                          "citizen, regardless of external origin. Section 9 "
                          "retains external dimension.",
                "crown_override_available": True,
                "crown_override_deadline_hours": JURISDICTIONAL_OVERRIDE_HOURS,
                "resolved": _format_dt(now),
            }

        if section_9_claim and not isd_claim:
            return {
                "resolution_id": _generate_id("JRES"),
                "jurisdiction": "section_9",
                "method": "uncontested",
                "resolved": _format_dt(now),
            }

        if isd_claim and not section_9_claim:
            return {
                "resolution_id": _generate_id("JRES"),
                "jurisdiction": "isd",
                "method": "uncontested",
                "resolved": _format_dt(now),
            }

        return {
            "error": "no_jurisdiction_claimed",
            "detail": "At least one organ must claim jurisdiction",
        }

    # ── Fusion Coordinator management ────────────────────────

    def check_coordinator_status(self) -> Dict[str, Any]:
        """
        Check Fusion Coordinator term status and access compliance.
        Coordinator serves 90-day terms with no consecutive terms.
        """
        coordinator = self.fusion.get("coordinator")

        if coordinator is None:
            return {
                "coordinator_active": False,
                "detail": "No Fusion Coordinator designated. Crown may "
                          "serve as coordinator during Founding Period.",
            }

        now = _now()
        term_start = _parse_dt(self.fusion.get("coordinator_term_start"))
        term_days = self.fusion.get("coordinator_term_days", COORDINATOR_TERM_DAYS)

        if term_start is None:
            return {
                "coordinator_active": True,
                "coordinator": coordinator,
                "term_status": "unknown",
                "detail": "Term start date not recorded",
            }

        term_end = term_start + timedelta(days=term_days)
        expired = now > term_end
        days_remaining = max(0, (term_end - now).days)

        return {
            "coordinator_active": not expired,
            "coordinator": coordinator,
            "term_start": _format_dt(term_start),
            "term_end": _format_dt(term_end),
            "expired": expired,
            "days_remaining": days_remaining,
            "access_level": COORDINATOR_ACCESS_LEVEL,
            "rotation_required": expired,
            "consecutive_terms_prohibited": True,
        }

    # ── Fusion health metrics ────────────────────────────────

    def fusion_health_report(self) -> Dict[str, Any]:
        """
        Compute fusion system health for quarterly review.
        Identifies gaps, delays, and missed connections.
        """
        pending = self.fusion.get("pending_referrals", [])
        now = _now()

        overdue_referrals = []
        stalled_referrals = []

        for ref in pending:
            tx_deadline = _parse_dt(ref.get("transmission_deadline"))
            if tx_deadline and now > tx_deadline:
                if ref.get("status") == "pending_transmission":
                    overdue_referrals.append(ref.get("referral_id"))

            ack_deadline = _parse_dt(ref.get("crown_ack_deadline"))
            if ack_deadline and now > ack_deadline:
                if not ref.get("crown_acknowledged", False):
                    stalled_referrals.append(ref.get("referral_id"))

        coordinator = self.check_coordinator_status()

        return {
            "report_type": "fusion_health",
            "generated": _format_dt(now),
            "pending_referrals": len(pending),
            "overdue_referrals": len(overdue_referrals),
            "stalled_at_crown": len(stalled_referrals),
            "coordinator_active": coordinator.get("coordinator_active", False),
            "intelligence_gaps_detected": len(overdue_referrals) > 0,
            "health_status": self._compute_fusion_health(
                len(overdue_referrals), len(stalled_referrals)
            ),
            "overdue_ids": overdue_referrals,
            "stalled_ids": stalled_referrals,
        }

    # ── Anti-stovepipe check ─────────────────────────────────

    def anti_stovepipe_audit(self) -> Dict[str, Any]:
        """
        Audit the fusion system for stovepipe indicators.
        Checks all five mandatory anti-stovepipe requirements
        from Act Section III.
        """
        now = _now()
        checks = []

        # 1. Referral deadlines (48 hours)
        pending = self.fusion.get("pending_referrals", [])
        overdue = sum(
            1 for r in pending
            if _parse_dt(r.get("transmission_deadline"))
            and _now() > _parse_dt(r.get("transmission_deadline"))
            and r.get("status") == "pending_transmission"
        )
        checks.append({
            "requirement": "referral_deadlines",
            "compliant": overdue == 0,
            "overdue_count": overdue,
        })

        # 2. Crown acknowledgment (24 hours)
        unacked = sum(
            1 for r in pending
            if _parse_dt(r.get("crown_ack_deadline"))
            and _now() > _parse_dt(r.get("crown_ack_deadline"))
            and not r.get("crown_acknowledged", False)
        )
        checks.append({
            "requirement": "crown_acknowledgment",
            "compliant": unacked == 0,
            "unacknowledged_count": unacked,
            "auto_alert_triggered": unacked > 0,
        })

        # 3. Quarterly fusion review
        reviews = self.fusion.get("quarterly_reviews", [])
        last_review = None
        if reviews:
            last_review = _parse_dt(reviews[-1].get("date"))
        review_overdue = (
            last_review is None
            or (now - last_review).days > 100
        )
        checks.append({
            "requirement": "quarterly_fusion_review",
            "compliant": not review_overdue,
            "last_review": _format_dt(last_review) if last_review else None,
        })

        # 4. Annual structural audit (by Intelligence Court)
        # Placeholder — tracked in intelligence_court state
        checks.append({
            "requirement": "annual_structural_audit",
            "compliant": True,
            "note": "Tracked by Intelligence Court",
        })

        # 5. Oversight saturation circuit breaker
        court = self.state.get("intelligence_court", {})
        saturated = court.get("oversight_saturation", False)
        checks.append({
            "requirement": "oversight_capacity_circuit_breaker",
            "saturated": saturated,
            "compliant": not saturated,
        })

        all_compliant = all(c.get("compliant", False) for c in checks)

        return {
            "audit_type": "anti_stovepipe",
            "generated": _format_dt(now),
            "all_compliant": all_compliant,
            "checks": checks,
            "stovepipe_risk": not all_compliant,
        }

    # ── Private helpers ──────────────────────────────────────

    def _get_referral(self, referral_id: str) -> Optional[Dict]:
        """Find a referral by ID."""
        for r in self.fusion.get("pending_referrals", []):
            if r.get("referral_id") == referral_id:
                return r
        # Also check inbound/outbound in main state
        for r in self.state.get("threat_referrals_inbound", []):
            if r.get("referral_id") == referral_id:
                return r
        for r in self.state.get("threat_referrals_outbound", []):
            if r.get("referral_id") == referral_id:
                return r
        return None

    def _determine_flow(
        self, source_organ: str, threat_category: str
    ) -> Dict[str, str]:
        """Determine which fusion flow applies."""
        if source_organ == "section_9":
            if threat_category in (
                "insider_threat",
                "penetration_operation",
                "sybil_in_progress",
            ):
                return {
                    "flow_id": "flow_1",
                    "name": "External to Internal",
                    "destination": "isd",
                    "route_via": "crown",
                }
            return {
                "flow_id": "flow_4",
                "name": "Joint Threat Picture",
                "destination": "isd",
                "route_via": "crown",
            }

        if source_organ == "wardens":
            return {
                "flow_id": "flow_3",
                "name": "Routine to Deeper Threat",
                "destination": "isd",
                "route_via": "crown",
            }

        if source_organ == "isd":
            return {
                "flow_id": "flow_2",
                "name": "Surfacing for Prosecution",
                "destination": "wardens",
                "route_via": "intelligence_court",
            }

        return {
            "flow_id": "unknown",
            "name": "Unknown",
            "destination": "unknown",
            "route_via": "crown",
        }

    def _compute_fusion_health(
        self, overdue: int, stalled: int
    ) -> str:
        """Compute fusion health status from metrics."""
        if overdue == 0 and stalled == 0:
            return "healthy"
        elif overdue > 3 or stalled > 2:
            return "critical"
        elif overdue > 0 or stalled > 0:
            return "degraded"
        return "healthy"
