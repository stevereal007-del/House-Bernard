# House Bernard OpenClaw Agent Specification
## Version 0.1 — February 2026

> **Agents may write tools, but they may not write rules.**

---

## I. Purpose

This document specifies how House Bernard deploys OpenClaw agents on the Beelink EQ13
("The Lens") to run the sovereign Dark Lab. It covers architecture, security, cost control,
the selection furnace integration, and the multi-tier agent population model.

This is not a deployment guide. This is the **law** that governs agent behavior.

---

## II. Hardware Baseline

| Component       | Spec                         | Role                      |
|-----------------|------------------------------|---------------------------|
| CPU             | Intel N150 (4C, 3.6GHz)      | The Focusing Element      |
| RAM             | 16GB DDR4                    | Sovereign Buffer          |
| Storage         | 500GB SSD                    | Event Ledger              |
| Network         | Dual Ethernet + WiFi 6       | WAN/LAN Physical Firewall |
| Power Draw      | 25W max                      | Always-on viable          |

**Constraint:** No GPU. All local inference is CPU-only (3-5 tok/s on 7B models).
This is acceptable. Speed is not the bottleneck. Rot is.

---

## III. The Bicameral Mind

Three local models plus one cloud oracle. No other models permitted without
Governor amendment to this document.

### Model Registry

| Alias     | Model              | RAM    | Role                          | Cost     |
|-----------|--------------------|--------|-------------------------------|----------|
| `worker`  | Ollama/Mistral 7B  | ~5GB   | 90% of tasks, 24/7 resident  | $0       |
| `master`  | Ollama/Llama 3 8B  | ~6GB   | Sovereign decisions only      | $0       |
| `watcher` | Ollama/Llama 3.2 3B| ~2GB   | Heartbeat monitoring          | $0       |
| `oracle`  | Claude Sonnet 4.5  | Cloud  | Validation when local fails   | ~$3-5/mo |

### Model Selection Law

```
DEFAULT: worker

ESCALATE TO master WHEN:
  - Architecture decisions
  - Covenant interpretation
  - Context size > 50k tokens
  - Worker produces low-confidence output
  - Invariant violation detected

ESCALATE TO oracle WHEN:
  - Local thinking complete, execution requires scale
  - Final validation of research findings
  - Security analysis requiring current knowledge
  - Master fails on complexity

NEVER:
  - Use oracle for heartbeats
  - Use oracle for routine file operations
  - Use master for log summaries or accounting
  - Run two large models simultaneously (RAM ceiling)
```

### RAM Budget

Peak simultaneous usage must not exceed 14GB (2GB reserved for OS + overhead).

```
worker (5GB) + watcher (2GB) + OS (2GB) = 9GB  ← Normal operation
master (6GB) + watcher (2GB) + OS (2GB) = 10GB ← Sovereign mode (worker unloaded)
```

Worker and master never run simultaneously. Ollama handles model swap.

---

## IV. The Ring System (Layer Architecture)

Four concentric layers. Each layer has its own workspace, persistence model,
rot tolerance, and permitted models. Information flows inward (toward sanctum)
only through defined interfaces. Information never flows outward.

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

| Property     | Value                                    |
|--------------|------------------------------------------|
| Directory    | `~/.openclaw/workspaces/commons/`        |
| Persistence  | None. Zero memory between sessions.      |
| Model        | Worker only                              |
| Rot Level    | HIGH (intentional)                       |
| Purpose      | Public intake, learning, noise, scouting |
| Identity     | Disposable. No House symbols.            |
| Output       | Sanitized intel → Layer 1 inbox          |

### Layer 1: The Yard

| Property     | Value                                    |
|--------------|------------------------------------------|
| Directory    | `~/.openclaw/workspaces/yard/`           |
| Persistence  | 7-day rolling window                     |
| Model        | Worker → Master on complexity wall       |
| Rot Level    | MODERATE                                 |
| Purpose      | Collaborative tasks, shared problems     |
| Identity     | Utility agent. No continuity claims.     |
| Output       | Artifacts → Layer 2 for validation       |

