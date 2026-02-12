---
name: house-bernard-executioner
description: Run the Selection Furnace (T0-T4 torture tests) against contributor artifacts. Validates SAIF contract compliance, Docker sandbox execution, degradation resistance, compaction, and persistence. Use when testing new submissions, re-running furnace tests, or checking an artifact's survivability verdict.
---

# Selection Furnace (Executioner)

Runs T0-T4 torture tests against artifacts that implement the SAIF v1.1 contract.

## SAIF Contract (Frozen)

Every artifact must implement:
- `ingest(event_payload, state) -> (new_state, lineage_item)`
- `compact(state, lineage, target_bytes) -> new_state`
- `audit(state, lineage) -> "OK" | ("HALT", reason)`

## Test Tiers

| Tier | Name | What It Tests |
|------|------|---------------|
| T0 | SELFTEST | Artifact runs its own tests in Docker sandbox |
| T1 | Syntax/Import | Host compile + Docker import validation |
| T2 | Degradation | Progressive ledger truncation — does it survive data loss? |
| T3 | Compaction | Forced target_bytes reduction + audit pass |
| T4 | Restart | Persistent `/work` across container restarts |

Dies at first failure. No partial credit.

## Running Tests

```bash
cd ~/House-Bernard
python3 executioner/executioner_production.py /path/to/artifact.zip
```

Output: structured JSON verdict with tier results, hashes, and timing.

## Scripts

- `scripts/executioner_production.py` — Main furnace harness

## Docker Sandbox

- Image: `python:3.10.15-alpine` (pinned)
- Network: disabled
- Timeout: 300 seconds per tier
- Workspace: `/work` mount (read-write)
