"""
House Bernard Guild Engine v1.0
Manages guild lifecycle: formation, governance, membership, financial incentives,
constitutional constraints, secession, and lab charters.

Authority: GUILD_SYSTEM.md
The engine computes and records. It does not disburse tokens.

Usage:
    from guild.guild_engine import GuildEngine
    engine = GuildEngine("guild/guild_state.json")
    result = engine.register_guild(charter)
"""

import json
import shutil
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Shared utilities
import sys as _sys
_repo_root = str(Path(__file__).resolve().parents[1])
if _repo_root not in _sys.path:
    _sys.path.insert(0, _repo_root)
from hb_utils import now as _now, parse_dt as _parse_dt, format_dt as _format_dt, months_between as _months_between, days_between as _days_between, atomic_save as _atomic_save
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Utility (matches treasury_engine.py patterns)
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
# Constants from GUILD_SYSTEM.md
# ---------------------------------------------------------------------------

# Section II: Formation
MIN_GUILD_MEMBERS = 3
MIN_CITIZENSHIP_TIER = "journeyman"  # 3,000 $HB held, 100 $HB/month tax

# Section IV: Collaboration Multiplier
COLLABORATION_MULTIPLIER = {
    "two_guilds":           1.25,
    "three_plus_guilds":    1.50,
    "guild_plus_independent": 1.15,
    "single_guild":         1.00,
}

# Section IV: Achievement Bonuses
ACHIEVEMENT_BONUSES = {
    "five_flame_quarter":           10_000,
    "ten_flame_quarter":            25_000,
    "first_invariant":              50_000,
    "subsequent_invariant":         25_000,
    "cross_guild_invariant":        75_000,
}

# Section IV: Endowment Milestones (bonded at founder rate: 30% over 3 years)
ENDOWMENT_MILESTONES = {
    2:  50_000,    # 2 years continuous operation
    5:  150_000,   # 5 years continuous operation
    10: 500_000,   # 10 years continuous operation
}
ENDOWMENT_BOND_RATE = 0.30
ENDOWMENT_BOND_MONTHS = 36

# Section IV: Lab Charter Revenue Sharing
LAB_REVENUE_SPLITS = {
    "lab_access":       {"guild": 0.30, "treasury": 0.20, "burned": 0.50},
    "api_access":       {"guild": 0.30, "treasury": 0.20, "burned": 0.50},
    "research_license": {"guild": 0.40, "treasury": 0.10, "burned": 0.50},
}

# Section V: Constitutional Constraints
MAX_GUILD_COUNCIL_SEATS = 2
MAX_COALITION_COUNCIL_SEATS = 3
MAX_GUILD_TREASURY_PCT = 0.02       # 2% of total supply
MAX_GUILD_EPOCH_EMISSION_PCT = 0.15  # 15% of total epoch emission

# Section VII: Lab Charter Requirements
LAB_MIN_GUILD_AGE_MONTHS = 12
LAB_MIN_GENES = 10
LAB_MIN_GENES_FOUNDING = 5           # Reduced during Founding Period
LAB_MIN_MEMBERS = 7
LAB_MIN_GENES_PER_YEAR = 3

# Section VII: Lab Charter Terms (days)
LAB_INITIAL_TERM_DAYS = 365
LAB_FIRST_RENEWAL_DAYS = 730
LAB_SUBSEQUENT_RENEWAL_DAYS = 1095

# Section XI: Founding Period
GENESIS_GUILD_BONUS = 25_000

# Guild statuses
GUILD_STATUSES = {"active", "probationary", "suspended", "dissolved"}

