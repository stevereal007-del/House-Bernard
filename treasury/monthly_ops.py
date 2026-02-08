#!/usr/bin/env python3
"""
House Bernard — Monthly Operations Automation v1.0
Runs on cron. Handles all repeatable maintenance that doesn't need the Governor.

What it does (every run):
  1. Lifecycle — expire royalties, mature bonds
  2. Royalty decay — compute current rates, flag suspensions
  3. Gene usage decay — suspend royalties for genes idle 90+ days
  4. Reputation decay — deduct 5 rep/month after 90 days inactive
  5. Emission tracking — check epoch utilization, flag warnings
  6. Generate report — write JSON + human-readable summary
  7. Escalation — flag items that REQUIRE Governor action

What it does NOT do:
  - Disburse tokens (Governor signs off on the report first)
  - Change tier assignments (Governor-only)
  - Modify emission caps or epoch transitions (Governor-only)
  - Touch anything outside treasury_state.json and ops_state.json

Design principles:
  - Idempotent: running twice in one day changes nothing
  - Deterministic: same state + same date = same output
  - Append-only logging: ops_log.jsonl is never truncated
  - Atomic saves: crash mid-write won't corrupt state

Usage:
    python3 monthly_ops.py run                    # Full monthly cycle
    python3 monthly_ops.py run --date 2026-03-01  # Backdate for testing
    python3 monthly_ops.py check                  # Dry run, no state changes
    python3 monthly_ops.py log                    # Show recent ops log entries

Cron (1st of month, 6am UTC):
    0 6 1 * * cd ~/House-Bernard/treasury && python3 monthly_ops.py run >> /var/log/hb_monthly.log 2>&1
"""

import json
import sys
import os
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Import the treasury engine (same directory)
sys.path.insert(0, str(Path(__file__).parent))
from treasury_engine import TreasuryEngine, TIER_CONFIG, _now, _parse_dt, _format_dt, _months_between


# ---------------------------------------------------------------------------
# Constants from ROYALTIES.md
# ---------------------------------------------------------------------------

GENE_IDLE_THRESHOLD_DAYS = 90       # Suspend royalty after 90 days inactive
REP_DECAY_RATE = 5                  # -5 rep/month
REP_INACTIVE_THRESHOLD_DAYS = 90    # Decay starts after 90 days inactive
MIN_PAYOUT_THRESHOLD = 100          # Minimum tokens before payout triggers
PAYOUT_DEADLINE_DAYS = 14           # Payout within 14 days of period close


# ---------------------------------------------------------------------------
# Ops State — tracks reputation and gene usage (separate from treasury)
# ---------------------------------------------------------------------------

def _default_ops_state():
    """Return a clean ops state. Created on first run."""
    return {
        "_schema_version": "1.0",
        "_description": "House Bernard Ops State — reputation, gene usage, run history",
        "_last_updated": None,
        "contributors": {},
        "genes": {},
        "last_run_date": None,
        "run_count": 0,
    }


