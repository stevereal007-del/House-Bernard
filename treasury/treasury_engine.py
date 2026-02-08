"""
House Bernard Treasury Engine v1.1
Computes financial obligations, tracks decay, enforces emission caps.
The Governor reviews output. The engine does not disburse — it computes.

Red Team Audit: 2026-02-08 — 18 findings resolved.

Usage:
    from treasury_engine import TreasuryEngine
    engine = TreasuryEngine("treasury_state.json")
    report = engine.monthly_report()
"""

import json
import shutil
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants from ROYALTIES.md and TREASURY.md
# ---------------------------------------------------------------------------

TIER_CONFIG = {
    1: {"name": "Spark",          "royalty": False, "window_months": 0,  "rate_start": 0.0,  "rate_end": 0.0},
    2: {"name": "Flame",          "royalty": True,  "window_months": 6,  "rate_start": 0.02, "rate_end": 0.0},
    3: {"name": "Furnace-Forged", "royalty": True,  "window_months": 18, "rate_start": 0.05, "rate_end": 0.01},
    4: {"name": "Invariant",      "royalty": True,  "window_months": 24, "rate_start": 0.08, "rate_end": 0.02},
}

VALID_TIERS = set(TIER_CONFIG.keys())

BOND_CONFIG = {
    "contributor": {"lock_months": 3,  "yield_rate": 0.05, "label": "Contributor Bond"},
    "builder":     {"lock_months": 12, "yield_rate": 0.15, "label": "Builder Bond"},
    "founder":     {"lock_months": 36, "yield_rate": 0.30, "label": "Founder Bond"},
}

BURN_RATE_BASE_PAYMENT = 0.05
BURN_RATE_LAB_ACCESS   = 0.50
BURN_RATE_API_ACCESS   = 0.50
EARLY_EXIT_FORFEIT     = 0.50


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _now():
    return datetime.now(timezone.utc)

def _parse_dt(s):
    if s is None:
        return None
    if isinstance(s, datetime):
        return s
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

def _months_between(start, end):
    delta = end - start
    return max(0, delta.days / 30.44)

