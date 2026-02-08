#!/usr/bin/env python3
"""
House Bernard Treasury — Red Team Test Suite
Attacks edge cases, financial math, state corruption, and missing guardrails.
"""

import json
import os
import sys
import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add treasury to path
sys.path.insert(0, str(Path(__file__).parent))
from treasury_engine import TreasuryEngine, TIER_CONFIG, BOND_CONFIG

PASS = 0
FAIL = 0
FINDINGS = []

def clean_state():
    """Return a fresh treasury state dict."""
    return {
        "_schema_version": "1.0",
        "_description": "Test state",
        "_last_updated": "2026-02-08T00:00:00Z",
        "_signed_by": "governor",
        "emission": {
            "current_epoch": 1,
            "epoch_start": "2026-01-01T00:00:00Z",
            "epochs": [
                {"epoch": 1, "label": "Genesis", "max_emission": 10000000, "per_contribution_cap": 100000},
                {"epoch": 2, "label": "Year 2",  "max_emission": 5000000,  "per_contribution_cap": 50000},
            ],
            "total_emitted": 0, "epoch_emitted": 0,
            "total_burned": 0, "total_circulating": 0,
        },
        "royalties": [], "bonds": [], "base_payments": [], "burns": [],
    }

def write_state(state, path="test_state.json"):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return path

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

def expect_error(name, fn, error_type=ValueError, finding=None):
    global PASS, FAIL
    try:
        fn()
        FAIL += 1
        msg = finding or f"Expected {error_type.__name__} but no error raised"
        FINDINGS.append(msg)
        print(f"  ✗ {name} — no error raised")
    except error_type:
        PASS += 1
        print(f"  ✓ {name}")
    except Exception as e:
        FAIL += 1
        FINDINGS.append(f"{name}: Got {type(e).__name__}: {e}")
        print(f"  ✗ {name} — wrong error: {type(e).__name__}: {e}")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: FINANCIAL MATH")
print("=" * 60)

# Test 1: Royalty decay linearity
print("\n[Royalty Decay Math]")
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)

activation = datetime(2026, 1, 1, tzinfo=timezone.utc)
engine.activate_royalty("GENE-T1", "alice", 2, activation)

# At t=0, rate should be exactly rate_start (2%)
rate_t0 = engine.current_royalty_rate(engine.state["royalties"][0], activation)
test("Flame rate at t=0 = 2.0%", abs(rate_t0 - 0.02) < 0.0001)

# At t=3mo (halfway), rate should be 1.0%
mid = activation + timedelta(days=91)
rate_mid = engine.current_royalty_rate(engine.state["royalties"][0], mid)
test("Flame rate at midpoint ≈ 1.0%", abs(rate_mid - 0.01) < 0.002,
     f"Expected ~0.01, got {rate_mid}")

# At t=6mo (end), rate should be 0.0%
end = activation + timedelta(days=183)
rate_end = engine.current_royalty_rate(engine.state["royalties"][0], end)
test("Flame rate at expiry = 0.0%", rate_end == 0.0)

# At t=7mo (past end), rate should still be 0.0%
past = activation + timedelta(days=213)
rate_past = engine.current_royalty_rate(engine.state["royalties"][0], past)
test("Flame rate past expiry = 0.0%", rate_past == 0.0)

# Test 2: Furnace-Forged decay
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)
engine.activate_royalty("GENE-FF", "bob", 3, activation)

rate_ff_start = engine.current_royalty_rate(engine.state["royalties"][0], activation)
test("Furnace-Forged rate at t=0 = 5.0%", abs(rate_ff_start - 0.05) < 0.0001)

end_ff = activation + timedelta(days=int(18 * 30.44) + 1)  # Just past window
rate_ff_end = engine.current_royalty_rate(engine.state["royalties"][0], end_ff)
test("Furnace-Forged rate at expiry = 0.0%", rate_ff_end == 0.0)

# Test 3: Invariant decay
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)
engine.activate_royalty("GENE-INV", "carol", 4, activation)

rate_inv = engine.current_royalty_rate(engine.state["royalties"][0], activation)
test("Invariant rate at t=0 = 8.0%", abs(rate_inv - 0.08) < 0.0001)

