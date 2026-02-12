---
name: house-bernard-airlock
description: Monitor the House Bernard airlock inbox for incoming artifacts (ZIP submissions). Run security scanning, quarantine threats, and route clean artifacts to the executioner pipeline. Use when processing new contributor submissions, checking airlock status, or managing the intake queue.
---

# Airlock Monitor

Watches the airlock inbox directory for incoming ZIP artifacts. Pipeline:
1. New file detected in inbox
2. Security scanner runs (`security/security_scanner.py`) — AST analysis for dangerous patterns
3. REJECT/QUARANTINE → moved to quarantine dir with JSON verdict
4. CLEAN → extracted to sandbox, forwarded to executioner

## Running the Airlock

```bash
cd ~/House-Bernard
python3 airlock/airlock_monitor.py --inbox /path/to/inbox --quarantine /path/to/quarantine
```

Default paths (relative to repo root):
- Inbox: watched directory (configurable)
- Quarantine: sibling `quarantine/` directory
- Executioner: `executioner/executioner_production.py`
- Security scanner: `security/security_scanner.py`

## Key Behaviors

- Uses `watchdog` library for filesystem monitoring
- Security scan runs BEFORE executioner (never skip)
- All verdicts logged as structured JSON
- Paths resolve relative to repo root, not hardcoded

## Scripts

- `scripts/airlock_monitor.py` — Main monitor (symlink to `airlock/airlock_monitor.py`)

## Integration

The airlock is the entry point for all external code entering House Bernard.
Nothing reaches the executioner without passing the security scanner first.
Quarantined artifacts require Crown review before re-processing.
