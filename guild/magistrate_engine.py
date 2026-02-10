"""
House Bernard Magistrate Engine v1.0
Manages the Magistrate Court system for guild-related disputes.

Authority: GUILD_SYSTEM.md Section IX
The Judiciary appoints magistrates. The engine tracks cases and rulings.

Court hierarchy:
    Full Bench (5 judges) — Constitutional review, revocations, Crown
    Lower Court (single judge) — Furnace challenges, serious violations, appeals
    Magistrate Court — Guild disputes, revenue splits, brief access, conduct

Usage:
    from guild.magistrate_engine import MagistrateEngine
    engine = MagistrateEngine("guild/guild_state.json")
    result = engine.file_case(...)
"""

import json
import shutil
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def _days_between(start: datetime, end: datetime) -> float:
    return max(0, (end - start).days)


# ---------------------------------------------------------------------------
# Constants from GUILD_SYSTEM.md Section IX
# ---------------------------------------------------------------------------

# Magistrate terms
MAGISTRATE_TERM_DAYS = 180
COOLING_PERIOD_DAYS = 180  # From Council/guild leadership roles

# Response deadlines (days)
RESPONSE_DEADLINES = {
    "magistrate_court": 14,
    "lower_court": 30,
    "full_bench": 60,
}

# Case types handled by Magistrate Court
MAGISTRATE_JURISDICTION = {
    "guild_internal_dispute",
    "guild_vs_guild_domain",
    "revenue_split_disagreement",
    "brief_access_complaint",
    "advocate_disciplinary",
    "minor_conduct_violation",
}

# Case types NOT handled by Magistrate Court
EXCLUDED_FROM_MAGISTRATE = {
    "constitutional_review",
    "citizenship_revocation",
    "guild_charter_revocation",
    "crown_proceeding",
    "classified_operations",
}

# Case statuses
CASE_STATUSES = {
    "filed", "assigned", "response_pending", "hearing_scheduled",
    "under_review", "ruling_issued", "appealed", "appeal_ruling",
    "closed", "dismissed",
}

