# Section 9 Weapons Registry

**Classification:** CROWN EYES ONLY
**Maintained by:** Section 9 Director
**Last Review:** February 2026

-----

## Registry Format

Each weapon is logged with the following fields:

| Field | Description |
|-------|-------------|
| **Designation** | Unique identifier (S9-W-XXX) |
| **Name** | Operational name |
| **Class** | I (Passive), II (Active Defense), III (Offensive), IV (Scorched Earth) |
| **Status** | CONCEPT / IN DEVELOPMENT / TESTED / OPERATIONAL / RETIRED |
| **Authorization** | Who can deploy (Director / Crown) |
| **Description** | What it does |
| **Dependencies** | What it requires to operate |
| **Last tested** | Date of last test or deployment |
| **Deployment log** | Record of live deployments |

-----

## Active Registry

### Class I — Passive

#### S9-W-001: Tripwire Alpha

| Field | Value |
|-------|-------|
| **Designation** | S9-W-001 |
| **Name** | Tripwire Alpha |
| **Class** | I (Passive) |
| **Status** | TESTED |
| **Authorization** | Director (autonomous) |
| **Description** | Monitors Airlock submission logs for anomalous patterns (rate spikes, clusters, time anomalies, sequential probes). Produces alert JSON. Never blocks, never modifies. |
| **Dependencies** | Python 3.10+, stdlib only. Airlock log files (JSONL). |
| **Last tested** | 2026-02-09 — 20/20 tests passed |
| **Deployment log** | Not yet deployed (awaiting Beelink connection) |
| **Scanner exceptions** | `open()`, `sys.exit()` — documented in design doc, Crown authorized |

### Class II — Active Defense

*No weapons currently operational.*

### Class III — Offensive

*No weapons currently operational.*

### Class IV — Scorched Earth

#### S9-W-006: Dead Man's Switch

| Field | Value |
|-------|-------|
| **Designation** | S9-W-006 |
| **Name** | Dead Man's Switch |
| **Class** | IV (Scorched Earth) |
| **Status** | TESTED |
| **Authorization** | Crown (automated activation after threshold) |
| **Description** | Three-component system (heartbeat sender, monitor, lockdown sequence). Activates if Crown + Director unreachable for 72+ hours. Defaults to simulation mode; requires --live flag for real lockdown. |
| **Dependencies** | Python 3.10+, stdlib only. Heartbeat file, THREATS.md, LOG.md. |
| **Last tested** | 2026-02-09 — 13/13 tests passed |
| **Deployment log** | Not yet deployed (awaiting Beelink connection) |
| **Scanner exceptions** | `open()`, `sys.exit()`, `/tmp` path — documented in design doc, Crown authorized |

-----

## Development Queue

| Priority | Designation | Name | Class | Notes |
|----------|-------------|------|-------|-------|
| 1 | ~~S9-W-001~~ | ~~Tripwire Alpha~~ | ~~I~~ | **BUILT** — moved to Active Registry |
| 2 | S9-W-002 | Honeypot Submitter | I | Fake brief that only an attacker probing the system would attempt |
| 3 | S9-W-003 | Tar Pit | II | Slow-response system for automated probes |
| 4 | S9-W-004 | Sybil Bait | II | Counter-Sybil trap submissions |
| 5 | S9-W-005 | Scam Takedown Kit | III | Evidence bundle generator for platform abuse reports |
| 6 | ~~S9-W-006~~ | ~~Dead Man's Switch~~ | ~~IV~~ | **BUILT** — moved to Active Registry |

Weapons are developed in order of priority unless an active
threat changes the sequence. The Director may reprioritize
at any time. Class III+ development requires Crown awareness
(not approval — the Director builds what the Director sees
fit, but the Crown should know what's being built before it
needs to be deployed).

-----

## Retired Weapons

*None.*

-----

*Classification: CROWN EYES ONLY*
