# Executioner - Lab A Phase 0

The torture harness. Tests SAIF v1.1 artifacts through T0-T4.

## What It Does

Tests memory mechanisms for survivability:
- **T0:** SELFTEST (artifact validates itself)
- **T1:** Syntax & Isolation (compiles, runs in Docker)
- **T2:** Degradation (survives history truncation: 1000→500→250→100→50→10 events)
- **T3:** Compaction (survives byte reduction: 8000→5000→3000→1000 bytes)
- **T4:** Restart (reconstructs state after cold restart: 5 cycles)

**Verdict:** SURVIVOR or KILLED (with reason)

## Requirements

- Docker (for isolation)
- Python 3.10+
- Ubuntu/Linux (tested on Beelink EQ13)

## Installation
```bash
