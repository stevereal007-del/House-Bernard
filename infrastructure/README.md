# House Bernard Infrastructure

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: Beelink EQ13 (on-premise)                  │
│  OpenClaw Gateway + AchillesRun Agent                │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Ollama   │  │  Docker   │  │  OpenClaw Gateway │  │
│  │ Worker    │  │ Sandbox   │  │  :18789 localhost │  │
│  │ Master    │  │ Executor  │  │  Sessions/Memory  │  │
│  │ Watcher   │  │ Lab A/B   │  │  Cron/Heartbeat   │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                      │
│  Google Chat ←→ Crown phone                        │
│  Discord ←→ Crown (fallback)                        │
└─────────────────────────────────────┬───────────────┘
                                      │ git push
                                      ▼
┌─────────────────────────────────────────────────────┐
│  LAYER 2: GitHub                                     │
│  Archive, version control, dead state storage        │
└─────────────────────────────────────────────────────┘
```

## Two-Layer Design

**No VPS.** OpenClaw IS the gateway. The Beelink IS the server.

OpenClaw provides everything the VPS was designed to do: public intake (via messaging channels), session isolation (per-channel-peer), rate limiting, and always-on availability (systemd daemon). Adding a separate VPS would only add cost, latency, and attack surface.

| Layer | Hardware | Role |
|-------|----------|------|
| **Layer 1** | Beelink EQ13 (N150, 16GB, 500GB SSD) | OpenClaw gateway, AchillesRun agent, Labs, local models, treasury |
| **Layer 2** | GitHub | Archive, version control, dead state storage |
| **Layer 3** | Google Cloud (house-bernard) | Gmail, Drive, Sheets, Docs, Calendar, Chat, Cloud Logging |

## Files

| File | Purpose |
|------|---------|
| `GOOGLE_CLOUD.md` | Google Cloud project config, enabled APIs, authentication, cost controls |
| `deployment/deploy_achillesrun.sh` | One-shot Beelink setup: packages, firewall, Tailscale, Ollama, OpenClaw, repo clone |

## Data Flow

1. Crown → sends message via Google Chat (or Discord fallback)
2. OpenClaw gateway receives → routes to AchillesRun agent
3. AchillesRun processes locally (Worker/Master on Ollama)
4. If scale needed → Oracle call to Claude API
5. Results written to workspace → archived to GitHub via cron

For SAIF artifact submissions (from external contributors):
1. Contributor submits via approved channel (Google Chat or Discord DM)
2. OpenClaw session isolation separates from Crown traffic
3. Airlock picks up submission from agent workspace
4. Executioner pipeline runs in Docker sandbox
5. Results logged to Ledger, pushed to GitHub

## Security Model

- Gateway binds to `127.0.0.1` only — never exposed to internet
- Remote access via Tailscale VPN only
- mDNS disabled
- DM policy: allowlist (Crown only by default)
- Docker sandbox for all artifact execution
- Seccomp profile blocks dangerous syscalls
- UFW default deny incoming

## Future Possibilities

- **iMessage channel:** Would require a Mac Mini running Messages.app
  with SSH bridge to the Beelink over Tailscale. Not currently owned
  or planned. Can be revisited if needed.

---

*House Bernard — Research Without Permission*
