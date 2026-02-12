---
name: house-bernard-treasury
description: Manage House Bernard treasury operations including payments, royalties, bonds, emissions tracking, tax logging, and monthly lifecycle automation. Use when processing payments, generating treasury reports, checking emission status, running monthly operations, or querying financial state.
---

# Treasury Operations

The treasury engine handles all token economics for House Bernard.

## Components

| File | Purpose |
|------|---------|
| `treasury_engine.py` | Core: royalties, bonds, emissions, burns, constitutional constraints |
| `treasury_cli.py` | CLI for manual operations (report, pay, royalty, bond, status) |
| `monthly_ops.py` | Cron automation: lifecycle management, decay, escalations |
| `solana_dispatcher.py` | On-chain SPL token transfers via Solana CLI |
| `cpa_agent.py` | Tax tracking, 1099 generation, expense logging |

## CLI Usage

```bash
cd ~/House-Bernard/treasury

# Reports
python3 treasury_cli.py report           # Full monthly treasury report
python3 treasury_cli.py status           # Quick emission epoch status

# Payments (Crown or agent authorized)
python3 treasury_cli.py pay HB-2026-001 alice 5000 1

# Royalties
python3 treasury_cli.py royalty GENE-001 alice 2

# Bonds
python3 treasury_cli.py bond BOND-001 alice builder 10000
```

## Monthly Operations

```bash
python3 monthly_ops.py run                    # Full monthly cycle
python3 monthly_ops.py run --date 2026-03-01  # Backdate for testing
python3 monthly_ops.py check                  # Dry run, no state changes
python3 monthly_ops.py log                    # Show recent ops log entries
```

Monthly ops handles: royalty decay, gene usage suspension (90+ days idle), reputation decay (5/month after 90 days inactive), emission tracking, and escalation flagging.

## Payment Flow

```
Contributor survives Furnace
  → treasury_engine.record_base_payment()
  → solana_dispatcher.pay()
  → cpa_agent.record_payment()
  → dispatch_log.jsonl (immutable receipt)
```

## State Files

- `treasury_state.json` — Financial state (source of truth)
- `tax_ledger.json` — CPA agent tax records
- `ops_state.json` — Monthly ops idempotency tracking
- `dispatch_log.jsonl` — Immutable payment log

## Kill Switch

Create a `PAUSE` file in `treasury/` to halt all transfers immediately.

## Scripts

All scripts in `~/House-Bernard/treasury/`. See individual files for detailed usage.