# At end (24mo), should reach rate_end (2%), NOT 0%
almost_end = activation + timedelta(days=int(24 * 30.44) - 1)
rate_inv_near_end = engine.current_royalty_rate(engine.state["royalties"][0], almost_end)
test("Invariant rate near expiry ≈ 2.0%", abs(rate_inv_near_end - 0.02) < 0.005,
     f"Expected ~0.02, got {rate_inv_near_end}")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: BURN MATH")
print("=" * 60)

print("\n[Burn Calculations]")
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)

p = engine.record_base_payment("T-001", "alice", 10000, 1)
test("5% burn on 10,000 = 500", p["burn"] == 500.0)
test("Net = 9,500", p["net"] == 9500.0)
test("Gross = 10,000", p["gross"] == 10000.0)
test("Circulating = net (9,500)", engine.state["emission"]["total_circulating"] == 9500.0)
test("Burned tracked", engine.state["emission"]["total_burned"] == 500.0)

# Fractional amounts
p2 = engine.record_base_payment("T-002", "bob", 333, 1)
test("Burn on 333 = 16.65", p2["burn"] == 16.65)
test("Net on 333 = 316.35", p2["net"] == 316.35)


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: EMISSION CAP ENFORCEMENT")
print("=" * 60)

print("\n[Hard Cap Tests]")
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)

# Per-contribution cap
expect_error("Reject payment > per-contribution cap",
    lambda: engine.record_base_payment("T-X", "hacker", 100001, 4))

# Epoch headroom exhaustion
state = clean_state()
state["emission"]["epoch_emitted"] = 9950000  # Nearly full
path = write_state(state)
engine = TreasuryEngine(path)

expect_error("Reject payment exceeding epoch headroom",
    lambda: engine.record_base_payment("T-X", "hacker", 60000, 1))

# Exact boundary: should succeed at exactly remaining headroom
state = clean_state()
state["emission"]["epoch_emitted"] = 9900000
path = write_state(state)
engine = TreasuryEngine(path)
p = engine.record_base_payment("T-EDGE", "edge", 100000, 4)
test("Accept payment at exact headroom boundary", p["gross"] == 100000)


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: MISSING GUARDRAILS")
print("=" * 60)

print("\n[Input Validation Gaps]")
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)

# BUG HUNT: Negative payment
try:
    p = engine.record_base_payment("T-NEG", "thief", -5000, 1)
    test("REJECT negative payment", False,
         "BUG: Negative payment accepted! Gross=-5000, this would SUBTRACT from emission and ADD negative burn")
except (ValueError, Exception):
    test("REJECT negative payment", True)

# BUG HUNT: Zero payment
try:
    p = engine.record_base_payment("T-ZERO", "freeloader", 0, 1)
    test("REJECT zero payment", False,
         "BUG: Zero payment accepted — creates noise in ledger with no value")
except (ValueError, Exception):
    test("REJECT zero payment", True)

# BUG HUNT: Negative bond principal
try:
    engine.activate_bond("B-NEG", "thief", "builder", -10000)
    test("REJECT negative bond principal", False,
         "BUG: Negative bond principal accepted! Would ADD to circulating supply on activation")
except (ValueError, Exception):
    test("REJECT negative bond principal", True)

# BUG HUNT: Zero bond principal
try:
    engine.activate_bond("B-ZERO", "freeloader", "builder", 0)
    test("REJECT zero bond principal", False,
         "BUG: Zero-principal bond accepted — phantom bond with yield obligations")
except (ValueError, Exception):
    test("REJECT zero bond principal", True)

# BUG HUNT: Invalid tier
try:
    engine.record_base_payment("T-BAD", "confused", 1000, 99)
    test("REJECT invalid tier on payment", False,
         "MINOR: Invalid tier accepted on base payment — no crash but bad data")
except (ValueError, KeyError, Exception):
    test("REJECT invalid tier on payment", True)

# BUG HUNT: Duplicate gene_id royalties
engine2 = TreasuryEngine(write_state(clean_state()))
engine2.activate_royalty("GENE-DUP", "alice", 2)
expect_error("REJECT duplicate gene_id royalty",
    lambda: engine2.activate_royalty("GENE-DUP", "alice", 2),
    finding="BUG: Duplicate gene_id royalty accepted — double payments possible")

