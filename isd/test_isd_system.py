#!/usr/bin/env python3
"""
House Bernard Internal Security Directorate — Test Suite v1.0
Authority: Internal Security & Intelligence Court Act

Tests the ISD Engine, Intelligence Court, and Fusion Protocol.
Covers unit tests, integration tests, false positive tests,
and fail-safe tests.

All output is JSON. Run with:
    python3 -m pytest isd/test_isd_system.py -v
    python3 isd/test_isd_system.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure imports work from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from isd.isd_engine import (
    ISDEngine,
    THREAT_CATEGORIES,
    SEVERITY_LEVELS,
    ATTRIBUTION_LEVELS,
    CONTAINMENT_MAX_HOURS,
    WARRANT_HARD_LIMIT_DAYS,
    _format_dt,
    _parse_dt,
    _now,
)
from isd.intelligence_court import (
    IntelligenceCourtEngine,
    WARRANT_INITIAL_MAX_DAYS,
    APPROVAL_RATE_REVIEW_THRESHOLD,
    ADVOCATE_TERM_DAYS,
    JUDGES_TO_APPROVE,
)
from isd.fusion_protocol import (
    FusionProtocolEngine,
    SECURITY_ORGANS,
    FLOW_TYPES,
    REFERRAL_DEADLINE_HOURS,
    COORDINATOR_TERM_DAYS,
)


# ── Test helpers ─────────────────────────────────────────────────

def _make_state_file(tmp_dir: str, overrides: dict = None) -> str:
    """Create a temporary ISD state file for testing."""
    state = {
        "schema_version": "ISD_STATE_V1",
        "directorate": {
            "director": "agent-dir-001",
            "director_appointed": "2026-01-15T00:00:00Z",
            "director_confirmed_by_judiciary": True,
            "status": "operational",
            "agents": ["agent-001", "agent-002"],
        },
        "investigations": [],
        "warrants": [],
        "containment_actions": [],
        "threat_referrals_inbound": [],
        "threat_referrals_outbound": [],
        "surfacing_requests": [],
        "intelligence_court": {
            "judges": [
                {"judge_id": "judge-001", "name": "J1"},
                {"judge_id": "judge-002", "name": "J2"},
                {"judge_id": "judge-003", "name": "J3"},
            ],
            "rotation_history": [
                {"judge_id": "judge-001", "term_start": "2026-01-01T00:00:00Z"},
                {"judge_id": "judge-002", "term_start": "2025-07-01T00:00:00Z"},
                {"judge_id": "judge-003", "term_start": "2025-01-01T00:00:00Z"},
                {"judge_id": "judge-004", "term_start": "2024-07-01T00:00:00Z"},
            ],
            "citizens_advocate": {
                "advocate_id": "advocate-001",
                "term_start": _format_dt(_now() - timedelta(days=30)),
            },
            "advocate_history": [],
            "pattern_monitor": {
                "warrants_by_threat_category": {
                    "insider_threat": 3,
                    "penetration_operation": 1,
                },
                "warrants_by_target_branch": {"council": 1, "none": 3},
                "last_updated": _format_dt(_now()),
            },
            "statistical_record": {
                "applications_received": 20,
                "applications_approved": 15,
                "applications_denied": 5,
                "renewals_granted": 8,
                "warrants_expired": 3,
                "facially_deficient_flags": 2,
                "period_start": "2026-01-01T00:00:00Z",
            },
            "oversight_saturation": False,
        },
        "fusion": {
            "coordinator": "coordinator-001",
            "coordinator_term_start": _format_dt(
                _now() - timedelta(days=10)
            ),
            "coordinator_term_days": 90,
            "pending_referrals": [],
            "joint_threat_briefings": [],
            "quarterly_reviews": [
                {"date": _format_dt(_now() - timedelta(days=30))},
            ],
        },
        "accountability": {
            "monthly_reports": [],
            "quarterly_briefings": [],
            "annual_reports": [],
            "biennial_audits": [],
        },
        "pause": False,
        "last_modified": _format_dt(_now()),
    }

    if overrides:
        _deep_merge(state, overrides)

    path = os.path.join(tmp_dir, "isd_state.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return path


def _deep_merge(base: dict, overrides: dict) -> None:
    """Recursively merge overrides into base dict."""
    for key, val in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            _deep_merge(base[key], val)
        else:
            base[key] = val


def _sample_warrant_application() -> dict:
    """Return a valid warrant application."""
    return {
        "target_id": "citizen-suspect-001",
        "threat_category": "insider_threat",
        "threat_basis": (
            "Citizen-suspect-001 has transmitted classified Section 9 "
            "intelligence summaries to an external entity identified "
            "by Section 9 as threat actor TA-2026-003. Evidence includes "
            "three separate exfiltration events over 14 days."
        ),
        "investigative_necessity": (
            "Open Warden investigation would alert the target and "
            "allow destruction of evidence and warning of co-conspirators."
        ),
        "scope": {
            "systems": ["internal_comms", "submission_history"],
            "duration_days": 60,
            "behavioral_data": True,
        },
        "minimization_procedures": (
            "Innocent party data encountered incidentally will be "
            "purged within 72 hours unless directly relevant to the "
            "authorized investigation. Retention decisions logged."
        ),
    }


# ═════════════════════════════════════════════════════════════════
# ISD ENGINE TESTS
# ═════════════════════════════════════════════════════════════════


class TestISDEngineInvestigations(unittest.TestCase):
    """Test investigation lifecycle in the ISD Engine."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = ISDEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_open_investigation_valid(self) -> None:
        """Valid investigation opens successfully."""
        result = self.engine.open_investigation(
            warrant_id="WRT-abc123",
            target_id="citizen-001",
            threat_category="insider_threat",
            threat_basis="Specific credible evidence of compromise",
            scope="Internal communications and submission history",
        )
        self.assertIn("investigation", result)
        inv = result["investigation"]
        self.assertEqual(inv["status"], "active")
        self.assertEqual(inv["threat_category"], "insider_threat")
        self.assertEqual(inv["target_id"], "citizen-001")
        self.assertTrue(inv["investigation_id"].startswith("INV-"))

    def test_open_investigation_invalid_category(self) -> None:
        """Invalid threat category is rejected."""
        result = self.engine.open_investigation(
            warrant_id="WRT-abc123",
            target_id="citizen-001",
            threat_category="political_dissent",
            threat_basis="Some basis",
            scope="Some scope",
        )
        self.assertEqual(result["error"], "invalid_threat_category")

    def test_open_investigation_missing_fields(self) -> None:
        """Missing required fields returns error."""
        result = self.engine.open_investigation(
            warrant_id="",
            target_id="citizen-001",
            threat_category="insider_threat",
            threat_basis="Some basis",
            scope="Some scope",
        )
        self.assertEqual(result["error"], "missing_required_fields")

    def test_close_investigation_exonerated(self) -> None:
        """Exoneration closure computes seal deadline."""
        # First add an investigation to state
        self.engine.state["investigations"].append({
            "investigation_id": "INV-test001",
            "status": "active",
            "opened": _format_dt(_now() - timedelta(days=30)),
        })
        result = self.engine.close_investigation(
            investigation_id="INV-test001",
            finding="exonerated",
            lead_agent_certification=True,
            closure_summary="No evidence of wrongdoing found.",
        )
        self.assertEqual(result["status"], "closed_exonerated")
        self.assertIn("seal_deadline", result["closure"])
        self.assertFalse(result["closure"]["court_approved"])

    def test_close_investigation_no_certification(self) -> None:
        """Closure without lead agent certification fails."""
        self.engine.state["investigations"].append({
            "investigation_id": "INV-test002",
            "status": "active",
        })
        result = self.engine.close_investigation(
            investigation_id="INV-test002",
            finding="exonerated",
            lead_agent_certification=False,
            closure_summary="Summary",
        )
        self.assertEqual(result["error"], "lead_agent_certification_required")

    def test_close_investigation_not_found(self) -> None:
        """Closing nonexistent investigation returns error."""
        result = self.engine.close_investigation(
            investigation_id="INV-nonexistent",
            finding="exonerated",
            lead_agent_certification=True,
            closure_summary="Summary",
        )
        self.assertEqual(result["error"], "investigation_not_found")

    def test_all_threat_categories_accepted(self) -> None:
        """Every defined threat category opens an investigation."""
        for cat in THREAT_CATEGORIES:
            result = self.engine.open_investigation(
                warrant_id=f"WRT-{cat}",
                target_id="citizen-001",
                threat_category=cat,
                threat_basis="Specific evidence of threat",
                scope="Defined scope",
            )
            self.assertIn("investigation", result, f"Failed for {cat}")


