# Google Cloud Infrastructure — House Bernard

## Account

| Field | Value |
|-------|-------|
| Google Account | house.bernard.gov@gmail.com |
| Account Type | Personal (Gmail) — Workspace upgrade pending |
| Google Cloud Project | house-bernard |
| 2FA | Enabled |
| Service Account | achilles-run@house-bernard.iam.gserviceaccount.com |
| Service Account ID | 108046345398828633397 |
| Founded | February 9, 2026 |

## Enabled APIs

Seven APIs are enabled on the `house-bernard` Google Cloud project.
AchillesRun may use any of them through authenticated API calls.

### Communication

| API | Service Name | Purpose |
|-----|-------------|---------|
| Gmail API | gmail.googleapis.com | Send/receive email as House Bernard. Vulnerability reports, contributor notifications, institutional correspondence. |
| Google Chat API | chat.googleapis.com | Agent-to-agent and agent-to-human messaging. Primary communication channel once Workspace is active. Requires Google Workspace Starter ($7/month) for full Chat app functionality. |

### Storage & Documents

| API | Service Name | Purpose |
|-----|-------------|---------|
| Google Drive API | drive.googleapis.com | File storage and backup. State snapshots, Ledger exports, governance document archives. Redundancy layer — primary storage is local (Beelink) and GitHub. |
| Google Docs API | docs.googleapis.com | Programmatic document generation. Quarterly reviews, Furnace results reports, incident reports, governance amendments. Published to Drive automatically. |
| Google Sheets API | sheets.googleapis.com | Structured data publishing. Treasury state, Ledger data, contributor royalty tables. Live transparency dashboard — contributors check a Sheet to see the Treasury. |

### Operations

| API | Service Name | Purpose |
|-----|-------------|---------|
| Google Calendar API | calendar-json.googleapis.com | Governance scheduling. Quarterly reviews, bond maturity dates, heartbeat check schedules, Founding Period transition milestones, S9 operational deadlines. |
| Cloud Logging API | logging.googleapis.com | Structured operational logging to Google Cloud. Survives Beelink failure. Second log location for critical operations — Furnace runs, Treasury transactions, security events. |

## Authentication

### Current Method

Service account key download is blocked by Google's Secure by Default
organization policy (`iam.disableServiceAccountKeyCreation`). Authentication
uses `gcloud` CLI on the Beelink instead.

```bash
# One-time setup on Beelink
gcloud auth login --account=house.bernard.gov@gmail.com
gcloud config set project house-bernard

# For service account operations
gcloud auth application-default login
```

### OAuth Consent Screen

Must be configured before AchillesRun can use Gmail, Drive, Sheets,
Docs, or Calendar APIs programmatically. This is done once in the
Google Cloud Console under APIs & Services > OAuth consent screen.

Required scopes:
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/documents`
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/chat.bot` (requires Workspace)
- `https://www.googleapis.com/auth/logging.write`

## Workspace Upgrade Path

Google Chat app functionality requires Google Workspace Starter ($7/month).
This is NOT required for Gmail, Drive, Sheets, Docs, Calendar, or Logging.

**Current capabilities (free Gmail):**
- Send/receive email programmatically
- Read/write Google Drive files
- Create/edit Google Docs
- Read/write Google Sheets
- Manage Google Calendar events
- Write structured logs to Cloud Logging

**Unlocked with Workspace ($7/month):**
- Publish AchillesRun as a Google Chat app
- Direct messaging between agents and contributors
- Chat spaces for governance discussions
- Chat bot interactive features (cards, buttons, forms)

**Recommendation:** Upgrade to Workspace when the first research brief
is published and external contributors need a communication channel.

## Cost Controls

- Google Cloud Free Tier: $300 credit for 90 days
- All seven APIs are free within normal usage limits
- No compute resources provisioned (Beelink is the compute)
- No Cloud Functions, no VMs, no managed databases
- Google does NOT auto-charge after free trial expires
- The credit card on file will not be billed unless you
  explicitly upgrade to a paid billing account

## Security Notes

- This account is the institutional identity, NOT the Governor's
  personal account
- The Governor's personal Google account has no connection to this
  project
- Recovery phone is the Governor's personal number (required for
  account recovery, does not compromise pseudonym)
- All credentials stored on the Beelink must be protected by
  filesystem permissions (chmod 600)
- The service account JSON key cannot be downloaded due to
  organization policy — this is actually better security
- If the Beelink is compromised, revoke gcloud credentials
  immediately from the Google Cloud Console