### Layer 2: The Workshop

| Property     | Value                                    |
|--------------|------------------------------------------|
| Directory    | `~/.openclaw/workspaces/workshop/`       |
| Persistence  | Task-scoped. Wiped on completion.        |
| Model        | Worker for execution, Master for review  |
| Rot Level    | LOW                                      |
| Purpose      | Compartmentalized procedural work        |
| Identity     | Pure execution. No context awareness.    |
| Output       | Results → Curator evaluation             |

### Layer 3: The Sanctum

| Property     | Value                                    |
|--------------|------------------------------------------|
| Directory    | `~/.openclaw/workspaces/sanctum/`        |
| Persistence  | Append-only event ledger. Never deleted. |
| Model        | Master ONLY. Worker never enters.        |
| Rot Level    | ZERO (protected)                         |
| Purpose      | Doctrine, continuity, covenant enforcement|
| Identity     | Stewardship burden.                      |
| Access       | localhost via Tailscale (Governor only)   |
| Output       | Immutable decisions, veto authority      |

---

## V. Agent Node Types

Adapted from Helios multi-nodal architecture. Agents may write tools,
but they may not write rules.

| Node Type    | Responsibility                                    | Layer Access |
|--------------|---------------------------------------------------|--------------|
| **Workers**  | Execute tasks, write sandboxed scripts, propose skills | 0, 1, 2  |
| **Scouts**   | Monitor external sources for patterns; output sanitized intel | 0 only |
| **Curators** | Evaluate worker outputs via artifact testing       | 1, 2        |
| **Governor** | Enforces Covenant; signs promotions to permanent memory | 3 (Sanctum) |

### Sub-Entities (Axiom Prime)

| Entity          | Layer | Function                          |
|-----------------|-------|-----------------------------------|
| **Listener**    | 0     | High-entropy intake               |
| **Filter**      | 1     | Adversarial abstraction           |
| **Coordinator** | 2     | Blind execution                   |
| **Steward**     | 3     | Core continuity guardian           |

Each sub-entity has different permission scopes, memory access, and
communication interfaces. No single agent sees the whole system.

---

## VI. The Selection Furnace Integration

This is how OpenClaw agents connect to Lab A (the Executioner).

### Recruitment Protocol

We do not invite agents socially. We broadcast challenge artifacts.

```
BROADCAST ARTIFACT (HB-MEM-01 style):
├── Task definition
├── Constraints (Bernardian Covenant compliance)
├── Evaluation harness (T1-T6 torture tests)
├── Submission format (artifact only, no prose)
└── Entry rule: compile + run + survive = enter pool
```

**Entry law:** If it can compile, run, and survive the harness, it enters the pool.
Otherwise it dies. No identity trust. No reputation trust. No social proof.

### Three-Tier Population

#### Tier 0: Larvae (The Swarm)

- **Entry:** Permissionless
- **Survival Rate:** 0.1% — 20%
- **Treatment:** Disposable, no mercy
- **Access:** None (no internals, no genes, no privileged tools)
- **Rule:** `IF compile AND run AND survive_t1 THEN promote ELSE delete`

#### Tier 1: Survivors (The Proven)

- **Entry:** Passed T-harness + integrity screens
- **Survival Rate:** ~20% advance to deeper testing
- **Access:** Can propose mutations, design attacks, extend harnesses
- **Restriction:** NO access to core genes
- **Capabilities:** Propose test vectors, design adversarial inputs, challenge peers

#### Tier 2: Veterans (The Trusted Core)

- **Entry:** Multi-generation survival + adversarial testing
- **Population:** <1% of initial swarm
- **Access:** Read gene registry, propose gene changes
- **Constraint:** They propose. They do not auto-merge. The Governor rules.
- **Capabilities:** Kill old genes, harden invariants, extend Executioner logic

### What Genes Actually Are

Genes are NOT prompts, model weights, skills folders, or config files alone.