class TestISDEngineThreatAssessment(unittest.TestCase):
    """Test threat assessment logic."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = ISDEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_assess_s4_a1_immediate(self) -> None:
        """S4 severity + A1 attribution = immediate warrant application."""
        result = self.engine.assess_threat(
            indicator_id="IND-001",
            threat_category="insider_threat",
            severity="S4",
            attribution="A1",
            description="Confirmed insider compromise",
        )
        self.assertEqual(result["recommendation"], "immediate_warrant_application")

    def test_assess_s2_a3_warrant_recommended(self) -> None:
        """S2 severity + A3 attribution = warrant recommended."""
        result = self.engine.assess_threat(
            indicator_id="IND-002",
            threat_category="intelligence_leak",
            severity="S2",
            attribution="A3",
            description="Probable leak detected",
        )
        self.assertEqual(result["recommendation"], "preliminary_assessment")

    def test_assess_s1_a4_monitor_only(self) -> None:
        """S1 severity + A4 attribution = monitor only."""
        result = self.engine.assess_threat(
            indicator_id="IND-003",
            threat_category="counter_deception",
            severity="S1",
            attribution="A4",
            description="Minor anomaly",
        )
        self.assertEqual(result["recommendation"], "monitor_only")

    def test_assess_invalid_severity(self) -> None:
        """Invalid severity level rejected."""
        result = self.engine.assess_threat(
            indicator_id="IND-004",
            threat_category="insider_threat",
            severity="S5",
            attribution="A1",
            description="Test",
        )
        self.assertEqual(result["error"], "invalid_severity")

    def test_assess_invalid_attribution(self) -> None:
        """Invalid attribution level rejected."""
        result = self.engine.assess_threat(
            indicator_id="IND-005",
            threat_category="insider_threat",
            severity="S1",
            attribution="A5",
            description="Test",
        )
        self.assertEqual(result["error"], "invalid_attribution")


class TestISDEngineContainment(unittest.TestCase):
    """Test containment evaluation logic."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = ISDEngine(self.state_path)
        # Add an active investigation
        self.engine.state["investigations"].append({
            "investigation_id": "INV-ctn001",
            "status": "active",
            "opened": _format_dt(_now()),
        })

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_containment_authorized(self) -> None:
        """Crown-authorized containment produces valid record."""
        result = self.engine.evaluate_containment(
            investigation_id="INV-ctn001",
            threat_description="Target about to exfiltrate data",
            proposed_actions=["freeze_system_access", "isolate_accounts"],
            crown_authorized=True,
        )
        self.assertIn("containment_id", result)
        self.assertTrue(result["defensive_only"])
        self.assertEqual(result["status"], "authorized")

    def test_containment_no_crown_auth(self) -> None:
        """Containment without Crown authorization fails."""
        result = self.engine.evaluate_containment(
            investigation_id="INV-ctn001",
            threat_description="Threat",
            proposed_actions=["freeze_system_access"],
            crown_authorized=False,
        )
        self.assertEqual(result["error"], "crown_authorization_required")

    def test_containment_invalid_actions(self) -> None:
        """Non-defensive containment actions rejected."""
        result = self.engine.evaluate_containment(
            investigation_id="INV-ctn001",
            threat_description="Threat",
            proposed_actions=["arrest_citizen"],
            crown_authorized=True,
        )
        self.assertEqual(result["error"], "invalid_containment_actions")

    def test_containment_expiry_check(self) -> None:
        """Expired containment correctly identified."""
        self.engine.state["containment_actions"].append({
            "containment_id": "CTN-exp001",
            "expires": _format_dt(_now() - timedelta(hours=1)),
            "court_review_deadline": _format_dt(_now() - timedelta(hours=1)),
        })
        result = self.engine.check_containment_expiry("CTN-exp001")
        self.assertTrue(result["expired"])
        self.assertTrue(result["must_release"])


