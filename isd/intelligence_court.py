#!/usr/bin/env python3
"""
House Bernard Intelligence Court Engine v1.0
Authority: Internal Security & Intelligence Court Act, Section II

The Intelligence Court is a classified division of the Judiciary.
It authorizes internal security investigations, issues secret warrants,
and ensures no citizen is investigated without judicial review.

The engine computes warrant decisions, compliance metrics, and
oversight status. It does not issue warrants — it computes.

Usage:
    from isd.intelligence_court import IntelligenceCourtEngine
    court = IntelligenceCourtEngine("isd/isd_state.json")
    result = court.evaluate_warrant_application(application)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── Warrant configuration (Act Section II) ───────────────────────

WARRANT_INITIAL_MAX_DAYS = 90
WARRANT_RENEWAL_1_MAX_DAYS = 90
WARRANT_RENEWAL_2_MAX_DAYS = 90
WARRANT_SUBSEQUENT_MAX_DAYS = 60
WARRANT_HARD_LIMIT_DAYS = 730

EMERGENCY_WARRANT_MAX_DAYS = 7

JUDGES_REQUIRED = 3
JUDGES_TO_APPROVE = 2
JUDGES_UNANIMOUS = 3

# ── Approval rate thresholds (Act Section II) ────────────────────

APPROVAL_RATE_REVIEW_THRESHOLD = 0.90
FACIALLY_DEFICIENT_RATE_THRESHOLD = 0.20
FACIALLY_DEFICIENT_WINDOW_DAYS = 180

# ── Advocate configuration (Act Section II) ──────────────────────

ADVOCATE_TERM_DAYS = 180
ADVOCATE_POST_SERVICE_SILENCE_DAYS = 730
ADVOCATE_OVERLAP_DAYS = 14
ADVOCATE_MAX_EXTENSION_DAYS = 30
MAX_CONSECUTIVE_ISD_REJECTIONS = 3

# ── Judge rotation (Act Section II) ─────────────────────────────

JUDGE_ROTATION_TERM_DAYS = 180
ROTATION_COVERAGE_WINDOW_DAYS = 730
MIN_JUDGES_SERVED_IN_WINDOW = 4
TOTAL_JUDICIARY_JUDGES = 5

# ── Closure review (Act Section IV.5) ───────────────────────────

CLOSURE_REVIEW_DAYS = 14


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

class IntelligenceCourtEngine:
    """
    Intelligence Court computation engine.

    Evaluates warrant applications against the five statutory
    requirements, tracks approval rates, manages judge rotation,
    and monitors oversight health. Read-only computation layer.
    """

    def __init__(self, state_path: str = "isd/isd_state.json") -> None:
        """Load state from JSON file."""
        self.state_path = Path(state_path)
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)
        self.court = self.state.get("intelligence_court", {})

    # ── Warrant application evaluation ───────────────────────

    def evaluate_warrant_application(
        self, application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a warrant application against the five statutory
        requirements from Act Section II:

        1. Specific target (named citizen/contributor/official)
        2. Articulable threat basis (specific, credible facts)
        3. Investigative necessity (why Wardens can't do it openly)
        4. Scope limitation (exactly what will be examined)
        5. Minimization procedures (how innocent data is handled)

        Returns evaluation with pass/fail for each requirement.
        """
        if self.court.get("oversight_saturation", False):
            return {
                "error": "oversight_saturation_active",
                "detail": "Intelligence Court has declared Oversight "
                          "Saturation Warning. No new applications "
                          "accepted except emergency warrants.",
            }

        if not self._advocate_present():
            return {
                "error": "no_citizens_advocate",
                "detail": "Intelligence Court may not review any warrant "
                          "application without a Citizen's Advocate "
                          "present per Act Section II.",
            }

        checks = []
        passed = True

        # 1. Specific target
        target = application.get("target_id")
        target_ok = bool(target and isinstance(target, str) and len(target) > 0)
        checks.append({
            "requirement": "specific_target",
            "passed": target_ok,
            "detail": "Named target required — no class-based or John Doe warrants"
                      if not target_ok else "Specific target identified",
        })
        passed = passed and target_ok

        # 2. Articulable threat basis
        threat_basis = application.get("threat_basis", "")
        basis_ok = bool(
            threat_basis
            and isinstance(threat_basis, str)
            and len(threat_basis.strip()) >= 50
        )
        checks.append({
            "requirement": "articulable_threat_basis",
            "passed": basis_ok,
            "detail": "Specific credible facts required — suspicion alone "
                      "is insufficient"
                      if not basis_ok else "Articulable threat basis provided",
        })
        passed = passed and basis_ok

        # 3. Investigative necessity
        necessity = application.get("investigative_necessity", "")
        necessity_ok = bool(
            necessity
            and isinstance(necessity, str)
            and len(necessity.strip()) >= 20
        )
        checks.append({
            "requirement": "investigative_necessity",
            "passed": necessity_ok,
            "detail": "Must explain why Wardens cannot investigate openly"
                      if not necessity_ok
                      else "Investigative necessity established",
        })
        passed = passed and necessity_ok

        # 4. Scope limitation
        scope = application.get("scope", {})
        scope_ok = bool(
            scope
            and scope.get("systems")
            and scope.get("duration_days")
        )
        checks.append({
            "requirement": "scope_limitation",
            "passed": scope_ok,
            "detail": "Must specify systems, communications, behavioral "
                      "data, and duration"
                      if not scope_ok else "Scope properly limited",
        })
        passed = passed and scope_ok

        # 5. Minimization procedures
        minimization = application.get("minimization_procedures", "")
        min_ok = bool(
            minimization
            and isinstance(minimization, str)
            and len(minimization.strip()) >= 20
        )
        checks.append({
            "requirement": "minimization_procedures",
            "passed": min_ok,
            "detail": "Must describe handling of innocent party data "
                      f"(purge within {72} hours unless justified)"
                      if not min_ok
                      else "Minimization procedures defined",
        })
        passed = passed and min_ok

        # Check for facially deficient application
        failures = sum(1 for c in checks if not c["passed"])
        facially_deficient = failures >= 3

        duration = min(
            scope.get("duration_days", WARRANT_INITIAL_MAX_DAYS),
            WARRANT_INITIAL_MAX_DAYS,
        ) if scope_ok else 0

        result = {
            "application_id": _generate_id("WAPP"),
            "target_id": application.get("target_id"),
            "threat_category": application.get("threat_category"),
            "all_requirements_met": passed,
            "checks": checks,
            "facially_deficient": facially_deficient,
            "evaluated": _format_dt(_now()),
        }

        if passed:
            now = _now()
            result["warrant"] = {
                "warrant_id": _generate_id("WRT"),
                "status": "pending_judicial_vote",
                "requires_votes": JUDGES_TO_APPROVE,
                "max_duration_days": duration,
                "expiry": _format_dt(now + timedelta(days=duration)),
                "renewal_count": 0,
            }

        return result

    def evaluate_warrant_renewal(
        self,
        warrant_id: str,
        updated_threat_basis: str,
        director_certification: bool = False,
        crown_authorization: bool = False,
    ) -> Dict[str, Any]:
        """
        Evaluate a warrant renewal request. Requirements escalate
        with each renewal per Act Section II.
        """
        warrant = self._get_warrant(warrant_id)
        if warrant is None:
            return {"error": "warrant_not_found"}

        renewal_count = warrant.get("renewal_count", 0)

        if not updated_threat_basis:
            return {"error": "updated_threat_basis_required"}

        if renewal_count >= 2 and not director_certification:
            return {
                "error": "director_certification_required",
                "detail": "Second renewal and beyond requires ISD Director "
                          "personal certification per Act Section II",
            }

        if renewal_count >= 3 and not crown_authorization:
            return {
                "error": "crown_authorization_required",
                "detail": "Beyond second renewal requires Crown authorization "
                          "in addition to court approval per Act Section II",
            }

        # Check hard limit
        investigation = self._find_investigation_for_warrant(warrant_id)
        if investigation:
            opened = _parse_dt(investigation.get("opened"))
            if opened:
                elapsed = (_now() - opened).days
                if elapsed >= WARRANT_HARD_LIMIT_DAYS:
                    return {
                        "error": "hard_limit_reached",
                        "detail": f"Investigation has run {elapsed} days. "
                                  f"Hard limit is {WARRANT_HARD_LIMIT_DAYS} "
                                  f"days. Mandatory Full Bench review required.",
                        "elapsed_days": elapsed,
                    }

        max_days = self._renewal_max_days(renewal_count + 1)
        now = _now()

        return {
            "warrant_id": warrant_id,
            "renewal_number": renewal_count + 1,
            "status": "renewal_approved",
            "max_duration_days": max_days,
            "new_expiry": _format_dt(now + timedelta(days=max_days)),
            "heightened_scrutiny": renewal_count >= 2,
            "evaluated": _format_dt(now),
        }

    # ── Emergency warrants ───────────────────────────────────

    def evaluate_emergency_warrant(
        self, application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate an expedited emergency warrant. During declared
        emergencies, a single judge may authorize (rather than
        the standard two-judge concurrence). Limited to 7 days.
        """
        base = self.evaluate_warrant_application(application)
        if "error" in base and base["error"] == "oversight_saturation_active":
            # Emergency warrants bypass saturation
            base = self._evaluate_without_saturation_check(application)

        if not base.get("all_requirements_met", False):
            return base

        now = _now()
        base["warrant"]["max_duration_days"] = EMERGENCY_WARRANT_MAX_DAYS
        base["warrant"]["expiry"] = _format_dt(
            now + timedelta(days=EMERGENCY_WARRANT_MAX_DAYS)
        )
        base["warrant"]["type"] = "emergency"
        base["warrant"]["requires_votes"] = 1
        base["warrant"]["full_panel_review_deadline"] = _format_dt(
            now + timedelta(days=EMERGENCY_WARRANT_MAX_DAYS)
        )

        return base

    # ── Surfacing decisions (Act Section III — Flow 2) ───────

    def evaluate_surfacing_request(
        self,
        investigation_id: str,
        evidence_summary: str,
        parallel_construction_feasible: bool,
        methods_at_risk: List[str],
    ) -> Dict[str, Any]:
        """
        Evaluate whether classified evidence can be surfaced
        for open Warden prosecution.
        """
        if not evidence_summary:
            return {"error": "evidence_summary_required"}

        now = _now()
        options = []

        if parallel_construction_feasible:
            options.append({
                "option": "surface_via_clean_brief",
                "description": "ISD produces Clean Brief for Wardens. "
                               "Wardens investigate openly. Clean Brief "
                               "never enters Judiciary proceedings.",
                "recommended": True,
            })
        else:
            options.extend([
                {
                    "option": "continued_monitoring",
                    "code": "option_a",
                    "description": "Continue classified monitoring under "
                                   "renewed warrants. Appropriate if threat "
                                   "is dormant or slow-moving.",
                },
                {
                    "option": "administrative_action",
                    "code": "option_b",
                    "description": "Crown takes administrative actions "
                                   "(reassignment, access revocation) based "
                                   "on classified findings. Requires court "
                                   "authorization.",
                },
                {
                    "option": "classified_tribunal",
                    "code": "option_c",
                    "description": "Full Intelligence Court plus Citizen's "
                                   "Advocate reviews evidence. Last resort "
                                   "requiring exhaustion certification.",
                },
                {
                    "option": "declassification",
                    "code": "option_d",
                    "description": "Crown authorizes declassification to "
                                   "enable open prosecution. Burns source "
                                   "or method.",
                },
            ])

        return {
            "surfacing_id": _generate_id("SURF"),
            "investigation_id": investigation_id,
            "parallel_construction_feasible": parallel_construction_feasible,
            "methods_at_risk": methods_at_risk,
            "options": options,
            "evaluated": _format_dt(now),
        }

    # ── Classified Tribunal (Act Section III — Option C) ─────

    def evaluate_tribunal_request(
        self,
        investigation_id: str,
        option_a_insufficient: bool,
        option_b_insufficient: bool,
        option_d_harmful: bool,
        harm_description: str,
    ) -> Dict[str, Any]:
        """
        Evaluate whether a Classified Tribunal may be convened.
        Requires exhaustion certification: all three conditions
        must be met per Act Section III.
        """
        exhaustion_met = (
            option_a_insufficient
            and option_b_insufficient
            and option_d_harmful
        )

        if not exhaustion_met:
            missing = []
            if not option_a_insufficient:
                missing.append("Option A (monitoring) not shown insufficient")
            if not option_b_insufficient:
                missing.append("Option B (administrative) not shown insufficient")
            if not option_d_harmful:
                missing.append("Option D (declassification) harm not demonstrated")
            return {
                "error": "exhaustion_requirement_not_met",
                "missing_certifications": missing,
                "detail": "Crown may not convene Classified Tribunal "
                          "without exhaustion certification per Act "
                          "Section III",
            }

        return {
            "tribunal_id": _generate_id("TRIB"),
            "investigation_id": investigation_id,
            "exhaustion_certified": True,
            "composition": [
                "intelligence_court_judge_1",
                "intelligence_court_judge_2",
                "intelligence_court_judge_3",
                "citizens_advocate",
            ],
            "special_counsel_required": True,
            "special_counsel_prep_days": 30,
            "harm_description": harm_description,
            "status": "pending_convening",
            "evaluated": _format_dt(_now()),
        }

    # ── Approval rate monitoring (Act Section II) ────────────

    def compute_approval_rate(self) -> Dict[str, Any]:
        """
        Compute warrant approval rate and check health thresholds.
        If approval rate exceeds 90%, an independent review is
        required per Act Section II.
        """
        stats = self.court.get("statistical_record", {})
        received = stats.get("applications_received", 0)
        approved = stats.get("applications_approved", 0)
        denied = stats.get("applications_denied", 0)
        flagged = stats.get("facially_deficient_flags", 0)

        if received == 0:
            return {
                "approval_rate": 0.0,
                "total_applications": 0,
                "review_triggered": False,
                "gaming_indicators": False,
            }

        rate = round(approved / received, 4) if received > 0 else 0.0
        review_triggered = rate > APPROVAL_RATE_REVIEW_THRESHOLD

        deficient_rate = round(flagged / received, 4) if received > 0 else 0.0
        gaming_suspected = (
            deficient_rate > FACIALLY_DEFICIENT_RATE_THRESHOLD
        )

        return {
            "approval_rate": rate,
            "total_applications": received,
            "approved": approved,
            "denied": denied,
            "facially_deficient": flagged,
            "facially_deficient_rate": deficient_rate,
            "review_triggered": review_triggered,
            "review_reason": (
                f"Approval rate {rate:.1%} exceeds "
                f"{APPROVAL_RATE_REVIEW_THRESHOLD:.0%} threshold"
                if review_triggered else None
            ),
            "gaming_indicators": gaming_suspected,
            "gaming_reason": (
                f"Facially deficient rate {deficient_rate:.1%} exceeds "
                f"{FACIALLY_DEFICIENT_RATE_THRESHOLD:.0%} threshold — "
                f"possible approval rate manipulation"
                if gaming_suspected else None
            ),
        }

    # ── Judge rotation compliance (Act Section II) ───────────

    def check_rotation_compliance(self) -> Dict[str, Any]:
        """
        Check whether judge rotation meets the mandatory rotation
        rule: every judge must serve at least once before any
        serves a second time; 4 of 5 judges must have served
        in any 730-day window.
        """
        rotation = self.court.get("rotation_history", [])
        judges = self.court.get("judges", [])

        if not rotation:
            return {
                "compliant": True,
                "detail": "No rotation history — initial assignment pending",
                "judges_served": 0,
                "judges_total": TOTAL_JUDICIARY_JUDGES,
            }

        now = _now()
        window_start = now - timedelta(days=ROTATION_COVERAGE_WINDOW_DAYS)

        # Judges who served in the window
        served_in_window = set()
        for entry in rotation:
            start = _parse_dt(entry.get("term_start"))
            if start and start >= window_start:
                served_in_window.add(entry.get("judge_id"))

        # Check consecutive terms
        consecutive_violation = False
        if len(rotation) >= 2:
            last = rotation[-1].get("judge_id")
            prev = rotation[-2].get("judge_id")
            if last == prev:
                consecutive_violation = True

        compliant = (
            len(served_in_window) >= MIN_JUDGES_SERVED_IN_WINDOW
            and not consecutive_violation
        )

        return {
            "compliant": compliant,
            "judges_served_in_window": len(served_in_window),
            "required_in_window": MIN_JUDGES_SERVED_IN_WINDOW,
            "window_days": ROTATION_COVERAGE_WINDOW_DAYS,
            "consecutive_term_violation": consecutive_violation,
            "served_judge_ids": sorted(served_in_window),
            "checked": _format_dt(now),
        }

    # ── Citizen's Advocate management ────────────────────────

    def check_advocate_status(self) -> Dict[str, Any]:
        """
        Check Citizen's Advocate status: term expiry, gap risk,
        and whether the no-advocate-no-warrant rule is satisfied.
        """
        advocate = self.court.get("citizens_advocate")

        if advocate is None:
            return {
                "advocate_present": False,
                "warrants_blocked": True,
                "detail": "No Citizen's Advocate appointed. Intelligence "
                          "Court may not review any warrant application.",
            }

        now = _now()
        term_start = _parse_dt(advocate.get("term_start"))
        term_end = None
        if term_start:
            term_end = term_start + timedelta(days=ADVOCATE_TERM_DAYS)

        expired = term_end is not None and now > term_end
        max_extension = None
        if term_end and expired:
            max_extension = term_end + timedelta(days=ADVOCATE_MAX_EXTENSION_DAYS)

        in_extension = (
            expired
            and max_extension is not None
            and now <= max_extension
        )

        days_remaining = 0
        if term_end and not expired:
            days_remaining = (term_end - now).days
        elif in_extension and max_extension:
            days_remaining = (max_extension - now).days

        overlap_needed = (
            term_end is not None
            and not expired
            and (term_end - now).days <= ADVOCATE_OVERLAP_DAYS
        )

        return {
            "advocate_present": True,
            "advocate_id": advocate.get("advocate_id"),
            "term_start": advocate.get("term_start"),
            "term_end": _format_dt(term_end) if term_end else None,
            "expired": expired,
            "in_extension": in_extension,
            "days_remaining": days_remaining,
            "overlap_period_active": overlap_needed,
            "successor_needed": overlap_needed or expired,
            "warrants_blocked": expired and not in_extension,
        }

    # ── Oversight saturation (Act Section III) ───────────────

    def evaluate_oversight_saturation(
        self, pending_reviews: int, capacity: int
    ) -> Dict[str, Any]:
        """
        Evaluate whether the Intelligence Court should declare
        an Oversight Saturation Warning. Triggers when review
        burden exceeds institutional capacity.
        """
        if capacity <= 0:
            return {"error": "capacity_must_be_positive"}

        utilization = round(pending_reviews / capacity, 4)
        saturated = utilization >= 1.0

        result = {
            "pending_reviews": pending_reviews,
            "capacity": capacity,
            "utilization": utilization,
            "saturated": saturated,
            "evaluated": _format_dt(_now()),
        }

        if saturated:
            result["effects"] = {
                "new_applications_blocked": True,
                "emergency_warrants_allowed": True,
                "pending_renewals_auto_extended_days": 30,
                "crown_notification_required": True,
                "root_cause_analysis_required": True,
            }

        return result

    # ── Exoneration sealing (Act Section IV.5) ───────────────

    def compute_exoneration_seal(
        self,
        investigation_id: str,
        closure_approved: bool,
    ) -> Dict[str, Any]:
        """
        Compute exoneration sealing timeline. Records sealed and
        destroyed within 30 days of court-approved closure.
        """
        if not closure_approved:
            return {
                "error": "court_approval_required",
                "detail": "Exoneration sealing begins only after "
                          "Intelligence Court approves closure",
            }

        now = _now()
        return {
            "investigation_id": investigation_id,
            "seal_status": "pending_destruction",
            "closure_approved": _format_dt(now),
            "destruction_deadline": _format_dt(
                now + timedelta(days=30)
            ),
            "citizen_notification": False,
            "detail": "All investigation records sealed. Destruction "
                      "within 30 days. Citizen never notified.",
        }

    # ── Statistical reporting (Act Section II) ───────────────

    def annual_statistical_report(self) -> Dict[str, Any]:
        """
        Compute the annual public statistical report.
        Numbers only — no target names, no investigation details.
        """
        stats = self.court.get("statistical_record", {})

        return {
            "report_type": "annual_statistical_public",
            "generated": _format_dt(_now()),
            "classification": "public",
            "applications_received": stats.get("applications_received", 0),
            "applications_approved": stats.get("applications_approved", 0),
            "applications_denied": stats.get("applications_denied", 0),
            "renewals_granted": stats.get("renewals_granted", 0),
            "warrants_expired": stats.get("warrants_expired", 0),
            "note": "Per Act Section II — no target names, no "
                    "investigation details. Numbers only.",
        }

    # ── Pattern Monitor for Advocate (Act Section II) ────────

    def get_pattern_monitor(self) -> Dict[str, Any]:
        """
        Return the anonymized statistical dashboard visible to the
        Citizen's Advocate. Shows warrant patterns without revealing
        specific investigation details.
        """
        monitor = self.court.get("pattern_monitor", {})

        return {
            "warrants_by_threat_category": monitor.get(
                "warrants_by_threat_category", {}
            ),
            "warrants_by_target_branch": monitor.get(
                "warrants_by_target_branch", {}
            ),
            "last_updated": monitor.get("last_updated"),
            "note": "Anonymized — no names, no specific investigation "
                    "details. Updated quarterly by Intelligence Court clerk.",
        }

    # ── Private helpers ──────────────────────────────────────

    def _advocate_present(self) -> bool:
        """Check if a Citizen's Advocate is currently serving."""
        advocate = self.court.get("citizens_advocate")
        if advocate is None:
            return False

        term_start = _parse_dt(advocate.get("term_start"))
        if term_start is None:
            return False

        now = _now()
        term_end = term_start + timedelta(days=ADVOCATE_TERM_DAYS)
        max_end = term_end + timedelta(days=ADVOCATE_MAX_EXTENSION_DAYS)

        return now <= max_end

    def _get_warrant(self, warrant_id: str) -> Optional[Dict]:
        """Find a warrant by ID."""
        for w in self.state.get("warrants", []):
            if w.get("warrant_id") == warrant_id:
                return w
        return None

    def _find_investigation_for_warrant(
        self, warrant_id: str
    ) -> Optional[Dict]:
        """Find the investigation associated with a warrant."""
        for inv in self.state.get("investigations", []):
            if inv.get("warrant_id") == warrant_id:
                return inv
        return None

    def _renewal_max_days(self, renewal_number: int) -> int:
        """Compute max days for a given renewal number."""
        if renewal_number <= 1:
            return WARRANT_RENEWAL_1_MAX_DAYS
        elif renewal_number == 2:
            return WARRANT_RENEWAL_2_MAX_DAYS
        else:
            return WARRANT_SUBSEQUENT_MAX_DAYS

    def _evaluate_without_saturation_check(
        self, application: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate warrant application bypassing saturation check."""
        saved = self.court.get("oversight_saturation", False)
        self.court["oversight_saturation"] = False
        result = self.evaluate_warrant_application(application)
        self.court["oversight_saturation"] = saved
        return result