# BUG HUNT: Duplicate bond_id
# Need circulating supply for bonds
state_b = clean_state()
state_b["emission"]["total_circulating"] = 100000
engine2b = TreasuryEngine(write_state(state_b))
engine2b.activate_bond("BOND-DUP", "alice", "contributor", 5000)
expect_error("REJECT duplicate bond_id",
    lambda: engine2b.activate_bond("BOND-DUP", "alice", "contributor", 5000),
    finding="BUG: Duplicate bond_id accepted — double yield obligations")

# BUG HUNT: Bond that would make circulating go negative
state = clean_state()
state["emission"]["total_circulating"] = 1000
path = write_state(state)
engine3 = TreasuryEngine(path)
expect_error("REJECT bond > circulating supply",
    lambda: engine3.activate_bond("B-DRAIN", "whale", "founder", 50000),
    finding="BUG: Circulating went negative — bond locked more than exists")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: LIFECYCLE & STATE INTEGRITY")
print("=" * 60)

print("\n[Lifecycle Edge Cases]")

# Double lifecycle run — should be idempotent
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)
activation = datetime(2025, 1, 1, tzinfo=timezone.utc)  # Already expired
engine.activate_royalty("GENE-OLD", "alice", 2, activation)

now = datetime(2026, 2, 8, tzinfo=timezone.utc)
changes1 = engine.run_lifecycle(now)
changes2 = engine.run_lifecycle(now)
test("Lifecycle is idempotent (no double-expire)",
     len(changes2["royalties_expired"]) == 0,
     f"BUG: Second lifecycle run expired {len(changes2['royalties_expired'])} royalties again")

# Report calls lifecycle internally — running report twice shouldn't corrupt
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)
engine.activate_royalty("GENE-RPT", "bob", 2, activation)
r1 = engine.monthly_report(now)
r2 = engine.monthly_report(now)
test("Double report doesn't double-expire",
     len(r2["lifecycle"]["royalties_expired"]) == 0)


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: BOND YIELD ACCOUNTING")
print("=" * 60)

print("\n[Bond Math]")
state = clean_state()
state["emission"]["total_circulating"] = 100000
path = write_state(state)
engine = TreasuryEngine(path)

start = datetime(2026, 1, 1, tzinfo=timezone.utc)
engine.activate_bond("BOND-B1", "alice", "builder", 10000, start)

# Check principal removed from circulation
test("Bond activation removes principal from circulation",
     engine.state["emission"]["total_circulating"] == 90000)

# At 6 months (halfway through 12-month builder bond)
mid = start + timedelta(days=182)
obs = engine.bond_obligations(mid)
test("Bond has 1 obligation", len(obs) == 1)
if obs:
    # Total yield = 10000 * 0.15 = 1500. At halfway, ~750 accrued
    test("Midpoint yield ≈ 750", abs(obs[0]["yield_due_now"] - 750) < 50,
         f"Got yield_due={obs[0]['yield_due_now']}, expected ~750")

# At maturity
mature = start + timedelta(days=366)
obs_mat = engine.bond_obligations(mature)
if obs_mat:
    test("Matured yield = 1500", abs(obs_mat[0]["yield_due_now"] - 1500) < 1,
         f"Got yield_due={obs_mat[0]['yield_due_now']}, expected 1500")

# Lifecycle maturity — does principal return to circulation?
circ_before = engine.state["emission"]["total_circulating"]
engine.run_lifecycle(mature)
circ_after = engine.state["emission"]["total_circulating"]
test("Matured bond returns principal to circulation",
     circ_after >= circ_before + 10000,
     f"Circulating went from {circ_before} to {circ_after}, expected +10000+yield")

# Bond yield emission — is yield added to total_emitted?
test("Bond yield counts as emission",
     engine.state["emission"]["total_emitted"] > 0,
     "BUG: Bond yield not tracked in total_emitted — stealth money printing")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: MONTHLY REPORT COMPUTATION COST")
print("=" * 60)

print("\n[Performance / Redundant Computation]")