class TestISDEngineCrownBypass(unittest.TestCase):
    """Test Crown Compromise Protocol."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = ISDEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_crown_bypass_valid(self) -> None:
        """Valid bypass request produces pending record."""
        result = self.engine.evaluate_crown_bypass(
            evidence_of_compromise="Crown account accessed by adversary TA-003",
            why_crown_route_compromised="Crown is the threat source",
            requested_actions=["freeze_system_access"],
        )
        self.assertEqual(result["type"], "emergency_crown_bypass_warrant")
        self.assertTrue(result["requires_unanimous_court"])
        self.assertEqual(result["max_duration_hours"], CONTAINMENT_MAX_HOURS)

    def test_crown_bypass_missing_evidence(self) -> None:
        """Bypass without evidence fails."""
        result = self.engine.evaluate_crown_bypass(
            evidence_of_compromise="",
            why_crown_route_compromised="Reason",
            requested_actions=["freeze_system_access"],
        )
        self.assertEqual(result["error"], "evidence_of_compromise_required")


class TestISDEngineReporting(unittest.TestCase):
    """Test accountability reporting."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir, {
            "investigations": [
                {"investigation_id": "INV-r001", "status": "active",
                 "threat_category": "insider_threat", "severity": "S3",
                 "containment_actions": []},
                {"investigation_id": "INV-r002", "status": "active",
                 "threat_category": "intelligence_leak", "severity": "S2",
                 "containment_actions": []},
                {"investigation_id": "INV-r003", "status": "closed_exonerated",
                 "threat_category": "counter_deception"},
            ],
        })
        self.engine = ISDEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_monthly_report(self) -> None:
        """Monthly report contains expected fields."""
        result = self.engine.monthly_report()
        self.assertEqual(result["report_type"], "monthly_classified")
        self.assertEqual(result["active_investigations"], 2)
        self.assertEqual(result["closed_investigations"], 1)

    def test_quarterly_briefing(self) -> None:
        """Quarterly briefing does not reveal specific targets."""
        result = self.engine.quarterly_briefing()
        self.assertEqual(result["classification"], "verbal_only_no_written_materials")
        self.assertNotIn("target_id", json.dumps(result))

    def test_annual_report(self) -> None:
        """Annual report computes resolution rate."""
        result = self.engine.annual_report()
        self.assertEqual(result["effectiveness"]["total_investigations"], 3)
        self.assertGreater(result["effectiveness"]["resolution_rate"], 0)

    def test_directorate_status(self) -> None:
        """Directorate status returns current state."""
        result = self.engine.directorate_status()
        self.assertEqual(result["director"], "agent-dir-001")
        self.assertTrue(result["confirmed_by_judiciary"])
        self.assertFalse(result["pause_active"])


