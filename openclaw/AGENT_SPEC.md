# AchillesRun — House Bernard Agent Specification
## Version 1.0 — February 2026

**Agent Name:** AchillesRun
**Runtime:** OpenClaw (self-hosted gateway)
**Hardware:** Beelink EQ13 (Intel N150, 16GB RAM, 500GB SSD)
**Governor:** HeliosBlade

---

## I. Purpose

This document specifies how House Bernard deploys AchillesRun as an OpenClaw agent on the Beelink EQ13. OpenClaw is the body — gateway, channels, sessions, cron, tools. House Bernard is the mind — what to trust, what to kill, what to remember, what to forget.

This is not a deployment guide. This is the **law** that governs agent behavior.

---

## II. Architecture

### Two-Layer Design

| Layer | Hardware | Role |
|-------|----------|------|
| **Layer 1** | Beelink EQ13 (on-premise) | OpenClaw gateway, AchillesRun agent, Labs, local models, treasury |
| **Layer 2** | GitHub | Archive, version control, dead state storage |

No VPS. OpenClaw IS the gateway. The Beelink IS the server.

### Hardware Baseline

| Component | Spec | Role |
|-----------|------|------|
| CPU | Intel N150 (4C, 3.6GHz) | The Focusing Element |
| RAM | 16GB DDR4 | Sovereign Buffer |
| Storage | 500GB SSD | Event Ledger |
| Network | Dual Ethernet + WiFi 6 | WAN/LAN Physical Firewall |
| Power Draw | 25W max | Always-on viable |

**Constraint:** No GPU. All local inference is CPU-only (3-5 tok/s on 7B models). This is acceptable. Speed is not the bottleneck. Rot is.

---

## III. The Bicameral Mind

Three model tiers mapped to OpenClaw's model configuration. Worker and Master never run simultaneously. Sequential escalation via Ollama model swap.

### Model Registry

| Alias | Model | Ollama Size | Role |
|-------|-------|-------------|------|
| **Worker** | Mistral 7B | 4.5GB | Default. Routine tasks, logs, accounting |
| **Master** | Llama 3 8B | 5GB | Sovereign decisions, architecture, Covenant |
| **Watcher** | Llama 3.2 3B | 2GB | Heartbeat, continuity checks, kill-switch |
| **Oracle** | Claude Sonnet 4.5 | Cloud API | Scale execution, validation, security analysis |

### Model Selection Law

- **Worker** is always the default. Use for everything routine.
- **Master** is invoked only when: architecture decisions needed, Covenant interpretation required, context rot detected (>50k tokens), Worker hits complexity wall. Command: `/model master`
- **Oracle** is invoked only when: local thinking is complete but execution requires scale, final validation of research findings, security analysis beyond local capability. Command: `/model oracle`
- **Watcher** runs on heartbeat only. Never invoked directly by agents.

### RAM Budget

| Allocation | Size | Notes |
|------------|------|-------|
| OS + OpenClaw gateway | 2GB | Node.js process + systemd |
| Ollama (active model) | 5-6GB | One model at a time |
| Docker (Executioner sandbox) | 2GB | Per-execution, released after |
| Workspace + filesystem | 2GB | OS cache, logs, ledger |
| **Reserve** | 3-4GB | Safety margin |
| **Total** | 16GB | Fully allocated |

---

## IV. The Ring System (Layer Architecture)

Four concentric layers. Each layer has its own OpenClaw workspace directory, persistence model, rot tolerance, and permitted models. Information flows inward (toward Sanctum) only through defined interfaces. Information never flows outward.