# The monthly_report method calls royalty_obligations() and bond_obligations()
# TWICE each — once to build the list, once to sum. This is wasteful and
# could produce inconsistent results if state changes between calls.
state = clean_state()
path = write_state(state)
engine = TreasuryEngine(path)

# Count how many times royalty_obligations would be called
# (can't easily instrument, but we can flag the design)
# The v1.1 monthly_report caches computed obligations in local vars.
# Verify by checking the source contains the pattern.
import inspect
src = inspect.getsource(engine.monthly_report)
uses_local = "royalty_obs" in src and "bond_obs" in src
test("Report computes obligations once (v1.1 fix)", uses_local,
     "PERF: monthly_report() still calls royalty_obligations() twice")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: SAVE SAFETY")
print("=" * 60)

print("\n[File Corruption Risks]")

# Verify save() uses atomic write (tempfile + os.replace)
import inspect
save_src = inspect.getsource(engine.save)
has_atomic = "tempfile" in save_src or "os.replace" in save_src or "mkstemp" in save_src
test("save() uses atomic write", has_atomic,
     "RISK: save() writes directly — crash mid-write corrupts state")

# Verify save() creates backup
has_backup = "copy2" in save_src or ".bak" in save_src or "backup" in save_src
test("save() creates backup", has_backup,
     "RISK: No backup created before overwriting state")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM: MISSING FEATURES")
print("=" * 60)

print("\n[Operational Gaps]")

# No early bond exit
test("Early bond exit supported", hasattr(engine, 'early_exit_bond'),
     "MISSING: No early_exit_bond() method. TREASURY.md specifies 50% forfeit penalty "
     "but the engine can't process it. Need: forfeit calc, partial yield return, unlock principal.")

# No royalty disbursement recording
test("Royalty disbursement recording", hasattr(engine, 'record_royalty_disbursement'),
     "MISSING: No way to record that a royalty was actually paid. total_royalties_paid field "
     "exists on royalty records but nothing updates it. Can't distinguish owed from paid.")

# No supersession (replacement decay)
test("Royalty supersession supported", hasattr(engine, 'supersede_royalty'),
     "MISSING: ROYALTIES.md specifies replacement decay — if a better gene replaces yours, "
     "your royalty terminates early. No mechanism to trigger this.")

# No epoch advancement
test("Epoch advancement supported", hasattr(engine, 'advance_epoch'),
     "MISSING: No way to advance from Epoch 1 to Epoch 2. When Year 2 starts, someone has "
     "to manually edit the JSON. Should have advance_epoch() with date validation.")

# No revenue attribution helper
test("Revenue attribution helper exists", hasattr(engine, 'set_attributed_revenue'),
     "MISSING: Revenue attribution requires manually editing JSON. Should have a method "
     "to set/update attributed_revenue_this_period per gene, with validation.")

# No audit trail on state changes
# Verify reason/notes field on all operations
import inspect
pay_sig = inspect.signature(engine.record_base_payment)
roy_sig = inspect.signature(engine.activate_royalty)
bond_sig = inspect.signature(engine.activate_bond)
has_reason = ("reason" in pay_sig.parameters
              and "reason" in roy_sig.parameters
              and "reason" in bond_sig.parameters)
test("State changes accept reason parameter", has_reason,
     "MISSING: Operations don't accept reason/notes for audit trail")


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM ROUND 2: ADVERSARIAL SCENARIOS")
print("=" * 60)

print("\n[New Feature Validation]")

# Test early bond exit
state = clean_state()
state["emission"]["total_circulating"] = 100000
path = write_state(state)
engine_r2 = TreasuryEngine(path)
start = datetime(2025, 7, 1, tzinfo=timezone.utc)
engine_r2.activate_bond("B-EXIT", "alice", "builder", 10000, start)

result = engine_r2.early_exit_bond("B-EXIT", reason="Need liquidity")
test("Early exit returns principal", result["principal_returned"] == 10000)
test("Early exit has forfeit > 0", result["yield_forfeited"] > 0)
test("Early exit records reason", result["reason"] == "Need liquidity")
test("Bond status = early_exit",
     any(b["status"] == "early_exit" for b in engine_r2.state["bonds"] if b["bond_id"] == "B-EXIT"))

