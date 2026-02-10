"""
House Bernard Advocate Engine v1.0
Manages advocate licensing, registration, pro bono obligations,
conflict-of-interest checks, and appointed representation.

Authority: GUILD_SYSTEM.md Section VIII
The Judiciary licenses advocates. The engine tracks compliance.

Usage:
    from guild.advocate_engine import AdvocateEngine
    engine = AdvocateEngine("guild/guild_state.json")
    result = engine.license_advocate(citizen_id, exam_scores)
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
# Constants from GUILD_SYSTEM.md Section VIII
# ---------------------------------------------------------------------------

# Licensing
EXAM_PASS_THRESHOLD = 0.70                  # 70% minimum to pass
CONTINUING_ED_INTERVAL_DAYS = 365           # Re-exam every 365 days
COOLING_PERIOD_DAYS = 180                   # From Council/guild leadership

# Pro bono
PRO_BONO_CASES_PER_YEAR = 1

# Fee caps
APPOINTED_STANDARD_RATE = 500               # $HB per case (set by Council)
GUILD_DISPUTE_FEE_CAP_MULTIPLIER = 2        # 2x appointed rate for guild disputes

# Advocate statuses
ADVOCATE_STATUSES = {"active", "suspended", "revoked", "expired"}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AdvocateEngine:

    def __init__(self, state_path: str = "guild/guild_state.json") -> None:
        self.state_path = Path(state_path)
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)
        # Ensure advocates list exists
        self.state.setdefault("advocates", [])

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _get_advocate(self, citizen_id: str) -> Optional[Dict[str, Any]]:
        """Find an advocate by citizen ID."""
        for a in self.state["advocates"]:
            if a["citizen_id"] == citizen_id:
                return a
        return None

    def _get_active_advocate(self, citizen_id: str) -> Dict[str, Any]:
        """Find an active advocate. Raises ValueError if not found."""
        adv = self._get_advocate(citizen_id)
        if adv is None:
            raise ValueError(f"No advocate record for citizen {citizen_id}")
        if adv["status"] != "active":
            raise ValueError(
                f"Advocate {citizen_id} is {adv['status']}, not active"
            )
        return adv

    # -------------------------------------------------------------------
    # Licensing
    # -------------------------------------------------------------------

    def license_advocate(
        self,
        citizen_id: str,
        covenant_exam_score: float,
        ethics_exam_score: float,
        guild_memberships: Optional[List[str]] = None,
        licensed_by: str = "judiciary",
    ) -> Dict[str, Any]:
        """License a new advocate.

        Requirements (Section VIII):
        - Standard citizenship tier or above
        - Pass Covenant Examination
        - Pass Ethics Examination
        - 180-day cooling period from Council/guild leadership
        - Registration in the Ledger

        Args:
            citizen_id: The citizen applying for advocate license.
            covenant_exam_score: Score on Covenant Examination (0.0-1.0).
            ethics_exam_score: Score on Ethics Examination (0.0-1.0).
            guild_memberships: Current guild memberships (for conflict tracking).
            licensed_by: 'judiciary' or 'governor' (Founding Period).
        """
        # Check not already licensed
        existing = self._get_advocate(citizen_id)
        if existing and existing["status"] == "active":
            raise ValueError(f"Citizen {citizen_id} is already a licensed advocate")

        # Validate exam scores
        if covenant_exam_score < EXAM_PASS_THRESHOLD:
            raise ValueError(
                f"Covenant exam score {covenant_exam_score:.1%} below "
                f"threshold {EXAM_PASS_THRESHOLD:.0%}"
            )
        if ethics_exam_score < EXAM_PASS_THRESHOLD:
            raise ValueError(
                f"Ethics exam score {ethics_exam_score:.1%} below "
                f"threshold {EXAM_PASS_THRESHOLD:.0%}"
            )

        now = _now()
        advocate = {
            "citizen_id": citizen_id,
            "licensed_date": _format_dt(now),
            "licensed_by": licensed_by,
            "status": "active",
            "covenant_exam_score": covenant_exam_score,
            "ethics_exam_score": ethics_exam_score,
            "last_exam_date": _format_dt(now),
            "guild_memberships": guild_memberships or [],
            "cases": [],
            "pro_bono_cases": [],
            "pro_bono_year_counts": {},
            "appointments": [],
            "disciplinary_history": [],
        }

        # Update or append
        if existing:
            idx = self.state["advocates"].index(existing)
            self.state["advocates"][idx] = advocate
        else:
            self.state["advocates"].append(advocate)

        return {
            "citizen_id": citizen_id,
            "status": "active",
            "licensed_date": _format_dt(now),
            "licensed_by": licensed_by,
            "covenant_score": covenant_exam_score,
            "ethics_score": ethics_exam_score,
            "next_exam_due": _format_dt(
                datetime.fromtimestamp(
                    now.timestamp() + CONTINUING_ED_INTERVAL_DAYS * 86400,
                    tz=timezone.utc
                )
            ),
        }

    def renew_license(
        self, citizen_id: str, covenant_exam_score: float,
        ethics_exam_score: float,
    ) -> Dict[str, Any]:
        """Renew an advocate license (continuing education exam).

        Must pass updated examination every 365 days.
        """
        adv = self._get_active_advocate(citizen_id)

        if covenant_exam_score < EXAM_PASS_THRESHOLD:
            adv["status"] = "expired"
            raise ValueError(
                f"Covenant exam score {covenant_exam_score:.1%} below threshold. "
                "License expired."
            )
        if ethics_exam_score < EXAM_PASS_THRESHOLD:
            adv["status"] = "expired"
            raise ValueError(
                f"Ethics exam score {ethics_exam_score:.1%} below threshold. "
                "License expired."
            )

        now = _now()
        adv["last_exam_date"] = _format_dt(now)
        adv["covenant_exam_score"] = covenant_exam_score
        adv["ethics_exam_score"] = ethics_exam_score

        return {
            "citizen_id": citizen_id,
            "renewed_date": _format_dt(now),
            "next_exam_due": _format_dt(
                datetime.fromtimestamp(
                    now.timestamp() + CONTINUING_ED_INTERVAL_DAYS * 86400,
                    tz=timezone.utc
                )
            ),
        }

    def check_continuing_education(
        self, as_of: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Check all advocates for continuing education compliance.

        Returns list of advocates with overdue or upcoming exams.
        """
        as_of = as_of or _now()
        results = []

        for adv in self.state["advocates"]:
            if adv["status"] != "active":
                continue

            last_exam = _parse_dt(adv.get("last_exam_date"))
            if last_exam is None:
                continue

            days_since = _days_between(last_exam, as_of)
            days_remaining = CONTINUING_ED_INTERVAL_DAYS - days_since

            if days_remaining <= 0:
                adv["status"] = "expired"
                results.append({
                    "citizen_id": adv["citizen_id"],
                    "status": "EXPIRED",
                    "days_overdue": abs(int(days_remaining)),
                })
            elif days_remaining <= 30:
                results.append({
                    "citizen_id": adv["citizen_id"],
                    "status": "DUE_SOON",
                    "days_remaining": int(days_remaining),
                })

        return results

    # -------------------------------------------------------------------
    # Conflict of Interest
    # -------------------------------------------------------------------

    def check_conflict_of_interest(
        self, advocate_id: str, opposing_guild_ids: List[str]
    ) -> Dict[str, Any]:
        """Check if an advocate has a conflict of interest.

        An advocate who is a member of a guild may not represent an
        opposing party in a dispute involving that guild.
        """
        adv = self._get_active_advocate(advocate_id)
        conflicts = []

        for gid in opposing_guild_ids:
            if gid in adv.get("guild_memberships", []):
                conflicts.append({
                    "guild_id": gid,
                    "reason": (
                        f"Advocate {advocate_id} is a member of guild {gid} "
                        "and cannot represent an opposing party"
                    ),
                })

        return {
            "advocate_id": advocate_id,
            "has_conflict": len(conflicts) > 0,
            "conflicts": conflicts,
        }

    # -------------------------------------------------------------------
    # Pro Bono Tracking
    # -------------------------------------------------------------------

    def record_pro_bono_case(
        self, advocate_id: str, case_id: str, year: int
    ) -> Dict[str, Any]:
        """Record a pro bono case for an advocate."""
        adv = self._get_active_advocate(advocate_id)

        case_record = {
            "case_id": case_id,
            "year": year,
            "date": _format_dt(_now()),
        }
        adv["pro_bono_cases"].append(case_record)

        year_key = str(year)
        adv["pro_bono_year_counts"][year_key] = (
            adv["pro_bono_year_counts"].get(year_key, 0) + 1
        )

        return {
            "advocate_id": advocate_id,
            "case_id": case_id,
            "year": year,
            "total_pro_bono_this_year": adv["pro_bono_year_counts"][year_key],
        }

    def check_pro_bono_compliance(
        self, year: int
    ) -> List[Dict[str, Any]]:
        """Check all advocates for pro bono compliance.

        Every licensed advocate must accept at least one pro bono case per year.
        """
        results = []
        year_key = str(year)

        for adv in self.state["advocates"]:
            if adv["status"] != "active":
                continue

            count = adv.get("pro_bono_year_counts", {}).get(year_key, 0)
            compliant = count >= PRO_BONO_CASES_PER_YEAR

            if not compliant:
                results.append({
                    "citizen_id": adv["citizen_id"],
                    "pro_bono_count": count,
                    "required": PRO_BONO_CASES_PER_YEAR,
                    "status": "NON_COMPLIANT",
                })

        return results

    # -------------------------------------------------------------------
    # Judiciary-Appointed Advocates
    # -------------------------------------------------------------------

    def appoint_advocate(
        self, advocate_id: str, case_id: str, case_type: str,
        appointed_by: str = "judiciary",
    ) -> Dict[str, Any]:
        """Appoint an advocate for a party that cannot afford representation.

        Appointed advocates are compensated from the Governance Fund
        at the standard rate set by Council.

        Serious proceedings requiring appointed advocates:
        - Citizenship revocation
        - Guild charter revocation
        - Criminal referral
        """
        adv = self._get_active_advocate(advocate_id)

        appointment = {
            "case_id": case_id,
            "case_type": case_type,
            "appointed_by": appointed_by,
            "date": _format_dt(_now()),
            "compensation_rate": APPOINTED_STANDARD_RATE,
            "compensation_source": "governance_fund",
        }
        adv["appointments"].append(appointment)

        return {
            "advocate_id": advocate_id,
            "case_id": case_id,
            "case_type": case_type,
            "compensation": APPOINTED_STANDARD_RATE,
            "source": "governance_fund",
        }

    # -------------------------------------------------------------------
    # Disciplinary Actions
    # -------------------------------------------------------------------

    def record_disciplinary_action(
        self, advocate_id: str, action_type: str, reason: str,
        imposed_by: str = "judiciary",
    ) -> Dict[str, Any]:
        """Record a disciplinary action against an advocate.

        Action types: 'warning', 'suspension', 'revocation'.
        """
        adv = self._get_advocate(advocate_id)
        if adv is None:
            raise ValueError(f"No advocate record for {advocate_id}")

        valid_actions = {"warning", "suspension", "revocation"}
        if action_type not in valid_actions:
            raise ValueError(f"Invalid action type: {action_type}")

        now = _now()
        record = {
            "action_type": action_type,
            "reason": reason,
            "imposed_by": imposed_by,
            "date": _format_dt(now),
        }
        adv["disciplinary_history"].append(record)

        if action_type == "suspension":
            adv["status"] = "suspended"
        elif action_type == "revocation":
            adv["status"] = "revoked"

        return {
            "advocate_id": advocate_id,
            "action": action_type,
            "reason": reason,
            "new_status": adv["status"],
            "timestamp": _format_dt(now),
        }

    # -------------------------------------------------------------------
    # Registry Queries
    # -------------------------------------------------------------------

    def list_advocates(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all advocates, optionally filtered by status."""
        advocates = self.state.get("advocates", [])
        if status:
            advocates = [a for a in advocates if a["status"] == status]

        return [
            {
                "citizen_id": a["citizen_id"],
                "status": a["status"],
                "licensed_date": a["licensed_date"],
                "guild_memberships": a.get("guild_memberships", []),
                "cases_count": len(a.get("cases", [])),
                "pro_bono_count": len(a.get("pro_bono_cases", [])),
                "appointments_count": len(a.get("appointments", [])),
            }
            for a in advocates
        ]

    def get_advocate(self, citizen_id: str) -> Optional[Dict[str, Any]]:
        """Get full advocate record."""
        return self._get_advocate(citizen_id)

    # -------------------------------------------------------------------
    # Fee Caps
    # -------------------------------------------------------------------

    def check_fee_cap(
        self, case_type: str, proposed_fee: float
    ) -> Dict[str, Any]:
        """Check if a proposed fee is within caps.

        Guild internal disputes are capped at 2x the standard appointed rate.
        """
        cap = None
        if case_type == "guild_internal_dispute":
            cap = APPOINTED_STANDARD_RATE * GUILD_DISPUTE_FEE_CAP_MULTIPLIER

        within_cap = True
        if cap is not None and proposed_fee > cap:
            within_cap = False

        return {
            "case_type": case_type,
            "proposed_fee": proposed_fee,
            "fee_cap": cap,
            "within_cap": within_cap,
            "note": (
                f"Fee capped at {cap:,.0f} $HB for guild internal disputes"
                if cap else "No fee cap for this case type"
            ),
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
            dir=target.parent, suffix=".tmp", prefix="advocate_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, sort_keys=False)
            os.replace(tmp_path, target)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
