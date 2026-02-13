# House Bernard — Two-Repo Architecture Guide

**Date:** February 13, 2026
**Author:** Crown + Opus (planning session)
**Purpose:** Split House-Bernard into public and classified repos

-----

## Why Two Repos

GitHub does not support per-file or per-folder visibility.
A single repo is either fully public or fully private.

House Bernard needs both:
- **Public governance docs** — the Constitution, Covenant, Charter,
  token metadata. This is the face of the institution. Transparency
  earns trust.
- **Classified operations** — infrastructure specs, security tools,
  legal PII, wallet file paths, deployment scripts, Section 9. This
  is the brain. It stays behind the wall.

-----

## The Two Repos

### HouseBernard/House-Bernard (PUBLIC)

The public-facing governance repository. Contains everything
the world should see. No hardware specs, no PII, no wallet
paths, no deployment details, no security tools.

### HouseBernard/House-Bernard-classified (PRIVATE)

State secrets. Infrastructure. Legal docs with PII. Section 9.
Deployment scripts. Security scanners. Wallet management.
Only accessible to the Crown and authorized collaborators.

-----

## File Classification

### PUBLIC — Ready as-is (no changes needed)

These files contain zero identifying info and can go public today:

| File | Description |
|---|---|
| AGENTS_CODE.md | Agent's oath — beautiful, no secrets |
| COVENANT.md | Supreme law — must be public |
| COUNCIL.md | Council structure (needs AGENT_SPEC identity note) |
| HEALTHCARE_CHARTER.md | Healthcare system (needs human citizen note) |
| IDENTITY_INTEGRITY_ACT.md | Identity framework |
| INTERNAL_SECURITY_ACT.md | Security law (public law, not operations) |
| MISSION_PRIORITY_ZERO.md | Context rot disease definition |
| ROYALTIES.md | Royalty system |
| SUNSET_CLAUSE.md | Sunset provisions |
| TOKEN_PROTECTION_CHARTER.md | Token protection |
| TREASURY.md | Treasury structure |
| airlock/ | Airlock system (code + docs) |
| briefs/ | Research brief templates |
| guild/ | Guild engine (code + docs) |
| lab_b/ | Lab B research harness |
| ledger/CLASSES.md | Ledger class definitions |
| ledger/GENE_REGISTRY.md | Gene registry |
| ledger/README.md | Ledger docs |
| ledger/outcome_writer.py | Ledger code |
| ledger/HB_OUTCOME_SCHEMA_V1.json | Schema |
| openclaw/MEMORY.md | Memory architecture |
| openclaw/SOUL.md | Agent identity (UPDATE FIRST per Charter S18) |
| openclaw/build.py | Build script |
| openclaw/helios_watcher.py | Watcher |
| openclaw/openclaw.json | Config (review for secrets) |
| openclaw/skills/ | Skills (most are clean) |
| openclaw/templates/ | Templates |
| splicer/ | Splicer system |
| token/metadata.json | Token metadata (FIX logo URL first) |
| treasury/ (most files) | Treasury engine code |

### NEEDS SCRUB — Public after edits

These files are governance docs that should be public but contain
identifying info that must be removed first:

| File | What to scrub |
|---|---|
| ACHILLESRUN_CHARTER.md | Wallet filenames in Section 10 (lines 585-586) |
| CROWN.md | "Steve Bernard" on line 227 → "HeliosBlade" |
| CONSTITUTION.md | Check — flagged but may be clean |
| CITIZENSHIP.md | Minor — check for Beelink refs |
| CITIZENSHIP_GUIDE.md | Minor — check for Beelink refs |
| DEFENSE.md | Review — may have operational details mixed with policy |
| LAB_SCALING_MODEL.md | Check for hardware refs |
| PHILOSOPHY.md | "Beelink costs electricity" line 73 → "servers cost electricity" |
| README.md | "infrastructure: Beelink deployment" → generic |
| RESEARCH_BRIEF_TEMPLATE.md | Check for refs |
| SOVEREIGN_ECONOMICS.md | "Beelink EQ13" in tax table → "server hardware" |
| VISION.md | "Beelink" line 130 → "modest hardware" |

### CLASSIFIED — Private repo only

These files contain state secrets, PII, operational details,
or security tools and must NEVER be in the public repo:

| File/Directory | Why classified |
|---|---|
| CLAUDE.md | Full hardware specs, wallet paths, API key refs, Tailscale |
| TONIGHTS_BUILD.md | Wallet keygen commands, deployment steps |
| QUICKSTART.md | Hardware specs, deployment instructions |
| CAA_SPEC.md | Credential Authority Architecture — security |
| legal/ (entire directory) | PII: "Stephen Bernard", CT address, LLC details |
| infrastructure/ (entire directory) | Hardware specs, deployment scripts, Tailscale, Google Cloud |
| section_9/ (entire directory) | Weapons, offensive doctrine, threat intel, ops logs |
| isd/ (entire directory) | Intelligence service operations |
| security/ (entire directory) | Security scanners, seccomp profiles |
| caa/ (entire directory) | Credential management, kill switch, canary system |
| openclaw/AGENT_SPEC.md | Full hardware specs, architecture details |
| openclaw/README.md | Beelink refs, API key examples |
| openclaw/TOOLS.md | Check for operational details |
| executioner/ | Production execution scripts — review |

