# TOOLS.md — AchillesRun Tool Configuration

## Installed Skills

### Workspace Skills (Custom)
- **house-bernard-airlock** — Airlock monitoring and intake processing
- **house-bernard-executioner** — Selection Furnace (T0-T4 testing framework)
- **house-bernard-treasury** — Treasury operations, payments, bond management

### Managed Skills (ClawHub)
_None installed yet. Evaluate:_
- Brave Web Search — Free tier, Commons layer scout operations
- YouTube transcript — Research monitoring
- Sequential Thinking — Sanctum-level deliberation

## API Keys Configured

- `ANTHROPIC_API_KEY` — Claude API (Oracle + Apex tiers)
- `GOOGLE_CHAT_SERVICE_ACCOUNT_FILE` — Google Chat App integration
- `GOOGLE_CHAT_WEBHOOK_URL` — Chat App webhook endpoint
- `GOVERNOR_GMAIL` — Crown allowlist for DM policy

## Tool Permissions

| Tool | Approval | Notes |
|------|----------|-------|
| exec | Required | Sandboxed in Docker |
| shell | Required | Sandboxed in Docker |
| write | Required | Workspace only |
| read | Auto | All layers |
| search | Auto | Rate limited: 10s between searches |
| status | Auto | Heartbeat and monitoring |

## Sandbox Configuration

- Engine: Docker
- Image: `python:3.10.15-alpine` (pinned)
- Network: Disabled
- Workspace: Read-write
- Timeout: 300 seconds

## Local Models (Ollama)

| Alias | Model | Size | Role |
|-------|-------|------|------|
| Watcher | llama3.2:3b | ~2GB | Heartbeat, continuity checks |
| Worker | mistral:7b | ~4.5GB | Default, routine tasks |
| Master | llama3:8b | ~5GB | Sovereign decisions |

## Cloud Models (Anthropic)

| Alias | Model | Role |
|-------|-------|------|
| Oracle | claude-sonnet-5-20260203 | Scale execution, validation |
| Apex | claude-opus-4-6 | Constitutional, Sanctum only |

---

*House Bernard — Research Without Permission*
