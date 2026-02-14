# House Bernard — AchillesRun Agent

## What This Is

AchillesRun is House Bernard deployed as an OpenClaw agent. OpenClaw is the body — gateway, channels, sessions, cron. House Bernard is the mind — what to trust, what to kill, what to remember, what to forget.

The Beelink EQ13 runs the OpenClaw gateway. AchillesRun runs inside it. The Crown communicates via Google Chat (Phase 0) or Discord (Phase 1 fallback).

## Files

| File | Purpose |
|------|---------|
| `AGENT_SPEC.md` | The law governing AchillesRun's behavior, model selection, layers, and security |
| `SOUL.md` | OpenClaw system prompt — AchillesRun's identity and operating principles |
| `openclaw.json` | OpenClaw configuration — models, channels, sessions, cron, budget |
| `build.py` | Static dashboard builder (reads HB_STATE.json, outputs HTML) |
| `templates/` | HTML templates for the dashboard |

## Architecture Mapping

| House Bernard Concept | OpenClaw Implementation |
|----------------------|------------------------|
| Bicameral Mind (Worker/Master/Oracle) | OpenClaw model config with Ollama aliases |
| Ring System (Commons/Yard/Workshop/Sanctum) | OpenClaw workspace directories |
| Selection Furnace | OpenClaw skills running Airlock→Executioner→Splicer |
| Monthly Ops | OpenClaw cron job (1st of month, 6am UTC) |
| Heartbeat / Watcher | OpenClaw heartbeat config (30min, Llama 3.2:3b) |
| Crown Contact | OpenClaw channel (Google Chat DM / Discord fallback) |
| Session Isolation | OpenClaw `dmScope: per-channel-peer` |
| Swarm (Phase 2) | OpenClaw multi-agent routing |

## Quick Start

```bash
# On the Beelink:
cd ~/House-Bernard/infrastructure/deployment
chmod +x deploy_achillesrun.sh
./deploy_achillesrun.sh

# Then:
export DISCORD_BOT_TOKEN='your-token'
export CROWN_DISCORD_ID='your-id'
export ANTHROPIC_API_KEY='your-key'
openclaw onboard
```

## Channels

**Phase 0 (now):** Google Chat DM — Crown only, allowlist enforced (free with personal Gmail).
**Phase 1:** Discord DM — fallback channel, Crown only.
**Phase 1:** Discord — free fallback if Google Chat has issues.

---

*House Bernard — Research Without Permission*
