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
| `monthly_ops.py` | Automated monthly cycle: lifecycle, decay, reputation, escalations. Runs on cron. |
| `ops_state.json` | Ops state: contributor reputation, gene usage tracking, run history. |
| `ops_log.jsonl` | Append-only log of every ops run. |
| `monthly_ops_report.json` | Latest ops report. Includes Governor escalations. |
| `redteam_monthly_ops.py` | Red team test suite for monthly_ops (51 tests). |

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

### Automated (cron runs this — you don't have to)

```bash
# Full monthly cycle: lifecycle, decay, reputation, emission check, escalations
python monthly_ops.py run

# Dry run (no state changes, just shows what would happen)
python monthly_ops.py check

# Backdate for testing
python monthly_ops.py run --date 2026-04-01

# View recent ops log
python monthly_ops.py log
```

Cron entry (1st of month, 6am UTC):
```
0 6 1 * * cd ~/House-Bernard/treasury && python3 monthly_ops.py run >> /var/log/hb_monthly.log 2>&1
```

### What the cron handles automatically

- Expire finished royalties (time decay complete)
- Mature bonds past their maturity date
- Suspend royalties for genes idle 90+ days
- Resume royalties for genes that re-enter active use
- Decay reputation for contributors inactive 90+ days (-5 rep/month)
- Check emission utilization and flag warnings
- Generate report with Governor escalations
- Write to ops_log.jsonl (append-only audit trail)

### What YOU review (only when escalated)

1. Open `monthly_ops_report.json` — check `governor_required` section
2. If bond matured → authorize principal + yield return
3. If payouts due → review and authorize disbursements within 14 days
4. If emission warning → review pace, consider slowing
5. Sign off. That's it.

### Manual operations (unchanged)

```bash
# Record a base payment
python treasury_cli.py pay HB-2026-001 alice 5000 1

# Activate a royalty stream
python treasury_cli.py royalty GENE-001 bob 2

# Activate a bond
python treasury_cli.py bond BOND-001 carol builder 10000
```

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