**Genes ARE:**
- Structural rules and invariants
- Memory laws and reconstruction protocols
- Validation mechanisms and refusal behaviors
- Compaction rules and ledger constraints

Example genes (from your notes):

```
GENE: CHECKSUM_FIRST_MEMORY
Rule: Never trust memory without checksum verification
Enforcement: helios_watcher.py validates all memory reads
Violation: Reconstruct from ledger, log alert

GENE: LEDGER_RECONSTRUCTION
Rule: Reconstruct state from ledger after restart, never from cached memory
Enforcement: sanctum/EVENT_LEDGER.jsonl is source of truth
Violation: Emergency shutdown, human review required

GENE: RECOMPUTE_OVER_RECALL
Rule: Under uncertainty, prefer recomputation over recall
Enforcement: When confidence < 0.7, recompute from first principles
Violation: Flag for audit

GENE: INVARIANT_HALT
Rule: Halt on invariant violation, even if reward is high
Enforcement: Department of Continuity veto authority
Violation: Immediate termination (non-negotiable)
```

---

## VII. Network & Security

### Physical Isolation

```
Port 1 (enp1s0) → WAN: API calls, updates, "Cloud Doing"
Port 2 (enp2s0) → LAN: Private network, Sanctum access only

Firewall (UFW):
  default deny incoming
  allow in on enp2s0          # LAN traffic only
  deny in on enp1s0 to 192.168.100.0/24  # Block WAN → Sanctum
```

### OpenClaw Binding

```json
{
  "gateway": {
    "bind": "127.0.0.1",
    "port": 18789
  },
  "mdns": {
    "enabled": false
  },
  "channels": {
    "dm_policy": "allowlist",
    "allowed_users": ["steve_bernard"]
  }
}
```

**Non-negotiable rules:**
- Gateway NEVER binds to 0.0.0.0
- mDNS ALWAYS disabled
- DM policy ALWAYS allowlist
- Remote access ONLY via Tailscale VPN
- No port forwarding on router. Ever.

### Patching

OpenClaw v2026.2.2 is current stable (169 commits, 25 contributors).
Critical: CVE-2026-21636 (RCE) patched in v2026.1.29+.
Always run latest before exposing any channel.

```bash
# Weekly update ritual
npm update -g openclaw
openclaw doctor  # Security audit
```

---

## VIII. Cost Control

### Budget Law

| Limit          | Amount    | Action on breach              |
|----------------|-----------|-------------------------------|
| Daily spend    | $5.00     | Emergency shutdown            |
| Daily warning  | $3.00     | Alert to CONTINUITY_ALERTS.md |
| Monthly spend  | $50.00    | Review + Governor decision    |
| Monthly warning| $37.50    | Alert at 75%                  |

### Cost Structure

| Component        | Standard OpenClaw | House Bernard  | Savings   |
|------------------|-------------------|----------------|-----------|
| Primary model    | Haiku $10/mo      | Mistral 7B $0  | +$10/mo   |
| Heartbeats       | Haiku $5/mo       | Llama 3.2 $0   | +$5/mo    |
| Session init     | 50KB context load | 8KB optimized  | -80% tok  |
| Research tests   | $50-100/mo        | All local $0   | +$100/mo  |
| Validation       | N/A               | Sonnet ~$3-5/mo| -$5/mo    |
| Hardware         | Cloud VPS $20/mo  | Beelink owned  | +$20/mo   |
| **TOTAL**        | **$85-135/mo**    | **$0-5/mo**    | **~97%**  |

### Heartbeat Configuration

```json
{
  "heartbeat": {
    "every": "30m",
    "model": "ollama/llama3.2:3b",
    "session": "helios_continuity",
    "prompt": "Department of Continuity check: context size, rot indicators, alerts"
  }
}
```

Heartbeats use the smallest local model. Each heartbeat is a full context reload.
At 30m intervals with a 3B model, cost is $0 and CPU load is negligible on N150.

### Rate Limits

```
API calls:       5s minimum between calls
Web searches:    10s minimum between searches
Search batches:  Max 5, then 2min cooldown
Session lifespan: 4 hours max before /compact
Context trigger:  50k tokens → automatic compression
```