# Test early exit on non-existent bond
expect_error("Reject early exit on missing bond",
    lambda: engine_r2.early_exit_bond("B-GHOST"))

# Test supersession
state = clean_state()
path = write_state(state)
engine_r2 = TreasuryEngine(path)
engine_r2.activate_royalty("GENE-OLD", "alice", 2)
new = engine_r2.supersede_royalty("GENE-OLD", "GENE-NEW", "bob", 3, reason="Superior gene")
test("Supersession deactivates old royalty",
     any(r["status"] == "superseded" for r in engine_r2.state["royalties"] if r["gene_id"] == "GENE-OLD"))
test("Supersession activates new royalty",
     any(r["status"] == "active" for r in engine_r2.state["royalties"] if r["gene_id"] == "GENE-NEW"))

# Supersede non-existent gene
expect_error("Reject supersession of missing gene",
    lambda: engine_r2.supersede_royalty("GENE-PHANTOM", "GENE-X", "carol", 2))

# Test revenue attribution
engine_r2.set_attributed_revenue("GENE-NEW", 50000)
target = [r for r in engine_r2.state["royalties"] if r["gene_id"] == "GENE-NEW"][0]
test("Revenue attribution sets value", target["attributed_revenue_this_period"] == 50000)

expect_error("Reject negative revenue",
    lambda: engine_r2.set_attributed_revenue("GENE-NEW", -1000))

expect_error("Reject revenue on missing gene",
    lambda: engine_r2.set_attributed_revenue("GENE-NOPE", 1000))

# Test royalty disbursement recording
state = clean_state()
path = write_state(state)
engine_r2 = TreasuryEngine(path)
engine_r2.activate_royalty("GENE-PAY", "alice", 3)
engine_r2.set_attributed_revenue("GENE-PAY", 100000)
result = engine_r2.record_royalty_disbursement("GENE-PAY", 5000)
test("Disbursement records total paid", result["total_paid"] == 5000)
paid_gene = [r for r in engine_r2.state["royalties"] if r["gene_id"] == "GENE-PAY"][0]
test("Disbursement resets period revenue", paid_gene["attributed_revenue_this_period"] == 0)

# Test epoch advancement
state = clean_state()
path = write_state(state)
engine_r2 = TreasuryEngine(path)
engine_r2.record_base_payment("T-EP1", "alice", 50000, 1)
old_emitted = engine_r2.state["emission"]["epoch_emitted"]
result = engine_r2.advance_epoch(reason="Year 2 begins")
test("Epoch advances to 2", engine_r2.state["emission"]["current_epoch"] == 2)
test("Epoch emitted resets to 0", engine_r2.state["emission"]["epoch_emitted"] == 0)

# New epoch should have lower caps
expect_error("New epoch enforces lower per-contribution cap",
    lambda: engine_r2.record_base_payment("T-EP2", "bob", 60000, 1),
    finding="BUG: Epoch 2 cap (50k) not enforced")

# Test atomic save actually works
state = clean_state()
path = write_state(state, "test_save_atomic.json")
engine_r2 = TreasuryEngine("test_save_atomic.json")
engine_r2.record_base_payment("T-SAVE", "alice", 1000, 1)
engine_r2.save()
test("Save creates backup file", os.path.exists("test_save_atomic.json.bak"))

# Reload and verify state persisted
engine_r2_reload = TreasuryEngine("test_save_atomic.json")
test("Save persists state across reload",
     len(engine_r2_reload.state["base_payments"]) == 1)

# Cleanup save test files
for f in ["test_save_atomic.json", "test_save_atomic.json.bak"]:
    if os.path.exists(f):
        os.remove(f)


# ===================================================================
print("\n" + "=" * 60)
print("  RED TEAM SUMMARY")
print("=" * 60)
print(f"\n  Passed: {PASS}")
print(f"  Failed: {FAIL}")
print(f"\n  FINDINGS ({len(FINDINGS)}):")
for i, f in enumerate(FINDINGS, 1):
    print(f"  {i:2d}. {f}")

# Cleanup
for f in ["test_state.json"]:
    if os.path.exists(f):
        os.remove(f)
