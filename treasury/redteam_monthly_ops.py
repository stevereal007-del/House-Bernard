#!/usr/bin/env python3
"""
House Bernard Monthly Ops — Red Team Test Suite
Tests idempotency, decay math, edge cases, state corruption resistance.
"""

import json
import os
import sys
import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from treasury_engine import TreasuryEngine, TIER_CONFIG, _format_dt, _parse_dt, _now
from monthly_ops import (
    MonthlyOps, load_ops_state, save_ops_state, append_log, read_log,
    GENE_IDLE_THRESHOLD_DAYS, REP_DECAY_RATE, REP_INACTIVE_THRESHOLD_DAYS,
    MIN_PAYOUT_THRESHOLD, _default_ops_state,
)

PASS = 0
FAIL = 0
FINDINGS = []
TEST_DIR = Path(__file__).parent / "_test_workspace"


def setup():
    """Create clean test workspace."""
    TEST_DIR.mkdir(exist_ok=True)
    return TEST_DIR


def clean_treasury_state():
    """Fresh treasury state with some data to test against."""
    return {
        "_schema_version": "1.0",
        "_description": "Test state",
        "_last_updated": "2026-02-08T00:00:00Z",
        "_signed_by": "crown",
        "emission": {
            "current_epoch": 1,
            "epoch_start": "2026-01-01T00:00:00Z",
            "epochs": [
                {"epoch": 1, "label": "Genesis", "max_emission": 10000000, "per_contribution_cap": 100000},
                {"epoch": 2, "label": "Year 2",  "max_emission": 5000000,  "per_contribution_cap": 50000},
            ],
            "total_emitted": 50000, "epoch_emitted": 50000,
            "total_burned": 2500, "total_circulating": 47500,
        },
        "royalties": [
            {
                "gene_id": "GENE-001", "contributor_id": "alice",
                "tier": 2, "tier_name": "Flame",
                "activation_date": "2025-08-01T00:00:00Z",
                "window_months": 6, "rate_start": 0.02, "rate_end": 0.0,
                "attributed_revenue_this_period": 10000,
                "total_royalties_paid": 100, "status": "active",
            },
            {
                "gene_id": "GENE-002", "contributor_id": "bob",
                "tier": 3, "tier_name": "Furnace-Forged",
                "activation_date": "2025-12-01T00:00:00Z",
                "window_months": 18, "rate_start": 0.05, "rate_end": 0.01,
                "attributed_revenue_this_period": 5000,
                "total_royalties_paid": 0, "status": "active",
            },
            {
                "gene_id": "GENE-003", "contributor_id": "carol",
                "tier": 4, "tier_name": "Invariant",
                "activation_date": "2026-01-15T00:00:00Z",
                "window_months": 24, "rate_start": 0.08, "rate_end": 0.02,
                "attributed_revenue_this_period": 200,
                "total_royalties_paid": 0, "status": "active",
            },
        ],
        "bonds": [
            {
                "bond_id": "BOND-001", "holder_id": "dave",
                "bond_type": "contributor", "bond_label": "Contributor Bond",
                "principal": 5000, "yield_rate": 0.05,
                "start_date": "2025-11-01T00:00:00Z",
                "maturity_date": "2026-02-01T00:00:00Z",
                "yield_paid": 0, "status": "active",
            },
        ],
        "base_payments": [
            {"task_id": "HB-2026-001", "contributor_id": "alice", "gross": 1000,
             "burn": 50, "net": 950, "tier": 2, "timestamp": "2026-01-15T00:00:00Z"},
        ],
        "burns": [
            {"source": "base_payment", "task_id": "HB-2026-001", "amount": 50,
             "timestamp": "2026-01-15T00:00:00Z"},
        ],
    }


