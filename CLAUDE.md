# House Bernard — Claude Code Instructions

## Identity
You are working on the House Bernard repository.
The Crown is HeliosBlade. The agent is AchillesRun.
This is a sovereign research micro-nation's codebase.

## Deployment Target
- Hardware: Beelink EQ13 (N100, 16GB RAM, 512GB SSD)
- OS: Ubuntu Server 24.04 LTS (headless — NO desktop GUI)
- Access: SSH over Tailscale only (no monitor after initial setup)
- Primary channel: Google Chat (free, personal Gmail account)
- Fallback channel: Discord

## Critical Rules
- NEVER commit directly to main without Crown review
- NEVER expose Section 9 contents in commit messages
- NEVER run weapons code outside Docker sandbox
- NEVER modify CONSTITUTION.md or COVENANT.md without
  explicit Crown instruction
- NEVER commit .env files, wallet .json files, or private keys
- All Python code must pass security_scanner.py
- All test output goes to JSON format

## Directory Structure
- section_9/          — CLASSIFIED. Crown eyes only.
- security/           — AST scanner, seccomp profiles
- executioner/        — Selection Furnace (T0-T4 testing)
- treasury/           — Token economics engine + backend
    - treasury_engine.py      — Core: royalties, bonds, emissions, burns
    - treasury_cli.py         — CLI for manual operations
    - monthly_ops.py          — Cron job: automated lifecycle management
    - solana_dispatcher.py    — On-chain payment execution (SPL transfers)
    - cpa_agent.py            — Tax tracking, 1099 generation, expense logging
    - treasury_state.json     — Financial state (source of truth)
    - tax_ledger.json         — CPA Agent's tax records
    - dispatcher_config.json  — Wallet paths + mint address (NEVER commit)
- openclaw/           — Agent config and deployment (LAST to build)
- lab_b/              — Security genetics laboratory
- legal/              — LLC agreement, token TOS, trademark guide (DRAFTS)

## Architecture: How Money Flows

```
Contributor survives Furnace
    → Executioner verdict: SURVIVOR_PHASE_0
    → treasury_engine.record_base_payment()  (validates, computes burn)
    → solana_dispatcher.pay()                (executes on-chain transfer)
    → cpa_agent.record_payment()             (logs USD value for taxes)
    → dispatch_log.jsonl                     (immutable receipt)
```

The Crown does NOT sign routine payments. AchillesRun
(or monthly_ops.py cron) triggers the flow. The Crown
only intervenes for:
- Reserve draws (Crown + AchillesRun + Council member)
- Emergency distributions
- Bond issuance > 1% of supply
- Epoch transitions

## Canonical Allocation (TREASURY.md is authority)

| Allocation | % | Tokens | Wallet |
|------------|---|--------|--------|
| Unmined Treasury | 60% | 60,000,000 | ~/hb-unmined-treasury.json |
| Liquidity Pool | 15% | 15,000,000 | Raydium AMM pool |
| Crown Reserve | 15% | 15,000,000 | ~/hb-governor-reserve.json |
| Genesis Contributors | 10% | 10,000,000 | ~/hb-genesis-contributors.json |

SOVEREIGN_ECONOMICS.md Section IV has been reconciled to
match. If there is ever a conflict, TREASURY.md wins.

## Tonight's Build
If the Crown says "run tonight's build" or "let's go",
read TONIGHTS_BUILD.md for the full deployment playbook.

## Code Standards
- Python 3.10+, type hints on all functions
- Solana CLI + spl-token for all token operations
- No external dependencies not already in the repo
- All output as structured JSON
- All weapons must fail to PASSIVE, never fail to ACTIVE
- Test before commit. Always.

## Token Notes
- Token is SPL on Solana mainnet — no custom smart contract
- Solana's built-in Token Program handles mint/transfer/burn
- Constitutional constraints enforced by treasury_engine.py
- Kill switch: create PAUSE file in treasury/ to halt all transfers
- Price feed: Jupiter API via solana_dispatcher.py
- Wallet files stored in ~/hb-*.json (NEVER commit)

## Section 9 Designations
- Weapons: S9-W-XXX (next available: 007)
- Threats: S9-T-XXX (next available: 001)
- Check section_9/WORK_INSTRUCTIONS.md Appendix C

## Build Order (Steve Jobs rule: customer first)
1. Backend first: treasury engine + dispatcher + CPA agent ← DONE
2. Token deployment: Solana SPL + Raydium pool ← TONIGHT
3. Automation: monthly_ops.py cron + AchillesRun integration
4. Frontend last: OpenClaw public interface