def _format_dt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class TreasuryEngine:

    def __init__(self, state_path="treasury_state.json"):
        self.state_path = Path(state_path)
        with open(self.state_path, "r") as f:
            self.state = json.load(f)

    # -------------------------------------------------------------------
    # Royalty computations
    # -------------------------------------------------------------------

    def current_royalty_rate(self, royalty, as_of=None):
        as_of = as_of or _now()
        tier = royalty["tier"]
        cfg = TIER_CONFIG.get(tier)
        if not cfg or not cfg["royalty"]:
            return 0.0
        if royalty["status"] != "active":
            return 0.0

        activation = _parse_dt(royalty["activation_date"])
        months_elapsed = _months_between(activation, as_of)
        window = cfg["window_months"]

        # Tolerance for floating-point edge at expiry boundary
        if months_elapsed >= window - 0.01:
            return 0.0

        progress = months_elapsed / window
        rate = cfg["rate_start"] + (cfg["rate_end"] - cfg["rate_start"]) * progress
        return round(rate, 6)

    def royalty_obligations(self, as_of=None):
        as_of = as_of or _now()
        obligations = []
        for r in self.state["royalties"]:
            rate = self.current_royalty_rate(r, as_of)
            if rate <= 0:
                continue
            attributed_revenue = r.get("attributed_revenue_this_period", 0)
            owed = round(attributed_revenue * rate, 2)
            activation = _parse_dt(r["activation_date"])
            window = TIER_CONFIG[r["tier"]]["window_months"]
            months_remaining = max(0, window - _months_between(activation, as_of))
            obligations.append({
                "gene_id": r["gene_id"],
                "contributor_id": r["contributor_id"],
                "tier": r["tier"],
                "tier_name": TIER_CONFIG[r["tier"]]["name"],
                "current_rate": rate,
                "attributed_revenue": attributed_revenue,
                "amount_owed": owed,
                "months_remaining": round(months_remaining, 1),
                "status": "DUE",
            })
        return obligations

    def expiring_royalties(self, lookahead_days=60, as_of=None):
        as_of = as_of or _now()
        expiring = []
        for r in self.state["royalties"]:
            if r["status"] != "active":
                continue
            cfg = TIER_CONFIG.get(r["tier"])
            if not cfg or not cfg["royalty"]:
                continue
            activation = _parse_dt(r["activation_date"])
            window_days = cfg["window_months"] * 30.44
            expiry = activation.timestamp() + (window_days * 86400)
            days_until = (expiry - as_of.timestamp()) / 86400
            if 0 < days_until <= lookahead_days:
                expiring.append({
                    "gene_id": r["gene_id"],
                    "contributor_id": r["contributor_id"],
                    "tier_name": cfg["name"],
                    "days_until_expiry": round(days_until, 0),
                })
        return expiring

    # -------------------------------------------------------------------
    # Bond computations
    # -------------------------------------------------------------------

    def bond_obligations(self, as_of=None):
        as_of = as_of or _now()
        obligations = []
        for b in self.state["bonds"]:
            if b["status"] != "active":
                continue
            cfg = BOND_CONFIG.get(b["bond_type"])
            if not cfg:
                continue
            start = _parse_dt(b["start_date"])
            maturity = _parse_dt(b["maturity_date"])
            principal = b["principal"]
            total_yield = round(principal * cfg["yield_rate"], 2)
            months_elapsed = _months_between(start, as_of)
            months_total = cfg["lock_months"]
            if as_of >= maturity:
                yield_due = total_yield - b.get("yield_paid", 0)
                status = "MATURED"
            else:
                accrued = total_yield * (months_elapsed / months_total)
                yield_due = round(accrued - b.get("yield_paid", 0), 2)
                status = "ACCRUING"
            days_to_maturity = max(0, (maturity - as_of).days)
            obligations.append({
                "bond_id": b["bond_id"],
                "holder_id": b["holder_id"],
                "bond_type": cfg["label"],
                "principal": principal,
                "total_yield": total_yield,
                "yield_paid": b.get("yield_paid", 0),
                "yield_due_now": max(0, yield_due),
                "days_to_maturity": days_to_maturity,
                "status": status,
            })
        return obligations

    def maturing_bonds(self, lookahead_days=90, as_of=None):
        as_of = as_of or _now()
        maturing = []
        for b in self.state["bonds"]:
            if b["status"] != "active":
                continue
            maturity = _parse_dt(b["maturity_date"])
            days_until = (maturity - as_of).days
            if 0 < days_until <= lookahead_days:
                cfg = BOND_CONFIG.get(b["bond_type"], {})
                maturing.append({
                    "bond_id": b["bond_id"],
                    "holder_id": b["holder_id"],
                    "bond_type": cfg.get("label", b["bond_type"]),
                    "principal": b["principal"],
                    "days_to_maturity": days_until,
                })
        return maturing

    # -------------------------------------------------------------------
    # Emission tracking
    # -------------------------------------------------------------------

    def emission_status(self):
        em = self.state["emission"]
        epoch = em["current_epoch"]
        epochs = em["epochs"]
        epoch_idx = min(epoch - 1, len(epochs) - 1)
        cfg = epochs[epoch_idx]
        headroom = cfg["max_emission"] - em["epoch_emitted"]
        utilization = (em["epoch_emitted"] / cfg["max_emission"] * 100) if cfg["max_emission"] > 0 else 0
        return {
            "epoch": epoch,
            "epoch_label": cfg["label"],
            "epoch_cap": cfg["max_emission"],
            "epoch_emitted": em["epoch_emitted"],
            "epoch_headroom": headroom,
            "epoch_utilization_pct": round(utilization, 1),
            "per_contribution_cap": cfg["per_contribution_cap"],
            "total_emitted": em["total_emitted"],
            "total_burned": em["total_burned"],
            "total_circulating": em["total_circulating"],
            "warnings": self._emission_warnings(em, cfg),
        }

    def _emission_warnings(self, em, cfg):
        warnings = []
        utilization = em["epoch_emitted"] / cfg["max_emission"] if cfg["max_emission"] > 0 else 0
        if utilization >= 0.90:
            warnings.append("CRITICAL: Epoch emission at 90%+ of cap")
        elif utilization >= 0.75:
            warnings.append("WARNING: Epoch emission at 75%+ of cap")
        return warnings

    # -------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------

    def _validate_payment(self, gross_amount, tier):
        if gross_amount <= 0:
            raise ValueError(f"Payment must be positive, got {gross_amount}")
        if tier not in VALID_TIERS:
            raise ValueError(f"Invalid tier {tier}, must be one of {sorted(VALID_TIERS)}")
        em = self.state["emission"]
        epochs = em["epochs"]
        epoch_idx = min(em["current_epoch"] - 1, len(epochs) - 1)
        cap = epochs[epoch_idx]["per_contribution_cap"]
        if gross_amount > cap:
            raise ValueError(f"Payment {gross_amount} exceeds per-contribution cap {cap} for epoch {em['current_epoch']}")
        remaining = epochs[epoch_idx]["max_emission"] - em["epoch_emitted"]
        if gross_amount > remaining:
            raise ValueError(f"Payment {gross_amount} exceeds epoch headroom {remaining}")

    def _validate_bond(self, bond_id, principal):
        if principal <= 0:
            raise ValueError(f"Bond principal must be positive, got {principal}")
        existing = [b for b in self.state["bonds"] if b["bond_id"] == bond_id]
        if existing:
            raise ValueError(f"Bond ID {bond_id} already exists")
        circ = self.state["emission"]["total_circulating"]
        if principal > circ:
            raise ValueError(f"Bond principal {principal} exceeds circulating supply {circ}")

    def _validate_royalty(self, gene_id, tier):
        cfg = TIER_CONFIG.get(tier)
        if not cfg or not cfg["royalty"]:
            raise ValueError(f"Tier {tier} does not earn royalties")
        existing = [r for r in self.state["royalties"] if r["gene_id"] == gene_id and r["status"] == "active"]
        if existing:
            raise ValueError(f"Active royalty for gene {gene_id} already exists. Use supersede_royalty() to replace.")

    # -------------------------------------------------------------------
    # Record operations
    # -------------------------------------------------------------------

    def record_base_payment(self, task_id, contributor_id, gross_amount, tier, gene_id=None, reason=None):
        self._validate_payment(gross_amount, tier)
        burn = round(gross_amount * BURN_RATE_BASE_PAYMENT, 2)
        net = round(gross_amount - burn, 2)
        payment = {
            "task_id": task_id, "contributor_id": contributor_id,
            "gross": gross_amount, "burn": burn, "net": net,
            "tier": tier, "gene_id": gene_id, "reason": reason,
            "timestamp": _format_dt(_now()),
        }
        em = self.state["emission"]
        self.state["base_payments"].append(payment)
        self.state["burns"].append({"source": "base_payment", "task_id": task_id, "amount": burn, "timestamp": payment["timestamp"]})
        em["epoch_emitted"] += gross_amount
        em["total_emitted"] += gross_amount
        em["total_burned"] += burn
        em["total_circulating"] += net
        return payment

    def activate_royalty(self, gene_id, contributor_id, tier, activation_date=None, reason=None):
        self._validate_royalty(gene_id, tier)
        cfg = TIER_CONFIG[tier]
        royalty = {
            "gene_id": gene_id, "contributor_id": contributor_id,
            "tier": tier, "tier_name": cfg["name"],
            "activation_date": _format_dt(activation_date or _now()),
            "window_months": cfg["window_months"],
            "rate_start": cfg["rate_start"], "rate_end": cfg["rate_end"],
            "attributed_revenue_this_period": 0, "total_royalties_paid": 0,
            "status": "active", "reason": reason,
        }
        self.state["royalties"].append(royalty)
        return royalty

    def activate_bond(self, bond_id, holder_id, bond_type, principal, start_date=None, reason=None):
        cfg = BOND_CONFIG.get(bond_type)
        if not cfg:
            raise ValueError(f"Unknown bond type: {bond_type}")
        self._validate_bond(bond_id, principal)
        start = start_date or _now()
        maturity_days = int(cfg["lock_months"] * 30.44)
        maturity = datetime.fromtimestamp(start.timestamp() + maturity_days * 86400, tz=timezone.utc)
        bond = {
            "bond_id": bond_id, "holder_id": holder_id,
            "bond_type": bond_type, "bond_label": cfg["label"],
            "principal": principal, "yield_rate": cfg["yield_rate"],
            "start_date": _format_dt(start), "maturity_date": _format_dt(maturity),
            "yield_paid": 0, "status": "active", "reason": reason,
        }
        self.state["bonds"].append(bond)
        self.state["emission"]["total_circulating"] -= principal
        return bond

    # -------------------------------------------------------------------
    # Royalty operations
    # -------------------------------------------------------------------

    def record_royalty_disbursement(self, gene_id, amount, reason=None):
        target = None
        for r in self.state["royalties"]:
            if r["gene_id"] == gene_id and r["status"] == "active":
                target = r
                break
        if not target:
            raise ValueError(f"No active royalty for gene {gene_id}")
        target["total_royalties_paid"] = round(target.get("total_royalties_paid", 0) + amount, 2)
        target["attributed_revenue_this_period"] = 0
        self.state["emission"]["total_emitted"] += amount
        self.state["emission"]["total_circulating"] += amount
        return {"gene_id": gene_id, "amount": amount, "total_paid": target["total_royalties_paid"], "reason": reason, "timestamp": _format_dt(_now())}

    def set_attributed_revenue(self, gene_id, revenue):
        if revenue < 0:
            raise ValueError(f"Revenue cannot be negative, got {revenue}")
        target = None
        for r in self.state["royalties"]:
            if r["gene_id"] == gene_id and r["status"] == "active":
                target = r
                break
        if not target:
            raise ValueError(f"No active royalty for gene {gene_id}")
        target["attributed_revenue_this_period"] = revenue
        return {"gene_id": gene_id, "attributed_revenue": revenue}

    def supersede_royalty(self, old_gene_id, new_gene_id, new_contributor_id, new_tier, reason=None):
        terminated = False
        for r in self.state["royalties"]:
            if r["gene_id"] == old_gene_id and r["status"] == "active":
                r["status"] = "superseded"
                r["superseded_by"] = new_gene_id
                terminated = True
                break
        if not terminated:
            raise ValueError(f"No active royalty for gene {old_gene_id} to supersede")
        return self.activate_royalty(new_gene_id, new_contributor_id, new_tier, reason=reason)

    # -------------------------------------------------------------------
    # Bond operations
    # -------------------------------------------------------------------

    def early_exit_bond(self, bond_id, reason=None):
        target = None
        for b in self.state["bonds"]:
            if b["bond_id"] == bond_id and b["status"] == "active":
                target = b
                break
        if not target:
            raise ValueError(f"No active bond with ID {bond_id}")
        cfg = BOND_CONFIG.get(target["bond_type"])
        start = _parse_dt(target["start_date"])
        now = _now()
        months_elapsed = _months_between(start, now)
        months_total = cfg["lock_months"]
        total_yield = target["principal"] * target["yield_rate"]
        accrued = total_yield * (months_elapsed / months_total)
        forfeited = round(accrued * EARLY_EXIT_FORFEIT, 2)
        returned_yield = max(0, round(accrued - forfeited - target.get("yield_paid", 0), 2))
        burn_amount = round(forfeited * 0.5, 2)
        target["status"] = "early_exit"
        target["exit_date"] = _format_dt(now)
        target["exit_reason"] = reason
        self.state["emission"]["total_circulating"] += target["principal"]
        self.state["emission"]["total_burned"] += burn_amount
        if returned_yield > 0:
            self.state["emission"]["total_emitted"] += returned_yield
            self.state["emission"]["total_circulating"] += returned_yield
        return {
            "bond_id": bond_id, "principal_returned": target["principal"],
            "yield_accrued": round(accrued, 2), "yield_forfeited": forfeited,
            "yield_burned": burn_amount, "yield_returned_to_holder": returned_yield,
            "unlock_date": _format_dt(now + timedelta(days=30)), "reason": reason,
        }

    # -------------------------------------------------------------------
    # Epoch management
    # -------------------------------------------------------------------

    def advance_epoch(self, reason=None):
        em = self.state["emission"]
        current = em["current_epoch"]
        max_defined = len(em["epochs"])
        if current >= max_defined:
            em["epoch_emitted"] = 0
            return {"new_epoch": current, "note": "Terminal epoch, counter reset only", "reason": reason}
        em["current_epoch"] = current + 1
        em["epoch_emitted"] = 0
        new_cfg = em["epochs"][min(current, max_defined - 1)]
        return {"new_epoch": em["current_epoch"], "new_cap": new_cfg["max_emission"], "reason": reason}

    # -------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------

    def run_lifecycle(self, as_of=None):
        as_of = as_of or _now()
        changes = {"royalties_expired": [], "bonds_matured": []}
        for r in self.state["royalties"]:
            if r["status"] != "active":
                continue
            rate = self.current_royalty_rate(r, as_of)
            if rate <= 0:
                r["status"] = "expired"
                changes["royalties_expired"].append(r["gene_id"])
        for b in self.state["bonds"]:
            if b["status"] != "active":
                continue
            maturity = _parse_dt(b["maturity_date"])
            if as_of >= maturity:
                b["status"] = "matured"
                remaining_yield = round(b["principal"] * b["yield_rate"] - b["yield_paid"], 2)
                self.state["emission"]["total_circulating"] += b["principal"]
                self.state["emission"]["total_emitted"] += max(0, remaining_yield)
                self.state["emission"]["total_circulating"] += max(0, remaining_yield)
                changes["bonds_matured"].append(b["bond_id"])
        return changes

    # -------------------------------------------------------------------
    # Monthly report
    # -------------------------------------------------------------------

    def monthly_report(self, as_of=None):
        as_of = as_of or _now()
        lifecycle = self.run_lifecycle(as_of)
        royalty_obs = self.royalty_obligations(as_of)
        bond_obs = self.bond_obligations(as_of)
        total_royalties_due = sum(r["amount_owed"] for r in royalty_obs)
        total_bond_yield_due = sum(b["yield_due_now"] for b in bond_obs)
        return {
            "report_date": _format_dt(as_of),
            "report_type": "MONTHLY_TREASURY",
            "schema_version": "1.1",
            "obligations": {
                "royalties": royalty_obs, "bonds": bond_obs,
                "total_royalties_due": total_royalties_due,
                "total_bond_yield_due": total_bond_yield_due,
                "total_due": round(total_royalties_due + total_bond_yield_due, 2),
            },
            "upcoming": {
                "expiring_royalties_60d": self.expiring_royalties(60, as_of),
                "maturing_bonds_90d": self.maturing_bonds(90, as_of),
            },
            "emission": self.emission_status(),
            "lifecycle": lifecycle,
            "governor_actions": self._governor_actions(as_of),
        }

    def _governor_actions(self, as_of=None):
        as_of = as_of or _now()
        actions = []
        for e in self.expiring_royalties(30, as_of):
            actions.append({"priority": "INFO", "action": f"Royalty for {e['gene_id']} expires in {e['days_until_expiry']:.0f} days", "requires": "No action needed unless renewal warranted"})
        for m in self.maturing_bonds(30, as_of):
            actions.append({"priority": "ACTION", "action": f"Bond {m['bond_id']} matures in {m['days_to_maturity']} days", "requires": f"Prepare {m['principal']} principal + yield return for {m['holder_id']}"})
        emission = self.emission_status()
        for w in emission["warnings"]:
            actions.append({"priority": "WARNING", "action": w, "requires": "Review emission pace, consider slowing disbursements"})
        if not self.state["royalties"] and not self.state["bonds"] and not self.state["base_payments"]:
            actions.append({"priority": "INFO", "action": "Treasury is empty — no active obligations", "requires": "Normal for pre-launch. No action needed."})
        return actions

    # -------------------------------------------------------------------
    # Save (atomic write with backup)
    # -------------------------------------------------------------------

    def save(self, path=None):
        path = Path(path) if path else self.state_path
        self.state["_last_updated"] = _format_dt(_now())
        if path.exists():
            shutil.copy2(path, path.with_suffix(".json.bak"))
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp", prefix="treasury_")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self.state, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def save_report(self, report, path="treasury_report.json"):
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
