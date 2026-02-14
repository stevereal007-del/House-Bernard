# S9-W-006: Dead Man's Switch

## Classification
Class: IV (Scorched Earth)
Authorization: Crown (automated activation after threshold)
Status: TESTED

## Purpose
Automated response system that activates if both the Crown
and Director are simultaneously unreachable for an extended
period. Ensures House Bernard enters a safe defensive posture
rather than operating without governance.

## Technical Design
Three components:

1. **Heartbeat sender** — Writes a proof-of-life signal every
   12 hours to a local file. Content: timestamp + SHA256 hash
   of current THREATS.md + incrementing sequence number.

2. **Heartbeat monitor** — Checks the heartbeat file on a
   schedule. Counts missed heartbeats (older than 13 hours =
   one miss). Alert thresholds:
   - 3 missed: WARNING (log)
   - 5 missed: CRITICAL (alert file)
   - 6 missed: ACTIVATION (lockdown sequence)

3. **Lockdown sequence** — When activated:
   - Writes LOCKDOWN status to heartbeat
   - Creates cryptographic snapshot (tar + SHA256 of repo)
   - Logs the snapshot hash
   - Requires --live flag for real execution; defaults to
     simulation mode

## Deployment Requirements
- Python 3.10+, stdlib only
- Must fail safely: crash = no lockdown triggered
- Must have --live flag guard on lockdown

## Security Scanner Exceptions

This weapon is Crown tooling (not a SAIF artifact). The following
security scanner findings are authorized exceptions:

| Finding | Component | Reason | Authorized by |
|---------|-----------|--------|---------------|
| `open()` — banned function | heartbeat, monitor, lockdown | Required to read/write heartbeat JSON and log files | Crown (HeliosBlade) |
| `sys.exit()` — banned function | monitor | CLI exit codes for status reporting | Crown (HeliosBlade) |
| `/tmp` path in string | heartbeat | Default backup path for heartbeat redundancy | Crown (HeliosBlade) |

These functions are necessary for the weapon's core operation.
All three components run in controlled environments under Crown
authority. The --live flag guard on lockdown prevents accidental
activation.

## Risks
- False activation from downtime/travel (mitigated by 72h threshold)
- Lockdown in simulation mode reveals nothing harmful
- Live lockdown is irreversible until Crown authenticates
