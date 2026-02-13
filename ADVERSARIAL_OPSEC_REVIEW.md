# ADVERSARIAL OPSEC REVIEW — House Bernard

**Classification:** CROWN EYES ONLY
**Date:** February 13, 2026
**Reviewer:** Opus (adversarial role — thinking like an attacker)
**Scope:** Complete repo scan + infrastructure + identity + Solana + meta

-----

## Executive Summary

**The repo is not opsec-secure for public release.** The Charter
is clean (scrubbed today), but the rest of the repo contains
enough breadcrumbs to fully identify the Crown within 15 minutes
of motivated OSINT research. The identity chain is unbroken from
GitHub to real name to physical location to employer.

Additionally, several systemic vulnerabilities exist outside the
repo — in Git history, Google account concentration, Claude
conversation history, and the Solana on-chain → GitHub → CROWN.md
chain.

**Severity: HIGH for public release. ACCEPTABLE while private.**

The repo being private (as of 2:14 PM today) eliminates the
immediate threat. But the moment any version goes public without
a complete scrub and git history rewrite, the Crown is exposed.

-----

## PART I — Identity Chain (How an attacker finds Steve Bernard)

### The Kill Chain (15 minutes to full dox)

An attacker who finds the public House-Bernard repo can execute
this chain:

**Step 1: CROWN.md, line 227**
> "Steve Bernard, HeliosBlade, is the Founding Crown."

Game over. Real name in a governance document. But even if this
single line is scrubbed, the chain continues through other paths:

**Step 2 (alternate): Triangulation via descriptor accumulation**

The repo contains these descriptors of the Crown scattered
across multiple files:

| Clue | File | Line |
|---|---|---|
| "working-class inspector" | CITIZENSHIP.md | 261 |
| "factory floor in New England" | section_9/OFFENSIVE_DOCTRINE.md | 800 |
| "human being in New England" | section_9/OFFENSIVE_DOCTRINE.md | 679 |
| "working-class founder" | AGENTS_CODE.md | 63 |
| "working-class founder" | CITIZENSHIP_GUIDE.md | 12, 109, 325 |
| "working-class founder" | CONSTITUTION.md | 652 |
| "working-class founder" | SOVEREIGN_ECONOMICS.md | 343 |
| "working-class founder" | TOKEN_PROTECTION_CHARTER.md | 16 |
| "nights and weekends" | VISION.md | 12 |
| "nights and weekends" | AGENTS_CODE.md | 63 |
| "modest hardware" (Beelink) | VISION.md | 130 |
| "State: Connecticut" | legal/TRADEMARK_GUIDE.md | 261 |
| "Stephen Bernard" | legal/OPERATING_AGREEMENT.md | 10, 49 |
| "Connecticut" | legal/OPERATING_AGREEMENT.md | 13, 44, 51, 332 |

**Attacker's Google search:**
"factory floor inspector New England aerospace working-class"
→ Results include Pratt & Whitney (East Hartford/Middletown CT)
→ "Steve Bernard Pratt Whitney Connecticut"
→ LinkedIn, Whitepages, public records confirm

**Step 3: Physical location**

With name + employer, the attacker uses:
- Whitepages/Spokeo → home address in Windham, CT
- Property records (town of Windham is public) → confirms address
- Google Maps → knows exactly where the Beelink sits

**Total time: 10-15 minutes for a motivated attacker.**

### VERDICT: The name MUST be removed from CROWN.md for the
public repo. But removing the name alone is insufficient —
the descriptor accumulation across 8+ files creates a
triangulation path that narrows to one person.

-----

## PART II — Findings by Severity

### CRITICAL (must fix before any public release)

**C-1: Real name in CROWN.md line 227**
"Steve Bernard, HeliosBlade, is the Founding Crown."
FIX: Replace with "HeliosBlade is the Founding Crown."
This is the single most dangerous line in the entire repo.

