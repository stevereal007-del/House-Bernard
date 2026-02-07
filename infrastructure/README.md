# Infrastructure

Three-Layer Fortress Architecture for House Bernard.

## Architecture

```
┌──────────────────────────────────────┐
│  LAYER 1: 1984 Hosting VPS (Iceland) │
│  intake_server.py — public shield    │
│  Accepts submissions, stores to      │
│  staging/, serves results/           │
│  NEVER processes artifacts           │
└──────────────┬───────────────────────┘
               │ Tailscale VPN (encrypted)
               │ rsync pull/push
┌──────────────▼───────────────────────┐
│  LAYER 2: Beelink EQ13 (home)       │
│  Lab A (memory) + Lab B (security)   │
│  Airlock → Scanner → Executioner     │
│  Local Ollama models                 │
│  ALL processing happens here         │
└──────────────┬───────────────────────┘
               │ git push (twice daily)
┌──────────────▼───────────────────────┐
│  LAYER 3: GitHub                     │
│  Archive / version control           │
│  Dead state storage                  │
│  Public README, private genetics     │
└──────────────────────────────────────┘
```

## Contents

### vps/
| File | Purpose |
|------|---------|
| `intake_server.py` | HTTP server for SAIF artifact submissions |
| `vps_setup.sh` | One-time VPS provisioning (UFW, Tailscale, fail2ban, systemd) |
| `vps_sync.sh` | Beelink-side sync script (pull artifacts, push results) |

### deployment/
| File | Purpose |
|------|---------|
| `fortress_deploy.sh` | Beelink-side deployment (cron, systemd timers, integration) |

## Data Flow

1. Submitter → POST artifact to VPS `:8443/submit`
2. VPS validates (size, format, rate limit) → stores in `staging/`
3. Beelink cron pulls `staging/*.zip` → local `inbox/`
4. Airlock detects → moves to `sandbox/`
5. Security scanner (I1) → Executioner (T0-T4) or Lab B (I2-I6)
6. Results → local `results/`
7. Beelink cron pushes results → VPS `results/`
8. Beelink timer archives to GitHub (twice daily)

## Security Rules

- VPS NEVER executes artifacts
- Beelink NEVER exposes ports to the internet
- All VPS ↔ Beelink traffic goes through Tailscale
- SSH is key-only, no passwords
- fail2ban protects both SSH and intake server

---

*House Bernard — The Shield Wall Holds*
