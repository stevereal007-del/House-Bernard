#!/usr/bin/env python3
"""
House Bernard Guild System — Test Suite v1.0
Tests guild formation, governance, financial incentives, constitutional
constraints, secession, lab charters, advocates, and magistrate court.

All output is JSON. Run with:
    python3 -m pytest guild/test_guild_system.py -v
    python3 guild/test_guild_system.py          # standalone
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Module setup — ensure imports work from repo root
# ---------------------------------------------------------------------------
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from guild.guild_engine import (
    GuildEngine,
    COLLABORATION_MULTIPLIER,
    ACHIEVEMENT_BONUSES,
    ENDOWMENT_MILESTONES,
    MIN_GUILD_MEMBERS,
    MAX_GUILD_COUNCIL_SEATS,
    MAX_GUILD_TREASURY_PCT,
    LAB_MIN_GUILD_AGE_MONTHS,
    LAB_MIN_GENES,
    LAB_MIN_GENES_FOUNDING,
    LAB_MIN_MEMBERS,
    LAB_MIN_GENES_PER_YEAR,
    GENESIS_GUILD_BONUS,
    _format_dt,
    _now,
)
from guild.advocate_engine import (
    AdvocateEngine,
    EXAM_PASS_THRESHOLD,
    APPOINTED_STANDARD_RATE,
    GUILD_DISPUTE_FEE_CAP_MULTIPLIER,
    PRO_BONO_CASES_PER_YEAR,
)
from guild.magistrate_engine import (
    MagistrateEngine,
    MAGISTRATE_TERM_DAYS,
    RESPONSE_DEADLINES,
    MAGISTRATE_JURISDICTION,
    EXCLUDED_FROM_MAGISTRATE,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def _make_state_file(tmp_dir: str, extra: dict = None) -> str:
    """Create a temporary guild state file for testing."""
    state = {
        "_schema_version": "1.0",
        "_description": "Test guild state",
        "_last_updated": None,
        "guilds": [],
        "guild_counter": 0,
        "founding_period": True,
        "genesis_guild_bonuses_remaining": 3,
        "total_supply": 100_000_000,
        "council_seats": {
            "total": 7,
            "guild_seat_limit": 2,
            "coalition_seat_limit": 3,
        },
    }
    if extra:
        state.update(extra)
    path = os.path.join(tmp_dir, "guild_state.json")
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return path


def _sample_charter(name: str = "Adversarial Robustness Guild",
                     domain: str = "adversarial robustness") -> dict:
    """Create a valid sample charter."""
    return {
        "name": name,
        "domain": domain,
        "membership_rules": "Journeyman tier or above. Must demonstrate expertise.",
        "revenue_sharing_model": "Equal split among all contributing members.",
        "guildmaster_election_process": "Simple majority vote every 180 days.",
        "dispute_resolution": "Internal mediation, then Judiciary petition.",
        "dissolution_terms": "Simple majority vote. Assets per charter.",
    }


# ---------------------------------------------------------------------------
# Guild Engine Tests
# ---------------------------------------------------------------------------

class TestGuildFormation(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_validate_valid_charter(self):
        charter = _sample_charter()
        result = self.engine.validate_charter(charter)
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])

    def test_validate_missing_fields(self):
        charter = {"name": "Test Guild"}
        result = self.engine.validate_charter(charter)
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_guildmaster_decides_rejected(self):
        charter = _sample_charter()
        charter["revenue_sharing_model"] = "The guildmaster decides."
        result = self.engine.validate_charter(charter)
        self.assertFalse(result["valid"])
        self.assertIn("explicit", result["errors"][0].lower())

    def test_register_guild_success(self):
        charter = _sample_charter()
        members = ["citizen_001", "citizen_002", "citizen_003"]
        result = self.engine.register_guild(charter, members, "citizen_001", "governor")
        self.assertEqual(result["guild_id"], "GUILD-001")
        self.assertEqual(result["name"], "Adversarial Robustness Guild")
        self.assertEqual(result["members"], 3)
        self.assertEqual(result["status"], "active")
        # Genesis bonus during Founding Period
        self.assertEqual(result["genesis_bonus"], GENESIS_GUILD_BONUS)

    def test_register_guild_too_few_members(self):
        charter = _sample_charter()
        with self.assertRaises(ValueError) as ctx:
            self.engine.register_guild(charter, ["c1", "c2"], "c1", "governor")
        self.assertIn("Minimum", str(ctx.exception))

    def test_register_guild_guildmaster_not_member(self):
        charter = _sample_charter()
        with self.assertRaises(ValueError):
            self.engine.register_guild(
                charter, ["c1", "c2", "c3"], "c4", "governor"
            )

    def test_register_guild_duplicate_members(self):
        charter = _sample_charter()
        with self.assertRaises(ValueError) as ctx:
            self.engine.register_guild(charter, ["c1", "c1", "c2"], "c1", "governor")
        self.assertIn("Duplicate", str(ctx.exception))

    def test_register_guild_duplicate_name(self):
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")
        charter2 = _sample_charter()
        with self.assertRaises(ValueError) as ctx:
            self.engine.register_guild(charter2, ["c4", "c5", "c6"], "c4", "governor")
        self.assertIn("already exists", str(ctx.exception))

    def test_genesis_bonus_limited_to_three(self):
        for i in range(3):
            charter = _sample_charter(name=f"Guild {i+1}", domain=f"domain {i+1}")
            members = [f"c{i*3+j}" for j in range(3)]
            result = self.engine.register_guild(charter, members, members[0], "governor")
            self.assertEqual(result["genesis_bonus"], GENESIS_GUILD_BONUS)

        # Fourth guild should not get bonus
        charter = _sample_charter(name="Guild 4", domain="domain 4")
        members = ["c9", "c10", "c11"]
        result = self.engine.register_guild(charter, members, "c9", "governor")
        self.assertNotIn("genesis_bonus", result)

    def test_governor_registration_blocked_outside_founding(self):
        self.engine.state["founding_period"] = False
        charter = _sample_charter()
        with self.assertRaises(ValueError) as ctx:
            self.engine.register_guild(
                charter, ["c1", "c2", "c3"], "c1", "governor"
            )
        self.assertIn("Founding Period", str(ctx.exception))

    def test_guild_id_increments(self):
        for i in range(3):
            charter = _sample_charter(name=f"G{i}", domain=f"d{i}")
            members = [f"m{i*3+j}" for j in range(3)]
            result = self.engine.register_guild(charter, members, members[0], "governor")
            self.assertEqual(result["guild_id"], f"GUILD-{i+1:03d}")


class TestGuildGovernance(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_elect_guildmaster(self):
        result = self.engine.elect_guildmaster("GUILD-001", "c2")
        self.assertEqual(result["old_guildmaster"], "c1")
        self.assertEqual(result["new_guildmaster"], "c2")

    def test_elect_non_member_fails(self):
        with self.assertRaises(ValueError):
            self.engine.elect_guildmaster("GUILD-001", "c99")

    def test_remove_guildmaster(self):
        result = self.engine.remove_guildmaster("GUILD-001")
        self.assertEqual(result["removed_guildmaster"], "c1")
        guild = self.engine.get_guild("GUILD-001")
        self.assertIsNone(guild["guildmaster"])

    def test_record_assembly(self):
        result = self.engine.record_assembly(
            "GUILD-001",
            summary="Discussed Q1 research direction",
            decisions=["Focus on compaction algorithms"],
            attendees=["c1", "c2", "c3"],
        )
        self.assertEqual(result["assembly_number"], 1)
        self.assertEqual(result["attendees"], 3)


class TestGuildMembership(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_add_member(self):
        result = self.engine.add_member("GUILD-001", "c4")
        self.assertEqual(result["total_members"], 4)
        self.assertEqual(result["membership_type"], "full")

    def test_add_provisional_member(self):
        result = self.engine.add_member("GUILD-001", "c4", provisional=True)
        self.assertEqual(result["membership_type"], "provisional")
        self.assertEqual(result["total_provisional"], 1)

    def test_add_duplicate_member_fails(self):
        with self.assertRaises(ValueError):
            self.engine.add_member("GUILD-001", "c1")

    def test_remove_member(self):
        result = self.engine.remove_member("GUILD-001", "c2")
        self.assertEqual(result["remaining_members"], 2)

    def test_remove_guildmaster_fails(self):
        with self.assertRaises(ValueError):
            self.engine.remove_member("GUILD-001", "c1")

    def test_below_minimum_triggers_probationary(self):
        self.engine.remove_member("GUILD-001", "c2")
        result = self.engine.remove_member("GUILD-001", "c3")
        self.assertEqual(result["status_change"], "probationary")
        guild = self.engine.get_guild("GUILD-001")
        self.assertEqual(guild["status"], "probationary")

    def test_promote_provisional(self):
        self.engine.add_member("GUILD-001", "c4", provisional=True)
        result = self.engine.promote_provisional_member("GUILD-001", "c4")
        self.assertEqual(result["promoted_to"], "full_member")
        self.assertEqual(result["total_members"], 4)

    def test_remove_non_member_fails(self):
        with self.assertRaises(ValueError):
            self.engine.remove_member("GUILD-001", "c99")


class TestCollaborationMultiplier(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_two_guilds(self):
        result = self.engine.calculate_collaboration_multiplier(["G1", "G2"])
        self.assertEqual(result["multiplier"], 1.25)
        self.assertEqual(result["type"], "two_guilds")

    def test_three_plus_guilds(self):
        result = self.engine.calculate_collaboration_multiplier(["G1", "G2", "G3"])
        self.assertEqual(result["multiplier"], 1.50)

    def test_guild_plus_independent(self):
        result = self.engine.calculate_collaboration_multiplier(
            ["G1"], has_independent=True
        )
        self.assertEqual(result["multiplier"], 1.15)

    def test_single_guild_no_bonus(self):
        result = self.engine.calculate_collaboration_multiplier(["G1"])
        self.assertEqual(result["multiplier"], 1.00)

    def test_independent_only(self):
        result = self.engine.calculate_collaboration_multiplier(
            [], has_independent=True
        )
        self.assertEqual(result["multiplier"], 1.00)

    def test_apply_multiplier(self):
        result = self.engine.apply_collaboration_multiplier(50000, ["G1", "G2"])
        self.assertEqual(result["base_payment"], 50000)
        self.assertEqual(result["adjusted_payment"], 62500.0)
        self.assertEqual(result["bonus"], 12500.0)

    def test_dedup_guilds(self):
        result = self.engine.calculate_collaboration_multiplier(
            ["G1", "G1", "G2"]
        )
        self.assertEqual(result["guild_count"], 2)
        self.assertEqual(result["multiplier"], 1.25)


class TestAchievementBonuses(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_five_flame_bonus(self):
        # Record 5 Flame-tier genes
        for i in range(4):
            self.engine.record_gene_production(
                "GUILD-001", f"gene_{i}", 2, "Flame"
            )
        result = self.engine.record_gene_production(
            "GUILD-001", "gene_4", 2, "Flame"
        )
        self.assertEqual(len(result["bonuses_triggered"]), 1)
        self.assertEqual(result["bonuses_triggered"][0]["type"], "five_flame_quarter")
        self.assertEqual(result["bonuses_triggered"][0]["amount"], 10000)

    def test_ten_flame_bonus(self):
        for i in range(9):
            self.engine.record_gene_production(
                "GUILD-001", f"gene_{i}", 2, "Flame"
            )
        result = self.engine.record_gene_production(
            "GUILD-001", "gene_9", 2, "Flame"
        )
        bonuses = [b for b in result["bonuses_triggered"] if b["type"] == "ten_flame_quarter"]
        self.assertEqual(len(bonuses), 1)
        self.assertEqual(bonuses[0]["amount"], 25000)

    def test_first_invariant_bonus(self):
        result = self.engine.record_gene_production(
            "GUILD-001", "inv_gene_1", 4, "Invariant"
        )
        invariant_bonuses = [
            b for b in result["bonuses_triggered"]
            if b["type"] == "first_invariant"
        ]
        self.assertEqual(len(invariant_bonuses), 1)
        self.assertEqual(invariant_bonuses[0]["amount"], 50000)

    def test_subsequent_invariant_bonus(self):
        self.engine.record_gene_production(
            "GUILD-001", "inv_gene_1", 4, "Invariant"
        )
        result = self.engine.record_gene_production(
            "GUILD-001", "inv_gene_2", 4, "Invariant"
        )
        subsequent = [
            b for b in result["bonuses_triggered"]
            if b["type"] == "subsequent_invariant"
        ]
        self.assertEqual(len(subsequent), 1)
        self.assertEqual(subsequent[0]["amount"], 25000)

    def test_quarterly_reset(self):
        for i in range(5):
            self.engine.record_gene_production(
                "GUILD-001", f"gene_{i}", 2, "Flame"
            )
        result = self.engine.reset_quarterly_counts("GUILD-001")
        self.assertEqual(result["previous_quarterly_flame_count"], 5)
        guild = self.engine.get_guild("GUILD-001")
        self.assertEqual(guild["quarterly_flame_count"], 0)


class TestConstitutionalConstraints(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_council_seat_limit_allowed(self):
        result = self.engine.check_council_seat_limit("GUILD-001", 2)
        self.assertTrue(result["allowed"])

    def test_council_seat_limit_exceeded(self):
        result = self.engine.check_council_seat_limit("GUILD-001", 3)
        self.assertFalse(result["allowed"])

    def test_update_council_seats(self):
        result = self.engine.update_council_seats("GUILD-001", 2)
        self.assertEqual(result["new_seats"], 2)

    def test_update_council_seats_over_limit(self):
        with self.assertRaises(ValueError):
            self.engine.update_council_seats("GUILD-001", 3)

    def test_coalition_limit(self):
        # Register two guilds
        charter2 = _sample_charter(name="Guild 2", domain="domain 2")
        self.engine.register_guild(charter2, ["c4", "c5", "c6"], "c4", "governor")

        # Set seats
        self.engine.update_council_seats("GUILD-001", 2)
        self.engine.update_council_seats("GUILD-002", 2)

        result = self.engine.check_coalition_limit(["GUILD-001", "GUILD-002"])
        self.assertFalse(result["allowed"])
        self.assertEqual(result["total_seats"], 4)

    def test_financial_cap_check(self):
        result = self.engine.check_financial_caps("GUILD-001")
        self.assertTrue(result["treasury_within_cap"])
        # Genesis bonus = 25,000 which is well under 2% of 100M = 2,000,000
        self.assertEqual(len(result["warnings"]), 0)

    def test_financial_cap_exceeded(self):
        guild = self.engine.get_guild("GUILD-001")
        guild["treasury_balance"] = 3_000_000  # Over 2% of 100M
        result = self.engine.check_financial_caps("GUILD-001")
        self.assertFalse(result["treasury_within_cap"])
        self.assertTrue(len(result["warnings"]) > 0)


class TestGuildSecession(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_dissolve_guild(self):
        result = self.engine.dissolve_guild("GUILD-001", "voluntary")
        self.assertEqual(result["status"], "dissolved")
        self.assertEqual(result["forfeitures"]["treasury_balance"], GENESIS_GUILD_BONUS)
        self.assertEqual(result["members_released"], 3)

        guild = self.engine.get_guild("GUILD-001")
        self.assertEqual(guild["status"], "dissolved")
        self.assertEqual(guild["treasury_balance"], 0.0)

    def test_dissolve_guild_with_endowments(self):
        guild = self.engine.get_guild("GUILD-001")
        guild["endowment_bonds"] = [{
            "bond_id": "GUILD-001-ENDOW-2Y",
            "milestone_years": 2,
            "principal": 50000,
            "status": "active",
        }]

        result = self.engine.dissolve_guild("GUILD-001")
        self.assertEqual(len(result["forfeitures"]["endowment_bonds"]), 1)
        self.assertEqual(result["forfeitures"]["endowment_bonds"][0]["principal"], 50000)

    def test_dissolved_name_retirement(self):
        self.engine.dissolve_guild("GUILD-001")
        charter = _sample_charter()
        with self.assertRaises(ValueError) as ctx:
            self.engine.register_guild(charter, ["c4", "c5", "c6"], "c4", "governor")
        self.assertIn("retired", str(ctx.exception))


class TestLabCharter(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(
            charter,
            [f"c{i}" for i in range(8)],  # 8 members (above minimum 7)
            "c0",
            "governor",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_lab_eligibility_new_guild(self):
        result = self.engine.check_lab_charter_eligibility("GUILD-001")
        self.assertFalse(result["eligible"])
        # Should fail age and genes checks
        self.assertFalse(result["checks"]["guild_age_months"]["met"])
        self.assertFalse(result["checks"]["flame_plus_genes"]["met"])
        self.assertTrue(result["checks"]["member_count"]["met"])

    def test_lab_eligibility_mature_guild(self):
        guild = self.engine.get_guild("GUILD-001")
        # Backdate charter to 13 months ago
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 13 * 30.44 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)
        # Set 5 flame genes (founding period reduced threshold)
        guild["genes_by_tier"]["flame"] = 5

        result = self.engine.check_lab_charter_eligibility("GUILD-001")
        self.assertTrue(result["eligible"])

    def test_grant_lab_charter(self):
        guild = self.engine.get_guild("GUILD-001")
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 13 * 30.44 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)
        guild["genes_by_tier"]["flame"] = 5

        result = self.engine.grant_lab_charter(
            "GUILD-001", "Lab X: Adversarial Robustness",
            "Research proposal text...",
        )
        self.assertIn("lab_designation", result)
        self.assertEqual(result["term_days"], 365)

    def test_grant_lab_charter_ineligible(self):
        with self.assertRaises(ValueError):
            self.engine.grant_lab_charter(
                "GUILD-001", "Lab X", "Proposal..."
            )

    def test_record_lab_gene(self):
        guild = self.engine.get_guild("GUILD-001")
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 13 * 30.44 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)
        guild["genes_by_tier"]["flame"] = 5
        self.engine.grant_lab_charter("GUILD-001", "Lab X", "Proposal...")

        result = self.engine.record_lab_gene("GUILD-001", "lab_gene_1")
        self.assertEqual(result["genes_this_term"], 1)

    def test_revoke_lab_charter(self):
        guild = self.engine.get_guild("GUILD-001")
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 13 * 30.44 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)
        guild["genes_by_tier"]["flame"] = 5
        self.engine.grant_lab_charter("GUILD-001", "Lab X", "Proposal...")

        result = self.engine.revoke_lab_charter(
            "GUILD-001", "Zero genes in 12 months",
            "judiciary_order",
        )
        self.assertIn("Lab X", result["lab_designation"])

    def test_renew_lab_charter_insufficient_genes(self):
        guild = self.engine.get_guild("GUILD-001")
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 13 * 30.44 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)
        guild["genes_by_tier"]["flame"] = 5
        self.engine.grant_lab_charter("GUILD-001", "Lab X", "Proposal...")

        with self.assertRaises(ValueError) as ctx:
            self.engine.renew_lab_charter("GUILD-001")
        self.assertIn("minimum", str(ctx.exception).lower())


class TestLabRevenueSharing(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(
            charter, [f"c{i}" for i in range(8)], "c0", "governor"
        )
        # Make eligible and grant lab
        guild = self.engine.get_guild("GUILD-001")
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 13 * 30.44 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)
        guild["genes_by_tier"]["flame"] = 5
        self.engine.grant_lab_charter("GUILD-001", "Lab X", "Proposal...")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_lab_access_split(self):
        result = self.engine.calculate_lab_revenue_split(
            "GUILD-001", "lab_access", 10000
        )
        self.assertEqual(result["guild_share"], 3000)
        self.assertEqual(result["treasury_share"], 2000)
        self.assertEqual(result["burned"], 5000)

    def test_api_access_split(self):
        result = self.engine.calculate_lab_revenue_split(
            "GUILD-001", "api_access", 10000
        )
        self.assertEqual(result["guild_share"], 3000)

    def test_research_license_split(self):
        result = self.engine.calculate_lab_revenue_split(
            "GUILD-001", "research_license", 10000
        )
        self.assertEqual(result["guild_share"], 4000)
        self.assertEqual(result["treasury_share"], 1000)
        self.assertEqual(result["burned"], 5000)

    def test_no_lab_raises(self):
        charter2 = _sample_charter(name="No Lab Guild", domain="other")
        self.engine.register_guild(charter2, ["x1", "x2", "x3"], "x1", "governor")
        with self.assertRaises(ValueError):
            self.engine.calculate_lab_revenue_split("GUILD-002", "lab_access", 1000)


class TestEndowments(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_no_eligibility_new_guild(self):
        result = self.engine.check_endowment_eligibility("GUILD-001")
        self.assertEqual(result["eligible_milestones"], [])

    def test_two_year_eligibility(self):
        guild = self.engine.get_guild("GUILD-001")
        # Backdate to 2+ years ago
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 2.1 * 365.25 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)

        result = self.engine.check_endowment_eligibility("GUILD-001")
        self.assertEqual(len(result["eligible_milestones"]), 1)
        self.assertEqual(result["eligible_milestones"][0]["endowment_amount"], 50000)

    def test_activate_endowment(self):
        guild = self.engine.get_guild("GUILD-001")
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 2.1 * 365.25 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)

        result = self.engine.activate_endowment_bond("GUILD-001", 2)
        self.assertEqual(result["principal"], 50000)
        self.assertEqual(result["yield_rate"], 0.30)

    def test_duplicate_endowment_fails(self):
        guild = self.engine.get_guild("GUILD-001")
        old_date = datetime.fromtimestamp(
            _now().timestamp() - 2.1 * 365.25 * 86400, tz=timezone.utc
        )
        guild["charter_date"] = _format_dt(old_date)

        self.engine.activate_endowment_bond("GUILD-001", 2)
        with self.assertRaises(ValueError):
            self.engine.activate_endowment_bond("GUILD-001", 2)


class TestGuildOath(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_generate_oath(self):
        oath = self.engine.generate_guild_oath("GUILD-001")
        self.assertIn("Adversarial Robustness Guild", oath)
        self.assertIn("adversarial robustness", oath)
        self.assertIn("Ad Astra Per Aspera", oath)
        self.assertIn("gene registry", oath)


class TestGuildRegistry(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)
        for i in range(3):
            charter = _sample_charter(name=f"Guild {i}", domain=f"domain {i}")
            members = [f"m{i*3+j}" for j in range(3)]
            self.engine.register_guild(charter, members, members[0], "governor")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_list_all_guilds(self):
        result = self.engine.list_guilds()
        self.assertEqual(len(result), 3)

    def test_list_active_guilds(self):
        self.engine.dissolve_guild("GUILD-001")
        result = self.engine.list_guilds(status="active")
        self.assertEqual(len(result), 2)

    def test_financial_summary(self):
        result = self.engine.guild_financial_summary("GUILD-001")
        self.assertEqual(result["treasury_balance"], GENESIS_GUILD_BONUS)
        self.assertIn("treasury_cap", result)


class TestGuildSave(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = GuildEngine(self.state_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_save_and_reload(self):
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")
        self.engine.save()

        # Reload
        engine2 = GuildEngine(self.state_path)
        self.assertEqual(len(engine2.list_guilds()), 1)
        self.assertEqual(engine2.list_guilds()[0]["name"], "Adversarial Robustness Guild")

    def test_backup_created(self):
        charter = _sample_charter()
        self.engine.register_guild(charter, ["c1", "c2", "c3"], "c1", "governor")
        self.engine.save()
        # Save again to trigger backup
        self.engine.save()
        backup_path = Path(self.state_path).with_suffix(".json.bak")
        self.assertTrue(backup_path.exists())


# ---------------------------------------------------------------------------
# Advocate Engine Tests
# ---------------------------------------------------------------------------

class TestAdvocateLicensing(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = AdvocateEngine(self.state_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_license_advocate(self):
        result = self.engine.license_advocate("adv_001", 0.85, 0.80)
        self.assertEqual(result["status"], "active")
        self.assertIn("next_exam_due", result)

    def test_license_fails_low_covenant_score(self):
        with self.assertRaises(ValueError) as ctx:
            self.engine.license_advocate("adv_001", 0.50, 0.80)
        self.assertIn("Covenant exam", str(ctx.exception))

    def test_license_fails_low_ethics_score(self):
        with self.assertRaises(ValueError) as ctx:
            self.engine.license_advocate("adv_001", 0.85, 0.50)
        self.assertIn("Ethics exam", str(ctx.exception))

    def test_duplicate_license_fails(self):
        self.engine.license_advocate("adv_001", 0.85, 0.80)
        with self.assertRaises(ValueError):
            self.engine.license_advocate("adv_001", 0.85, 0.80)

    def test_renew_license(self):
        self.engine.license_advocate("adv_001", 0.85, 0.80)
        result = self.engine.renew_license("adv_001", 0.90, 0.85)
        self.assertIn("next_exam_due", result)

    def test_renew_fails_below_threshold(self):
        self.engine.license_advocate("adv_001", 0.85, 0.80)
        with self.assertRaises(ValueError):
            self.engine.renew_license("adv_001", 0.50, 0.80)
        # Verify status is now expired
        adv = self.engine.get_advocate("adv_001")
        self.assertEqual(adv["status"], "expired")


class TestAdvocateConflicts(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = AdvocateEngine(self.state_path)
        self.engine.license_advocate(
            "adv_001", 0.85, 0.80,
            guild_memberships=["GUILD-001"],
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_conflict_detected(self):
        result = self.engine.check_conflict_of_interest("adv_001", ["GUILD-001"])
        self.assertTrue(result["has_conflict"])

    def test_no_conflict(self):
        result = self.engine.check_conflict_of_interest("adv_001", ["GUILD-002"])
        self.assertFalse(result["has_conflict"])


class TestAdvocateProBono(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = AdvocateEngine(self.state_path)
        self.engine.license_advocate("adv_001", 0.85, 0.80)
        self.engine.license_advocate("adv_002", 0.90, 0.85)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_record_pro_bono(self):
        result = self.engine.record_pro_bono_case("adv_001", "MC-0001", 2026)
        self.assertEqual(result["total_pro_bono_this_year"], 1)

    def test_pro_bono_compliance(self):
        # adv_001 has no pro bono cases for 2026
        non_compliant = self.engine.check_pro_bono_compliance(2026)
        self.assertEqual(len(non_compliant), 2)

        # Record one for adv_001
        self.engine.record_pro_bono_case("adv_001", "MC-0001", 2026)
        non_compliant = self.engine.check_pro_bono_compliance(2026)
        self.assertEqual(len(non_compliant), 1)
        self.assertEqual(non_compliant[0]["citizen_id"], "adv_002")


class TestAdvocateAppointment(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = AdvocateEngine(self.state_path)
        self.engine.license_advocate("adv_001", 0.85, 0.80)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_appoint_advocate(self):
        result = self.engine.appoint_advocate(
            "adv_001", "MC-0001", "citizenship_revocation"
        )
        self.assertEqual(result["compensation"], APPOINTED_STANDARD_RATE)
        self.assertEqual(result["source"], "governance_fund")

    def test_fee_cap_guild_dispute(self):
        cap = APPOINTED_STANDARD_RATE * GUILD_DISPUTE_FEE_CAP_MULTIPLIER
        result = self.engine.check_fee_cap("guild_internal_dispute", cap + 100)
        self.assertFalse(result["within_cap"])

    def test_no_fee_cap_other_cases(self):
        result = self.engine.check_fee_cap("other_case", 99999)
        self.assertTrue(result["within_cap"])


class TestAdvocateDisciplinary(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = AdvocateEngine(self.state_path)
        self.engine.license_advocate("adv_001", 0.85, 0.80)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_warning(self):
        result = self.engine.record_disciplinary_action(
            "adv_001", "warning", "Missed filing deadline"
        )
        self.assertEqual(result["new_status"], "active")

    def test_suspension(self):
        result = self.engine.record_disciplinary_action(
            "adv_001", "suspension", "False evidence"
        )
        self.assertEqual(result["new_status"], "suspended")

    def test_revocation(self):
        result = self.engine.record_disciplinary_action(
            "adv_001", "revocation", "Repeated violations"
        )
        self.assertEqual(result["new_status"], "revoked")


# ---------------------------------------------------------------------------
# Magistrate Engine Tests
# ---------------------------------------------------------------------------

class TestMagistrateAppointment(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_appoint_magistrate(self):
        result = self.engine.appoint_magistrate(
            "mag_001", "judge_001", covenant_exam_passed=True
        )
        self.assertEqual(result["status"], "active")
        self.assertEqual(result["term_days"], MAGISTRATE_TERM_DAYS)

    def test_appoint_without_exam_fails(self):
        with self.assertRaises(ValueError):
            self.engine.appoint_magistrate(
                "mag_001", "judge_001", covenant_exam_passed=False
            )

    def test_remove_magistrate(self):
        self.engine.appoint_magistrate("mag_001", "judge_001")
        result = self.engine.remove_magistrate("mag_001", "conduct_violation")
        self.assertEqual(result["new_status"], "removed")

    def test_renew_magistrate(self):
        self.engine.appoint_magistrate("mag_001", "judge_001")
        result = self.engine.renew_magistrate("mag_001")
        self.assertIn("new_term_end", result)


class TestCaseManagement(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)
        self.engine.appoint_magistrate("mag_001", "judge_001")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_file_case(self):
        result = self.engine.file_case(
            "guild_internal_dispute", "c1", "c2",
            "Revenue split disagreement",
            related_guild_ids=["GUILD-001"],
        )
        self.assertEqual(result["case_id"], "MC-0001")
        self.assertEqual(result["status"], "filed")

    def test_file_excluded_case_type(self):
        with self.assertRaises(ValueError) as ctx:
            self.engine.file_case(
                "constitutional_review", "c1", "c2",
                "Constitutional question",
            )
        self.assertIn("outside Magistrate Court jurisdiction", str(ctx.exception))

    def test_file_unknown_case_type(self):
        with self.assertRaises(ValueError):
            self.engine.file_case("made_up_type", "c1", "c2", "Something")

    def test_assign_case(self):
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Test"
        )
        result = self.engine.assign_case("MC-0001", "mag_001")
        self.assertEqual(result["magistrate"], "mag_001")
        self.assertEqual(result["status"], "assigned")

    def test_file_response(self):
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Test"
        )
        result = self.engine.file_response("MC-0001", "c2", "My response")
        self.assertFalse(result["late"])

    def test_file_motion(self):
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Test"
        )
        result = self.engine.file_motion(
            "MC-0001", "c1", "discovery_request", "Requesting documents"
        )
        self.assertEqual(result["motion_number"], 1)

    def test_issue_ruling(self):
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Test"
        )
        self.engine.assign_case("MC-0001", "mag_001")
        result = self.engine.issue_ruling(
            "MC-0001", "mag_001",
            ruling_text="Defendant must adjust revenue split.",
            orders=["Adjust split to 50/50", "File new agreement within 30 days"],
        )
        self.assertEqual(result["status"], "closed")
        self.assertTrue(result["appealable"])

    def test_ruling_by_wrong_magistrate_fails(self):
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Test"
        )
        self.engine.assign_case("MC-0001", "mag_001")
        self.engine.appoint_magistrate("mag_002", "judge_002")
        with self.assertRaises(ValueError):
            self.engine.issue_ruling(
                "MC-0001", "mag_002",
                ruling_text="Some ruling",
                orders=["Something"],
            )


class TestAppealProcess(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)
        self.engine.appoint_magistrate("mag_001", "judge_001")
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Test dispute"
        )
        self.engine.assign_case("MC-0001", "mag_001")
        self.engine.issue_ruling(
            "MC-0001", "mag_001",
            ruling_text="Ruling in favor of plaintiff.",
            orders=["Pay damages"],
            case_closed=False,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_file_appeal(self):
        result = self.engine.file_appeal(
            "MC-0001", "c2",
            "Magistrate misapplied revenue-sharing precedent"
        )
        self.assertEqual(result["appeal_court"], "lower_court")

        case = self.engine.get_case("MC-0001")
        self.assertEqual(case["status"], "appealed")

    def test_appeal_without_ruling_fails(self):
        self.engine.file_case(
            "brief_access_complaint", "c3", "c4", "No ruling yet"
        )
        with self.assertRaises(ValueError):
            self.engine.file_appeal("MC-0002", "c4", "Some grounds")


class TestEmergencyInjunction(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)
        self.engine.appoint_magistrate("mag_001", "judge_001")
        self.engine.file_case(
            "revenue_split_disagreement", "c1", "c2", "Urgent split dispute"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_emergency_injunction(self):
        result = self.engine.issue_emergency_injunction(
            "MC-0001", "mag_001",
            "Freeze guild treasury pending resolution",
            duration_days=14,
        )
        self.assertEqual(result["duration_days"], 14)
        self.assertIn("expires", result)


class TestDefaultJudgment(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Unresponsive defendant"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_check_defaults_not_yet(self):
        defaults = self.engine.check_default_judgments()
        self.assertEqual(len(defaults), 0)

    def test_check_defaults_overdue(self):
        # Backdate the deadline
        case = self.engine.get_case("MC-0001")
        past = datetime.fromtimestamp(
            _now().timestamp() - 20 * 86400, tz=timezone.utc
        )
        case["response_deadline"] = _format_dt(past)

        defaults = self.engine.check_default_judgments()
        self.assertEqual(len(defaults), 1)
        self.assertTrue(defaults[0]["eligible_for_default"])


class TestDismissCase(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)
        self.engine.file_case(
            "minor_conduct_violation", "c1", "c2", "Minor issue"
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_dismiss(self):
        result = self.engine.dismiss_case("MC-0001", "mag_001", "Insufficient evidence")
        self.assertEqual(result["status"], "dismissed")


class TestCourtStatistics(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)
        self.engine.appoint_magistrate("mag_001", "judge_001")
        for i in range(3):
            self.engine.file_case(
                "guild_internal_dispute", f"p{i}", f"d{i}", f"Case {i}"
            )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_statistics(self):
        stats = self.engine.court_statistics()
        self.assertEqual(stats["total_cases"], 3)
        self.assertEqual(stats["active_magistrates"], 1)


class TestMagistrateSave(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.state_path = _make_state_file(self.tmp_dir)
        self.engine = MagistrateEngine(self.state_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_save_and_reload(self):
        self.engine.appoint_magistrate("mag_001", "judge_001")
        self.engine.file_case(
            "guild_internal_dispute", "c1", "c2", "Test"
        )
        self.engine.save()

        engine2 = MagistrateEngine(self.state_path)
        self.assertEqual(len(engine2.list_magistrates()), 1)
        self.assertEqual(len(engine2.list_cases()), 1)


# ---------------------------------------------------------------------------
# JSON output runner (standalone mode)
# ---------------------------------------------------------------------------

def run_tests_json():
    """Run all tests and output results as JSON."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])

    class JSONResult(unittest.TestResult):
        def __init__(self):
            super().__init__()
            self.results = []

        def addSuccess(self, test):
            super().addSuccess(test)
            self.results.append({"test": str(test), "status": "PASS"})

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.results.append({
                "test": str(test), "status": "FAIL",
                "error": self._exc_info_to_string(err, test),
            })

        def addError(self, test, err):
            super().addError(test, err)
            self.results.append({
                "test": str(test), "status": "ERROR",
                "error": self._exc_info_to_string(err, test),
            })

    result = JSONResult()
    suite.run(result)

    output = {
        "test_suite": "House Bernard Guild System v1.0",
        "tests_run": result.testsRun,
        "passed": len(result.results) - len(result.failures) - len(result.errors),
        "failed": len(result.failures),
        "errors": len(result.errors),
        "results": result.results,
    }

    print(json.dumps(output, indent=2))
    return output


if __name__ == "__main__":
    if "--json" in sys.argv:
        run_tests_json()
    else:
        unittest.main(verbosity=2)