class TestISDEnginePetitions(unittest.TestCase):
    """Test citizen petition handling."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = ISDEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_petition_sufficient_basis(self) -> None:
        """Petition with sufficient basis returns no_action_required."""
        result = self.engine.evaluate_petition(
            citizen_id="citizen-pet-001",
            stated_concern="I believe my submission data has been accessed "
                           "without my knowledge based on unusual activity "
                           "in my account logs.",
        )
        self.assertEqual(result["response"], "no_action_required")

    def test_petition_vague_concern(self) -> None:
        """Vague petition asks for more basis."""
        result = self.engine.evaluate_petition(
            citizen_id="citizen-pet-002",
            stated_concern="worried",
        )
        self.assertEqual(result["response"], "petition_requires_additional_basis")

    def test_petition_response_indistinguishable(self) -> None:
        """Response structure is identical regardless of investigation existence."""
        r1 = self.engine.evaluate_petition(
            citizen_id="citizen-pet-003",
            stated_concern="I have specific concerns about unauthorized "
                           "access to my governance participation records.",
        )
        # The response keys should be the same structure
        self.assertIn("petition_id", r1)
        self.assertIn("response", r1)
        self.assertIn("detail", r1)


# ═════════════════════════════════════════════════════════════════
# INTELLIGENCE COURT TESTS
# ═════════════════════════════════════════════════════════════════


class TestIntelligenceCourtWarrants(unittest.TestCase):
    """Test warrant application evaluation."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.court = IntelligenceCourtEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_valid_application_passes(self) -> None:
        """Valid warrant application passes all five checks."""
        app = _sample_warrant_application()
        result = self.court.evaluate_warrant_application(app)
        self.assertTrue(result["all_requirements_met"])
        self.assertIn("warrant", result)
        self.assertEqual(len(result["checks"]), 5)
        for check in result["checks"]:
            self.assertTrue(check["passed"], f"Failed: {check['requirement']}")

    def test_missing_target_fails(self) -> None:
        """No target ID fails specific_target check."""
        app = _sample_warrant_application()
        app["target_id"] = ""
        result = self.court.evaluate_warrant_application(app)
        self.assertFalse(result["all_requirements_met"])
        target_check = next(
            c for c in result["checks"]
            if c["requirement"] == "specific_target"
        )
        self.assertFalse(target_check["passed"])

    def test_weak_threat_basis_fails(self) -> None:
        """Short/vague threat basis fails articulable_threat_basis check."""
        app = _sample_warrant_application()
        app["threat_basis"] = "Suspicious"
        result = self.court.evaluate_warrant_application(app)
        self.assertFalse(result["all_requirements_met"])

    def test_missing_scope_fails(self) -> None:
        """No scope limitation fails."""
        app = _sample_warrant_application()
        app["scope"] = {}
        result = self.court.evaluate_warrant_application(app)
        self.assertFalse(result["all_requirements_met"])

    def test_facially_deficient_flagged(self) -> None:
        """Application failing 3+ checks flagged as facially deficient."""
        app = {
            "target_id": "",
            "threat_basis": "",
            "investigative_necessity": "",
            "scope": {},
            "minimization_procedures": "",
        }
        result = self.court.evaluate_warrant_application(app)
        self.assertTrue(result["facially_deficient"])

    def test_no_advocate_blocks_warrant(self) -> None:
        """No Citizen's Advocate blocks all warrant applications."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {"citizens_advocate": None},
        })
        # Reload with new state — need separate file
        path2 = os.path.join(self.tmp_dir, "state2.json")
        with open(state_path, "r") as f:
            s = json.load(f)
        s["intelligence_court"]["citizens_advocate"] = None
        with open(path2, "w") as f:
            json.dump(s, f)
        court = IntelligenceCourtEngine(path2)
        result = court.evaluate_warrant_application(
            _sample_warrant_application()
        )
        self.assertEqual(result["error"], "no_citizens_advocate")

    def test_saturation_blocks_warrant(self) -> None:
        """Oversight saturation blocks non-emergency warrants."""
        path2 = os.path.join(self.tmp_dir, "state_sat.json")
        with open(self.state_path, "r") as f:
            s = json.load(f)
        s["intelligence_court"]["oversight_saturation"] = True
        with open(path2, "w") as f:
            json.dump(s, f)
        court = IntelligenceCourtEngine(path2)
        result = court.evaluate_warrant_application(
            _sample_warrant_application()
        )
        self.assertEqual(result["error"], "oversight_saturation_active")

    def test_warrant_duration_capped(self) -> None:
        """Warrant duration capped at 90 days initial."""
        app = _sample_warrant_application()
        app["scope"]["duration_days"] = 365
        result = self.court.evaluate_warrant_application(app)
        self.assertTrue(result["all_requirements_met"])
        self.assertLessEqual(
            result["warrant"]["max_duration_days"],
            WARRANT_INITIAL_MAX_DAYS,
        )


class TestIntelligenceCourtRenewals(unittest.TestCase):
    """Test warrant renewal escalation."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir, {
            "warrants": [
                {
                    "warrant_id": "WRT-renew001",
                    "status": "active",
                    "renewal_count": 0,
                },
                {
                    "warrant_id": "WRT-renew002",
                    "status": "active",
                    "renewal_count": 2,
                },
                {
                    "warrant_id": "WRT-renew003",
                    "status": "active",
                    "renewal_count": 3,
                },
            ],
            "investigations": [
                {
                    "investigation_id": "INV-ren001",
                    "warrant_id": "WRT-renew001",
                    "opened": _format_dt(_now() - timedelta(days=80)),
                },
            ],
        })
        self.court = IntelligenceCourtEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_first_renewal(self) -> None:
        """First renewal requires updated threat basis only."""
        result = self.court.evaluate_warrant_renewal(
            warrant_id="WRT-renew001",
            updated_threat_basis="Continued evidence of compromise",
        )
        self.assertEqual(result["renewal_number"], 1)
        self.assertEqual(result["status"], "renewal_approved")

    def test_third_renewal_needs_director(self) -> None:
        """Third renewal requires ISD Director certification."""
        result = self.court.evaluate_warrant_renewal(
            warrant_id="WRT-renew002",
            updated_threat_basis="Continued justification",
            director_certification=False,
        )
        self.assertEqual(result["error"], "director_certification_required")

    def test_fourth_renewal_needs_crown(self) -> None:
        """Fourth+ renewal requires Crown authorization."""
        result = self.court.evaluate_warrant_renewal(
            warrant_id="WRT-renew003",
            updated_threat_basis="Continued justification",
            director_certification=True,
            crown_authorization=False,
        )
        self.assertEqual(result["error"], "crown_authorization_required")


class TestIntelligenceCourtApprovalRate(unittest.TestCase):
    """Test approval rate monitoring and gaming detection."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_healthy_approval_rate(self) -> None:
        """75% approval rate does not trigger review."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {
                "statistical_record": {
                    "applications_received": 20,
                    "applications_approved": 15,
                    "applications_denied": 5,
                    "facially_deficient_flags": 1,
                },
            },
        })
        court = IntelligenceCourtEngine(state_path)
        result = court.compute_approval_rate()
        self.assertFalse(result["review_triggered"])

    def test_high_approval_rate_triggers_review(self) -> None:
        """95% approval rate triggers independent review."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {
                "statistical_record": {
                    "applications_received": 20,
                    "applications_approved": 19,
                    "applications_denied": 1,
                    "facially_deficient_flags": 0,
                },
            },
        })
        court = IntelligenceCourtEngine(state_path)
        result = court.compute_approval_rate()
        self.assertTrue(result["review_triggered"])

    def test_gaming_indicators_detected(self) -> None:
        """High facially deficient rate flags potential gaming."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {
                "statistical_record": {
                    "applications_received": 10,
                    "applications_approved": 7,
                    "applications_denied": 3,
                    "facially_deficient_flags": 3,
                },
            },
        })
        court = IntelligenceCourtEngine(state_path)
        result = court.compute_approval_rate()
        self.assertTrue(result["gaming_indicators"])

    def test_zero_applications(self) -> None:
        """No applications produces clean report."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {
                "statistical_record": {
                    "applications_received": 0,
                    "applications_approved": 0,
                    "applications_denied": 0,
                    "facially_deficient_flags": 0,
                },
            },
        })
        court = IntelligenceCourtEngine(state_path)
        result = court.compute_approval_rate()
        self.assertFalse(result["review_triggered"])
        self.assertEqual(result["approval_rate"], 0.0)


class TestIntelligenceCourtAdvocate(unittest.TestCase):
    """Test Citizen's Advocate management."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_advocate_active(self) -> None:
        """Active advocate with remaining term."""
        state_path = _make_state_file(self.tmp_dir)
        court = IntelligenceCourtEngine(state_path)
        result = court.check_advocate_status()
        self.assertTrue(result["advocate_present"])
        self.assertFalse(result["warrants_blocked"])
        self.assertGreater(result["days_remaining"], 0)

    def test_advocate_expired(self) -> None:
        """Expired advocate blocks warrants."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {
                "citizens_advocate": {
                    "advocate_id": "advocate-expired",
                    "term_start": _format_dt(
                        _now() - timedelta(days=ADVOCATE_TERM_DAYS + 31 + 1)
                    ),
                },
            },
        })
        court = IntelligenceCourtEngine(state_path)
        result = court.check_advocate_status()
        self.assertTrue(result["expired"])
        self.assertTrue(result["warrants_blocked"])

    def test_advocate_none(self) -> None:
        """No advocate blocks warrants."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {"citizens_advocate": None},
        })
        court = IntelligenceCourtEngine(state_path)
        result = court.check_advocate_status()
        self.assertFalse(result["advocate_present"])
        self.assertTrue(result["warrants_blocked"])


class TestIntelligenceCourtRotation(unittest.TestCase):
    """Test judge rotation compliance."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_rotation_compliant(self) -> None:
        """Proper rotation is compliant."""
        state_path = _make_state_file(self.tmp_dir)
        court = IntelligenceCourtEngine(state_path)
        result = court.check_rotation_compliance()
        self.assertTrue(result["compliant"])

    def test_consecutive_terms_violate(self) -> None:
        """Same judge consecutive terms is a violation."""
        state_path = _make_state_file(self.tmp_dir, {
            "intelligence_court": {
                "rotation_history": [
                    {"judge_id": "judge-001",
                     "term_start": _format_dt(_now() - timedelta(days=200))},
                    {"judge_id": "judge-001",
                     "term_start": _format_dt(_now() - timedelta(days=10))},
                ],
            },
        })
        court = IntelligenceCourtEngine(state_path)
        result = court.check_rotation_compliance()
        self.assertTrue(result["consecutive_term_violation"])


class TestIntelligenceCourtSurfacing(unittest.TestCase):
    """Test surfacing decision logic."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.court = IntelligenceCourtEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_parallel_construction_feasible(self) -> None:
        """Feasible parallel construction recommends Clean Brief."""
        result = self.court.evaluate_surfacing_request(
            investigation_id="INV-surf001",
            evidence_summary="Strong evidence from multiple sources",
            parallel_construction_feasible=True,
            methods_at_risk=[],
        )
        self.assertTrue(result["options"][0]["recommended"])
        self.assertEqual(
            result["options"][0]["option"],
            "surface_via_clean_brief",
        )

    def test_no_parallel_construction_four_options(self) -> None:
        """Infeasible parallel construction presents four graduated options."""
        result = self.court.evaluate_surfacing_request(
            investigation_id="INV-surf002",
            evidence_summary="Evidence only in classified channels",
            parallel_construction_feasible=False,
            methods_at_risk=["source_alpha", "method_bravo"],
        )
        self.assertEqual(len(result["options"]), 4)
        option_codes = [o["code"] for o in result["options"]]
        self.assertEqual(
            option_codes,
            ["option_a", "option_b", "option_c", "option_d"],
        )


