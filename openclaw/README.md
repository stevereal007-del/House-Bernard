# OpenClaw — House Bernard Integration

## Overview

This directory contains the specification, configuration, and tooling for deploying
OpenClaw agents within the House Bernard sovereign Dark Lab architecture.

## Files

| File | Purpose |
|------|---------|
| `AGENT_SPEC.md` | The law. Complete agent architecture, security, cost control, and selection furnace integration. |
| `build.py` | OpenClaw static site builder (public-facing results viewer) |
| `openclaw.json` | Reference configuration for Beelink EQ13 deployment |
| `SOUL.md` | Agent behavioral directives (loaded at session init) |

## Architecture

```
OpenClaw Gateway (localhost:18789)
        │
        ├── Layer 0: Commons  → Scouts, intake, noise
        ├── Layer 1: Yard     → Collaborative work
        ├── Layer 2: Workshop → Executioner integration
        └── Layer 3: Sanctum  → Covenant enforcement
```

## Quick Reference

- **Spec:** Read `AGENT_SPEC.md` before touching anything
- **Models:** Ollama local (Mistral 7B worker, Llama 3 8B master)
- **Cost:** $0-5/month (97% reduction vs standard OpenClaw)
- **Security:** Localhost-only, Tailscale VPN, UFW firewall
- **Version:** OpenClaw v2026.2.2+ required

## Integration with House Bernard

OpenClaw agents submit SAIF v1.1 artifacts to the Airlock (`~/.openclaw/inbox/`).
The Executioner processes them through T0-T4. Survivors are spliced.
Genes are promoted to the Sanctum's append-only ledger.

The agent does not judge quality. The harness defines what dies.
