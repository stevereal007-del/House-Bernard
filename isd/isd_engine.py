#!/usr/bin/env python3
"""
House Bernard Internal Security Directorate (ISD) Engine v1.0
Authority: Internal Security & Intelligence Court Act

The ISD is House Bernard's counterintelligence organ. Section 9
watches outward. The ISD watches inward. The engine computes
investigation outcomes, threat assessments, and compliance status.
It does not take action — it computes.

Usage:
    from isd.isd_engine import ISDEngine
    engine = ISDEngine("isd/isd_state.json")
    result = engine.open_investigation(warrant_id, target, threat_basis)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Threat categories (Act Section I — Mandate) ─────────────────

THREAT_CATEGORIES = {
    "insider_threat",
    "penetration_operation",
    "sybil_in_progress",
    "corruption",
    "intelligence_leak",
    "counter_deception",
}

# ── Severity and attribution (aligned with Section 9 matrix) ────

SEVERITY_LEVELS = {"S1", "S2", "S3", "S4"}
ATTRIBUTION_LEVELS = {"A1", "A2", "A3", "A4"}

# ── Investigation status lifecycle ───────────────────────────────

INVESTIGATION_STATUSES = {
    "active",
    "suspended",
    "pending_renewal",
    "surfacing_requested",
    "surfaced",
    "closed_exonerated",
    "closed_referred",
    "closed_terminated",
}

# ── Containment (12-hour defensive max per Act Section I) ───────

CONTAINMENT_MAX_HOURS = 12
CONTAINMENT_REVIEW_HOURS = 24

# ── Warrant duration limits (Act Section II) ────────────────────

WARRANT_INITIAL_DAYS = 90
WARRANT_RENEWAL_1_DAYS = 90
WARRANT_RENEWAL_2_DAYS = 90
WARRANT_SUBSEQUENT_DAYS = 60
WARRANT_HARD_LIMIT_DAYS = 730

# ── Minimization purge window (Act Section IV.4) ────────────────

MINIMIZATION_PURGE_HOURS = 72

# ── Exoneration seal window (Act Section IV.5) ──────────────────

EXONERATION_SEAL_DAYS = 30

# ── Closure review window (Act Section IV.5 safeguard) ──────────

CLOSURE_REVIEW_DAYS = 14

# ── Investigation petition cooldown (Act Section IV) ────────────

PETITION_COOLDOWN_DAYS = 180


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

class ISDEngine:
    """
    Internal Security Directorate computation engine.

    Manages investigation lifecycle, threat assessment, containment
    evaluation, and compliance tracking. Read-only computation layer:
    loads JSON state, computes outcomes, returns JSON-serializable
    results. Never modifies state on disk.
    """

    def __init__(self, state_path: str = "isd/isd_state.json") -> None:
        """Load ISD state from JSON file."""
        self.state_path = Path(state_path)
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)

    # ── Investigation lifecycle ──────────────────────────────

    def open_investigation(
        self,
        warrant_id: str,
        target_id: str,
        threat_category: str,
        threat_basis: str,
        scope: str,
        lead_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Open a new investigation backed by an Intelligence Court warrant.

        Returns the investigation record. Does not persist — the caller
        is responsible for appending to state and saving.
        """
        if threat_category not in THREAT_CATEGORIES:
            return {
                "error": "invalid_threat_category",
                "valid_categories": sorted(THREAT_CATEGORIES),
            }

        if not warrant_id or not target_id or not threat_basis:
            return {"error": "missing_required_fields"}

        now = _now()
        investigation = {
            "investigation_id": _generate_id("INV"),
            "warrant_id": warrant_id,
            "target_id": target_id,
            "threat_category": threat_category,
            "threat_basis": threat_basis,
            "scope": scope,
            "lead_agent": lead_agent,
            "status": "active",
            "opened": _format_dt(now),
            "last_reviewed": _format_dt(now),
            "renewals": 0,
            "containment_actions": [],
            "minimization_log": [],
            "closure": None,
        }
        return {"investigation": investigation}

    def close_investigation(
        self,
        investigation_id: str,
        finding: str,
        lead_agent_certification: bool,
        closure_summary: str,
    ) -> Dict[str, Any]:
        """
        Compute investigation closure. Requires lead agent certification
        per Act Section IV.5 safeguard. Closure must be reviewed by the
        Intelligence Court within 14 days.

        finding must be one of: "exonerated", "referred", "terminated"
        """
        inv = self._get_investigation(investigation_id)
        if inv is None:
            return {"error": "investigation_not_found"}

        if finding not in ("exonerated", "referred", "terminated"):
            return {
                "error": "invalid_finding",
                "valid_findings": ["exonerated", "referred", "terminated"],
            }

        if not lead_agent_certification:
            return {"error": "lead_agent_certification_required"}

        if not closure_summary:
            return {"error": "closure_summary_required"}

        now = _now()
        closure = {
            "finding": finding,
            "closure_summary": closure_summary,
            "lead_agent_certified": True,
            "closure_requested": _format_dt(now),
            "court_review_deadline": _format_dt(
                now + timedelta(days=CLOSURE_REVIEW_DAYS)
            ),
            "court_approved": False,
            "sealed": False,
        }

        if finding == "exonerated":
            closure["seal_deadline"] = _format_dt(
                now + timedelta(days=CLOSURE_REVIEW_DAYS + EXONERATION_SEAL_DAYS)
            )

        return {
            "investigation_id": investigation_id,
            "status": f"closed_{finding}",
            "closure": closure,
        }

    def compute_investigation_duration(
        self, investigation_id: str
    ) -> Dict[str, Any]:
        """
        Compute how long an investigation has been running and whether
        it is approaching or has exceeded warrant limits.
        """
        inv = self._get_investigation(investigation_id)
        if inv is None:
            return {"error": "investigation_not_found"}

        opened = _parse_dt(inv.get("opened"))
        if opened is None:
            return {"error": "invalid_opened_timestamp"}

        now = _now()
        elapsed = now - opened
        elapsed_days = elapsed.days

        renewals = inv.get("renewals", 0)
        current_limit = self._compute_warrant_limit_days(renewals)

        return {
            "investigation_id": investigation_id,
            "elapsed_days": elapsed_days,
            "renewals": renewals,
            "current_warrant_limit_days": current_limit,
            "hard_limit_days": WARRANT_HARD_LIMIT_DAYS,
            "hard_limit_reached": elapsed_days >= WARRANT_HARD_LIMIT_DAYS,
            "approaching_hard_limit": elapsed_days >= (WARRANT_HARD_LIMIT_DAYS - 60),
            "requires_crown_authorization": renewals >= 3,
            "requires_full_bench_review": elapsed_days >= WARRANT_HARD_LIMIT_DAYS,
        }

    # ── Threat assessment ────────────────────────────────────

    def assess_threat(
        self,
        indicator_id: str,
        threat_category: str,
        severity: str,
        attribution: str,
        description: str,
        source_organ: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assess a threat indicator and produce a recommendation.
        The ISD does not act — it computes a recommendation.
        """
        if threat_category not in THREAT_CATEGORIES:
            return {"error": "invalid_threat_category"}
        if severity not in SEVERITY_LEVELS:
            return {"error": "invalid_severity"}
        if attribution not in ATTRIBUTION_LEVELS:
            return {"error": "invalid_attribution"}

        recommendation = self._compute_recommendation(severity, attribution)

        return {
            "assessment_id": _generate_id("ASMT"),
            "indicator_id": indicator_id,
            "threat_category": threat_category,
            "severity": severity,
            "attribution": attribution,
            "description": description,
            "source_organ": source_organ,
            "recommendation": recommendation,
            "timestamp": _format_dt(_now()),
        }

    # ── Containment (Act Section I — 12-hour defensive) ─────

    def evaluate_containment(
        self,
        investigation_id: str,
        threat_description: str,
        proposed_actions: List[str],
        crown_authorized: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate whether a defensive containment action is justified.
        Containment is limited to 12 hours and is defensive only:
        freezing access, isolating accounts, quarantining submissions.

        Returns containment record. Does not execute containment.
        """
        inv = self._get_investigation(investigation_id)
        if inv is None:
            return {"error": "investigation_not_found"}

        if not crown_authorized:
            return {
                "error": "crown_authorization_required",
                "reason": "Containment actions require Crown authorization "
                          "per Act Section I",
            }

        valid_actions = {
            "freeze_system_access",
            "isolate_accounts",
            "quarantine_submissions",
        }
        invalid = [a for a in proposed_actions if a not in valid_actions]
        if invalid:
            return {
                "error": "invalid_containment_actions",
                "invalid": invalid,
                "valid_actions": sorted(valid_actions),
            }

        now = _now()
        return {
            "containment_id": _generate_id("CTN"),
            "investigation_id": investigation_id,
            "threat_description": threat_description,
            "actions": proposed_actions,
            "crown_authorized": True,
            "initiated": _format_dt(now),
            "expires": _format_dt(now + timedelta(hours=CONTAINMENT_MAX_HOURS)),
            "court_review_deadline": _format_dt(
                now + timedelta(hours=CONTAINMENT_REVIEW_HOURS)
            ),
            "status": "authorized",
            "defensive_only": True,
        }

    def check_containment_expiry(
        self, containment_id: str
    ) -> Dict[str, Any]:
        """
        Check whether a containment action has expired or needs
        Intelligence Court review.
        """
        containment = self._get_containment(containment_id)
        if containment is None:
            return {"error": "containment_not_found"}

        now = _now()
        expires = _parse_dt(containment.get("expires"))
        review_deadline = _parse_dt(containment.get("court_review_deadline"))

        expired = expires is not None and now >= expires
        review_overdue = review_deadline is not None and now >= review_deadline

        return {
            "containment_id": containment_id,
            "expired": expired,
            "review_overdue": review_overdue,
            "must_release": expired,
            "hours_remaining": max(
                0, round((expires - now).total_seconds() / 3600, 2)
            ) if expires else 0,
        }

    # ── Crown Compromise Protocol (Act Section I) ───────────

    def evaluate_crown_bypass(
        self,
        evidence_of_compromise: str,
        why_crown_route_compromised: str,
        requested_actions: List[str],
    ) -> Dict[str, Any]:
        """
        Evaluate an Emergency Crown Bypass Warrant request.
        This is the most extraordinary power in the Act.
        Requires unanimous Intelligence Court authorization.

        Returns the bypass request record for Intelligence Court review.
        """
        if not evidence_of_compromise:
            return {"error": "evidence_of_compromise_required"}
        if not why_crown_route_compromised:
            return {"error": "crown_route_compromise_explanation_required"}
        if not requested_actions:
            return {"error": "requested_actions_required"}

        now = _now()
        return {
            "bypass_id": _generate_id("BYPASS"),
            "type": "emergency_crown_bypass_warrant",
            "evidence_of_compromise": evidence_of_compromise,
            "why_crown_route_compromised": why_crown_route_compromised,
            "requested_actions": requested_actions,
            "requires_unanimous_court": True,
            "max_duration_hours": CONTAINMENT_MAX_HOURS,
            "mandatory_full_bench_review_days": 7,
            "submitted": _format_dt(now),
            "status": "pending_court_review",
        }

    # ── Imminent Threat Alert (Act Section I) ────────────────

    def imminent_threat_alert(
        self,
        investigation_id: str,
        threat_description: str,
        recommended_response: str,
    ) -> Dict[str, Any]:
        """
        Produce an Imminent Threat Alert for the Crown.
        The Crown decides response: emergency declaration,
        Warden activation via clean brief, or containment.
        """
        inv = self._get_investigation(investigation_id)
        if inv is None:
            return {"error": "investigation_not_found"}

        if inv.get("status") != "active":
            return {
                "error": "investigation_not_active",
                "status": inv.get("status"),
            }

        valid_responses = {
            "declare_emergency",
            "warden_activation",
            "defensive_containment",
        }
        if recommended_response not in valid_responses:
            return {
                "error": "invalid_recommended_response",
                "valid_responses": sorted(valid_responses),
            }

        return {
            "alert_id": _generate_id("ITA"),
            "investigation_id": investigation_id,
            "threat_description": threat_description,
            "recommended_response": recommended_response,
            "crown_options": sorted(valid_responses),
            "timestamp": _format_dt(_now()),
            "status": "pending_crown_decision",
        }

    # ── Accountability (Act Section I — reporting) ───────────

    def monthly_report(self) -> Dict[str, Any]:
        """
        Compute monthly classified report for the Intelligence Court.
        Details all active investigations, warrant utilization, and findings.
        """
        active = [
            i for i in self.state.get("investigations", [])
            if i.get("status") == "active"
        ]
        suspended = [
            i for i in self.state.get("investigations", [])
            if i.get("status") == "suspended"
        ]
        closed_this_period = [
            i for i in self.state.get("investigations", [])
            if i.get("status", "").startswith("closed_")
        ]

        warrants = self.state.get("warrants", [])
        active_warrants = [w for w in warrants if w.get("status") == "active"]

        return {
            "report_type": "monthly_classified",
            "recipient": "intelligence_court",
            "generated": _format_dt(_now()),
            "active_investigations": len(active),
            "suspended_investigations": len(suspended),
            "closed_investigations": len(closed_this_period),
            "active_warrants": len(active_warrants),
            "threat_categories": self._count_by_field(active, "threat_category"),
            "containment_actions": len(self.state.get("containment_actions", [])),
        }

    def quarterly_briefing(self) -> Dict[str, Any]:
        """
        Compute quarterly classified briefing for the Gang of Two.
        Summarizes threat landscape and ISD activities WITHOUT
        revealing specific targets or methods.
        """
        investigations = self.state.get("investigations", [])
        categories = self._count_by_field(investigations, "threat_category")

        return {
            "report_type": "quarterly_classified_briefing",
            "recipients": ["speaker", "designated_council_member"],
            "generated": _format_dt(_now()),
            "classification": "verbal_only_no_written_materials",
            "threat_landscape": {
                "total_investigations": len(investigations),
                "categories": categories,
                "posture": self._compute_threat_posture(),
            },
            "note": "No specific investigation counts, target demographics, "
                    "or information allowing inference about specific "
                    "investigations per Act Section I",
        }

    def annual_report(self) -> Dict[str, Any]:
        """
        Compute annual classified report for the Crown assessing
        ISD effectiveness, resource utilization, and proposed budget.
        """
        investigations = self.state.get("investigations", [])
        active = [i for i in investigations if i.get("status") == "active"]
        closed = [
            i for i in investigations
            if i.get("status", "").startswith("closed_")
        ]
        agents = self.state.get("directorate", {}).get("agents", [])

        return {
            "report_type": "annual_classified",
            "recipient": "crown",
            "generated": _format_dt(_now()),
            "effectiveness": {
                "total_investigations": len(investigations),
                "active": len(active),
                "resolved": len(closed),
                "resolution_rate": round(
                    len(closed) / max(1, len(investigations)), 4
                ),
            },
            "resources": {
                "agents_deployed": len(agents),
                "director_status": self.state.get("directorate", {}).get("status"),
            },
            "threat_posture": self._compute_threat_posture(),
        }

    # ── Minimization compliance (Act Section II/IV) ──────────

    def check_minimization_compliance(
        self, investigation_id: str
    ) -> Dict[str, Any]:
        """
        Check whether an investigation's minimization procedures
        are compliant. Innocent party data must be purged within
        72 hours per Act Section IV.4.
        """
        inv = self._get_investigation(investigation_id)
        if inv is None:
            return {"error": "investigation_not_found"}

        now = _now()
        violations = []

        for entry in inv.get("minimization_log", []):
            if entry.get("action") != "retained":
                continue
            retained_at = _parse_dt(entry.get("timestamp"))
            if retained_at is None:
                continue
            hours_held = (now - retained_at).total_seconds() / 3600
            if hours_held > MINIMIZATION_PURGE_HOURS and not entry.get("justified"):
                violations.append({
                    "data_id": entry.get("data_id"),
                    "hours_held": round(hours_held, 2),
                    "max_allowed_hours": MINIMIZATION_PURGE_HOURS,
                    "justification_provided": False,
                })

        return {
            "investigation_id": investigation_id,
            "compliant": len(violations) == 0,
            "violations": violations,
            "checked": _format_dt(now),
        }

    # ── Citizen petition (Act Section IV) ────────────────────

    def evaluate_petition(
        self, citizen_id: str, stated_concern: str
    ) -> Dict[str, Any]:
        """
        Process a citizen's petition to the Intelligence Court.
        The Court responds with one of two outcomes, intentionally
        indistinguishable across scenarios per Act Section IV.

        Does NOT confirm or deny the existence of any investigation.
        """
        if not citizen_id or not stated_concern:
            return {"error": "citizen_id_and_concern_required"}

        # Check petition frequency limit (180 days)
        petition_history = [
            p for p in self.state.get("investigations", [])
            if p.get("petitioner") == citizen_id
        ]
        # This is a placeholder — actual implementation would check
        # petition records, not investigations

        now = _now()

        # Intentionally identical response structure regardless of
        # whether an investigation exists
        if len(stated_concern.strip()) < 10:
            return {
                "petition_id": _generate_id("PET"),
                "citizen_id": citizen_id,
                "response": "petition_requires_additional_basis",
                "detail": "The stated concern is too vague to evaluate. "
                          "Please provide more specific facts.",
                "timestamp": _format_dt(now),
            }

        return {
            "petition_id": _generate_id("PET"),
            "citizen_id": citizen_id,
            "response": "no_action_required",
            "detail": "The Court has reviewed the matter and determined "
                      "that no action is required.",
            "timestamp": _format_dt(now),
            "note": "Response is intentionally identical across: no "
                    "investigation, lawful investigation, and remediated "
                    "investigation per Act Section IV",
        }

    # ── Directorate status ───────────────────────────────────

    def directorate_status(self) -> Dict[str, Any]:
        """Return current ISD directorate status summary."""
        d = self.state.get("directorate", {})
        investigations = self.state.get("investigations", [])
        active = [i for i in investigations if i.get("status") == "active"]

        return {
            "director": d.get("director"),
            "director_appointed": d.get("director_appointed"),
            "confirmed_by_judiciary": d.get("director_confirmed_by_judiciary", False),
            "status": d.get("status", "unknown"),
            "agent_count": len(d.get("agents", [])),
            "active_investigations": len(active),
            "pause_active": self.state.get("pause", False),
            "timestamp": _format_dt(_now()),
        }

    # ── Private helpers ──────────────────────────────────────

    def _get_investigation(self, investigation_id: str) -> Optional[Dict]:
        """Find an investigation by ID. Returns None if not found."""
        for inv in self.state.get("investigations", []):
            if inv.get("investigation_id") == investigation_id:
                return inv
        return None

    def _get_containment(self, containment_id: str) -> Optional[Dict]:
        """Find a containment action by ID. Returns None if not found."""
        for c in self.state.get("containment_actions", []):
            if c.get("containment_id") == containment_id:
                return c
        return None

    def _compute_recommendation(
        self, severity: str, attribution: str
    ) -> str:
        """
        Compute investigation recommendation based on severity
        and attribution confidence.
        """
        sev_rank = {"S1": 1, "S2": 2, "S3": 3, "S4": 4}.get(severity, 0)
        attr_rank = {"A1": 4, "A2": 3, "A3": 2, "A4": 1}.get(attribution, 0)

        score = sev_rank * attr_rank

        if score >= 12:
            return "immediate_warrant_application"
        elif score >= 8:
            return "warrant_application_recommended"
        elif score >= 4:
            return "preliminary_assessment"
        else:
            return "monitor_only"

    def _compute_warrant_limit_days(self, renewals: int) -> int:
        """Compute current warrant duration limit based on renewal count."""
        if renewals == 0:
            return WARRANT_INITIAL_DAYS
        elif renewals == 1:
            return WARRANT_RENEWAL_1_DAYS
        elif renewals == 2:
            return WARRANT_RENEWAL_2_DAYS
        else:
            return WARRANT_SUBSEQUENT_DAYS

    def _compute_threat_posture(self) -> str:
        """Compute overall threat posture from active investigations."""
        investigations = self.state.get("investigations", [])
        active = [i for i in investigations if i.get("status") == "active"]

        if not active:
            return "nominal"

        severities = []
        for inv in active:
            # Check if any containment is active
            if inv.get("containment_actions"):
                return "elevated"
            severities.append(inv.get("severity", "S1"))

        if "S4" in severities:
            return "critical"
        elif "S3" in severities:
            return "elevated"
        elif "S2" in severities:
            return "heightened"
        else:
            return "nominal"

    def _count_by_field(
        self, items: List[Dict], field: str
    ) -> Dict[str, int]:
        """Count items by a given field value."""
        counts: Dict[str, int] = {}
        for item in items:
            val = item.get(field, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts
