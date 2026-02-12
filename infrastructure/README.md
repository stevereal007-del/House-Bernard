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
| `deployment/deploy_achillesrun.sh` | Main deployment: packages, firewall, Tailscale, Ollama, OpenClaw, repo (Beelink + WSL2) |
| `deployment/achillesrun_start.sh` | WSL2 service startup (Ollama + Docker + gateway) |
| `deployment/wsl2_docker_setup.sh` | WSL2 Docker setup (Docker Desktop or docker-ce) |
| `deployment/wslconfig.template` | Windows-side `.wslconfig` for memory/CPU allocation |
| `deployment/post_gateway_setup.sh` | Post-deploy: cron jobs, channels, smoke tests |
| `deployment/verify_deployment.py` | 12-check verification (includes WSL2-specific checks) |
| `deployment/.env.template` | Environment variables template |

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

## WSL2 Deployment

AchillesRun supports WSL2/Ubuntu 24.04 as a development target alongside the production Beelink EQ13.

### Quick Start (WSL2)

```bash
# 1. Configure Windows-side memory (copy to %USERPROFILE%\.wslconfig)
#    See deployment/wslconfig.template

# 2. Run the deployment script
cd ~/House-Bernard/infrastructure/deployment
chmod +x deploy_achillesrun.sh
./deploy_achillesrun.sh --wsl2

# 3. Set environment variables
export ANTHROPIC_API_KEY='sk-ant-...'

# 4. Start services
~/.openclaw/achillesrun_start.sh

# 5. Run post-gateway setup (once, after gateway starts)
./post_gateway_setup.sh

# 6. Verify
python3 verify_deployment.py
```

### WSL2 vs Beelink Differences

| Component | Beelink (Production) | WSL2 (Development) |
|-----------|---------------------|---------------------|
| Firewall | UFW (default deny) | Windows Defender |
| Remote access | Tailscale VPN | Local terminal |
| Service mgmt | systemd | achillesrun_start.sh (or systemd if enabled) |
| Docker | docker.io (apt) | Docker Desktop or docker-ce |
| Auto-start | systemd enable | .bashrc hook |

### Enabling systemd on WSL2

Modern WSL2 supports systemd natively. Add to `/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Then restart WSL: `wsl --shutdown && wsl`

With systemd enabled, the deploy script will install OpenClaw as a systemd service (same as Beelink).

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