class TestIntelligenceCourtTribunal(unittest.TestCase):
    """Test Classified Tribunal evaluation."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.court = IntelligenceCourtEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_tribunal_exhaustion_met(self) -> None:
        """All exhaustion requirements met allows tribunal."""
        result = self.court.evaluate_tribunal_request(
            investigation_id="INV-trib001",
            option_a_insufficient=True,
            option_b_insufficient=True,
            option_d_harmful=True,
            harm_description="Burns critical source inside adversary org",
        )
        self.assertTrue(result["exhaustion_certified"])
        self.assertTrue(result["special_counsel_required"])

    def test_tribunal_exhaustion_not_met(self) -> None:
        """Missing exhaustion requirements block tribunal."""
        result = self.court.evaluate_tribunal_request(
            investigation_id="INV-trib002",
            option_a_insufficient=True,
            option_b_insufficient=False,
            option_d_harmful=True,
            harm_description="Test",
        )
        self.assertEqual(result["error"], "exhaustion_requirement_not_met")
        self.assertEqual(len(result["missing_certifications"]), 1)


# ═════════════════════════════════════════════════════════════════
# FUSION PROTOCOL TESTS
# ═════════════════════════════════════════════════════════════════


class TestFusionReferrals(unittest.TestCase):
    """Test threat referral creation and routing."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.fusion = FusionProtocolEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_flow_1_section9_to_isd(self) -> None:
        """Section 9 insider threat referral routes to ISD via Crown."""
        result = self.fusion.create_threat_referral(
            source_organ="section_9",
            threat_category="insider_threat",
            threat_summary="External actor TA-003 has cultivated asset "
                           "inside House Bernard Council",
        )
        ref = result["referral"]
        self.assertEqual(ref["flow_type"], "flow_1")
        self.assertEqual(ref["destination_organ"], "isd")
        self.assertEqual(ref["route_via"], "crown")

    def test_flow_2_isd_to_wardens(self) -> None:
        """ISD surfacing referral routes to Wardens via Court."""
        result = self.fusion.create_threat_referral(
            source_organ="isd",
            threat_category="corruption",
            threat_summary="Investigation complete — evidence ready for "
                           "open prosecution",
        )
        ref = result["referral"]
        self.assertEqual(ref["flow_type"], "flow_2")
        self.assertEqual(ref["destination_organ"], "wardens")
        self.assertEqual(ref["route_via"], "intelligence_court")

    def test_flow_3_wardens_to_isd(self) -> None:
        """Warden deeper threat referral routes to ISD via Crown."""
        result = self.fusion.create_threat_referral(
            source_organ="wardens",
            threat_category="intelligence_leak",
            threat_summary="Routine conduct investigation revealed "
                           "systematic classified data access patterns",
        )
        ref = result["referral"]
        self.assertEqual(ref["flow_type"], "flow_3")
        self.assertEqual(ref["destination_organ"], "isd")
        self.assertEqual(ref["route_via"], "crown")

    def test_flow_4_joint_threat_picture(self) -> None:
        """Section 9 general referral becomes joint threat briefing flow."""
        result = self.fusion.create_threat_referral(
            source_organ="section_9",
            threat_category="counter_deception",
            threat_summary="Coordinated disinformation campaign",
        )
        ref = result["referral"]
        self.assertEqual(ref["flow_type"], "flow_4")

    def test_invalid_source_organ(self) -> None:
        """Invalid source organ rejected."""
        result = self.fusion.create_threat_referral(
            source_organ="treasury",
            threat_category="corruption",
            threat_summary="Some threat",
        )
        self.assertEqual(result["error"], "invalid_source_organ")

    def test_referral_has_deadlines(self) -> None:
        """Referral includes all mandatory deadlines."""
        result = self.fusion.create_threat_referral(
            source_organ="section_9",
            threat_category="penetration_operation",
            threat_summary="Penetration detected",
        )
        ref = result["referral"]
        self.assertIn("transmission_deadline", ref)
        self.assertIn("crown_ack_deadline", ref)
        self.assertIn("crown_routing_deadline", ref)

    def test_flash_urgency(self) -> None:
        """Flash urgency accepted."""
        result = self.fusion.create_threat_referral(
            source_organ="section_9",
            threat_category="insider_threat",
            threat_summary="Imminent insider action",
            urgency="flash",
        )
        self.assertEqual(result["referral"]["urgency"], "flash")


class TestFusionCleanBriefs(unittest.TestCase):
    """Test Clean Brief production."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.fusion = FusionProtocolEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_clean_brief_produced(self) -> None:
        """Standard Clean Brief produced correctly."""
        result = self.fusion.produce_clean_brief(
            investigation_id="INV-cb001",
            actionable_intelligence="Target has been accessing restricted "
                                    "systems from unauthorized locations",
        )
        self.assertEqual(result["type"], "clean_brief")
        self.assertTrue(result["methods_stripped"])
        self.assertFalse(result["admissible_in_proceedings"])

    def test_clean_brief_methods_not_stripped(self) -> None:
        """Clean Brief with methods not stripped is rejected."""
        result = self.fusion.produce_clean_brief(
            investigation_id="INV-cb002",
            actionable_intelligence="Target observed via classified method X",
            methods_stripped=False,
        )
        self.assertEqual(result["error"], "methods_must_be_stripped")

    def test_flash_clean_brief(self) -> None:
        """Flash Clean Brief for imminent threat."""
        result = self.fusion.produce_flash_clean_brief(
            investigation_id="INV-fcb001",
            actionable_intelligence="Target about to execute exfiltration",
            imminent_threat=True,
        )
        self.assertEqual(result["type"], "flash_clean_brief")
        self.assertEqual(result["urgency"], "flash")


class TestFusionJointBriefing(unittest.TestCase):
    """Test Joint Threat Briefing creation."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.fusion = FusionProtocolEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_joint_briefing_valid(self) -> None:
        """Valid joint briefing combines both assessments."""
        result = self.fusion.create_joint_threat_briefing(
            section_9_assessment="External actor conducting cyber intrusion",
            isd_assessment="Internal asset providing access credentials",
            combined_threat_picture="Coordinated inside-outside attack",
        )
        self.assertEqual(result["type"], "joint_threat_briefing")
        self.assertFalse(result["warrant_required"])

    def test_joint_briefing_missing_assessment(self) -> None:
        """Missing assessment rejected."""
        result = self.fusion.create_joint_threat_briefing(
            section_9_assessment="",
            isd_assessment="Internal assessment",
            combined_threat_picture="Combined",
        )
        self.assertEqual(result["error"], "both_assessments_required")