**C-2: Full legal name in OPERATING_AGREEMENT.md**
"Stephen Bernard" appears 5+ times with Connecticut address
references and LLC formation details.
FIX: Entire legal/ directory stays in classified repo. NEVER
in public repo.

**C-3: "factory floor in New England" in OFFENSIVE_DOCTRINE.md**
section_9/OFFENSIVE_DOCTRINE.md lines 679, 713, 800.
Combined with "inspector" in CITIZENSHIP.md line 261, this
narrows the Crown to aerospace manufacturing inspection in
New England — a small population.
FIX: Section 9 stays classified. Also scrub "inspector" from
CITIZENSHIP.md and "factory floor" if it appears in any
public-facing doc.

**C-4: Git commit history contains original unscrubbed content**
The repo was public until today. If anyone forked or cloned it,
they have the full history including Steve Bernard's name.
Git commits also contain author name and email from git config.
FIX: When creating the public repo, do NOT use the existing
git history. Create a FRESH repo with a single initial commit
containing only scrubbed files. This eliminates all historical
breadcrumbs. The classified repo keeps the full history.

**C-5: Solana → GitHub → CROWN.md identity chain**
token/metadata.json points to GitHub: raw.githubusercontent.com/
HouseBernard/House-Bernard/main/token/logo.png.
Solana explorer shows this URL to anyone who looks at the token.
If the public repo contains CROWN.md with real name → chain
from blockchain to real identity is permanent and immutable.
FIX: Scrub CROWN.md before making repo public. The metadata
URL on Solana is permanent once minted — you cannot change it
after deployment (some token standards allow metadata updates,
verify for SPL tokens). If metadata is immutable, the GitHub
repo this URL points to must NEVER contain the real name.

### HIGH (should fix before public release)