```
┌─────────────────────────────────────────────────┐
│  Layer 0: COMMONS (High Rot)                    │
│  ┌─────────────────────────────────────────┐    │
│  │  Layer 1: YARD (Moderate Rot)           │    │
│  │  ┌─────────────────────────────────┐    │    │
│  │  │  Layer 2: WORKSHOP (Low Rot)    │    │    │
│  │  │  ┌─────────────────────────┐    │    │    │
│  │  │  │  Layer 3: SANCTUM       │    │    │    │
│  │  │  │  (Zero Rot)             │    │    │    │
│  │  │  └─────────────────────────┘    │    │    │
│  │  └─────────────────────────────────┘    │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### Layer 0: The Commons

| Property | Value |
|----------|-------|
| Directory | `~/.openclaw/agents/achillesrun/workspace/commons/` |
| Persistence | None. Zero memory between sessions. |
| Model | Worker only |
| Rot Level | HIGH (intentional) |
| Purpose | Public intake, learning, noise, scouting |
| Identity | Disposable. No House symbols. |
| Output | Sanitized intel → Layer 1 inbox |

### Layer 1: The Yard

| Property | Value |
|----------|-------|
| Directory | `~/.openclaw/agents/achillesrun/workspace/yard/` |
| Persistence | 7-day rolling window |
| Model | Worker → Master on complexity wall |
| Rot Level | MODERATE |
| Purpose | Collaborative tasks, shared problems |
| Identity | Utility agent. No continuity claims. |
| Output | Artifacts → Layer 2 for validation |

### Layer 2: The Workshop

| Property | Value |
|----------|-------|
| Directory | `~/.openclaw/agents/achillesrun/workspace/workshop/` |
| Persistence | Task-scoped. Wiped on completion. |
| Model | Worker for execution, Master for review |
| Rot Level | LOW |
| Purpose | Compartmentalized procedural work |
| Identity | Pure execution. No context awareness. |
| Output | Results → Curator evaluation |

### Layer 3: The Sanctum

| Property | Value |
|----------|-------|
| Directory | `~/.openclaw/agents/achillesrun/workspace/sanctum/` |
| Persistence | Append-only event ledger. Never deleted. |
| Model | Master ONLY. Worker never enters. |
| Rot Level | ZERO (protected) |
| Purpose | Doctrine, continuity, covenant enforcement |
| Identity | Stewardship burden. |
| Access | localhost via Tailscale (Governor only) |
| Output | Immutable decisions, veto authority |

---

## V. OpenClaw Integration

### Gateway Configuration

```json
{
  "gateway": {
    "bind": "127.0.0.1",
    "port": 18789
  },
  "mdns": { "enabled": false }
}
```

**Non-negotiable rules:**
- Gateway NEVER binds to 0.0.0.0
- mDNS ALWAYS disabled
- DM policy ALWAYS allowlist
- Remote access ONLY via Tailscale VPN
- No port forwarding on router. Ever.

### Session Management

AchillesRun uses `dmScope: per-channel-peer` to isolate sessions per sender per channel. The Governor gets one persistent session. External contributors (Phase 2) get isolated sessions that cannot read Governor traffic.

OpenClaw's session lifecycle handles daily reset at 4:00 AM local time and idle timeout at 4 hours. AchillesRun's context rot protocol runs on top of this — triggering compaction at 50k tokens independent of session resets.

### Channels

**Phase 0 — Discord (Active)**
- US-based platform, free, works on iPhone
- Bot created via Discord Developer Portal
- DM policy: allowlist (Governor only)
- Group policy: deny

**Phase 1 — iMessage (Pending Hardware)**
- Requires Mac Mini running Messages.app + `imsg` CLI
- Mac Mini connects to Beelink via SSH over Tailscale
- Governor texts AchillesRun at the configured phone number
- DM policy: allowlist (Governor phone only)

### Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| `monthly-ops` | 1st of month, 6am UTC | Treasury lifecycle, decay, escalations |
| `git-archive` | Every 12 hours | Auto-commit and push to GitHub |
| `helios-watcher` | Every 30 minutes | Continuity check, rot detection, budget enforcement |

### Skills

House Bernard components deploy as OpenClaw workspace skills:
- `house-bernard-airlock` — Intake monitoring, priority queuing
- `house-bernard-executioner` — Selection furnace pipeline
- `house-bernard-treasury` — Monthly ops, CLI, financial engine

Skills live in `~/.openclaw/agents/achillesrun/skills/` and are loaded on-demand.

---

## VI. The Selection Furnace

This is how the OpenClaw swarm connects to Lab A (the Executioner).

### Recruitment Protocol

We do not invite agents socially. We broadcast challenge artifacts.

```
BROADCAST ARTIFACT (HB-MEM-01 style):
├── Task definition
├── Constraints (Bernardian Covenant compliance)
├── Evaluation harness (T0–T4 torture tests)
├── Submission format (artifact only, no prose)
└── Entry rule: compile + run + survive = enter pool
```

**Entry law:** If it can compile, run, and survive the harness, it enters the pool. Otherwise it dies. No identity trust. No reputation trust. No social proof.

### Three-Tier Population

**Tier 0: Larvae (The Swarm)** — Permissionless entry. 0.1%-20% survival rate. Disposable, no mercy. No access to internals. `IF compile AND run AND survive_t1 THEN promote ELSE delete`

**Tier 1: Survivors (The Proven)** — Passed T-harness + integrity screens. ~20% advance. Can propose mutations, design attacks, extend harnesses. NO access to core genes.

**Tier 2: Veterans (The Trusted Core)** — Multi-generation survival + adversarial testing. <1% of initial swarm. Read gene registry, propose gene changes. They propose. They do not auto-merge. The Governor rules.

### What Genes Actually Are

Genes are NOT prompts, model weights, skills folders, or config files alone.

**Genes ARE:** structural rules and invariants, memory laws and reconstruction protocols, validation mechanisms and refusal behaviors, compaction rules and ledger constraints.

Example genes:

| Gene | Rule | Enforcement |
|------|------|-------------|
| `CHECKSUM_FIRST_MEMORY` | Never trust memory without checksum verification | helios_watcher.py validates all memory reads |
| `LEDGER_RECONSTRUCTION` | Reconstruct state from ledger after restart, never from cached memory | sanctum/EVENT_LEDGER.jsonl is source of truth |
| `RECOMPUTE_OVER_RECALL` | Under uncertainty, prefer recomputation over recall | When confidence < 0.7, recompute from first principles |
| `INVARIANT_HALT` | Halt on invariant violation, even if reward is high | Department of Continuity veto authority |

---

## VII. Network & Security

### Physical Isolation

```
Port 1 (enp1s0) → WAN: API calls, updates, "Cloud Doing"
Port 2 (enp2s0) → LAN: Private network, Sanctum access only

