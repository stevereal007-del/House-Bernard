# House Bernard Treasury Module

## Purpose

Automated bookkeeping for the Governor. Tracks royalties, bonds, emission caps, and generates monthly obligation reports. The engine computes — the Governor decides.

## Files

| File | Purpose |
|------|---------|
| `treasury_engine.py` | Core computation module. Royalty decay, bond yields, emission tracking. |
| `treasury_cli.py` | Command-line interface. Run reports, record payments, activate royalties/bonds. |
| `treasury_state.json` | Master state. All active obligations. Governor commits changes. |
| `treasury_report.json` | Generated monthly report. Archive in Ledger after signing. |

## Usage

```bash
# Monthly report (run this on the 1st of each month)
python treasury_cli.py report

# Quick status check
python treasury_cli.py status

# Record a base payment (task_id, contributor, amount, tier, [gene_id])
python treasury_cli.py pay HB-2026-001 alice 5000 1
python treasury_cli.py pay HB-2026-002 bob 25000 2 GENE-001

# Activate a royalty stream (gene_id, contributor, tier)
python treasury_cli.py royalty GENE-001 bob 2

# Activate a bond (bond_id, holder, type, principal)
python treasury_cli.py bond BOND-001 carol builder 10000
```

## Monthly Process

1. Update `attributed_revenue_this_period` on each active royalty in `treasury_state.json`
2. Run `python treasury_cli.py report`
3. Review the report output
4. If approved, execute disbursements and log in Ledger
5. Archive `treasury_report.json` in `/ledger/reports/`

## What It Tracks

**Royalties:** Linear decay from activation date. Tier 2 (Flame) decays 2%→0% over 6 months. Tier 3 (Furnace-Forged) decays 5%→1% over 18 months. Tier 4 (Invariant) decays 8%→2% over 24 months. Auto-expires when window closes.

**Bonds:** Contributor (3mo, 5%), Builder (1yr, 15%), Founder (3yr, 30%). Pro-rata yield accrual. Flags upcoming maturities.

**Emission:** Enforces epoch caps. Rejects payments that exceed per-contribution or epoch limits. Tracks burn, circulating supply.

**Lifecycle:** Auto-expires finished royalties and matured bonds on each report run.

## Design Principles

- **Compute, don't execute.** The engine tells you what's owed. You decide what to pay.
- **State is explicit.** Everything in `treasury_state.json`, nothing in memory.
- **Caps are hard.** Emission limits raise errors, not warnings.
- **Grow linearly.** Zero obligations today? Report says so. 50 royalties next year? Same code handles it.

## Dependencies

Python 3.10+ standard library only. No external packages.

---

*House Bernard — Research Without Permission*