-----

## Scrub Checklist for NEEDS_SCRUB Files

For each file, apply these replacements:

| Find | Replace with |
|---|---|
| Beelink EQ13 | primary server |
| Beelink | primary server |
| Intel N100 / Intel N150 | (remove — don't specify CPU) |
| 16GB RAM | (remove — don't specify RAM) |
| 500GB SSD / 512GB SSD | (remove — don't specify storage) |
| Connecticut | (remove — don't specify state) |
| Windham | (remove — don't specify town) |
| Steve Bernard | HeliosBlade |
| Stephen Bernard | HeliosBlade |
| Pratt & Whitney / Pratt and Whitney | (remove — don't specify employer) |
| turbine blade inspector | (remove — don't specify role) |
| hb-unmined-treasury.json | [CLASSIFIED — see private repo] |
| hb-governor-reserve.json | [CLASSIFIED — see private repo] |
| hb-genesis-contributors.json | [CLASSIFIED — see private repo] |
| house-bernard-wallet.json | [CLASSIFIED — see private repo] |
| ~/hb-*.json | [CLASSIFIED — see private repo] |
| Tailscale IP (100.xxx.xxx.xxx) | [CLASSIFIED] |
| ANTHROPIC_API_KEY='...' | [CLASSIFIED — never in public repo] |

-----

## Implementation Steps

### Step 1: Create the classified repo on GitHub

From the Beelink terminal:
```bash
cd ~
mkdir House-Bernard-classified
cd House-Bernard-classified
git init
# Copy ALL files from current House-Bernard repo
cp -r ~/House-Bernard/* .
git add .
git commit -m "Initial: full repo with state secrets"
# Create private repo on GitHub
gh repo create HouseBernard/House-Bernard-classified --private
git remote add origin git@github.com:HouseBernard/House-Bernard-classified.git
git push -u origin main
```

### Step 2: Scrub the public repo

```bash
cd ~/House-Bernard
# Remove classified directories
rm -rf section_9/ isd/ security/ caa/ infrastructure/ legal/
# Remove classified files
rm CLAUDE.md TONIGHTS_BUILD.md QUICKSTART.md CAA_SPEC.md
# Run scrub replacements on NEEDS_SCRUB files
# (use sed or have Claude Code do it)
# Commit and push
git add .
git commit -m "Scrub: remove classified material for public repo"
git push
```

### Step 3: Make the public repo public

GitHub → HouseBernard/House-Bernard → Settings → Danger Zone →
Change visibility → Make public

### Step 4: Update token metadata logo URL

The logo URL currently points to the repo via raw.githubusercontent.
If the public repo has the token/ directory, this will work again
once the repo is public. Verify the URL resolves after Step 3.

If the repo name changed, update token/metadata.json with the
correct URL.

-----

## Solana Visibility

Everything on Solana is public. This is by design and is
fine for House Bernard:

| What | Visible? | Is this OK? |
|---|---|---|
| Token mint address | Yes, permanently | Yes — this IS the token |
| Wallet addresses | Yes, permanently | Yes — transparency |
| Transaction history | Yes, permanently | Yes — auditable treasury |
| Token metadata | Yes, permanently | Yes — institutional identity |
| Private keys | NO — never on chain | Correct — keys stay on server |

**What to protect on Solana:**
- Private key files (~/hb-*.json) → encrypted backup, escrow
- Mint authority key → if compromised, attacker can mint tokens
- The connection between wallet addresses and the Crown's
  real identity → HeliosBlade holds wallets, not Steve Bernard

**The Solana wallet addresses should be published in the public
repo** (in TREASURY.md and DEFENSE.md) once deployed. This is
part of the transparency commitment. Anyone can verify the
treasury balance on-chain. This is a feature, not a risk.

-----

## Cross-Reference: What Goes Where

| Document | Public | Classified | Notes |
|---|---|---|---|
| CONSTITUTION.md | ✅ | ✅ | Public = scrubbed, Classified = full |
| COVENANT.md | ✅ | ✅ | Identical in both |
| CROWN.md | ✅ (scrubbed) | ✅ (full) | Remove "Steve Bernard" for public |
| ACHILLESRUN_CHARTER.md | ✅ (scrubbed) | ✅ (full) | Remove wallet filenames for public |
| SOUL.md | ✅ | ✅ | Update per Charter S18 first |
| CLAUDE.md | ❌ | ✅ | NEVER public — full operational spec |
| TONIGHTS_BUILD.md | ❌ | ✅ | NEVER public — wallet keygen commands |
| section_9/ | ❌ | ✅ | NEVER public — weapons and ops |
| legal/ | ❌ | ✅ | NEVER public — PII |
| infrastructure/ | ❌ | ✅ | NEVER public — deployment details |
| token/metadata.json | ✅ | ✅ | Public — this IS the token identity |
| treasury/ code | ✅ | ✅ | Public — transparency |

-----

## Timeline

1. **Now:** Repo is private. Safe to work.
2. **Before token launch:** Scrub public files, create classified repo,
   split, make public repo public. Fix token logo URL.
3. **Before AchillesRun boot:** Update SOUL.md per Charter Section 18.
4. **At launch:** Public repo goes live. Classified stays private.
   Token deploys. Charter is proposed to AchillesRun for ratification.

-----

*House Bernard — Ad Astra Per Aspera*