def load_ops_state(path):
    """Load ops state, creating default if missing."""
    path = Path(path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_ops_state()


def save_ops_state(state, path):
    """Atomic write ops state."""
    path = Path(path)
    state["_last_updated"] = _format_dt(_now())
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp", prefix="ops_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# ---------------------------------------------------------------------------
# Ops Log — append-only event log
# ---------------------------------------------------------------------------

def append_log(log_path, entry):
    """Append a single JSON line to the ops log."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def read_log(log_path, n=20):
    """Read last n entries from ops log."""
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    return [json.loads(line) for line in lines[-n:] if line.strip()]


# ---------------------------------------------------------------------------
# Monthly Operations
# ---------------------------------------------------------------------------

class MonthlyOps:

    def __init__(self, treasury_state_path, ops_state_path, log_path):
        self.treasury_state_path = Path(treasury_state_path)
        self.ops_state_path = Path(ops_state_path)
        self.log_path = Path(log_path)
        self.engine = TreasuryEngine(str(self.treasury_state_path))
        self.ops = load_ops_state(self.ops_state_path)
        self.escalations = []
        self.changes = {
            "royalties_expired": [],
            "royalties_suspended": [],
            "royalties_resumed": [],
            "bonds_matured": [],
            "rep_decayed": [],
            "genes_suspended": [],
        }

    # -------------------------------------------------------------------
    # Idempotency guard
    # -------------------------------------------------------------------

    def _already_ran_today(self, as_of):
        last = self.ops.get("last_run_date")
        if not last:
            return False
        last_dt = _parse_dt(last)
        return (last_dt.year == as_of.year and
                last_dt.month == as_of.month and
                last_dt.day == as_of.day)

    # -------------------------------------------------------------------
    # Step 1: Lifecycle (delegates to treasury engine)
    # -------------------------------------------------------------------

    def run_lifecycle(self, as_of):
        """Expire royalties and mature bonds via the treasury engine."""
        result = self.engine.run_lifecycle(as_of)
        self.changes["royalties_expired"] = result.get("royalties_expired", [])
        self.changes["bonds_matured"] = result.get("bonds_matured", [])

        for gene_id in self.changes["royalties_expired"]:
            self.escalations.append({
                "priority": "INFO",
                "type": "royalty_expired",
                "detail": f"Royalty for {gene_id} has expired (time decay complete)",
                "action": "No action needed unless renewal warranted",
            })

        for bond_id in self.changes["bonds_matured"]:
            # Find the bond to get holder info
            holder = "unknown"
            principal = 0
            for b in self.engine.state["bonds"]:
                if b["bond_id"] == bond_id:
                    holder = b.get("holder_id", "unknown")
                    principal = b.get("principal", 0)
                    break
            self.escalations.append({
                "priority": "ACTION",
                "type": "bond_matured",
                "detail": f"Bond {bond_id} matured — return {principal:,.0f} principal + yield to {holder}",
                "action": "Governor must authorize disbursement",
            })

        return result

    # -------------------------------------------------------------------
    # Step 2: Gene usage decay (90-day idle suspension)
    # -------------------------------------------------------------------

    def check_gene_usage(self, as_of):
        """Suspend royalties for genes idle 90+ days. Resume if re-active."""
        for r in self.engine.state["royalties"]:
            if r["status"] not in ("active", "suspended"):
                continue

            gene_id = r["gene_id"]
            gene_record = self.ops["genes"].get(gene_id, {})
            last_active = _parse_dt(gene_record.get("last_active_date"))

            if last_active is None:
                # No usage data — skip, don't punish for missing telemetry
                continue

            idle_days = (as_of - last_active).days

            if r["status"] == "active" and idle_days >= GENE_IDLE_THRESHOLD_DAYS:
                r["status"] = "suspended"
                r["suspension_reason"] = "usage_decay"
                r["suspension_date"] = _format_dt(as_of)
                self.changes["genes_suspended"].append(gene_id)
                self.changes["royalties_suspended"].append(gene_id)
                self.escalations.append({
                    "priority": "INFO",
                    "type": "gene_suspended",
                    "detail": f"Gene {gene_id} idle {idle_days} days — royalty suspended",
                    "action": "Royalty resumes automatically if gene re-enters active use",
                })

            elif r["status"] == "suspended" and idle_days < GENE_IDLE_THRESHOLD_DAYS:
                # Gene is active again — resume
                if r.get("suspension_reason") == "usage_decay":
                    r["status"] = "active"
                    del r["suspension_reason"]
                    if "suspension_date" in r:
                        del r["suspension_date"]
                    self.changes["royalties_resumed"].append(gene_id)

    # -------------------------------------------------------------------
    # Step 3: Reputation decay
    # -------------------------------------------------------------------

    def apply_rep_decay(self, as_of):
        """Deduct 5 rep/month for contributors inactive 90+ days."""
        for cid, record in self.ops["contributors"].items():
            last_active = _parse_dt(record.get("last_active_date"))
            if last_active is None:
                continue

            inactive_days = (as_of - last_active).days
            if inactive_days < REP_INACTIVE_THRESHOLD_DAYS:
                continue

            old_rep = record.get("reputation", 0)
            if old_rep <= 0:
                continue

            new_rep = max(0, old_rep - REP_DECAY_RATE)
            record["reputation"] = new_rep
            record["last_decay_date"] = _format_dt(as_of)
            self.changes["rep_decayed"].append({
                "contributor_id": cid,
                "old_rep": old_rep,
                "new_rep": new_rep,
                "inactive_days": inactive_days,
            })

    # -------------------------------------------------------------------
    # Step 4: Emission check
    # -------------------------------------------------------------------

    def check_emission(self):
        """Check epoch utilization and add warnings to escalations."""
        status = self.engine.emission_status()
        for w in status.get("warnings", []):
            self.escalations.append({
                "priority": "WARNING",
                "type": "emission",
                "detail": w,
                "action": "Review emission pace, consider slowing disbursements",
            })
        return status

    # -------------------------------------------------------------------
    # Step 5: Payout readiness check
    # -------------------------------------------------------------------

    def check_payouts(self, as_of):
        """Identify royalties that are due and above minimum threshold."""
        obligations = self.engine.royalty_obligations(as_of)
        due = []
        rollover = []
        for ob in obligations:
            if ob["amount_owed"] >= MIN_PAYOUT_THRESHOLD:
                due.append(ob)
            elif ob["amount_owed"] > 0:
                rollover.append(ob)

        if due:
            total = sum(o["amount_owed"] for o in due)
            self.escalations.append({
                "priority": "ACTION",
                "type": "payouts_due",
                "detail": f"{len(due)} royalty payouts ready — total {total:,.2f} $HOUSEBERNARD",
                "action": "Governor must review and authorize disbursements within 14 days",
            })

        return {"due": due, "rollover": rollover}

    # -------------------------------------------------------------------
    # Generate report
    # -------------------------------------------------------------------

    def generate_report(self, as_of, dry_run=False):
        """Assemble the full monthly ops report."""
        emission = self.check_emission()
        payouts = self.check_payouts(as_of)
        treasury_report = self.engine.monthly_report(as_of)

        # Separate escalations by priority
        governor_required = [e for e in self.escalations if e["priority"] in ("ACTION", "CRITICAL")]
        info_items = [e for e in self.escalations if e["priority"] in ("INFO", "WARNING")]

        report = {
            "report_type": "MONTHLY_OPS",
            "report_date": _format_dt(as_of),
            "schema_version": "1.0",
            "dry_run": dry_run,
            "run_number": self.ops.get("run_count", 0) + (0 if dry_run else 1),

            "changes": {
                "royalties_expired": self.changes["royalties_expired"],
                "royalties_suspended": self.changes["royalties_suspended"],
                "royalties_resumed": self.changes["royalties_resumed"],
                "bonds_matured": self.changes["bonds_matured"],
                "genes_suspended": self.changes["genes_suspended"],
                "reputation_decayed": self.changes["rep_decayed"],
            },

            "payouts": payouts,
            "emission": emission,
            "treasury_summary": {
                "total_due": treasury_report["obligations"]["total_due"],
                "active_royalties": len([r for r in self.engine.state["royalties"] if r["status"] == "active"]),
                "active_bonds": len([b for b in self.engine.state["bonds"] if b["status"] == "active"]),
                "total_circulating": emission.get("total_circulating", 0),
                "total_burned": emission.get("total_burned", 0),
            },

            "governor_required": governor_required,
            "info": info_items,
        }

        return report

    # -------------------------------------------------------------------
    # Run (the main entry point)
    # -------------------------------------------------------------------

    def run(self, as_of=None, dry_run=False):
        """Execute the full monthly ops cycle."""
        as_of = as_of or _now()

        # Idempotency check
        if not dry_run and self._already_ran_today(as_of):
            print(f"[OPS] Already ran today ({_format_dt(as_of)[:10]}). Skipping.")
            print("[OPS] Use --date to force a different date, or delete last_run_date from ops_state.json.")
            return None

        mode = "DRY RUN" if dry_run else "LIVE"
        print(f"[OPS] House Bernard Monthly Operations — {mode}")
        print(f"[OPS] Date: {_format_dt(as_of)}")
        print()

        # Step 1: Lifecycle
        print("[1/5] Running lifecycle (expire royalties, mature bonds)...")
        self.run_lifecycle(as_of)
        if self.changes["royalties_expired"]:
            print(f"      Expired: {', '.join(self.changes['royalties_expired'])}")
        if self.changes["bonds_matured"]:
            print(f"      Matured: {', '.join(self.changes['bonds_matured'])}")

        # Step 2: Gene usage decay
        print("[2/5] Checking gene usage (90-day idle threshold)...")
        self.check_gene_usage(as_of)
        if self.changes["genes_suspended"]:
            print(f"      Suspended: {', '.join(self.changes['genes_suspended'])}")
        if self.changes["royalties_resumed"]:
            print(f"      Resumed: {', '.join(self.changes['royalties_resumed'])}")

        # Step 3: Reputation decay
        print("[3/5] Applying reputation decay (5 rep/month after 90 days)...")
        self.apply_rep_decay(as_of)
        if self.changes["rep_decayed"]:
            for d in self.changes["rep_decayed"]:
                print(f"      {d['contributor_id']}: {d['old_rep']} → {d['new_rep']} (inactive {d['inactive_days']}d)")

        # Step 4-5: Emission + payouts + report
        print("[4/5] Checking emission and payouts...")
        report = self.generate_report(as_of, dry_run)

        print("[5/5] Generating report...")
        print()

        # Print escalations
        governor_items = report["governor_required"]
        if governor_items:
            print("=" * 60)
            print("  GOVERNOR ACTION REQUIRED")
            print("=" * 60)
            for e in governor_items:
                print(f"  ► [{e['type']}] {e['detail']}")
                print(f"    → {e['action']}")
            print()

        info_items = report["info"]
        if info_items:
            print("-" * 40)
            print("  INFO / WARNINGS")
            print("-" * 40)
            for e in info_items:
                icon = "⚠" if e["priority"] == "WARNING" else "ℹ"
                print(f"  {icon} [{e['type']}] {e['detail']}")
            print()

        if not governor_items and not info_items:
            print("  ✓ No escalations. Treasury is clean.")
            print()

        # Summary
        ts = report["treasury_summary"]
        em = report["emission"]
        print(f"  Circulating: {ts['total_circulating']:,.0f} | Burned: {ts['total_burned']:,.0f}")
        print(f"  Active royalties: {ts['active_royalties']} | Active bonds: {ts['active_bonds']}")
        print(f"  Epoch {em['epoch']} utilization: {em['epoch_utilization_pct']}%")
        print(f"  Total due this period: {ts['total_due']:,.2f} $HOUSEBERNARD")
        print()

        # Save
        if not dry_run:
            # Save treasury state
            self.engine.save()
            print(f"  Treasury state saved → {self.treasury_state_path}")

            # Update ops state
            self.ops["last_run_date"] = _format_dt(as_of)
            self.ops["run_count"] = self.ops.get("run_count", 0) + 1
            save_ops_state(self.ops, self.ops_state_path)
            print(f"  Ops state saved → {self.ops_state_path}")

            # Write report
            report_path = self.treasury_state_path.parent / "monthly_ops_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"  Report saved → {report_path}")

            # Append to ops log
            log_entry = {
                "timestamp": _format_dt(as_of),
                "run_number": report["run_number"],
                "changes_count": sum(
                    len(v) if isinstance(v, list) else 0
                    for v in report["changes"].values()
                ),
                "governor_actions": len(governor_items),
                "total_due": ts["total_due"],
                "epoch_utilization": em["epoch_utilization_pct"],
            }
            append_log(self.log_path, log_entry)
            print(f"  Log appended → {self.log_path}")
        else:
            print("  [DRY RUN — no state changes written]")

        print()
        print("=" * 60)
        if governor_items:
            print("  AWAITING GOVERNOR REVIEW")
        else:
            print("  OPS COMPLETE — NO ACTION REQUIRED")
        print("=" * 60)

        return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    base = Path(__file__).parent
    treasury_path = base / "treasury_state.json"
    ops_path = base / "ops_state.json"
    log_path = base / "ops_log.jsonl"

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "run":
        as_of = None
        dry_run = False
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--date" and i + 1 < len(sys.argv):
                as_of = _parse_dt(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--dry-run":
                dry_run = True
                i += 1
            else:
                print(f"Unknown flag: {sys.argv[i]}")
                sys.exit(1)

        ops = MonthlyOps(treasury_path, ops_path, log_path)
        ops.run(as_of=as_of, dry_run=dry_run)

    elif cmd == "check":
        ops = MonthlyOps(treasury_path, ops_path, log_path)
        ops.run(dry_run=True)

    elif cmd == "log":
        entries = read_log(log_path, n=20)
        if not entries:
            print("No ops log entries yet.")
        else:
            print(f"Last {len(entries)} ops runs:")
            for e in entries:
                print(f"  [{e['timestamp'][:10]}] Run #{e['run_number']} — "
                      f"{e['changes_count']} changes, "
                      f"{e['governor_actions']} escalations, "
                      f"due: {e['total_due']:,.0f}, "
                      f"epoch: {e['epoch_utilization']}%")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