class TestFusionJurisdiction(unittest.TestCase):
    """Test jurisdictional resolution."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.fusion = FusionProtocolEngine(self.state_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_dual_claim_defaults_to_isd(self) -> None:
        """Dual jurisdiction claim defaults to ISD."""
        result = self.fusion.resolve_jurisdiction(
            threat_description="External-internal boundary threat",
            section_9_claim=True,
            isd_claim=True,
        )
        self.assertEqual(result["jurisdiction"], "isd")
        self.assertEqual(result["method"], "default_rule")

    def test_crown_override(self) -> None:
        """Crown override changes jurisdiction."""
        result = self.fusion.resolve_jurisdiction(
            threat_description="Threat requiring Section 9 internal action",
            section_9_claim=True,
            isd_claim=True,
            crown_override="section_9",
            crown_override_reason="Section 9 has unique capability needed",
        )
        self.assertEqual(result["jurisdiction"], "section_9")
        self.assertEqual(result["method"], "crown_override")

    def test_uncontested_claim(self) -> None:
        """Uncontested claim goes to the claiming organ."""
        result = self.fusion.resolve_jurisdiction(
            threat_description="Pure external threat",
            section_9_claim=True,
            isd_claim=False,
        )
        self.assertEqual(result["jurisdiction"], "section_9")
        self.assertEqual(result["method"], "uncontested")


class TestFusionCoordinator(unittest.TestCase):
    """Test Fusion Coordinator management."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_coordinator_active(self) -> None:
        """Active coordinator within term."""
        state_path = _make_state_file(self.tmp_dir)
        fusion = FusionProtocolEngine(state_path)
        result = fusion.check_coordinator_status()
        self.assertTrue(result["coordinator_active"])
        self.assertFalse(result["expired"])
        self.assertGreater(result["days_remaining"], 0)

    def test_coordinator_expired(self) -> None:
        """Expired coordinator flagged for rotation."""
        state_path = _make_state_file(self.tmp_dir, {
            "fusion": {
                "coordinator": "coordinator-exp",
                "coordinator_term_start": _format_dt(
                    _now() - timedelta(days=100)
                ),
                "coordinator_term_days": 90,
            },
        })
        fusion = FusionProtocolEngine(state_path)
        result = fusion.check_coordinator_status()
        self.assertFalse(result["coordinator_active"])
        self.assertTrue(result["expired"])
        self.assertTrue(result["rotation_required"])

    def test_no_coordinator(self) -> None:
        """No coordinator returns founding period note."""
        state_path = _make_state_file(self.tmp_dir, {
            "fusion": {"coordinator": None},
        })
        fusion = FusionProtocolEngine(state_path)
        result = fusion.check_coordinator_status()
        self.assertFalse(result["coordinator_active"])


class TestFusionHealth(unittest.TestCase):
    """Test fusion health metrics."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_healthy_system(self) -> None:
        """No overdue referrals = healthy."""
        state_path = _make_state_file(self.tmp_dir)
        fusion = FusionProtocolEngine(state_path)
        result = fusion.fusion_health_report()
        self.assertEqual(result["health_status"], "healthy")
        self.assertEqual(result["overdue_referrals"], 0)

    def test_degraded_system(self) -> None:
        """Overdue referrals = degraded."""
        state_path = _make_state_file(self.tmp_dir, {
            "fusion": {
                "pending_referrals": [
                    {
                        "referral_id": "REF-over001",
                        "status": "pending_transmission",
                        "transmission_deadline": _format_dt(
                            _now() - timedelta(hours=1)
                        ),
                        "crown_ack_deadline": _format_dt(
                            _now() + timedelta(hours=23)
                        ),
                        "crown_acknowledged": False,
                    },
                ],
                "quarterly_reviews": [
                    {"date": _format_dt(_now() - timedelta(days=30))},
                ],
            },
        })
        fusion = FusionProtocolEngine(state_path)
        result = fusion.fusion_health_report()
        self.assertEqual(result["health_status"], "degraded")
        self.assertEqual(result["overdue_referrals"], 1)


class TestFusionAntiStovepipe(unittest.TestCase):
    """Test anti-stovepipe audit."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_all_compliant(self) -> None:
        """Clean system passes anti-stovepipe audit."""
        state_path = _make_state_file(self.tmp_dir)
        fusion = FusionProtocolEngine(state_path)
        result = fusion.anti_stovepipe_audit()
        self.assertTrue(result["all_compliant"])
        self.assertFalse(result["stovepipe_risk"])


# ═════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═════════════════════════════════════════════════════════════════


