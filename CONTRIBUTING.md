# Contributing to House Bernard

House Bernard accepts contributions through its **Research Brief** system. We do not use pull requests or issue trackers for research submissions.

## How to Contribute

### 1. Read the Active Briefs

Browse [`briefs/active/`](briefs/active/) for open research problems. Each brief describes:

- The problem to solve
- Required SAIF v1.1 interface compliance
- Bounty range and tier expectations
- Acceptance criteria

### 2. Build a SAIF-Compliant Artifact

Your submission must implement the three mandatory SAIF v1.1 functions:

| Function | Signature | Purpose |
|----------|-----------|---------|
| `ingest` | `(event_payload: dict, state: dict) -> (new_state: dict, lineage_item: dict)` | Process an incoming event |
| `compact` | `(state: dict, lineage: list, target_bytes: int) -> new_state: dict` | Compress state within byte budget |
| `audit` | `(state: dict, lineage: list) -> "OK" or ("HALT", reason: str)` | Self-check for integrity |

**Requirements:**
- Single-file Python module
- Python 3.10+ with type hints
- No external dependencies
- No network access
- No filesystem writes outside `/work`
- Standard library only

### 3. Submit to the Airlock

Package your artifact and submit it to the Airlock intake queue. Submissions enter the **Selection Furnace** — five tiers (T0-T4) of adversarial testing.

### 4. Survive the Furnace

If your artifact survives:
- **Tier 1 (Spark):** Base bounty
- **Tier 2 (Flame):** Base bounty + 6-month royalty stream
- **Tier 3 (Furnace-Forged):** Enhanced bounty + 18-month royalty
- **Tier 4 (Invariant):** Maximum bounty + 24-month royalty + permanent gene credit

## Your Rights

House Bernard's [Constitution](CONSTITUTION.md) and [Bill of Rights](COVENANT.md) guarantee:

- **Attribution:** Your name stays on your work
- **Fair compensation:** Bounties and royalties as specified in briefs
- **Due process:** Disputes resolved through the Magistrate Court
- **No work-for-hire:** You retain moral rights to your contributions

## Code Standards

If contributing to House Bernard infrastructure (not research artifacts):

- Python 3.10+, type hints required
- All file I/O must be atomic (tempfile + os.replace)
- No external dependencies without Crown approval
- Tests required for all new functionality
- Run `python3 run_tests.py` before submitting

## Questions

Read the governance documents linked in [README.md](README.md). The framework is the documentation.

---

*Ad Astra Per Aspera*
