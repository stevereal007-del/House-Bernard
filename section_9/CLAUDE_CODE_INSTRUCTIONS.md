# Section 9 — Claude Code Work Instructions

**Classification:** CROWN EYES ONLY
**Purpose:** Step-by-step procedures for using Claude Code
on the Beelink EQ13 to build, test, deploy, and maintain
the Section 9 module within the House Bernard repository.
**Audience:** HeliosBlade (Crown / acting Director)
**Version:** 1.0
**Date:** February 2026

-----

## 0. Before You Start

### What This Document Is

This is the hands-on technical companion to
`section_9/WORK_INSTRUCTIONS.md`. That document tells you
WHAT to do. This document tells you HOW to do it with
Claude Code on the Beelink.

### Prerequisites

|Requirement                        |How to verify                  |
|-----------------------------------|-------------------------------|
|Beelink EQ13 running Ubuntu 24.04  |`lsb_release -a`               |
|WSL2 (if running from Windows side)|`wsl --version`                |
|Claude Code installed              |`claude --version`             |
|Node.js 22+                        |`node --version`               |
|Docker running                     |`docker ps`                    |
|Git configured with SSH key        |`ssh -T git@github.com`        |
|House Bernard repo cloned          |`ls ~/House-Bernard/section_9/`|
|Python 3.10+                       |`python3 --version`            |
|Ollama running with models pulled  |`ollama list`                  |

If any prerequisite fails, run through the deployment
script first: `infrastructure/deployment/deploy_achillesrun.sh`

### Starting Claude Code

From the Beelink terminal (or WSL2 terminal):

```bash
cd ~/House-Bernard
claude
```

Claude Code will open in the repo root. It can see all
files, run commands, edit code, and execute tests. It
cannot access the internet unless you've configured
network access.

### The CLAUDE.md File

The `CLAUDE.md` file in the repo root is Claude Code's
project-level instruction file — it reads this automatically
on every session start. See `~/House-Bernard/CLAUDE.md`.

-----

## 1. Initialize Section 9 (WI-001)

Run this once to stand up Section 9 from the repo.
See session script in WORK_INSTRUCTIONS.md WI-001.

**Commit message convention for Section 9:**
Always prefix with `sec9:` — this makes it easy to filter
Section 9 activity in git log. Keep messages vague enough
that they don't reveal operational details.

-----

## 2. Build a Weapon (WI-002)

Five-phase workflow: Design Doc → Build → Test → Register → Commit.
Each weapon follows the same pattern. See WORK_INSTRUCTIONS.md WI-002.

All weapons must:
- Pass security_scanner.py
- Have no external dependencies beyond stdlib
- Fail to PASSIVE, never fail to ACTIVE
- Run in Docker for production testing

-----

## 3-10. Operational Procedures

See WORK_INSTRUCTIONS.md for full procedures:
- WI-003: Threat Assessment
- WI-004: Intelligence Collection
- WI-006: Quarterly Review
- WI-007: Incident Response
- WI-008: Dead Man's Switch
- WI-009: Parallel Construction Handoff

-----

## Git Workflow for Section 9

### Commit Conventions

|Prefix       |Use for                              |
|-------------|-------------------------------------|
|`sec9:`      |All Section 9 changes                |
|`sec9-w:`    |Weapon-specific changes              |
|`sec9-t:`    |Threat intelligence updates          |
|`sec9-ops:`  |Operational log updates              |
|`sec9-admin:`|Administrative (budget, review, etc.)|

### What NOT to Put in Commit Messages

- Threat actor names or identifiers
- Specific attack details
- Weapon capabilities or techniques
- Intelligence source descriptions

-----

## File Paths Quick Reference

```
~/House-Bernard/
├── CLAUDE.md                              ← Claude Code reads this on start
├── section_9/
│   ├── CHARTER.md                         ← The law
│   ├── README.md                          ← Public-facing (says nothing)
│   ├── WORK_INSTRUCTIONS.md               ← What to do
│   ├── CLAUDE_CODE_INSTRUCTIONS.md        ← How to do it (this file)
│   ├── weapons/
│   │   ├── REGISTRY.md                    ← Weapons inventory
│   │   ├── S9-W-XXX_name.md              ← Design docs
│   │   ├── S9-W-XXX_name.py             ← Weapon code
│   │   ├── S9-W-XXX_test.py             ← Weapon tests
│   │   └── S9-W-XXX_test_results.json   ← Test output
│   ├── operations/
│   │   ├── LOG.md                         ← Append-only audit trail
│   │   ├── heartbeat.json                 ← Dead Man's Switch pulse
│   │   ├── REVIEW_YYYY_QX.md             ← Quarterly reviews
│   │   ├── INCIDENT_YYYY-MM-DD_name.md   ← Incident reports
│   │   └── HANDOFF_S9-T-XXX_sanitized.md ← Parallel construction briefs
│   └── intelligence/
│       ├── THREATS.md                     ← Threat register
│       ├── collection_log.jsonl           ← OSINT collection record
│       ├── osint_monitor.py               ← Automated OSINT script
│       └── S9-T-XXX_name/               ← Per-threat intel folders
├── security/
│   └── security_scanner.py                ← Run weapons through this
├── airlock/
│   └── airlock_monitor.py                 ← Log source for Tripwire
└── openclaw/
    └── openclaw.json                      ← Cron jobs configured here
```

-----

*Classification: CROWN EYES ONLY*
*Section 9 — The Sword of the House*
*Ad Astra Per Aspera*