# Magistrate statuses
MAGISTRATE_STATUSES = {"active", "expired", "removed"}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class MagistrateEngine:

    def __init__(self, state_path: str = "guild/guild_state.json") -> None:
        self.state_path = Path(state_path)
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)
        # Ensure court data structures exist
        self.state.setdefault("magistrates", [])
        self.state.setdefault("cases", [])
        self.state.setdefault("case_counter", 0)

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _get_magistrate(self, citizen_id: str) -> Optional[Dict[str, Any]]:
        """Find a magistrate by citizen ID."""
        for m in self.state["magistrates"]:
            if m["citizen_id"] == citizen_id:
                return m
        return None

    def _get_active_magistrate(self, citizen_id: str) -> Dict[str, Any]:
        """Find an active magistrate. Raises ValueError if not found."""
        mag = self._get_magistrate(citizen_id)
        if mag is None:
            raise ValueError(f"No magistrate record for {citizen_id}")
        if mag["status"] != "active":
            raise ValueError(f"Magistrate {citizen_id} is {mag['status']}")
        return mag

    def _get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Find a case by ID."""
        for c in self.state["cases"]:
            if c["case_id"] == case_id:
                return c
        return None

    def _next_case_id(self) -> str:
        """Generate the next case ID (MC-0001, MC-0002, etc.)."""
        self.state["case_counter"] = self.state.get("case_counter", 0) + 1
        return f"MC-{self.state['case_counter']:04d}"

    # -------------------------------------------------------------------
    # Magistrate Appointments
    # -------------------------------------------------------------------

    def appoint_magistrate(
        self,
        citizen_id: str,
        supervising_judge_id: str,
        covenant_exam_passed: bool = True,
        appointed_by: str = "chief_justice",
    ) -> Dict[str, Any]:
        """Appoint a magistrate.

        Requirements:
        - Must pass Covenant Examination
        - 180-day cooling period from Council/guild leadership
        - Appointed by Chief Justice with Full Bench approval
        - During Founding Period, appointed by Governor

        Args:
            citizen_id: The citizen being appointed.
            supervising_judge_id: The sitting judge who supervises.
            covenant_exam_passed: Whether they passed the exam.
            appointed_by: 'chief_justice' or 'governor' (Founding Period).
        """
        if not covenant_exam_passed:
            raise ValueError("Magistrate must pass the Covenant Examination")

        existing = self._get_magistrate(citizen_id)
        if existing and existing["status"] == "active":
            raise ValueError(f"Citizen {citizen_id} is already an active magistrate")

        now = _now()
        term_end = datetime.fromtimestamp(
            now.timestamp() + MAGISTRATE_TERM_DAYS * 86400,
            tz=timezone.utc
        )

        magistrate = {
            "citizen_id": citizen_id,
            "supervising_judge": supervising_judge_id,
            "appointed_by": appointed_by,
            "appointment_date": _format_dt(now),
            "term_end": _format_dt(term_end),
            "status": "active",
            "cases_assigned": [],
            "rulings_count": 0,
        }

        if existing:
            idx = self.state["magistrates"].index(existing)
            self.state["magistrates"][idx] = magistrate
        else:
            self.state["magistrates"].append(magistrate)

        return {
            "citizen_id": citizen_id,
            "supervising_judge": supervising_judge_id,
            "appointed_by": appointed_by,
            "term_end": _format_dt(term_end),
            "term_days": MAGISTRATE_TERM_DAYS,
            "status": "active",
        }

    def remove_magistrate(
        self, citizen_id: str, reason: str = "term_expired"
    ) -> Dict[str, Any]:
        """Remove a magistrate (term expiry or removal)."""
        mag = self._get_active_magistrate(citizen_id)
        mag["status"] = "expired" if reason == "term_expired" else "removed"
        mag["removal_date"] = _format_dt(_now())
        mag["removal_reason"] = reason

        return {
            "citizen_id": citizen_id,
            "new_status": mag["status"],
            "reason": reason,
            "timestamp": mag["removal_date"],
            "active_cases": len([
                c for c in self.state["cases"]
                if c.get("assigned_magistrate") == citizen_id
                and c["status"] not in ("closed", "dismissed")
            ]),
        }

    def renew_magistrate(
        self, citizen_id: str, renewed_by: str = "chief_justice"
    ) -> Dict[str, Any]:
        """Renew a magistrate's term (180 days, renewable)."""
        mag = self._get_active_magistrate(citizen_id)

        now = _now()
        new_term_end = datetime.fromtimestamp(
            now.timestamp() + MAGISTRATE_TERM_DAYS * 86400,
            tz=timezone.utc
        )
        mag["term_end"] = _format_dt(new_term_end)

        return {
            "citizen_id": citizen_id,
            "renewed_by": renewed_by,
            "new_term_end": _format_dt(new_term_end),
        }

    def check_magistrate_terms(
        self, as_of: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Check magistrate terms for expiry."""
        as_of = as_of or _now()
        results = []

        for mag in self.state["magistrates"]:
            if mag["status"] != "active":
                continue

            term_end = _parse_dt(mag["term_end"])
            if term_end is None:
                continue

            days_remaining = _days_between(as_of, term_end)
            if days_remaining <= 0:
                mag["status"] = "expired"
                results.append({
                    "citizen_id": mag["citizen_id"],
                    "status": "EXPIRED",
                    "days_overdue": int(abs(days_remaining)),
                })
            elif days_remaining <= 30:
                results.append({
                    "citizen_id": mag["citizen_id"],
                    "status": "EXPIRING_SOON",
                    "days_remaining": int(days_remaining),
                })

        return results

    # -------------------------------------------------------------------
    # Case Management
    # -------------------------------------------------------------------

    def file_case(
        self,
        case_type: str,
        plaintiff_id: str,
        defendant_id: str,
        description: str,
        plaintiff_advocate_id: Optional[str] = None,
        defendant_advocate_id: Optional[str] = None,
        related_guild_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """File a new case with the Magistrate Court.

        Validates jurisdiction — some case types cannot be heard by magistrates.
        """
        # Jurisdiction check
        if case_type in EXCLUDED_FROM_MAGISTRATE:
            raise ValueError(
                f"Case type '{case_type}' is outside Magistrate Court jurisdiction. "
                f"Must be filed with {'Full Bench' if case_type in ('constitutional_review', 'crown_proceeding') else 'Lower Court'}."
            )

        if case_type not in MAGISTRATE_JURISDICTION:
            raise ValueError(
                f"Unknown case type '{case_type}'. "
                f"Valid types: {', '.join(sorted(MAGISTRATE_JURISDICTION))}"
            )

        case_id = self._next_case_id()
        now = _now()
        response_deadline = datetime.fromtimestamp(
            now.timestamp() + RESPONSE_DEADLINES["magistrate_court"] * 86400,
            tz=timezone.utc
        )

        case = {
            "case_id": case_id,
            "case_type": case_type,
            "court": "magistrate_court",
            "plaintiff_id": plaintiff_id,
            "defendant_id": defendant_id,
            "description": description,
            "plaintiff_advocate": plaintiff_advocate_id,
            "defendant_advocate": defendant_advocate_id,
            "related_guild_ids": related_guild_ids or [],
            "filed_date": _format_dt(now),
            "response_deadline": _format_dt(response_deadline),
            "assigned_magistrate": None,
            "supervising_judge": None,
            "status": "filed",
            "rulings": [],
            "motions": [],
            "appeal": None,
            "timeline": [
                {
                    "event": "case_filed",
                    "date": _format_dt(now),
                    "detail": f"Case filed by {plaintiff_id}",
                }
            ],
        }

        self.state["cases"].append(case)

        return {
            "case_id": case_id,
            "case_type": case_type,
            "court": "magistrate_court",
            "plaintiff": plaintiff_id,
            "defendant": defendant_id,
            "filed_date": _format_dt(now),
            "response_deadline": _format_dt(response_deadline),
            "status": "filed",
        }

    def assign_case(
        self, case_id: str, magistrate_id: str
    ) -> Dict[str, Any]:
        """Assign a case to a magistrate."""
        case = self._get_case(case_id)
        if case is None:
            raise ValueError(f"Case {case_id} not found")
        if case["status"] not in ("filed", "assigned"):
            raise ValueError(f"Case {case_id} is {case['status']}, cannot assign")

        mag = self._get_active_magistrate(magistrate_id)

        case["assigned_magistrate"] = magistrate_id
        case["supervising_judge"] = mag["supervising_judge"]
        case["status"] = "assigned"
        case["timeline"].append({
            "event": "case_assigned",
            "date": _format_dt(_now()),
            "detail": f"Assigned to Magistrate {magistrate_id}",
        })

        mag["cases_assigned"].append(case_id)

        return {
            "case_id": case_id,
            "magistrate": magistrate_id,
            "supervising_judge": mag["supervising_judge"],
            "status": "assigned",
        }

    def file_response(
        self, case_id: str, respondent_id: str, response_text: str
    ) -> Dict[str, Any]:
        """File a response from the defendant."""
        case = self._get_case(case_id)
        if case is None:
            raise ValueError(f"Case {case_id} not found")

        now = _now()
        deadline = _parse_dt(case.get("response_deadline"))
        late = deadline is not None and now > deadline

        case["status"] = "response_pending"
        case["timeline"].append({
            "event": "response_filed",
            "date": _format_dt(now),
            "detail": f"Response filed by {respondent_id}" + (" (LATE)" if late else ""),
        })

        return {
            "case_id": case_id,
            "respondent": respondent_id,
            "filed_date": _format_dt(now),
            "late": late,
        }

    def file_motion(
        self, case_id: str, filed_by: str, motion_type: str,
        description: str,
    ) -> Dict[str, Any]:
        """File a motion in a case."""
        case = self._get_case(case_id)
        if case is None:
            raise ValueError(f"Case {case_id} not found")
        if case["status"] in ("closed", "dismissed"):
            raise ValueError(f"Case {case_id} is {case['status']}")

        now = _now()
        motion = {
            "filed_by": filed_by,
            "motion_type": motion_type,
            "description": description,
            "filed_date": _format_dt(now),
            "ruling": None,
        }
        case["motions"].append(motion)
        case["timeline"].append({
            "event": "motion_filed",
            "date": _format_dt(now),
            "detail": f"Motion ({motion_type}) filed by {filed_by}",
        })

        return {
            "case_id": case_id,
            "motion_number": len(case["motions"]),
            "motion_type": motion_type,
            "filed_by": filed_by,
        }

    def issue_ruling(
        self,
        case_id: str,
        magistrate_id: str,
        ruling_text: str,
        orders: List[str],
        case_closed: bool = True,
    ) -> Dict[str, Any]:
        """Issue a ruling on a case.

        Magistrate rulings are binding but may be appealed to Lower Court.
        """
        case = self._get_case(case_id)
        if case is None:
            raise ValueError(f"Case {case_id} not found")

        mag = self._get_active_magistrate(magistrate_id)
        if case.get("assigned_magistrate") != magistrate_id:
            raise ValueError(
                f"Magistrate {magistrate_id} is not assigned to case {case_id}"
            )

        now = _now()
        ruling = {
            "magistrate": magistrate_id,
            "supervising_judge": case.get("supervising_judge"),
            "ruling_text": ruling_text,
            "orders": orders,
            "date": _format_dt(now),
        }
        case["rulings"].append(ruling)
        case["status"] = "closed" if case_closed else "ruling_issued"
        case["timeline"].append({
            "event": "ruling_issued",
            "date": _format_dt(now),
            "detail": f"Ruling by Magistrate {magistrate_id}",
        })

        mag["rulings_count"] = mag.get("rulings_count", 0) + 1

        return {
            "case_id": case_id,
            "magistrate": magistrate_id,
            "orders": orders,
            "status": case["status"],
            "appealable": True,
            "appeal_deadline_days": RESPONSE_DEADLINES["lower_court"],
        }

    def file_appeal(
        self, case_id: str, appellant_id: str, grounds: str
    ) -> Dict[str, Any]:
        """File an appeal of a Magistrate ruling to Lower Court.

        Appeals go to a sitting judge (not another magistrate).
        """
        case = self._get_case(case_id)
        if case is None:
            raise ValueError(f"Case {case_id} not found")

        if not case.get("rulings"):
            raise ValueError(f"Case {case_id} has no ruling to appeal")

        now = _now()
        last_ruling_date = _parse_dt(case["rulings"][-1]["date"])
        appeal_deadline = datetime.fromtimestamp(
            last_ruling_date.timestamp() + RESPONSE_DEADLINES["lower_court"] * 86400,
            tz=timezone.utc
        )

        if now > appeal_deadline:
            raise ValueError(
                f"Appeal deadline has passed "
                f"({RESPONSE_DEADLINES['lower_court']} days from ruling)"
            )

        case["appeal"] = {
            "appellant_id": appellant_id,
            "grounds": grounds,
            "filed_date": _format_dt(now),
            "status": "pending",
            "appeal_court": "lower_court",
        }
        case["status"] = "appealed"
        case["timeline"].append({
            "event": "appeal_filed",
            "date": _format_dt(now),
            "detail": f"Appeal filed by {appellant_id} to Lower Court",
        })

        return {
            "case_id": case_id,
            "appellant": appellant_id,
            "appeal_court": "lower_court",
            "filed_date": _format_dt(now),
        }

    def issue_emergency_injunction(
        self, case_id: str, magistrate_id: str,
        injunction_text: str, duration_days: int = 14,
    ) -> Dict[str, Any]:
        """Issue an emergency injunction to preserve status quo."""
        case = self._get_case(case_id)
        if case is None:
            raise ValueError(f"Case {case_id} not found")

        self._get_active_magistrate(magistrate_id)

        now = _now()
        expires = datetime.fromtimestamp(
            now.timestamp() + duration_days * 86400,
            tz=timezone.utc
        )

        injunction = {
            "magistrate": magistrate_id,
            "text": injunction_text,
            "issued_date": _format_dt(now),
            "expires_date": _format_dt(expires),
            "duration_days": duration_days,
        }

        case.setdefault("injunctions", []).append(injunction)
        case["timeline"].append({
            "event": "emergency_injunction",
            "date": _format_dt(now),
            "detail": f"Emergency injunction issued for {duration_days} days",
        })

        return {
            "case_id": case_id,
            "injunction_text": injunction_text,
            "expires": _format_dt(expires),
            "duration_days": duration_days,
        }

    def dismiss_case(
        self, case_id: str, dismissed_by: str, reason: str
    ) -> Dict[str, Any]:
        """Dismiss a case."""
        case = self._get_case(case_id)
        if case is None:
            raise ValueError(f"Case {case_id} not found")

        case["status"] = "dismissed"
        case["timeline"].append({
            "event": "case_dismissed",
            "date": _format_dt(_now()),
            "detail": f"Dismissed by {dismissed_by}: {reason}",
        })

        return {
            "case_id": case_id,
            "status": "dismissed",
            "dismissed_by": dismissed_by,
            "reason": reason,
        }

    # -------------------------------------------------------------------
    # Default Judgment
    # -------------------------------------------------------------------

    def check_default_judgments(
        self, as_of: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Check for cases where response deadline has passed."""
        as_of = as_of or _now()
        defaults = []

        for case in self.state["cases"]:
            if case["status"] != "filed":
                continue

            deadline = _parse_dt(case.get("response_deadline"))
            if deadline and as_of > deadline:
                defaults.append({
                    "case_id": case["case_id"],
                    "case_type": case["case_type"],
                    "plaintiff": case["plaintiff_id"],
                    "defendant": case["defendant_id"],
                    "deadline_passed": _format_dt(deadline),
                    "days_overdue": int(_days_between(deadline, as_of)),
                    "eligible_for_default": True,
                })

        return defaults

    # -------------------------------------------------------------------
    # Registry Queries
    # -------------------------------------------------------------------

    def list_magistrates(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all magistrates."""
        mags = self.state.get("magistrates", [])
        if status:
            mags = [m for m in mags if m["status"] == status]

        return [
            {
                "citizen_id": m["citizen_id"],
                "status": m["status"],
                "supervising_judge": m["supervising_judge"],
                "appointment_date": m["appointment_date"],
                "term_end": m["term_end"],
                "cases_assigned": len(m.get("cases_assigned", [])),
                "rulings_count": m.get("rulings_count", 0),
            }
            for m in mags
        ]

    def list_cases(
        self, status: Optional[str] = None,
        case_type: Optional[str] = None,
        guild_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List cases with optional filters."""
        cases = self.state.get("cases", [])

        if status:
            cases = [c for c in cases if c["status"] == status]
        if case_type:
            cases = [c for c in cases if c["case_type"] == case_type]
        if guild_id:
            cases = [
                c for c in cases
                if guild_id in c.get("related_guild_ids", [])
            ]

        return [
            {
                "case_id": c["case_id"],
                "case_type": c["case_type"],
                "court": c["court"],
                "plaintiff": c["plaintiff_id"],
                "defendant": c["defendant_id"],
                "status": c["status"],
                "filed_date": c["filed_date"],
                "assigned_magistrate": c.get("assigned_magistrate"),
                "rulings_count": len(c.get("rulings", [])),
            }
            for c in cases
        ]

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get full case record including timeline."""
        return self._get_case(case_id)

    def court_statistics(self) -> Dict[str, Any]:
        """Get court statistics summary."""
        cases = self.state.get("cases", [])
        mags = self.state.get("magistrates", [])

        by_status = {}
        by_type = {}
        for c in cases:
            by_status[c["status"]] = by_status.get(c["status"], 0) + 1
            by_type[c["case_type"]] = by_type.get(c["case_type"], 0) + 1

        return {
            "total_cases": len(cases),
            "cases_by_status": by_status,
            "cases_by_type": by_type,
            "active_magistrates": len([m for m in mags if m["status"] == "active"]),
            "total_rulings": sum(m.get("rulings_count", 0) for m in mags),
        }

    # -------------------------------------------------------------------
    # Save (atomic write with backup)
    # -------------------------------------------------------------------

    def save(self, path: Optional[str] = None) -> None:
        """Atomic write state with backup."""
        target = Path(path) if path else self.state_path
        self.state["_last_updated"] = _format_dt(_now())
        if target.exists():
            shutil.copy2(target, target.with_suffix(".json.bak"))
        fd, tmp_path = tempfile.mkstemp(
            dir=target.parent, suffix=".tmp", prefix="magistrate_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, sort_keys=False)
            os.replace(tmp_path, target)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