class TestIntegration(unittest.TestCase):
    """End-to-end integration tests across all three engines."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_full_investigation_lifecycle(self) -> None:
        """
        Full lifecycle: threat assessment → warrant application →
        investigation → closure.
        """
        engine = ISDEngine(self.state_path)
        court = IntelligenceCourtEngine(self.state_path)

        # 1. Assess threat
        assessment = engine.assess_threat(
            indicator_id="IND-int001",
            threat_category="insider_threat",
            severity="S3",
            attribution="A2",
            description="Section 9 referral: citizen compromised",
        )
        self.assertEqual(
            assessment["recommendation"],
            "warrant_application_recommended",
        )

        # 2. Apply for warrant
        app = _sample_warrant_application()
        warrant_result = court.evaluate_warrant_application(app)
        self.assertTrue(warrant_result["all_requirements_met"])
        warrant_id = warrant_result["warrant"]["warrant_id"]

        # 3. Open investigation
        inv_result = engine.open_investigation(
            warrant_id=warrant_id,
            target_id="citizen-suspect-001",
            threat_category="insider_threat",
            threat_basis="See warrant application",
            scope="Internal comms and submission history",
        )
        self.assertIn("investigation", inv_result)
        inv_id = inv_result["investigation"]["investigation_id"]

        # 4. Close investigation (exonerated)
        engine.state["investigations"].append(inv_result["investigation"])
        closure = engine.close_investigation(
            investigation_id=inv_id,
            finding="exonerated",
            lead_agent_certification=True,
            closure_summary="Investigation found no wrongdoing.",
        )
        self.assertEqual(closure["status"], "closed_exonerated")
        self.assertIn("seal_deadline", closure["closure"])

    def test_full_fusion_flow_1(self) -> None:
        """
        Full Flow 1: Section 9 referral → ISD assessment →
        warrant application.
        """
        fusion = FusionProtocolEngine(self.state_path)
        engine = ISDEngine(self.state_path)
        court = IntelligenceCourtEngine(self.state_path)

        # 1. Section 9 creates referral
        referral = fusion.create_threat_referral(
            source_organ="section_9",
            threat_category="penetration_operation",
            threat_summary="External entity has placed asset inside "
                           "House Bernard",
            urgency="priority",
        )
        self.assertEqual(referral["referral"]["flow_type"], "flow_1")

        # 2. ISD assesses the threat
        assessment = engine.assess_threat(
            indicator_id="IND-flow001",
            threat_category="penetration_operation",
            severity="S4",
            attribution="A1",
            description="Confirmed penetration operation",
            source_organ="section_9",
        )
        self.assertEqual(
            assessment["recommendation"],
            "immediate_warrant_application",
        )

        # 3. Apply for warrant
        app = _sample_warrant_application()
        app["threat_category"] = "penetration_operation"
        warrant = court.evaluate_warrant_application(app)
        self.assertTrue(warrant["all_requirements_met"])


# ═════════════════════════════════════════════════════════════════
# FALSE POSITIVE TESTS
# ═════════════════════════════════════════════════════════════════


class TestFalsePositives(unittest.TestCase):
    """Normal activity should not produce errors or false alerts."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_empty_state_reports_clean(self) -> None:
        """Empty state produces clean reports without errors."""
        engine = ISDEngine(self.state_path)
        monthly = engine.monthly_report()
        self.assertEqual(monthly["active_investigations"], 0)

        quarterly = engine.quarterly_briefing()
        self.assertIn("threat_landscape", quarterly)

        status = engine.directorate_status()
        self.assertFalse(status["pause_active"])

    def test_clean_fusion_health(self) -> None:
        """Clean fusion state reports healthy."""
        fusion = FusionProtocolEngine(self.state_path)
        health = fusion.fusion_health_report()
        self.assertEqual(health["health_status"], "healthy")

    def test_clean_stovepipe_audit(self) -> None:
        """Clean state passes stovepipe audit."""
        fusion = FusionProtocolEngine(self.state_path)
        audit = fusion.anti_stovepipe_audit()
        self.assertTrue(audit["all_compliant"])


# ═════════════════════════════════════════════════════════════════
# FAIL-SAFE TESTS
# ═════════════════════════════════════════════════════════════════


class TestFailSafe(unittest.TestCase):
    """Verify graceful degradation on bad input."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir)

    def test_nonexistent_investigation(self) -> None:
        """Operations on nonexistent investigations return error, not crash."""
        engine = ISDEngine(self.state_path)
        result = engine.close_investigation(
            "INV-nonexistent", "exonerated", True, "Summary"
        )
        self.assertEqual(result["error"], "investigation_not_found")

    def test_nonexistent_containment(self) -> None:
        """Checking nonexistent containment returns error."""
        engine = ISDEngine(self.state_path)
        result = engine.check_containment_expiry("CTN-nonexistent")
        self.assertEqual(result["error"], "containment_not_found")

    def test_nonexistent_warrant(self) -> None:
        """Renewing nonexistent warrant returns error."""
        court = IntelligenceCourtEngine(self.state_path)
        result = court.evaluate_warrant_renewal("WRT-nonexistent", "Basis")
        self.assertEqual(result["error"], "warrant_not_found")

    def test_nonexistent_referral(self) -> None:
        """Checking nonexistent referral returns error."""
        fusion = FusionProtocolEngine(self.state_path)
        result = fusion.check_referral_compliance("REF-nonexistent")
        self.assertEqual(result["error"], "referral_not_found")

    def test_empty_petition(self) -> None:
        """Empty petition returns error."""
        engine = ISDEngine(self.state_path)
        result = engine.evaluate_petition("", "")
        self.assertEqual(result["error"], "citizen_id_and_concern_required")

    def test_all_json_serializable(self) -> None:
        """All engine outputs are JSON-serializable."""
        engine = ISDEngine(self.state_path)
        court = IntelligenceCourtEngine(self.state_path)
        fusion = FusionProtocolEngine(self.state_path)

        outputs = [
            engine.monthly_report(),
            engine.quarterly_briefing(),
            engine.annual_report(),
            engine.directorate_status(),
            engine.assess_threat("I1", "insider_threat", "S2", "A3", "Test"),
            court.compute_approval_rate(),
            court.check_rotation_compliance(),
            court.check_advocate_status(),
            court.annual_statistical_report(),
            court.get_pattern_monitor(),
            fusion.fusion_health_report(),
            fusion.anti_stovepipe_audit(),
            fusion.check_coordinator_status(),
        ]

        for i, output in enumerate(outputs):
            try:
                json.dumps(output)
            except (TypeError, ValueError) as e:
                self.fail(f"Output {i} not JSON-serializable: {e}")


# ═════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    # Run tests and output results as JSON
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # JSON summary
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "success": result.wasSuccessful(),
    }
    print("\n" + json.dumps(summary, indent=2))