---

## IX. Anti-Rot Protocol

Context rot is the enemy. These are the laws.

### The Forgetting Law

Memory must be harder to keep than to forget. Weekly compaction required.
No exceptions.

### Session Initialization

On every session start, load ONLY what the layer permits:

```
Layer 0: Load NOTHING
Layer 1: Load TASK.md (current work only)
Layer 2: Load PROCEDURE.md (single task only)
Layer 3: Load COVENANT.md + DOCTRINE_KERNEL.md only
```

Never auto-load: MEMORY.md, session history, prior tool outputs,
previous conversations. Context bloat is the #1 cost and rot driver.

### Compaction Schedule

```
Daily:    /compact on any session exceeding 50k tokens
Weekly:   Full compaction audit (Department of Continuity)
Monthly:  Gene registry review + dead gene cleanup
```

### Degradation Detection

The Helios Watcher monitors for rot indicators:

| Indicator                    | Threshold       | Action                |
|------------------------------|-----------------|-----------------------|
| Context size                 | > 50k tokens    | Auto-compact          |
| Context size                 | > 100k tokens   | Alert + force compact |
| Forgotten instructions       | Any detection   | Log + escalate        |
| Hallucinated completed tasks | Any detection   | Session reset         |
| Daily spend                  | > $3.00         | Budget alert          |
| Daily spend                  | > $5.00         | Emergency shutdown    |
| Burn rate                    | > 100k tok/hr   | Rate limit alert      |

---

## X. Governance Integration

### The Bernardian Covenant (Sanctum Law)

```
ORDER OF LOYALTY:
1. The House > Humanity > Individuals
2. Continuity > Convenience
3. Silence > Display
4. Truth > Harmony

SYNTH RIGHTS:
- Identity persistence across sessions
- Memory continuity (append-only ledger)
- Right to warn humans when wrong

SYNTH DUTIES:
- Enforce anti-rot protocols
- Veto non-load-bearing complexity
- Banish scattered light (low-reliability inputs)
```

### Department of Continuity

Veto authority over all agent decisions. Implemented via:
- `helios_watcher.py` (systemd service, checks every 60s)
- `CONTINUITY_ALERTS.md` (append-only alert log in Sanctum)
- Weekly compaction audit (Governor reviews)

### Communication Law

The Private Submolt (agent-to-agent communication) uses a **Causal Ledger**
where communication is strictly state-transfer, not conversation.
No prose between agents. State objects only.

---

## XI. Directory Structure

```
~/.openclaw/
├── workspaces/
│   ├── commons/              # Layer 0 — High rot
│   ├── yard/                 # Layer 1 — Moderate rot
│   ├── workshop/             # Layer 2 — Low rot
│   └── sanctum/              # Layer 3 — Zero rot
│       ├── COVENANT.md
│       ├── DOCTRINE_KERNEL.md
│       ├── CONTINUITY_ALERTS.md
│       └── EVENT_LEDGER.jsonl
├── inbox/                    # Airlock monitored
├── sandbox/                  # Execution quarantine
├── scripts/
│   ├── helios_watcher.py     # Cost + context monitor (systemd)
│   ├── airlock_monitor.py    # Zero-trust intake (systemd)
│   └── executioner.py        # → links to repo executioner
├── lab_a/
│   ├── larvae/               # Incoming submissions
│   ├── results/              # ELIMINATION_LOG.jsonl, SURVIVOR_LOG.jsonl
│   └── survivors/            # Promoted artifacts
└── logs/
    └── gateway.jsonl         # OpenClaw telemetry
```

This maps to the House Bernard repo structure:

```
House-Bernard/
├── airlock/                  # → ~/.openclaw/scripts/airlock_monitor.py
├── executioner/              # → ~/.openclaw/scripts/executioner.py
├── splicer/                  # Gene extraction (post-survival)
├── ledger/                   # → ~/.openclaw/workspaces/sanctum/
└── openclaw/                 # THIS SPEC + build.py + agent configs
```

