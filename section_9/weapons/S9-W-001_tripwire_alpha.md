# S9-W-001: Tripwire Alpha

## Classification
Class: I (Passive)
Authorization: Director (autonomous)
Status: TESTED

## Purpose
Monitor Airlock submission logs for anomalous patterns that
indicate probing, flooding, or reconnaissance. Tripwire Alpha
is a passive detection capability — it observes and alerts,
it never blocks or modifies.

## Technical Design
Reads Airlock log JSONL (one JSON object per line). Maintains
rolling windows per contributor identity and detects four
anomaly types:

1. **Rate spike** — Submission rate per identity exceeds 3x
   the rolling 7-day average
2. **Cluster detection** — Multiple identities submitting
   structurally similar artifacts within a short window
3. **Time anomaly** — Submissions at unusual hours relative
   to the contributor's established pattern
4. **Sequential probing** — Submissions that systematically
   test boundary conditions

## Inputs
- Airlock log files (JSONL format) via stdin or file path
- Each line: `{"timestamp": "ISO8601", "identity": "...",
  "artifact": "...", "verdict": "...", "size": N, ...}`

## Outputs
- Alert JSON to stdout (one per alert)
- Format: `{"weapon": "S9-W-001", "timestamp": "...",
  "alert_type": "...", "severity": "...", ...}`

## Deployment Requirements
- Python 3.10+, stdlib only
- < 100MB RAM, < 5% CPU sustained
- Must fail to passive (crash = no alerts, never blocks Airlock)

## Test Plan
- Unit tests for each detection function
- Integration test with sample JSONL
- False positive test with normal activity
- False negative test with known anomalies
- Resource test with 1000-line synthetic log
- Fail-safe test with malformed input

## Security Scanner Exceptions

This weapon is Crown tooling (not a SAIF artifact). The following
security scanner findings are authorized exceptions:

| Finding | Reason | Authorized by |
|---------|--------|---------------|
| `open()` — banned function | Required to read JSONL log files from disk | Crown (HeliosBlade) |
| `sys.exit()` — banned function | CLI exit codes for fail-to-passive behavior | Crown (HeliosBlade) |

These functions are necessary for the weapon's core operation.
The weapon runs in a controlled environment under Director
authority and does not process untrusted input from the Airlock
pipeline (it reads Airlock *logs*, not submissions).

## Risks
- False positives could waste investigation time
- Tuning thresholds too low = noise; too high = missed threats

## Proportionality Notes
Appropriate for S1-S2 detection. Produces alerts only — no
action taken. Alerts feed threat assessments (WI-003).