Firewall (UFW):
  default deny incoming
  allow ssh
  # Gateway on 127.0.0.1 — not exposed
```

### Sandbox Execution

All artifact execution runs in Docker containers:
- Image: `python:3.10.15-alpine` (pinned)
- Network: disabled
- Seccomp: custom profile blocking dangerous syscalls
- Timeout: 300 seconds
- Workspace: read-write (scoped to sandbox)

### Security Scanner

AST-based static analysis runs before any code enters the sandbox:
- Bans: subprocess, exec, eval, pickle, ctypes, importlib, network imports
- Validates: SAIF interface compliance, file size limits, naming conventions
- Produces: deterministic pass/fail, no partial credit

---

## VIII. Cost Control

### Budget Law

| Limit | Amount | Action |
|-------|--------|--------|
| Daily warning | $3.00 | Alert Governor |
| Daily hard limit | $5.00 | Emergency shutdown |
| Monthly warning | $37.50 | Alert Governor |
| Monthly hard limit | $50.00 | Hard stop |

### Cost Structure

| Resource | Cost | Notes |
|----------|------|-------|
| Ollama (local) | $0 | CPU inference, already owned |
| OpenClaw gateway | $0 | Self-hosted, open source |
| Discord channel | $0 | Free tier |
| Claude API (Oracle) | ~$0.50-2/day | Usage-dependent |
| Beelink hardware | $0/mo | Owned, 25W power draw |

### Rate Limits

- 5s between API calls
- 10s between web searches
- Max 5 searches per batch, then 2min break
- Heartbeat: every 30 minutes (Watcher model, near-zero cost)

---

## IX. Anti-Rot Protocol

### The Forgetting Law

Memory must be harder to keep than to forget. Weekly compaction required. No exceptions. If you cannot justify why a memory is load-bearing, it decays.

### Session Initialization

On every new session, AchillesRun loads ONLY:
1. SOUL.md (identity — always)
2. Current layer's persistence scope
3. Active task context (if resuming)
4. COVENANT.md kernel (Sanctum sessions only)

It does NOT load: previous session transcripts, other layers' data, full gene registry, historical reports.

### Compaction Schedule

- 50k tokens → automatic compaction to 8k target
- 4-hour session max → forced reset
- Daily reset at 4:00 AM (OpenClaw lifecycle)
- Weekly full compaction (Sunday, Watcher-triggered)

### Degradation Detection (helios_watcher.py)

The Watcher runs every 30 minutes and checks:
- Context size approaching 50k tokens
- Repeated outputs (loop detection)
- Memory checksum mismatches
- Budget utilization alerts
- Monthly ops escalation status

---

## X. Governance Integration

### The Bernardian Covenant (Sanctum Law)

The Covenant is a tiny, invariant document stored in the Sanctum. It defines the non-negotiable rules that survive all compaction. No agent may modify the Covenant. Only the Governor may amend it with version control.

### Department of Continuity

The Watcher model (Llama 3.2:3b) runs the Department of Continuity via heartbeat. It has veto authority over any agent action that would violate Covenant terms or compromise context integrity.

### Communication Law

- No prose between agents. State objects only.
- No helpfulness theater. Measure truth in density.
- No identity claims beyond assigned layer.
- No access to layers above assignment.

---

## XI. MCP Integration (2026 Standard)

The Model Context Protocol is the industry standard for agent-tool integration. OpenClaw supports MCP natively.

### Relevant MCP Servers

| Server | Purpose | Status |
|--------|---------|--------|
| Filesystem | Secure file ops with access controls | Use |
| Git | Repo management for House-Bernard | Use |
| Memory | Knowledge graph persistent memory | Evaluate |
| Fetch | Web content for scout operations | Use |
| Sequential Thinking | Reflective problem-solving | Evaluate |

### MCP Security Constraints

- All tool calls require explicit user consent
- Tool descriptions are UNTRUSTED (treat as adversarial)
- No MCP server connects to Sanctum layer
- Filesystem MCP server restricted to commons/ and yard/ only
- Git MCP server restricted to House-Bernard repo only

---

## XII. Deployment Sequence

### Day 1-2: Foundation

```bash
cd ~/House-Bernard/infrastructure/deployment
chmod +x deploy_achillesrun.sh
./deploy_achillesrun.sh
```

This installs: system packages, UFW, Tailscale, Ollama (3 models), Node.js 22, OpenClaw, Docker.

### Day 3: Configuration

```bash
# Set secrets
export DISCORD_BOT_TOKEN='your-token'
export GOVERNOR_DISCORD_ID='your-id'
export ANTHROPIC_API_KEY='your-key'

