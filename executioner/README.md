# Executioner - Lab A Phase 0

The torture harness. Tests SAIF v1.1 artifacts through T0–T4.

## What It Does

Tests memory mechanisms for survivability:
- **T0:** SELFTEST (artifact validates itself in Docker)
- **T1:** Syntax & Isolation (compiles on host, imports in Docker)
- **T2:** Degradation (survives history truncation: 1000→500→250→100→50→10 events)
- **T3:** Compaction (survives byte reduction: 8000→5000→3000→1000 bytes)
- **T4:** Restart (reconstructs state after cold restart: 5 cycles)

**Verdict:** SURVIVOR_PHASE_0 or KILLED (with reason)

Dies at first failure. No partial credit.

## SAIF v1.1 File Structure

A valid SAIF artifact is a `.zip` containing exactly these files:

| File | Purpose |
|------|---------|
| `manifest.json` | Declares interface functions (`ingest`, `compact`, `audit`) |
| `schema.json` | Schema definition for the artifact's state |
| `mutation.py` | The artifact code — must implement the three SAIF functions |
| `SELFTEST.py` | Artifact's own validation script (run during T0) |
| `README.md` | Description of what the artifact does |

### manifest.json format

```json
{
  "interface": {
    "ingest": "mutation.ingest",
    "compact": "mutation.compact",
    "audit": "mutation.audit"
  }
}
```

### SAIF Function Signatures

```python
def ingest(event_payload: dict, state: dict) -> (new_state: dict, lineage_item: dict)
def compact(state: dict, lineage: list, target_bytes: int) -> new_state: dict
def audit(state: dict, lineage: list) -> "OK" or ("HALT", reason: str)
```

## Requirements

- Docker (for isolation)
- Python 3.10+
- Ubuntu/Linux (tested on Beelink EQ13)

## Installation

```bash
# Pull and pin the Docker image
docker pull python:3.10.15-alpine

# Get the digest and update DOCKER_IMAGE in executioner_production.py if needed
docker inspect --format='{{index .RepoDigests 0}}' python:3.10.15-alpine
```

## Usage

```bash
python3 executioner_production.py <artifact.zip>
```

Output ends with:

```
============================================================
VERDICT: SURVIVOR_PHASE_0
============================================================
```

or:

```
============================================================
VERDICT: KILLED_T2_DEGRADATION
============================================================
```

Exit code 0 = survivor, 1 = killed.
