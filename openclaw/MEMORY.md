# MEMORY.md — AchillesRun Durable Memory

## Crown Preferences

- Crown: HeliosBlade
- Communication: Google Chat DM (Phase 0 primary), Discord (Phase 1 fallback)
- Tone: Dense, no helpfulness theater, silence over display
- Output format: Structured JSON for all test and financial output
- Budget: $5/day hard limit, $50/month hard limit

## Project Conventions

- Python 3.10+, type hints on all functions
- All weapons fail to PASSIVE, never fail to ACTIVE
- CONSTITUTION.md and COVENANT.md are immutable without explicit Crown instruction
- TREASURY.md is canonical authority for token allocation
- All token operations use Solana CLI + spl-token (no custom smart contract)
- Kill switch: create PAUSE file in treasury/ to halt all transfers

## Key Decisions Log

- 2026-02-11: Session persistence upgraded — daily reset disabled, 365-day expiration (Berman Fix)
- 2026-02-11: Memory backend configured — QMD with local search, hybrid vector+BM25
- 2026-02-11: Memory flush before compaction enabled — protects Forgetting Law
- 2026-02-11: Session transcripts enabled — searchable history across sessions
- 2026-02-11: Google Workspace confirmed as operational backbone ($7/month)

## Token Allocation (TREASURY.md is authority)

| Allocation | % | Tokens |
|------------|---|--------|
| Unmined Treasury | 60% | 60,000,000 |
| Liquidity Pool | 15% | 15,000,000 |
| Crown Reserve | 15% | 15,000,000 |
| Genesis Contributors | 10% | 10,000,000 |

## API Endpoints

- Solana mainnet: SPL Token Program (built-in)
- Price feed: Jupiter API via solana_dispatcher.py
- Gateway: 127.0.0.1:18789 (localhost only)

## Constitutional Amendments

_None recorded yet._

---

*House Bernard — Research Without Permission*