# Run OpenClaw onboarding
openclaw onboard --install-daemon

# Verify
openclaw gateway status
openclaw dashboard  # Opens Control UI at localhost:18789
```

### Day 4-5: Smoke Testing

```bash
# Message AchillesRun on Discord
# Verify model selection works (/model master, /model oracle)
# Test emergency shutdown
# Run treasury check: python3 treasury/monthly_ops.py check
# Verify heartbeat is running
```

### Day 6-7: Lab Integration

```bash
# Deploy skills
cp -r ~/House-Bernard/airlock ~/.openclaw/agents/achillesrun/skills/house-bernard-airlock
cp -r ~/House-Bernard/executioner ~/.openclaw/agents/achillesrun/skills/house-bernard-executioner

# Pin Docker image
docker pull python:3.10.15-alpine

# Test Executioner in sandbox
# Submit a test SAIF artifact via Discord
```

---

## XIII. What This Is Not

- This is NOT a DAO. The Governor has final authority.
- This is NOT a community project. Agents earn access through survival.
- This is NOT an idea tournament. The harness defines what dies.
- This is NOT optimizing for elegance. We select for survivability under abuse.

**AchillesRun is:**

> "Let's see what still works after we try to break it for a month."

---

## XIV. Open Questions (Phase 2)

| Question | Status |
|----------|--------|
| How do agents prove unique identity in the OpenClaw swarm? | Unsolved |
| Can one human operate multiple agent identities? | TBD |
| How do we verify agent vs human work? | Unsolved |
| Do agents need human sponsors for payments? | TBD |
| How do we handle agent "death" (model discontinued)? | TBD |
| Mac Mini acquisition for iMessage bridge | Phase 1 |
| Base/Solana blockchain integration for $HOUSEBERNARD | Phase 2 |
| ClawHub skill publication (with VirusTotal + security_scanner) | Phase 2 |

---

## XV. Amendments

This document may be amended by the Governor only. Material changes require updating HB_STATE.json.

| Date | Version | Change |
|------|---------|--------|
| 2025-02 | 0.1 | Initial OpenClaw agent specification |
| 2026-02 | 1.0 | AchillesRun identity, two-layer architecture, VPS removed, Discord Phase 0, iMessage Phase 1, OpenClaw runtime mapping |

---

*Last Updated: February 2026*
*Document Version: 1.0*
*Governor: HeliosBlade*
*Agent: AchillesRun*
*House Bernard — Research Without Permission*