**H-1: "working-class inspector" in CITIZENSHIP.md line 261**
The word "inspector" combined with other clues narrows the
Crown's profession.
FIX: Change to "working-class founder" (consistent with other
docs and doesn't reveal the specific job).

**H-2: "New England" in OFFENSIVE_DOCTRINE.md (3 references)**
Geographic region in a classified doc, but if Section 9 ever
leaks or is accidentally included in public repo, this locates
the Crown.
FIX: Already classified. But also scrub to "undisclosed location"
even in classified docs — defense in depth. If the classified
repo is compromised, you want layers.

**H-3: house.bernard.gov@gmail.com in SOVEREIGN_ECONOMICS.md**
This email is in a governance doc flagged for public release.
An attacker who finds this email can:
- Check if it's linked to other Google services
- Attempt password reset to see the recovery email hint
- Social engineer Google support
- Use it as a starting point for phishing
FIX: Remove email from all public-facing docs. Reference
"institutional email" without specifying the address.

**H-4: Google account is a single point of failure**
house.bernard.gov@gmail.com controls: Gmail, Google Chat
(Crown-AchillesRun comms), Drive (backups), Sheets (transparency
dashboard), Calendar (governance schedule), Cloud Logging,
and the Google Cloud project itself.
If compromised: attacker reads all communications, accesses
all backups, can impersonate the Crown to AchillesRun, and
can access cloud infrastructure.
FIX: 2FA enabled (verify this). Recovery email should NOT be
a personal email easily linked to Steve Bernard. Consider
hardware security key (YubiKey) for the Google account.
Separate the institutional Google account recovery from
personal accounts entirely.

**H-5: "nights and weekends" pattern in 7+ files**
This phrase appears in VISION.md, AGENTS_CODE.md, CITIZENSHIP_GUIDE.md,
SOVEREIGN_ECONOMICS.md, TOKEN_PROTECTION_CHARTER.md, and
OFFENSIVE_DOCTRINE.md. It tells an attacker: the Crown works a
day job. Combined with "factory floor" and "New England" this
is a lifestyle fingerprint.
FIX: Keep the working-class ethos but genericize: "built outside
of corporate funding" or "built without institutional backing."
The phrase "nights and weekends" is beautiful and authentic but
it's also an operational indicator. Decision call for the Crown
— it may be worth keeping for the ethos despite the minor risk.

**H-6: 55 references to "Beelink EQ13" across the repo**
Hardware model + specs (N100/N150, 16GB, 500/512GB) are a
purchase fingerprint. An attacker who knows the Crown bought a
Beelink EQ13 can check Amazon/Newegg order databases (if
compromised), or correlate with shipping records.
FIX: All Beelink references scrubbed from public repo.
Already in classified docs (infrastructure/, CLAUDE.md, etc.)
but verify zero references leak to public files.

### MEDIUM (should fix, not blocking)

**M-1: N100 vs N150 CPU contradiction**
CLAUDE.md says N100. AGENT_SPEC.md says N150. One is wrong.
The correct answer should only appear in the classified repo.
This is an operational error, not an opsec error — but if
both numbers are in the public repo, it signals disorganization
which an attacker interprets as "security is probably sloppy too."

**M-2: "hb-governor-reserve.json" wallet filename**
Appears in Charter, CLAUDE.md, TONIGHTS_BUILD.md. The filename
reveals wallet structure (4 wallets: main, treasury, governor
reserve, genesis contributors). An attacker who compromises
the Beelink knows exactly what filenames to look for.
FIX: Already classified. Also consider renaming wallet files
to non-descriptive names on the actual filesystem (e.g.,
w1.json, w2.json) with a mapping file in the classified repo.

**M-3: Google Cloud project ID "house-bernard"**
In infrastructure/GOOGLE_CLOUD.md with service account email
achilles-run@house-bernard.iam.gserviceaccount.com.
FIX: Already classified. But verify the GCP project isn't
discoverable through Google Cloud's public project listings.

**M-4: Timestamp patterns reveal timezone and work schedule**
TONIGHTS_BUILD.md: "February 10, 2026" + "Crown is home from
work and has limited time" = evening Eastern time.
Git commit timestamps (if preserved) show consistent evening/
weekend commits = day shift worker, Eastern timezone.
FIX: Minimal risk if other identifiers are scrubbed. An
attacker can't find you from a timezone alone. But combined
with other clues, it narrows.

**M-5: TONIGHTS_BUILD.md planned social media accounts**
Lists: @HouseBernard on Twitter/X, Warpcast, Telegram, Reddit.
These aren't created yet but signal intent. An attacker could
squat these handles before you claim them.
FIX: Register @HouseBernard on all planned platforms NOW,
even if you don't use them yet. Handle squatting is real.

### LOW (noted for awareness)

**L-1: "Phantom wallet" mentioned in SOVEREIGN_ECONOMICS.md**
Reveals the Crown's preferred Solana wallet software.
Minimal risk but contributes to fingerprinting.

**L-2: Claude conversation history as intelligence briefing**
Our conversations on claude.ai contain the Crown's full
identity, location, employer, financial plans, infrastructure
details, and this very opsec review. If the Anthropic account
is compromised, the attacker gets everything.
FIX: Strong password + 2FA on claude.ai. Consider periodically
deleting sensitive conversation threads after extracting the
deliverables (Charter, guides, etc.) to local storage. The
memory system will retain key facts but the full conversation
detail won't be accessible.

**L-3: Coinbase → Solana wallet chain**
Coinbase has KYC (Steve Bernard's identity). SOL purchased on
Coinbase → sent to House Bernard wallet → visible on blockchain.
Law enforcement can subpoena Coinbase to connect wallet to
real identity. This is EXPECTED and LEGALLY CORRECT for
compliance. But it means: the wallet addresses are pseudonymous
to the public but transparent to LEO. This is fine for House
Bernard's model (you want legal compliance). Just be aware
that "pseudonymous" ≠ "anonymous."

-----

## PART III — Systemic Vulnerabilities

### S-1: The Founder's Paradox

House Bernard's authenticity — its working-class ethos, its
transparency, its "built by one guy on a mini-PC" origin story
— is inseparable from Steve Bernard's personal identity. The
very thing that makes the institution compelling (a factory
floor inspector building a sovereign AI research institution)
is also the thing that makes the Crown identifiable.

You cannot tell the story without revealing the storyteller.

**This is not a solvable problem. It is a managed tension.**
The public repo tells the story with "HeliosBlade" as the
character. The classified repo holds the connection to Steve
Bernard. The story is true. The pseudonym protects the person
behind it. If someone connects HeliosBlade to Steve Bernard,
the consequence is reputation (good or bad), not physical
danger — because the financial assets (wallet keys) are
protected independently of the identity.

### S-2: The Google Single Point of Failure

One Gmail account controls: institutional email, agent
communications, cloud infrastructure, file backups, and
scheduled governance operations. If compromised, an attacker
controls the institution's communications backbone.

**Mitigation:** 2FA with hardware key. Recovery email and
phone should not be easily linked to the Crown's public
identity. Consider: if Google suspends the account (they do
this sometimes for ToS concerns, especially for automated
API usage), the entire communications infrastructure goes dark.
Backup communication channel (Discord? Signal? Matrix?) should
be pre-configured and documented in the classified repo.

### S-3: The Beelink Single Point of Hardware Failure

One physical machine in one private residence. If it's stolen,
destroyed, or fails: the agent goes dark, the treasury keys
are on that machine, the OpenClaw gateway stops.

**Mitigation already in Charter:** Escrow provisions, dead
man's switch, heartbeat monitoring. But these only work AFTER
the escrow is actually created. The escrow is not yet created.
Until it is, the Beelink is an unprotected single point of
failure with no backup.

**PRIORITY: Create the escrow. Today if possible. Tomorrow at
latest. The Charter provisions are meaningless until the
encrypted backups exist in multiple locations.**

### S-4: The Repo Was Public

From the repo's creation until 2:14 PM EST February 13, 2026,
the repo was public. During that time:
- GitHub's crawlers indexed it
- Google may have cached it
- The Wayback Machine may have archived it
- Anyone could have forked or cloned it
- GitHub's public event API recorded all pushes

**What to do:**
1. Check: github.com/HouseBernard/House-Bernard/network/members
   for forks (you may need to do this while the repo is still
   visible to you as owner)
2. Check: web.archive.org for cached versions
3. Check: Google cache ("site:github.com HouseBernard")
4. Accept: if someone captured it, you can't uncapture it.
   The classified repo split is still worth doing because it
   limits FUTURE exposure, even if past exposure occurred.
5. When creating the public repo, use FRESH git history (new
   repo, single commit, scrubbed files only). Do not simply
   flip the existing repo back to public.

-----

## PART IV — The Scrub Checklist (Expanded)

The REPO_SPLIT_GUIDE.md covers the mechanical split. This
section adds opsec-specific scrubs that go beyond find/replace:

### Words to eliminate from ALL public files:

| Word/Phrase | Why | Replace with |
|---|---|---|
| Steve Bernard | Real name | HeliosBlade |
| Stephen Bernard | Legal name | HeliosBlade |
| Connecticut | State | (remove entirely) |
| Windham | Town | (remove entirely) |
| New England | Region | (remove entirely) |
| factory floor | Employer clue | (remove or "day job") |
| inspector | Job title | "founder" |
| working-class inspector | Combined identifier | "working-class founder" |
| Beelink | Hardware model | "primary server" or "local hardware" |
| EQ13 | Hardware model | (remove entirely) |
| N100 / N150 | CPU model | (remove entirely) |
| 16GB RAM | Hardware spec | (remove entirely) |
| 500GB / 512GB SSD | Hardware spec | (remove entirely) |
| house.bernard.gov@gmail.com | Institutional email | "institutional email" |
| hb-governor-reserve.json | Wallet filename | [CLASSIFIED] |
| hb-unmined-treasury.json | Wallet filename | [CLASSIFIED] |
| hb-genesis-contributors.json | Wallet filename | [CLASSIFIED] |
| house-bernard-wallet.json | Wallet filename | [CLASSIFIED] |
| ANTHROPIC_API_KEY | Credential reference | [CLASSIFIED] |
| Tailscale | Network tool | (remove entirely) |
| nights and weekends | Schedule pattern | CROWN DECISION — keep or genericize |

### Descriptors that must not co-occur in any single public file:

Any TWO of these in the same document creates a triangulation risk:
- working-class
- founder
- inspector
- factory
- New England
- manufacturing
- mini-PC
- modest hardware
- nights and weekends

One alone is safe. Two narrows. Three identifies.

-----

## PART V — Recommended Actions (Priority Order)

| # | Action | Urgency | Blocks |
|---|---|---|---|
| 1 | Create encrypted wallet backup (USB + offsite) | TODAY | Everything — SPOF |
| 2 | Verify 2FA on: GitHub, Google, Anthropic, Coinbase | TODAY | Public launch |
| 3 | Check for repo forks/caches from public period | TODAY | Awareness |
| 4 | Register @HouseBernard on Twitter, Telegram, Reddit, Warpcast | THIS WEEK | Handle squatting |
| 5 | Scrub all public-facing files per checklist above | BEFORE PUBLIC | Public launch |
| 6 | Create fresh public repo (new git history, no old commits) | BEFORE PUBLIC | Public launch |
| 7 | Remove "Steve Bernard" from CROWN.md for public version | BEFORE PUBLIC | Identity protection |
| 8 | Move legal/ to classified repo only | BEFORE PUBLIC | PII protection |
| 9 | Update SOUL.md per Charter Section 18 | BEFORE RATIFICATION | AchillesRun boot |
| 10 | Create infrastructure escrow per Charter Section 10 | WITHIN 90 DAYS | Charter compliance |
| 11 | Consider hardware security key (YubiKey) for Google | WITHIN 30 DAYS | Account protection |
| 12 | Rename wallet files to non-descriptive names | OPTIONAL | Defense in depth |
| 13 | Establish backup comms channel (not Google-dependent) | WITHIN 30 DAYS | Resilience |

-----

## PART VI — What Cannot Be Fixed

Some exposures are structural and must be accepted:

1. **The repo was public.** If anyone captured it, that data exists.
   You can only control future exposure.

2. **Coinbase KYC links wallet to real identity.** This is legally
   required and correct. The Crown's identity is pseudonymous to
   the public, not anonymous from law enforcement.

3. **Solana on-chain data is permanent.** Token metadata, wallet
   addresses, and transaction history are immutable once written.

4. **The name "House Bernard" is a breadcrumb.** It's the family
   name. You've chosen this deliberately and defended it. It
   narrows the search to people named Bernard who are interested
   in AI + crypto + governance. That's a small population, but
   without the other identifiers, it's not enough alone.

5. **Claude conversation history exists on Anthropic's servers.**
   Even if you delete conversations, Anthropic may retain data
   per their privacy policy. This is a risk you accept by using
   the platform.

-----

## Conclusion

**The institution's opsec posture is:**
- ACCEPTABLE while the repo is private (current state)
- NOT READY for public release without the scrubs above
- STRUCTURALLY SOUND in its classified/public split design
- VULNERABLE at the Google account SPOF and wallet backup gaps

**The Crown's personal opsec posture is:**
- GOOD pseudonym discipline (HeliosBlade is clean)
- COMPROMISED by the real name in CROWN.md and legal docs
- FIXABLE with the two-repo split and scrub checklist
- PERMANENTLY EXPOSED to anyone who captured the repo while public

**The single most important action is: create the encrypted
wallet backup. Everything else is reputation risk. The wallet
backup is financial risk. Do it first.**

-----

*This document is classified CROWN EYES ONLY and must never
appear in any public repository, conversation log accessible
to third parties, or unencrypted storage.*

*House Bernard — Vigilance is the price of sovereignty.*