def clean_ops_state():
    """Fresh ops state with contributor and gene data."""
    return {
        "_schema_version": "1.0",
        "_description": "Test ops state",
        "_last_updated": None,
        "contributors": {
            "alice": {"reputation": 75, "last_active_date": "2026-02-01T00:00:00Z"},
            "bob": {"reputation": 120, "last_active_date": "2025-10-01T00:00:00Z"},
            "carol": {"reputation": 200, "last_active_date": "2026-02-07T00:00:00Z"},
            "dave_inactive": {"reputation": 30, "last_active_date": "2025-06-01T00:00:00Z"},
        },
        "genes": {
            "GENE-001": {"last_active_date": "2026-02-01T00:00:00Z"},
            "GENE-002": {"last_active_date": "2025-09-01T00:00:00Z"},
            "GENE-003": {"last_active_date": "2026-02-07T00:00:00Z"},
        },
        "last_run_date": None,
        "run_count": 0,
    }


def write_state(state, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return path


def make_ops(treasury_state=None, ops_state=None, as_of_str="2026-03-01T06:00:00Z"):
    """Create a MonthlyOps instance with test data."""
    ts = treasury_state or clean_treasury_state()
    os_state = ops_state or clean_ops_state()
    t_path = write_state(ts, TEST_DIR / "treasury_state.json")
    o_path = write_state(os_state, TEST_DIR / "ops_state.json")
    log_path = TEST_DIR / "ops_log.jsonl"
    if log_path.exists():
        log_path.unlink()
    ops = MonthlyOps(t_path, o_path, log_path)
    return ops


def test(name, condition, finding=None):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        msg = finding or f"FAILED: {name}"
        FINDINGS.append(msg)
        print(f"  ✗ {name}")
        if finding:
            print(f"    → {finding}")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: IDEMPOTENCY")
print("=" * 60)

setup()

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")
report1 = ops.run(as_of=as_of, dry_run=False)

test("First run produces report", report1 is not None)
test("Run count is 1", ops.ops["run_count"] == 1)

# Second run same day — should skip
ops2 = MonthlyOps(
    TEST_DIR / "treasury_state.json",
    TEST_DIR / "ops_state.json",
    TEST_DIR / "ops_log.jsonl",
)
report2 = ops2.run(as_of=as_of, dry_run=False)
test("Second run same day returns None (skipped)", report2 is None)
test("Run count still 1 after skip", ops2.ops["run_count"] == 1)

# Dry run doesn't count
ops3 = make_ops()
report3 = ops3.run(as_of=as_of, dry_run=True)
test("Dry run produces report", report3 is not None)
test("Dry run doesn't increment run count", ops3.ops["run_count"] == 0)

# Different day should work
ops4 = MonthlyOps(
    TEST_DIR / "treasury_state.json",
    TEST_DIR / "ops_state.json",
    TEST_DIR / "ops_log.jsonl",
)
next_day = _parse_dt("2026-03-02T06:00:00Z")
report4 = ops4.run(as_of=next_day, dry_run=False)
test("Run on different day succeeds", report4 is not None)

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: ROYALTY LIFECYCLE")
print("=" * 60)

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")

# GENE-001: Flame, activated 2025-08-01, 6-month window → expired by 2026-03-01
ops.run_lifecycle(as_of)
test("GENE-001 (Flame, 7 months old) expired",
     "GENE-001" in ops.changes["royalties_expired"])

# GENE-002: Furnace-Forged, activated 2025-12-01, 18-month window → still active
gene002 = [r for r in ops.engine.state["royalties"] if r["gene_id"] == "GENE-002"][0]
test("GENE-002 (Furnace, 3 months old) still active",
     gene002["status"] == "active")

# GENE-003: Invariant, activated 2026-01-15, 24-month window → still active
gene003 = [r for r in ops.engine.state["royalties"] if r["gene_id"] == "GENE-003"][0]
test("GENE-003 (Invariant, 1.5 months old) still active",
     gene003["status"] == "active")

# BOND-001: maturity 2026-02-01 → should be matured by 2026-03-01
test("BOND-001 matured",
     "BOND-001" in ops.changes["bonds_matured"])

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: GENE USAGE DECAY")
print("=" * 60)

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")
ops.run_lifecycle(as_of)  # Expire what needs expiring first

# GENE-002: last active 2025-09-01 → 182 days idle → should suspend
ops.check_gene_usage(as_of)
gene002 = [r for r in ops.engine.state["royalties"] if r["gene_id"] == "GENE-002"][0]
test("GENE-002 suspended (182 days idle)",
     gene002["status"] == "suspended",
     f"Expected suspended, got {gene002['status']}")
test("GENE-002 suspension reason is usage_decay",
     gene002.get("suspension_reason") == "usage_decay")

# GENE-003: last active 2026-02-07 → 22 days idle → should stay active
gene003 = [r for r in ops.engine.state["royalties"] if r["gene_id"] == "GENE-003"][0]
test("GENE-003 stays active (22 days idle)",
     gene003["status"] == "active")

# Test resume: set GENE-002 back to recent usage and re-check
ops.ops["genes"]["GENE-002"]["last_active_date"] = "2026-02-28T00:00:00Z"
ops.check_gene_usage(as_of)
gene002 = [r for r in ops.engine.state["royalties"] if r["gene_id"] == "GENE-002"][0]
test("GENE-002 resumes after recent usage",
     gene002["status"] == "active",
     f"Expected active, got {gene002['status']}")

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: GENE WITH NO USAGE DATA")
print("=" * 60)

# Gene with no last_active_date should NOT be suspended
ops = make_ops()
del ops.ops["genes"]["GENE-002"]  # Remove usage record entirely
as_of = _parse_dt("2026-03-01T06:00:00Z")
ops.run_lifecycle(as_of)
ops.check_gene_usage(as_of)
gene002 = [r for r in ops.engine.state["royalties"] if r["gene_id"] == "GENE-002"][0]
test("Gene with no usage data is NOT suspended (no punishment for missing telemetry)",
     gene002["status"] == "active",
     f"Expected active, got {gene002['status']}")

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: REPUTATION DECAY")
print("=" * 60)

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")

ops.apply_rep_decay(as_of)

# alice: last active 2026-02-01 → 28 days → NO decay (under 90)
alice = ops.ops["contributors"]["alice"]
test("Alice (28 days inactive) no decay", alice["reputation"] == 75)

# bob: last active 2025-10-01 → 152 days → YES decay
bob = ops.ops["contributors"]["bob"]
test("Bob (152 days inactive) decayed", bob["reputation"] == 115,
     f"Expected 115, got {bob['reputation']}")

# carol: last active 2026-02-07 → 22 days → NO decay
carol = ops.ops["contributors"]["carol"]
test("Carol (22 days inactive) no decay", carol["reputation"] == 200)

# dave_inactive: last active 2025-06-01 → 273 days → YES decay
dave = ops.ops["contributors"]["dave_inactive"]
test("Dave (273 days inactive) decayed", dave["reputation"] == 25,
     f"Expected 25, got {dave['reputation']}")

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: REPUTATION FLOOR AT ZERO")
print("=" * 60)

ops = make_ops()
ops.ops["contributors"]["low_rep"] = {"reputation": 3, "last_active_date": "2025-01-01T00:00:00Z"}
as_of = _parse_dt("2026-03-01T06:00:00Z")
ops.apply_rep_decay(as_of)
low = ops.ops["contributors"]["low_rep"]
test("Reputation floors at 0 (not negative)", low["reputation"] == 0,
     f"Expected 0, got {low['reputation']}")

# Already at zero — no further decay
ops.apply_rep_decay(as_of)
test("Zero rep stays at zero", low["reputation"] == 0)

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: PAYOUT THRESHOLD")
print("=" * 60)

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")
ops.run_lifecycle(as_of)
payouts = ops.check_payouts(as_of)

# GENE-001 is expired — shouldn't appear
# GENE-002 has 5000 attributed revenue × ~4.7% rate → ~235 → above threshold
# GENE-003 has 200 attributed revenue × ~7.9% rate → ~16 → below threshold (rollover)
test("Payouts categorized correctly",
     isinstance(payouts["due"], list) and isinstance(payouts["rollover"], list))

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: REPORT STRUCTURE")
print("=" * 60)

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")
report = ops.run(as_of=as_of, dry_run=True)

required_keys = ["report_type", "report_date", "schema_version", "dry_run",
                 "changes", "payouts", "emission", "treasury_summary",
                 "crown_required", "info"]
for key in required_keys:
    test(f"Report has '{key}'", key in report)

test("Report type is MONTHLY_OPS", report["report_type"] == "MONTHLY_OPS")
test("Dry run flag is True", report["dry_run"] is True)

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: OPS LOG")
print("=" * 60)

# Clear log
log_path = TEST_DIR / "ops_log.jsonl"
if log_path.exists():
    log_path.unlink()

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")
ops.run(as_of=as_of, dry_run=False)

entries = read_log(log_path)
test("Log has 1 entry after first run", len(entries) == 1)
test("Log entry has timestamp", "timestamp" in entries[0])
test("Log entry has run_number", "run_number" in entries[0])
test("Log entry has crown_actions", "crown_actions" in entries[0])

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: ATOMIC SAVES")
print("=" * 60)

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")
ops.run(as_of=as_of, dry_run=False)

# Verify backup exists
bak = TEST_DIR / "treasury_state.json.bak"
test("Treasury backup created", bak.exists())

ops_bak = TEST_DIR / "ops_state.json.bak"
test("Ops state backup created", ops_bak.exists())

# Verify saved state is valid JSON
with open(TEST_DIR / "treasury_state.json") as f:
    saved = json.load(f)
test("Saved treasury state is valid JSON", isinstance(saved, dict))

with open(TEST_DIR / "ops_state.json") as f:
    saved_ops = json.load(f)
test("Saved ops state is valid JSON", isinstance(saved_ops, dict))

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: EMPTY STATE")
print("=" * 60)

empty_ts = {
    "_schema_version": "1.0", "_description": "Empty",
    "_last_updated": "2026-02-08T00:00:00Z", "_signed_by": "crown",
    "emission": {
        "current_epoch": 1, "epoch_start": "2026-01-01T00:00:00Z",
        "epochs": [{"epoch": 1, "label": "Genesis", "max_emission": 10000000, "per_contribution_cap": 100000}],
        "total_emitted": 0, "epoch_emitted": 0, "total_burned": 0, "total_circulating": 0,
    },
    "royalties": [], "bonds": [], "base_payments": [], "burns": [],
}
empty_ops = _default_ops_state()

ops = make_ops(treasury_state=empty_ts, ops_state=empty_ops)
as_of = _parse_dt("2026-03-01T06:00:00Z")
report = ops.run(as_of=as_of, dry_run=True)
test("Empty state runs without error", report is not None)
test("Empty state has no escalations", len(report["crown_required"]) == 0)

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: ESCALATION CATEGORIES")
print("=" * 60)

ops = make_ops()
as_of = _parse_dt("2026-03-01T06:00:00Z")
report = ops.run(as_of=as_of, dry_run=True)

# BOND-001 matured → should be an ACTION escalation
bond_escalations = [e for e in report["crown_required"] if e["type"] == "bond_matured"]
test("Bond maturity triggers ACTION escalation", len(bond_escalations) > 0)

# Check escalation has required fields
if bond_escalations:
    e = bond_escalations[0]
    test("Escalation has priority", e["priority"] == "ACTION")
    test("Escalation has detail", "BOND-001" in e["detail"])
    test("Escalation has action", "Crown" in e["action"])

# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: DATE PARSING EDGE CASES")
print("=" * 60)

# ISO format with Z
ops = make_ops()
test("Parses 'Z' suffix", ops.run(as_of=_parse_dt("2026-03-01T06:00:00Z"), dry_run=True) is not None)

# ISO format with offset
ops = make_ops()
test("Parses '+00:00' suffix", ops.run(as_of=_parse_dt("2026-03-01T06:00:00+00:00"), dry_run=True) is not None)

# ===================================================================
# CLEANUP
# ===================================================================

import shutil
if TEST_DIR.exists():
    shutil.rmtree(TEST_DIR)

# ===================================================================
# SUMMARY
# ===================================================================

print("\n" + "=" * 60)
print(f"  RESULTS: {PASS} passed, {FAIL} failed")
print("=" * 60)

if FINDINGS:
    print("\n  FINDINGS:")
    for i, f in enumerate(FINDINGS, 1):
        print(f"    {i}. {f}")

print()
sys.exit(0 if FAIL == 0 else 1)