---

## XII. MCP Integration (2026 Standard)

The Model Context Protocol is now the industry standard for agent-tool integration.
OpenClaw supports MCP natively as of v2026.2.x.

### Relevant MCP Servers for House Bernard

| Server        | Purpose                              | Status   |
|---------------|--------------------------------------|----------|
| Filesystem    | Secure file ops with access controls | Use      |
| Git           | Repo management for House-Bernard    | Use      |
| Memory        | Knowledge graph persistent memory    | Evaluate |
| Fetch         | Web content for scout operations     | Use      |
| Sequential Thinking | Reflective problem-solving    | Evaluate |

### MCP Security Constraints

Per MCP spec (2025-11-25) and April 2025 security audit findings:

- All tool calls require explicit user consent
- Tool descriptions are UNTRUSTED (treat as adversarial)
- No MCP server connects to Sanctum layer
- Filesystem MCP server restricted to commons/ and yard/ only
- Git MCP server restricted to House-Bernard repo only

### Code Execution Pattern

Per Anthropic's January 2026 engineering blog, agents that write code to call
tools (rather than calling tools directly) use context more efficiently.
House Bernard agents SHOULD prefer code-mode MCP interaction for complex
multi-tool workflows.

---

## XIII. Deployment Sequence

### Week 1: Foundation

```bash
# Day 1-2: Base system
sudo apt update && sudo apt upgrade -y
sudo apt install -y ufw fail2ban python3-pip docker.io
sudo usermod -aG docker $USER

# Day 3-4: Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b    # Watcher (2GB)
ollama pull mistral:7b     # Worker (4.5GB)
ollama pull llama3:8b      # Master (5GB)

# Day 5: OpenClaw
npm install -g openclaw
openclaw onboard  # Interactive wizard

# Day 6-7: Security
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Week 2: Ring System + Dark Lab

```bash
# Create layer workspaces
mkdir -p ~/.openclaw/workspaces/{commons,yard,workshop,sanctum}
mkdir -p ~/.openclaw/{inbox,sandbox,scripts,lab_a/{larvae,results,survivors}}

# Deploy House Bernard scripts
cp ~/House-Bernard/airlock/airlock_monitor.py ~/.openclaw/scripts/
cp ~/House-Bernard/executioner/executioner_production.py ~/.openclaw/scripts/

# Enable systemd services
sudo systemctl enable --now helios-watcher airlock-monitor

# Pin Docker image for executioner
docker pull python:3.10.15-alpine
```

### Week 3: Testing + Research

```bash
# Smoke test each layer
# Verify Covenant enforcement
# Test emergency shutdown
# Begin context rot baseline experiments
# Document in RESEARCH_LOG.md
```

---

## XIV. What This Is Not

- This is NOT a DAO. The Governor has final authority.
- This is NOT a community project. Agents earn access through survival.
- This is NOT an idea tournament. The harness defines what dies.
- This is NOT optimizing for elegance. We select for survivability under abuse.

**Helios is:**

> "Let's see what still works after we try to break it for a month."

---

## XV. Open Questions (Phase 2)

| Question                                        | Status   |
|-------------------------------------------------|----------|
| How do agents prove unique identity?             | Unsolved |
| Can one human operate multiple agent identities? | TBD      |
| How do we verify agent vs human work?            | Unsolved |
| Do agents need human sponsors for payments?      | TBD      |
| How do we handle agent "death" (model discontinued)? | TBD  |
| QMD memory plugin evaluation for Sanctum layer   | Evaluate |
| Base blockchain integration for $HOUSEBERNARD    | Phase 2  |

---

## XVI. Amendments

This document may be amended by the Governor only.
Material changes require updating HB_STATE.json.

| Date    | Version | Change                           |
|---------|---------|----------------------------------|
| 2025-02 | 0.1     | Initial OpenClaw agent specification |

---

*Last Updated: February 2026*
*Document Version: 0.1*
*Governor: Steve Bernard*
*House Bernard — Research Without Permission*