# Required charter fields (Section II)
REQUIRED_CHARTER_FIELDS = {
    "name", "domain", "membership_rules", "revenue_sharing_model",
    "guildmaster_election_process", "dispute_resolution", "dissolution_terms",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GuildEngine:

    def __init__(self, state_path: str = "guild/guild_state.json") -> None:
        self.state_path = Path(state_path)
        with open(self.state_path, "r", encoding="utf-8") as f:
            self.state = json.load(f)

    # -------------------------------------------------------------------
    # Guild lookup helpers
    # -------------------------------------------------------------------

    def _get_guild(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Find a guild by ID. Returns None if not found."""
        for g in self.state["guilds"]:
            if g["guild_id"] == guild_id:
                return g
        return None

    def _get_active_guild(self, guild_id: str) -> Dict[str, Any]:
        """Find an active guild by ID. Raises ValueError if not found or not active."""
        guild = self._get_guild(guild_id)
        if guild is None:
            raise ValueError(f"Guild {guild_id} not found")
        if guild["status"] not in ("active", "probationary"):
            raise ValueError(f"Guild {guild_id} is {guild['status']}, not active")
        return guild

    def _next_guild_id(self) -> str:
        """Generate the next guild ID (GUILD-001, GUILD-002, etc.)."""
        self.state["guild_counter"] = self.state.get("guild_counter", 0) + 1
        return f"GUILD-{self.state['guild_counter']:03d}"

    # -------------------------------------------------------------------
    # Section II: Formation
    # -------------------------------------------------------------------

    def validate_charter(self, charter: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a guild charter for constitutional compliance.

        Returns a validation result dict with 'valid' bool and any 'errors'.
        Does NOT evaluate research merit (that's the Furnace's job).
        """
        errors = []

        # Check required fields
        missing = REQUIRED_CHARTER_FIELDS - set(charter.keys())
        if missing:
            errors.append(f"Missing required charter fields: {', '.join(sorted(missing))}")

        # Name must be non-empty
        if not charter.get("name", "").strip():
            errors.append("Guild name must be non-empty")

        # Domain must be non-empty
        if not charter.get("domain", "").strip():
            errors.append("Domain declaration must be non-empty")

        # Revenue sharing must be explicit (not "guildmaster decides")
        rev_model = charter.get("revenue_sharing_model", "")
        if isinstance(rev_model, str):
            lower = rev_model.lower()
            if "guildmaster decides" in lower or not rev_model.strip():
                errors.append(
                    "Revenue-sharing model must be explicit. "
                    "'The Guildmaster decides' is not acceptable."
                )

        # Dissolution terms required
        if not charter.get("dissolution_terms", "").strip():
            errors.append("Dissolution terms must be specified")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "charter_fields_present": sorted(charter.keys()),
        }

    def register_guild(
        self,
        charter: Dict[str, Any],
        founding_members: List[str],
        guildmaster_id: str,
        registered_by: str = "council",
    ) -> Dict[str, Any]:
        """Register a new guild. Returns the guild record.

        Args:
            charter: The guild charter (must pass validate_charter).
            founding_members: List of citizen IDs (min 3 at Journeyman+).
            guildmaster_id: Citizen ID of the elected Guildmaster.
            registered_by: 'council' or 'crown' (Founding Period).

        Raises:
            ValueError: If charter is invalid, too few members, or
                        guildmaster is not a founding member.
        """
        # Validate charter
        validation = self.validate_charter(charter)
        if not validation["valid"]:
            raise ValueError(
                f"Charter validation failed: {'; '.join(validation['errors'])}"
            )

        # Validate founding members
        if len(founding_members) < MIN_GUILD_MEMBERS:
            raise ValueError(
                f"Minimum {MIN_GUILD_MEMBERS} founding members required, "
                f"got {len(founding_members)}"
            )

        # Check for duplicates
        if len(set(founding_members)) != len(founding_members):
            raise ValueError("Duplicate founding member IDs")

        # Guildmaster must be a founding member
        if guildmaster_id not in founding_members:
            raise ValueError(
                f"Guildmaster {guildmaster_id} must be a founding member"
            )

        # Check name uniqueness
        name = charter["name"].strip()
        for g in self.state["guilds"]:
            if g["name"].lower() == name.lower() and g["status"] != "dissolved":
                raise ValueError(f"Active guild with name '{name}' already exists")
        # Also check retired names (5-year retirement per Section VI)
        for g in self.state["guilds"]:
            if g["name"].lower() == name.lower() and g["status"] == "dissolved":
                dissolved_date = _parse_dt(g.get("dissolved_date"))
                if dissolved_date:
                    years_since = _months_between(dissolved_date, _now()) / 12
                    if years_since < 5:
                        raise ValueError(
                            f"Guild name '{name}' is retired for "
                            f"{5 - years_since:.1f} more years"
                        )

        # During Founding Period, crown can register directly
        is_founding = self.state.get("founding_period", False)
        if registered_by == "crown" and not is_founding:
            raise ValueError(
                "Crown direct registration only allowed during Founding Period"
            )

        guild_id = self._next_guild_id()
        now = _now()

        guild = {
            "guild_id": guild_id,
            "name": name,
            "domain": charter["domain"].strip(),
            "charter": charter,
            "charter_date": _format_dt(now),
            "guildmaster": guildmaster_id,
            "members": founding_members,
            "provisional_members": [],
            "treasury_balance": 0.0,
            "genes_produced": 0,
            "genes_by_tier": {"spark": 0, "flame": 0, "furnace_forged": 0, "invariant": 0},
            "lab_charter": None,
            "status": "active",
            "registered_by": registered_by,
            "endowment_bonds": [],
            "achievement_history": [],
            "assemblies": [],
            "council_seats_held": 0,
            "quarterly_flame_count": 0,
            "quarterly_start_date": _format_dt(now),
            "dissolved_date": None,
            "dissolution_reason": None,
        }

        self.state["guilds"].append(guild)

        result = {
            "guild_id": guild_id,
            "name": name,
            "domain": charter["domain"],
            "members": len(founding_members),
            "guildmaster": guildmaster_id,
            "registered_by": registered_by,
            "charter_date": _format_dt(now),
            "status": "active",
        }

        # Genesis Guild Bonus (Section XI)
        if is_founding and self.state.get("genesis_guild_bonuses_remaining", 0) > 0:
            guild["treasury_balance"] = GENESIS_GUILD_BONUS
            self.state["genesis_guild_bonuses_remaining"] -= 1
            result["genesis_bonus"] = GENESIS_GUILD_BONUS
            result["genesis_bonuses_remaining"] = self.state["genesis_guild_bonuses_remaining"]

        return result

    # -------------------------------------------------------------------
    # Section III: Governance — Guildmaster
    # -------------------------------------------------------------------

    def elect_guildmaster(
        self, guild_id: str, new_guildmaster_id: str, election_type: str = "scheduled"
    ) -> Dict[str, Any]:
        """Record a Guildmaster election result.

        Args:
            guild_id: The guild's ID.
            new_guildmaster_id: Citizen ID of the new Guildmaster.
            election_type: 'scheduled', 'removal', or 'resignation'.
        """
        guild = self._get_active_guild(guild_id)

        if new_guildmaster_id not in guild["members"]:
            raise ValueError(
                f"New guildmaster {new_guildmaster_id} must be a guild member"
            )

        old_guildmaster = guild["guildmaster"]
        guild["guildmaster"] = new_guildmaster_id

        return {
            "guild_id": guild_id,
            "old_guildmaster": old_guildmaster,
            "new_guildmaster": new_guildmaster_id,
            "election_type": election_type,
            "timestamp": _format_dt(_now()),
        }

    def remove_guildmaster(
        self, guild_id: str, reason: str = "member_vote"
    ) -> Dict[str, Any]:
        """Remove a Guildmaster by simple majority vote.

        The guild must subsequently elect a replacement via elect_guildmaster().
        """
        guild = self._get_active_guild(guild_id)
        removed = guild["guildmaster"]
        guild["guildmaster"] = None

        return {
            "guild_id": guild_id,
            "removed_guildmaster": removed,
            "reason": reason,
            "timestamp": _format_dt(_now()),
            "action_required": "Guild must elect a replacement Guildmaster",
        }

    # -------------------------------------------------------------------
    # Section III: Governance — Assemblies
    # -------------------------------------------------------------------

    def record_assembly(
        self, guild_id: str, summary: str, decisions: List[str],
        attendees: List[str], date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Record a guild assembly in the Ledger (summary only).

        Assemblies must occur at least once per quarter.
        """
        guild = self._get_active_guild(guild_id)
        now = date or _now()

        assembly_record = {
            "date": _format_dt(now),
            "attendees_count": len(attendees),
            "summary": summary,
            "decisions": decisions,
        }

        guild["assemblies"].append(assembly_record)

        return {
            "guild_id": guild_id,
            "assembly_number": len(guild["assemblies"]),
            "date": _format_dt(now),
            "attendees": len(attendees),
            "decisions_count": len(decisions),
        }

    # -------------------------------------------------------------------
    # Section III: Membership
    # -------------------------------------------------------------------

    def add_member(
        self, guild_id: str, citizen_id: str, provisional: bool = False
    ) -> Dict[str, Any]:
        """Add a member to a guild.

        Args:
            guild_id: The guild's ID.
            citizen_id: The citizen to add.
            provisional: True for Welcome Year citizens (don't count toward
                        minimum, can't vote in Guildmaster elections).
        """
        guild = self._get_active_guild(guild_id)

        if citizen_id in guild["members"]:
            raise ValueError(f"Citizen {citizen_id} is already a full member")
        if citizen_id in guild.get("provisional_members", []):
            raise ValueError(f"Citizen {citizen_id} is already a provisional member")

        if provisional:
            guild.setdefault("provisional_members", []).append(citizen_id)
        else:
            guild["members"].append(citizen_id)

        return {
            "guild_id": guild_id,
            "citizen_id": citizen_id,
            "membership_type": "provisional" if provisional else "full",
            "total_members": len(guild["members"]),
            "total_provisional": len(guild.get("provisional_members", [])),
            "timestamp": _format_dt(_now()),
        }

    def remove_member(
        self, guild_id: str, citizen_id: str, reason: str = "voluntary_exit"
    ) -> Dict[str, Any]:
        """Remove a member from a guild.

        Section III: Member exit without penalty. Earned royalties continue.
        Cannot remove the Guildmaster without first electing a replacement
        (unless the guild would drop below minimum members, triggering
        probationary status).
        """
        guild = self._get_active_guild(guild_id)

        was_provisional = False
        if citizen_id in guild.get("provisional_members", []):
            guild["provisional_members"].remove(citizen_id)
            was_provisional = True
        elif citizen_id in guild["members"]:
            # Can't remove Guildmaster this way
            if citizen_id == guild["guildmaster"]:
                raise ValueError(
                    f"Cannot remove Guildmaster {citizen_id} via remove_member. "
                    "Use remove_guildmaster() first, then remove_member()."
                )
            guild["members"].remove(citizen_id)
        else:
            raise ValueError(f"Citizen {citizen_id} is not a member of guild {guild_id}")

        result = {
            "guild_id": guild_id,
            "citizen_id": citizen_id,
            "reason": reason,
            "was_provisional": was_provisional,
            "remaining_members": len(guild["members"]),
            "timestamp": _format_dt(_now()),
        }

        # Check if guild drops below minimum
        if not was_provisional and len(guild["members"]) < MIN_GUILD_MEMBERS:
            guild["status"] = "probationary"
            result["status_change"] = "probationary"
            result["warning"] = (
                f"Guild dropped below {MIN_GUILD_MEMBERS} members. "
                "Status changed to probationary. Must recruit to restore."
            )

        return result

    def promote_provisional_member(
        self, guild_id: str, citizen_id: str
    ) -> Dict[str, Any]:
        """Promote a provisional member to full member (reached Journeyman tier)."""
        guild = self._get_active_guild(guild_id)

        if citizen_id not in guild.get("provisional_members", []):
            raise ValueError(
                f"Citizen {citizen_id} is not a provisional member of guild {guild_id}"
            )

        guild["provisional_members"].remove(citizen_id)
        guild["members"].append(citizen_id)

        return {
            "guild_id": guild_id,
            "citizen_id": citizen_id,
            "promoted_to": "full_member",
            "total_members": len(guild["members"]),
            "timestamp": _format_dt(_now()),
        }

    # -------------------------------------------------------------------
    # Section IV: Financial — Collaboration Multiplier
    # -------------------------------------------------------------------

    def calculate_collaboration_multiplier(
        self,
        submission_guild_ids: List[str],
        has_independent: bool = False,
    ) -> Dict[str, Any]:
        """Calculate the collaboration multiplier for a brief submission.

        Args:
            submission_guild_ids: List of guild IDs whose members contributed.
            has_independent: True if independent (non-guild) contributors
                           are included.

        Returns:
            Dict with multiplier value and type.
        """
        unique_guilds = list(set(submission_guild_ids))
        guild_count = len(unique_guilds)

        if guild_count == 0 and has_independent:
            # Purely independent — no multiplier
            return {"multiplier": 1.00, "type": "independent_only", "guild_count": 0}

        if guild_count >= 3:
            mult = COLLABORATION_MULTIPLIER["three_plus_guilds"]
            mult_type = "three_plus_guilds"
        elif guild_count == 2:
            mult = COLLABORATION_MULTIPLIER["two_guilds"]
            mult_type = "two_guilds"
        elif guild_count == 1 and has_independent:
            mult = COLLABORATION_MULTIPLIER["guild_plus_independent"]
            mult_type = "guild_plus_independent"
        elif guild_count == 1:
            mult = COLLABORATION_MULTIPLIER["single_guild"]
            mult_type = "single_guild"
        else:
            mult = 1.00
            mult_type = "none"

        return {
            "multiplier": mult,
            "type": mult_type,
            "guild_count": guild_count,
            "has_independent": has_independent,
        }

    def apply_collaboration_multiplier(
        self, base_payment: float, submission_guild_ids: List[str],
        has_independent: bool = False,
    ) -> Dict[str, Any]:
        """Apply the collaboration multiplier to a base payment.

        The multiplier applies only to the base payment, not to royalties.
        Multiplier tokens come from Treasury emission.
        """
        mult_info = self.calculate_collaboration_multiplier(
            submission_guild_ids, has_independent
        )
        adjusted = round(base_payment * mult_info["multiplier"], 2)
        bonus = round(adjusted - base_payment, 2)

        return {
            "base_payment": base_payment,
            "adjusted_payment": adjusted,
            "bonus": bonus,
            **mult_info,
        }

    # -------------------------------------------------------------------
    # Section IV: Financial — Achievement Bonuses
    # -------------------------------------------------------------------

    def record_gene_production(
        self, guild_id: str, gene_id: str, tier: int, tier_name: str,
        is_cross_guild: bool = False, collaborating_guild_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Record a gene produced by guild members.

        Checks for achievement bonus eligibility.
        """
        guild = self._get_active_guild(guild_id)
        guild["genes_produced"] += 1

        # Track by tier
        tier_key = tier_name.lower().replace("-", "_").replace(" ", "_")
        if tier_key in guild["genes_by_tier"]:
            guild["genes_by_tier"][tier_key] += 1

        result = {
            "guild_id": guild_id,
            "gene_id": gene_id,
            "tier": tier,
            "tier_name": tier_name,
            "total_genes": guild["genes_produced"],
            "bonuses_triggered": [],
        }

        # Track quarterly Flame+ count
        if tier >= 2:  # Flame or above
            guild["quarterly_flame_count"] = guild.get("quarterly_flame_count", 0) + 1
            qcount = guild["quarterly_flame_count"]

            # Check achievement thresholds
            if qcount == 5:
                bonus = self._award_achievement(
                    guild, "five_flame_quarter",
                    ACHIEVEMENT_BONUSES["five_flame_quarter"],
                )
                result["bonuses_triggered"].append(bonus)
            elif qcount == 10:
                bonus = self._award_achievement(
                    guild, "ten_flame_quarter",
                    ACHIEVEMENT_BONUSES["ten_flame_quarter"],
                )
                result["bonuses_triggered"].append(bonus)

        # Invariant bonuses
        if tier == 4:  # Invariant
            invariant_count = guild["genes_by_tier"].get("invariant", 0)
            if invariant_count == 1:
                bonus = self._award_achievement(
                    guild, "first_invariant",
                    ACHIEVEMENT_BONUSES["first_invariant"],
                )
                result["bonuses_triggered"].append(bonus)
            else:
                bonus = self._award_achievement(
                    guild, "subsequent_invariant",
                    ACHIEVEMENT_BONUSES["subsequent_invariant"],
                )
                result["bonuses_triggered"].append(bonus)

            # Cross-guild invariant
            if is_cross_guild and collaborating_guild_ids:
                bonus_amount = ACHIEVEMENT_BONUSES["cross_guild_invariant"]
                all_guilds = list(set([guild_id] + collaborating_guild_ids))
                per_guild = round(bonus_amount / len(all_guilds), 2)
                for gid in all_guilds:
                    g = self._get_guild(gid)
                    if g and g["status"] in ("active", "probationary"):
                        g["treasury_balance"] = round(
                            g["treasury_balance"] + per_guild, 2
                        )
                bonus = {
                    "type": "cross_guild_invariant",
                    "total_amount": bonus_amount,
                    "per_guild": per_guild,
                    "guilds": all_guilds,
                    "timestamp": _format_dt(_now()),
                }
                result["bonuses_triggered"].append(bonus)

        return result

    def _award_achievement(
        self, guild: Dict[str, Any], achievement_type: str, amount: float
    ) -> Dict[str, Any]:
        """Award an achievement bonus to a guild's treasury."""
        guild["treasury_balance"] = round(guild["treasury_balance"] + amount, 2)
        record = {
            "type": achievement_type,
            "amount": amount,
            "timestamp": _format_dt(_now()),
        }
        guild["achievement_history"].append(record)
        return record

    def reset_quarterly_counts(self, guild_id: str) -> Dict[str, Any]:
        """Reset quarterly achievement counters (called at quarter boundaries)."""
        guild = self._get_active_guild(guild_id)
        old_count = guild.get("quarterly_flame_count", 0)
        guild["quarterly_flame_count"] = 0
        guild["quarterly_start_date"] = _format_dt(_now())
        return {
            "guild_id": guild_id,
            "previous_quarterly_flame_count": old_count,
            "reset_date": guild["quarterly_start_date"],
        }

    # -------------------------------------------------------------------
    # Section IV: Financial — Endowments
    # -------------------------------------------------------------------

    def check_endowment_eligibility(
        self, guild_id: str, as_of: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Check if a guild is eligible for an endowment milestone."""
        as_of = as_of or _now()
        guild = self._get_active_guild(guild_id)
        charter_date = _parse_dt(guild["charter_date"])
        years_active = _months_between(charter_date, as_of) / 12

        existing_milestones = {
            b.get("milestone_years") for b in guild.get("endowment_bonds", [])
        }

        eligible = []
        for years_required, amount in sorted(ENDOWMENT_MILESTONES.items()):
            if years_active >= years_required and years_required not in existing_milestones:
                eligible.append({
                    "milestone_years": years_required,
                    "endowment_amount": amount,
                    "bond_rate": ENDOWMENT_BOND_RATE,
                    "bond_months": ENDOWMENT_BOND_MONTHS,
                })

        return {
            "guild_id": guild_id,
            "years_active": round(years_active, 2),
            "eligible_milestones": eligible,
            "existing_milestones": sorted(existing_milestones - {None}),
        }

    def activate_endowment_bond(
        self, guild_id: str, milestone_years: int, approved_by: str = "council"
    ) -> Dict[str, Any]:
        """Activate an endowment bond for a guild milestone.

        Requires Council approval (simple majority). Funded from Unmined Treasury.
        Bond is held in guild's treasury account under standard bond rules.
        """
        guild = self._get_active_guild(guild_id)

        if milestone_years not in ENDOWMENT_MILESTONES:
            raise ValueError(f"Invalid milestone: {milestone_years} years")

        # Check not already granted
        for b in guild.get("endowment_bonds", []):
            if b.get("milestone_years") == milestone_years:
                raise ValueError(
                    f"Endowment for {milestone_years}-year milestone already granted"
                )

        # Check financial cap
        total_supply = self.state.get("total_supply", 100_000_000)
        cap = total_supply * MAX_GUILD_TREASURY_PCT
        amount = ENDOWMENT_MILESTONES[milestone_years]
        projected = guild["treasury_balance"] + amount
        if projected > cap:
            raise ValueError(
                f"Endowment of {amount:,.0f} would push guild treasury to "
                f"{projected:,.0f}, exceeding {MAX_GUILD_TREASURY_PCT*100}% cap "
                f"of {cap:,.0f}. Excess must be distributed first."
            )

        now = _now()
        maturity = datetime.fromtimestamp(
            now.timestamp() + ENDOWMENT_BOND_MONTHS * 30.44 * 86400,
            tz=timezone.utc
        )

        bond = {
            "bond_id": f"{guild_id}-ENDOW-{milestone_years}Y",
            "milestone_years": milestone_years,
            "principal": amount,
            "yield_rate": ENDOWMENT_BOND_RATE,
            "start_date": _format_dt(now),
            "maturity_date": _format_dt(maturity),
            "status": "active",
            "approved_by": approved_by,
        }

        guild["endowment_bonds"].append(bond)
        guild["treasury_balance"] = round(guild["treasury_balance"] + amount, 2)

        return {
            "guild_id": guild_id,
            "bond_id": bond["bond_id"],
            "principal": amount,
            "yield_rate": ENDOWMENT_BOND_RATE,
            "maturity_date": _format_dt(maturity),
            "approved_by": approved_by,
            "timestamp": _format_dt(now),
        }

    # -------------------------------------------------------------------
    # Section IV: Financial — Lab Revenue Sharing
    # -------------------------------------------------------------------

    def calculate_lab_revenue_split(
        self, guild_id: str, revenue_source: str, gross_amount: float
    ) -> Dict[str, Any]:
        """Calculate revenue split for a guild-operated lab.

        Args:
            guild_id: The guild operating the lab.
            revenue_source: 'lab_access', 'api_access', or 'research_license'.
            gross_amount: Total revenue generated.
        """
        guild = self._get_active_guild(guild_id)

        if guild.get("lab_charter") is None:
            raise ValueError(f"Guild {guild_id} does not operate a lab")

        if revenue_source not in LAB_REVENUE_SPLITS:
            raise ValueError(
                f"Unknown revenue source: {revenue_source}. "
                f"Valid: {', '.join(LAB_REVENUE_SPLITS.keys())}"
            )

        splits = LAB_REVENUE_SPLITS[revenue_source]
        guild_share = round(gross_amount * splits["guild"], 2)
        treasury_share = round(gross_amount * splits["treasury"], 2)
        burned = round(gross_amount * splits["burned"], 2)

        return {
            "guild_id": guild_id,
            "revenue_source": revenue_source,
            "gross_amount": gross_amount,
            "guild_share": guild_share,
            "treasury_share": treasury_share,
            "burned": burned,
            "split_percentages": splits,
        }

    # -------------------------------------------------------------------
    # Section V: Constitutional Constraints
    # -------------------------------------------------------------------

    def check_council_seat_limit(
        self, guild_id: str, proposed_seats: int
    ) -> Dict[str, Any]:
        """Check if a guild would exceed the council seat limit.

        No single guild may hold more than 2 of 7 seats.
        """
        limit = self.state["council_seats"]["guild_seat_limit"]
        allowed = proposed_seats <= limit

        return {
            "guild_id": guild_id,
            "proposed_seats": proposed_seats,
            "limit": limit,
            "allowed": allowed,
            "reason": None if allowed else (
                f"Guild would hold {proposed_seats} seats, exceeding limit of {limit}. "
                "Third-place guild candidate must be disqualified."
            ),
        }

    def check_coalition_limit(
        self, coalition_guild_ids: List[str]
    ) -> Dict[str, Any]:
        """Check if a formal coalition exceeds the seat limit.

        No coalition may collectively control more than 3 seats.
        """
        limit = self.state["council_seats"]["coalition_seat_limit"]
        total_seats = 0
        guild_seats = {}

        for gid in coalition_guild_ids:
            guild = self._get_guild(gid)
            if guild:
                seats = guild.get("council_seats_held", 0)
                guild_seats[gid] = seats
                total_seats += seats

        allowed = total_seats <= limit

        return {
            "coalition_guilds": coalition_guild_ids,
            "guild_seats": guild_seats,
            "total_seats": total_seats,
            "limit": limit,
            "allowed": allowed,
            "reason": None if allowed else (
                f"Coalition controls {total_seats} seats, exceeding limit of {limit}. "
                "Judiciary must order coalition dissolved."
            ),
        }

    def check_financial_caps(
        self, guild_id: str, epoch_emission: float = 0
    ) -> Dict[str, Any]:
        """Check if a guild exceeds financial caps (Section V).

        - No guild treasury may hold > 2% of total supply.
        - No guild may receive > 15% of epoch emission per year.
        """
        guild = self._get_active_guild(guild_id)
        total_supply = self.state.get("total_supply", 100_000_000)

        treasury_cap = total_supply * MAX_GUILD_TREASURY_PCT
        treasury_ok = guild["treasury_balance"] <= treasury_cap

        emission_cap = epoch_emission * MAX_GUILD_EPOCH_EMISSION_PCT if epoch_emission > 0 else None

        warnings = []
        if not treasury_ok:
            excess = guild["treasury_balance"] - treasury_cap
            warnings.append(
                f"Treasury balance {guild['treasury_balance']:,.0f} exceeds "
                f"{MAX_GUILD_TREASURY_PCT*100}% cap of {treasury_cap:,.0f}. "
                f"Excess {excess:,.0f} must be distributed or bonded."
            )

        return {
            "guild_id": guild_id,
            "treasury_balance": guild["treasury_balance"],
            "treasury_cap": treasury_cap,
            "treasury_within_cap": treasury_ok,
            "emission_cap": emission_cap,
            "warnings": warnings,
        }

    def update_council_seats(
        self, guild_id: str, seats_held: int
    ) -> Dict[str, Any]:
        """Update the number of council seats held by a guild."""
        guild = self._get_active_guild(guild_id)

        # Validate against limit
        check = self.check_council_seat_limit(guild_id, seats_held)
        if not check["allowed"]:
            raise ValueError(check["reason"])

        old_seats = guild.get("council_seats_held", 0)
        guild["council_seats_held"] = seats_held

        return {
            "guild_id": guild_id,
            "old_seats": old_seats,
            "new_seats": seats_held,
            "timestamp": _format_dt(_now()),
        }

    # -------------------------------------------------------------------
    # Section VI: Secession and Exit
    # -------------------------------------------------------------------

    def dissolve_guild(
        self, guild_id: str, reason: str = "voluntary",
        initiated_by: str = "guildmaster",
    ) -> Dict[str, Any]:
        """Dissolve a guild. Exit rights are absolute.

        What the departing guild LEAVES BEHIND:
        - Guild treasury balance (forfeit to House Treasury)
        - All endowment bonds (forfeit — principal and yield)
        - Lab charter (reverts to Council)
        - Guild name (retired for 5 years)
        - Ledger records (immutable)

        What members KEEP:
        - Personal $HB holdings
        - Individual royalty streams
        - Collaborative royalty splits per original agreements
        """
        guild = self._get_active_guild(guild_id)
        now = _now()

        # Calculate forfeitures
        treasury_forfeit = guild["treasury_balance"]
        endowment_forfeit = []
        for bond in guild.get("endowment_bonds", []):
            if bond["status"] == "active":
                bond["status"] = "forfeit"
                bond["forfeit_date"] = _format_dt(now)
                endowment_forfeit.append({
                    "bond_id": bond["bond_id"],
                    "principal": bond["principal"],
                })

        lab_charter_reverted = guild.get("lab_charter") is not None

        # Update guild status
        guild["status"] = "dissolved"
        guild["dissolved_date"] = _format_dt(now)
        guild["dissolution_reason"] = reason
        guild["treasury_balance"] = 0.0

        if guild.get("lab_charter"):
            guild["lab_charter"]["status"] = "reverted"
            guild["lab_charter"]["reverted_date"] = _format_dt(now)

        return {
            "guild_id": guild_id,
            "name": guild["name"],
            "status": "dissolved",
            "reason": reason,
            "initiated_by": initiated_by,
            "dissolved_date": _format_dt(now),
            "forfeitures": {
                "treasury_balance": treasury_forfeit,
                "endowment_bonds": endowment_forfeit,
                "lab_charter_reverted": lab_charter_reverted,
            },
            "members_released": len(guild["members"]),
            "name_retired_until": _format_dt(
                datetime.fromtimestamp(
                    now.timestamp() + 5 * 365.25 * 86400, tz=timezone.utc
                )
            ),
            "note": (
                "Individual member royalty streams continue per original terms. "
                "Collaborative royalty splits continue per pre-filed agreements."
            ),
        }

    # -------------------------------------------------------------------
    # Section VII: Guild-Operated Labs
    # -------------------------------------------------------------------

    def check_lab_charter_eligibility(
        self, guild_id: str, as_of: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Check if a guild meets the requirements for a lab charter."""
        as_of = as_of or _now()
        guild = self._get_active_guild(guild_id)
        is_founding = self.state.get("founding_period", False)

        charter_date = _parse_dt(guild["charter_date"])
        age_months = _months_between(charter_date, as_of)

        required_genes = LAB_MIN_GENES_FOUNDING if is_founding else LAB_MIN_GENES
        flame_plus = sum(
            guild["genes_by_tier"].get(k, 0)
            for k in ("flame", "furnace_forged", "invariant")
        )

        checks = {
            "guild_age_months": {
                "current": round(age_months, 1),
                "required": LAB_MIN_GUILD_AGE_MONTHS,
                "met": age_months >= LAB_MIN_GUILD_AGE_MONTHS,
            },
            "flame_plus_genes": {
                "current": flame_plus,
                "required": required_genes,
                "met": flame_plus >= required_genes,
                "founding_period_reduction": is_founding,
            },
            "member_count": {
                "current": len(guild["members"]),
                "required": LAB_MIN_MEMBERS,
                "met": len(guild["members"]) >= LAB_MIN_MEMBERS,
            },
            "existing_lab": {
                "has_lab": guild.get("lab_charter") is not None,
                "met": guild.get("lab_charter") is None,
            },
        }

        all_met = all(c["met"] for c in checks.values())

        return {
            "guild_id": guild_id,
            "eligible": all_met,
            "checks": checks,
            "note": "Requires Council supermajority (5 of 7) to grant" if all_met else None,
        }

    def grant_lab_charter(
        self, guild_id: str, lab_designation: str,
        research_proposal: str, approved_by: str = "council_supermajority",
        as_of: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Grant a lab charter to a guild.

        Requires Council supermajority (5 of 7).
        """
        as_of = as_of or _now()
        guild = self._get_active_guild(guild_id)

        if guild.get("lab_charter") is not None:
            raise ValueError(f"Guild {guild_id} already has a lab charter")

        eligibility = self.check_lab_charter_eligibility(guild_id, as_of)
        if not eligibility["eligible"]:
            failed = [
                k for k, v in eligibility["checks"].items() if not v["met"]
            ]
            raise ValueError(
                f"Guild {guild_id} does not meet lab charter requirements: "
                f"{', '.join(failed)}"
            )

        term_end = datetime.fromtimestamp(
            as_of.timestamp() + LAB_INITIAL_TERM_DAYS * 86400, tz=timezone.utc
        )

        charter = {
            "lab_designation": lab_designation,
            "research_proposal": research_proposal,
            "granted_date": _format_dt(as_of),
            "term_end": _format_dt(term_end),
            "term_number": 1,
            "status": "active",
            "approved_by": approved_by,
            "genes_this_term": 0,
            "quarterly_reports": [],
        }

        guild["lab_charter"] = charter

        return {
            "guild_id": guild_id,
            "lab_designation": lab_designation,
            "granted_date": _format_dt(as_of),
            "term_end": _format_dt(term_end),
            "term_days": LAB_INITIAL_TERM_DAYS,
            "approved_by": approved_by,
        }

    def renew_lab_charter(
        self, guild_id: str, approved_by: str = "council",
        as_of: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Renew a guild's lab charter."""
        as_of = as_of or _now()
        guild = self._get_active_guild(guild_id)

        lab = guild.get("lab_charter")
        if lab is None:
            raise ValueError(f"Guild {guild_id} has no lab charter to renew")

        # Check minimum gene production
        if lab["genes_this_term"] < LAB_MIN_GENES_PER_YEAR:
            raise ValueError(
                f"Lab produced {lab['genes_this_term']} genes this term, "
                f"minimum {LAB_MIN_GENES_PER_YEAR} required for renewal"
            )

        term_number = lab["term_number"] + 1
        if term_number == 2:
            term_days = LAB_FIRST_RENEWAL_DAYS
        else:
            term_days = LAB_SUBSEQUENT_RENEWAL_DAYS

        term_end = datetime.fromtimestamp(
            as_of.timestamp() + term_days * 86400, tz=timezone.utc
        )

        lab["term_number"] = term_number
        lab["term_end"] = _format_dt(term_end)
        lab["genes_this_term"] = 0
        lab["quarterly_reports"] = []

        return {
            "guild_id": guild_id,
            "term_number": term_number,
            "term_days": term_days,
            "term_end": _format_dt(term_end),
            "approved_by": approved_by,
        }

    def revoke_lab_charter(
        self, guild_id: str, reason: str,
        revoked_by: str = "council_supermajority",
    ) -> Dict[str, Any]:
        """Revoke a guild's lab charter.

        Can be revoked by:
        - Council supermajority vote
        - Judiciary order
        - Automatic: zero surviving genes in 12-month period
        """
        guild = self._get_active_guild(guild_id)

        lab = guild.get("lab_charter")
        if lab is None:
            raise ValueError(f"Guild {guild_id} has no lab charter to revoke")

        now = _now()
        lab["status"] = "revoked"
        lab["revoked_date"] = _format_dt(now)
        lab["revocation_reason"] = reason
        lab["revoked_by"] = revoked_by

        return {
            "guild_id": guild_id,
            "lab_designation": lab["lab_designation"],
            "revocation_reason": reason,
            "revoked_by": revoked_by,
            "revoked_date": _format_dt(now),
            "note": "Lab designation returns to general pool. Active royalties continue.",
        }

    def record_lab_gene(self, guild_id: str, gene_id: str) -> Dict[str, Any]:
        """Record a gene produced by a guild's lab."""
        guild = self._get_active_guild(guild_id)
        lab = guild.get("lab_charter")
        if lab is None or lab.get("status") != "active":
            raise ValueError(f"Guild {guild_id} does not have an active lab charter")

        lab["genes_this_term"] = lab.get("genes_this_term", 0) + 1

        return {
            "guild_id": guild_id,
            "gene_id": gene_id,
            "genes_this_term": lab["genes_this_term"],
            "min_required": LAB_MIN_GENES_PER_YEAR,
        }

    def submit_lab_quarterly_report(
        self, guild_id: str, report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Submit a quarterly progress report for a guild lab."""
        guild = self._get_active_guild(guild_id)
        lab = guild.get("lab_charter")
        if lab is None:
            raise ValueError(f"Guild {guild_id} has no lab charter")

        report_entry = {
            "quarter": len(lab.get("quarterly_reports", [])) + 1,
            "submitted_date": _format_dt(_now()),
            "summary": report.get("summary", ""),
            "genes_produced": report.get("genes_produced", 0),
            "financial_summary": report.get("financial_summary", {}),
        }

        lab.setdefault("quarterly_reports", []).append(report_entry)

        return {
            "guild_id": guild_id,
            "report_number": report_entry["quarter"],
            "submitted_date": report_entry["submitted_date"],
        }

    # -------------------------------------------------------------------
    # Registry queries
    # -------------------------------------------------------------------

    def get_guild(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Get the full guild record from the registry."""
        return self._get_guild(guild_id)

    def list_guilds(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List guilds, optionally filtered by status.

        Returns summary records (not full charters).
        """
        guilds = self.state["guilds"]
        if status:
            guilds = [g for g in guilds if g["status"] == status]

        return [
            {
                "guild_id": g["guild_id"],
                "name": g["name"],
                "domain": g["domain"],
                "status": g["status"],
                "members": len(g["members"]),
                "guildmaster": g["guildmaster"],
                "treasury_balance": g["treasury_balance"],
                "genes_produced": g["genes_produced"],
                "has_lab": g.get("lab_charter") is not None,
                "charter_date": g["charter_date"],
            }
            for g in guilds
        ]

    def guild_financial_summary(self, guild_id: str) -> Dict[str, Any]:
        """Get a financial summary for a guild (public Ledger data)."""
        guild = self._get_active_guild(guild_id)

        total_supply = self.state.get("total_supply", 100_000_000)
        treasury_cap = total_supply * MAX_GUILD_TREASURY_PCT
        pct_of_supply = (
            guild["treasury_balance"] / total_supply * 100
            if total_supply > 0 else 0
        )

        return {
            "guild_id": guild_id,
            "name": guild["name"],
            "treasury_balance": guild["treasury_balance"],
            "treasury_cap": treasury_cap,
            "pct_of_total_supply": round(pct_of_supply, 4),
            "endowment_bonds": [
                {
                    "bond_id": b["bond_id"],
                    "principal": b["principal"],
                    "status": b["status"],
                    "maturity_date": b.get("maturity_date"),
                }
                for b in guild.get("endowment_bonds", [])
            ],
            "achievement_history": guild.get("achievement_history", []),
            "genes_produced": guild["genes_produced"],
            "genes_by_tier": guild["genes_by_tier"],
        }

    # -------------------------------------------------------------------
    # The Guild Oath (Section XII)
    # -------------------------------------------------------------------

    def generate_guild_oath(self, guild_id: str) -> str:
        """Generate the Guild Oath text for the Guildmaster to read."""
        guild = self._get_guild(guild_id)
        if guild is None:
            raise ValueError(f"Guild {guild_id} not found")

        return (
            f'We, the members of {guild["name"]}, declare ourselves a guild '
            f'of House Bernard. We organize freely around {guild["domain"]} '
            f'and commit to the following:\n\n'
            f'We serve the House. The House does not serve us.\n\n'
            f'We share knowledge. The gene registry is our common wealth.\n\n'
            f'We welcome all. No brief under our domain is closed to '
            f'non-members.\n\n'
            f'We account for ourselves. Our finances are public, our '
            f'splits are pre-declared, and our decisions are recorded.\n\n'
            f'We may leave. And if we leave, we leave with grace, taking '
            f'what is ours and leaving what is the House\'s.\n\n'
            f'Ad Astra Per Aspera.'
        )

    # -------------------------------------------------------------------
    # Save (atomic write with backup)
    # -------------------------------------------------------------------

    def save(self, path: Optional[str] = None) -> None:
        """Atomic write guild state with backup."""
        target = Path(path) if path else self.state_path
        self.state["_last_updated"] = _format_dt(_now())
        if target.exists():
            shutil.copy2(target, target.with_suffix(".json.bak"))
        fd, tmp_path = tempfile.mkstemp(
            dir=target.parent, suffix=".tmp", prefix="guild_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, sort_keys=False)
            os.replace(tmp_path, target)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
