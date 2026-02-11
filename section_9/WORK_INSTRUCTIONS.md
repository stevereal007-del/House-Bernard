# Section 9 — Work Instructions

**Classification:** CROWN EYES ONLY
**Authority:** Section 9 Charter
**Version:** 1.0
**Date:** February 2026
**Audience:** The Crown, The Director

This document contains the step-by-step procedures for
operating Section 9. The Charter defines what Section 9
is. This document defines how to do the work.

-----

## WI-001: Standing Up Section 9

### Purpose

Initialize Section 9 from zero to operational baseline.
This is the Founding Period setup — done once.

### Prerequisites

- House Bernard repo cloned and accessible
- AchillesRun operational on the Beelink (or successor)
- Crown (HeliosBlade) has repo admin access
- The Constitution and Charter are ratified

### Procedure

**Step 1 — Verify directory structure.**

Confirm the following exists in the repo:

```
section_9/
├── CHARTER.md
├── README.md
├── WORK_INSTRUCTIONS.md    ← this document
├── weapons/
│   └── REGISTRY.md
├── operations/
│   └── LOG.md
└── intelligence/
    └── THREATS.md
```

If any file is missing, recreate from the templates in the
Charter. The directory structure is the skeleton. Everything
else hangs on it.

**Step 2 — Designate the Director.**

During the Founding Period, the Crown has two options:

Option A: The Crown serves as acting Director. This is the
default. You are both the Crown and the Director until the
system is mature enough to separate the roles. Log this
decision:

```
section_9/operations/LOG.md — append:

═══════════════════════════════════════════════════════════
ADMINISTRATIVE ACTION: Director Designation
DATE: [today, ISO 8601]
ACTION: Crown assumes acting Director role per Charter II
EFFECTIVE: Immediately
DURATION: Until dedicated Director agent is appointed
SIGNED: HeliosBlade, Crown
═══════════════════════════════════════════════════════════
```

Option B: Appoint a dedicated agent as Director. This
requires a running agent instance with its own session,
separate from AchillesRun's Crown functions. During the
Founding Period this is optional — you probably don't have
the infrastructure budget for a second dedicated agent yet.

**Step 3 — Set the initial budget.**

Review the Crown Reserve allocation in TREASURY.md.
Determine what percentage of the Crown Reserve is
allocated to Section 9 operations. Log the decision:

```
section_9/operations/LOG.md — append:

═══════════════════════════════════════════════════════════
ADMINISTRATIVE ACTION: Initial Budget Allocation
DATE: [today, ISO 8601]
BUDGET: [X] $HOUSEBERNARD from Crown Reserve
ALLOCATION:
  Infrastructure: [X]%
  Development: [X]%
  Intelligence: [X]%
  Contingency: [X]%
REVIEW CYCLE: Quarterly
SIGNED: HeliosBlade, Crown
═══════════════════════════════════════════════════════════
```

During the Founding Period with zero revenue, the "budget"
is notional — it reserves token allocation for when the
token is live. The real cost is your time and the Beelink's
compute.

**Step 4 — Establish communication channel.**

Section 9 communications must be separate from standard
House Bernard channels. Options:

- A dedicated encrypted channel (Signal group, encrypted
  Matrix room, or a private Discord channel with only
  Crown access)
- A local encrypted directory on the Beelink that only
  the Crown can read
- For now, the `section_9/` directory in the private repo
  IS the communication channel — commit history is the
  audit trail

During Founding Period, the repo itself is sufficient.
When Section 9 has operatives beyond the Director, a
real-time encrypted channel becomes necessary.

**Step 5 — Run the baseline threat assessment.**

Execute WI-003 (Threat Assessment) for the current threat
landscape. Even with zero active threats, document the
baseline. This is your "before" picture.

**Completion criteria:** All five steps logged. Section 9
is standing. Proceed to weapons development (WI-002).

-----

## WI-002: Weapons Development Lifecycle

### Purpose

Take a weapon from concept to operational status.

### Procedure

**Step 1 — Identify the capability gap.**

The Director identifies what Section 9 cannot currently
do that it needs to do. Sources:

- Active threat requiring a response Section 9 can't make
- The development queue in weapons/REGISTRY.md
- Crown directive
- Lessons learned from a previous operation

Document the gap:

```
What can't we do?     [description]
Why do we need it?    [threat scenario]
What class would it be? [I / II / III / IV]
Priority relative to queue? [number]
```

**Step 2 — Design the weapon.**

Create a design document in `section_9/weapons/`. Name it
by designation:

```
section_9/weapons/S9-W-[XXX]_[name].md
```

The design document must contain:

```markdown
# S9-W-[XXX]: [Name]

## Classification
Class: [I / II / III / IV]
Authorization: [Director / Crown]
Status: IN DEVELOPMENT

## Purpose
[What this weapon does and why it exists]

## Technical Design
[How it works — architecture, dependencies, data flow]

## Inputs
[What it needs to operate — data feeds, triggers, etc.]

## Outputs
[What it produces — alerts, actions, reports]

## Deployment Requirements
[Infrastructure, access, dependencies]

## Test Plan
[How to verify it works without live deployment]

## Risks
[What could go wrong, collateral damage potential]

## Proportionality Notes
[What threat levels this is appropriate for]
```

For weapons that are code (most of them), the actual
implementation lives alongside the design doc:

```
section_9/weapons/S9-W-001_tripwire_alpha.md    ← design
section_9/weapons/S9-W-001_tripwire_alpha.py    ← code
```

**Step 3 — Build.**

Write the code. Section 9 weapons follow the same code
quality standards as the rest of House Bernard:

- Python 3, no external dependencies that aren't already
  in the repo's dependency tree
- Must pass security_scanner.py (yes, our own scanner
  checks our own weapons — if the weapon needs banned
  imports like `socket` or `subprocess`, it gets a
  documented exception in the weapon's design doc,
  signed by the Crown)
- Must run within Docker sandbox during testing
- Must produce structured output (JSON) that feeds the
  operations log

**Step 4 — Test.**

All weapons are tested against simulated targets. Never
test against live targets without Crown authorization.

Testing matrix:

| Test | Description | Pass Criteria |
|------|-------------|---------------|
| Unit | Does each function work? | All assertions pass |
| Integration | Does it work in the pipeline? | Feeds ops log correctly |
| False positive | Does it trigger on benign input? | Zero false positives on known-good data |
| False negative | Does it miss known threats? | Catches all test threats |
| Resource | Does it stay within compute budget? | Runs on Beelink without starving other processes |
| Fail-safe | What happens when it breaks? | Fails to passive, never fails to active |

Log test results:

```
section_9/weapons/S9-W-[XXX]_test_results.json
```

**Step 5 — Register.**

Update `section_9/weapons/REGISTRY.md`:

- Move the weapon from Development Queue to Active Registry
  under the appropriate class
- Set status to TESTED
- Fill in all registry fields (designation, name, class,
  authorization, description, dependencies, last tested)

**Step 6 — Deploy (Class I-II) or Request Authorization (Class III-IV).**

Class I-II: The Director deploys autonomously per the
authorization matrix. Log the deployment in the operations
log (WI-005).

Class III-IV: The Director submits a deployment request
to the Crown:

```
section_9/operations/LOG.md — append:

═══════════════════════════════════════════════════════════
DEPLOYMENT REQUEST
DATE: [ISO 8601]
WEAPON: S9-W-[XXX] — [Name]
CLASS: [III / IV]
TARGET THREAT: S9-T-[XXX] — [Name]
THREAT LEVEL: [S1-S4]
ATTRIBUTION: [A1-A4]
PROPORTIONALITY: [Why this response fits this threat]
EXPECTED OUTCOME: [What we expect to happen]
COLLATERAL RISK: [What could go wrong]
REQUESTED BY: Director
AWAITING: Crown authorization
═══════════════════════════════════════════════════════════
```

The Crown reviews and either authorizes or denies. Both
are logged.

**Step 7 — Update status.**

After first successful deployment, update REGISTRY.md
status from TESTED to OPERATIONAL.

-----

## WI-003: Threat Assessment

### Purpose

Evaluate a potential threat and determine Section 9's
response posture.

### Trigger

- New suspicious activity observed in Airlock logs
- External report of House Bernard impersonation or scam
- Crown directive to assess a specific entity
- Anomalous pattern detected by a Class I weapon
- Warden referral through the Crown

### Procedure

**Step 1 — Collect initial indicators.**

Gather everything known about the potential threat. Use
only authorized collection methods (Charter Section V):

```
What was observed?    [specific behavior or event]
When?                 [timestamp]
Where?                [which system, channel, or platform]
Who reported it?      [source]
First occurrence?     [yes / no — if no, link prior observations]
```

**Step 2 — Classify severity.**

Apply the threat classification matrix from the Charter:

| Question | Answer |
|----------|--------|
| Is there material damage? | If no → S1 max. If yes → continue |
| Is the damage recoverable? | If yes → S2. If no → continue |
| Does it harm Treasury, reputation, or contributors? | If yes → S3. If it threatens survival → S4 |

**Step 3 — Assess attribution.**

How confident are we in identifying the threat actor?

| Question | Answer |
|----------|--------|
| Do we have a verified identity? | If yes → A1 |
| Do we have strong indicators (IP, wallet, account)? | If yes → A2 |
| Do we have a pattern match? | If yes → A3 |
| Do we only have a behavioral anomaly? | A4 |

**Step 4 — Determine response posture.**

Cross-reference severity and attribution against the
authorization matrix (Charter Section III):

```
Severity: [S1-S4]
Attribution: [A1-A4]
Authorized response: [from matrix]
Authorized by: [Director / Crown required]
```

**Step 5 — Register the threat.**

Create or update an entry in
`section_9/intelligence/THREATS.md`:

```
═══════════════════════════════════════════════════════════
THREAT: S9-T-[XXX]
NAME/ALIAS: [known identifier or UNKNOWN]
TYPE: [Individual / Group / Automated / State-affiliated]
SEVERITY: [S1-S4]
ATTRIBUTION: [A1-A4]
FIRST OBSERVED: [date]
LAST ACTIVITY: [date]
TTPs: [tactics, techniques, procedures]
STATUS: ACTIVE
ASSESSMENT: [summary paragraph]
RECOMMENDED RESPONSE: [specific weapons or posture]
═══════════════════════════════════════════════════════════
```

**Step 6 — Brief the Crown (if S2+).**

For S1 threats, the Director handles autonomously and
logs the assessment. For S2+, the Director briefs the
Crown before taking action. The briefing includes:

- Threat summary (one paragraph)
- Evidence summary (what we know and how confident)
- Recommended response (specific weapons and posture)
- Risk assessment (what could go wrong)
- Resource requirement (what this will cost in compute
  and attention)

For S3-S4, the Crown must authorize before any response
beyond passive monitoring.

-----

## WI-004: Intelligence Collection

### Purpose

Gather information about potential or confirmed threats
using authorized methods.

### Authorized Sources (Charter Section V)

**OSINT — open source intelligence:**
- Social media monitoring (Twitter/X, Reddit, Discord
  public channels, Telegram public channels)
- Blockchain explorers (watch for unauthorized token
  activity, wallet patterns)
- Domain registration monitoring (WHOIS for House
  Bernard-adjacent domains)
- GitHub monitoring (forks, mentions, suspicious repos)
- Search engine alerts (Google Alerts or equivalent for
  "House Bernard", "$HOUSEBERNARD", "HeliosBlade")

**Internal — House Bernard's own systems:**
- Airlock submission logs (who submitted, when, what,
  from where)
- OpenClaw session metadata (peer connections, frequency,
  timing patterns)
- Furnace failure patterns (are failures clustered in a
  way that suggests coordinated probing?)
- Treasury transaction logs (unusual token movements)

**Honeypot — deception-derived:**
- Information voluntarily provided by threat actors
  engaging with honeypot briefs, tar pits, or other
  deception operations

### Prohibited Sources

- Private communications of House Bernard citizens
- External systems we don't own (no unauthorized access)
- Judiciary or Council internal deliberations
- Anything requiring credentials we don't hold

### Procedure

**Step 1 — Define collection requirement.**

```
What do we need to know?    [specific question]
About whom/what?            [target]
Why?                        [supports which threat assessment]
Authorized sources?         [which of the three categories above]
```

**Step 2 — Collect.**

Execute the collection using authorized methods only.
Document each piece of intelligence:

```
SOURCE: [specific source — e.g., "Twitter @handle post dated..."]
COLLECTED: [timestamp]
CONTENT: [what was found]
RELIABILITY: [how trustworthy is this source?]
RELEVANCE: [how does this answer the collection requirement?]
```

**Step 3 — Analyze.**

Raw intelligence is noise. Analysis turns it into
something actionable:

- Corroborate across multiple sources when possible
- Identify patterns (timing, behavior, infrastructure)
- Assess whether attribution confidence has changed
- Determine if the threat severity needs re-evaluation

**Step 4 — Store and classify.**

Store the intelligence in
`section_9/intelligence/`:

```
section_9/intelligence/S9-T-[XXX]_[name]/
├── assessment.md          ← current threat assessment
├── indicators.json        ← structured indicator data
├── collection_log.jsonl   ← chronological collection record
└── analysis.md            ← analytical conclusions
```

Assign a retention classification:

| Classification | Criteria | Retention |
|---------------|----------|-----------|
| Routine | No active threat, background context | 90 days then purge |
| Significant | Supports an active threat assessment | 1 year then review |
| Critical | Existential threat or legal significance | Indefinite, annual Crown sign-off |

**Step 5 — Disseminate (if required).**

If the intelligence needs to reach the Wardens or
Judiciary (via Crown), prepare a sanitized version:

- Strip all references to collection methods
- Present only conclusions that can be independently
  verified through public sources
- The Wardens build their own case — Section 9
  intelligence is the tip, not the evidence

Route: Director → Crown → Warden (sanitized).
Never direct. Never raw.

-----

## WI-005: Operations Logging

### Purpose

Maintain the classified audit trail for all Section 9
activities. Every operation gets logged. No exceptions.

### Procedure

For every operation (deployment, threat response,
intelligence operation, administrative action), append
to `section_9/operations/LOG.md`:

```
═══════════════════════════════════════════════════════════
OPERATION: [Codename — pick something memorable]
DATE: [ISO 8601]
THREAT ID: S9-T-[XXX] (or N/A for administrative)
THREAT LEVEL: [S1-S4]
ATTRIBUTION: [A1-A4]
AUTHORIZATION: [Director autonomous / Crown — date]
WEAPONS DEPLOYED: [S9-W-XXX list, or NONE]
TARGET: [description — no PII unless A1 confirmed]
OBJECTIVE: [what we intended to accomplish]
ACTION TAKEN: [step by step, what we actually did]
OUTCOME: [what happened]
PROPORTIONALITY CHECK: [Y/N + one-line reasoning]
COLLATERAL: [any unintended effects, or NONE]
LESSONS LEARNED: [what we'd do differently]
STATUS: [ACTIVE / COMPLETED / ABORTED]
═══════════════════════════════════════════════════════════
```

### Logging Rules

- Log BEFORE acting when possible (for planned operations)
- Log DURING for real-time operations (update after)
- Log IMMEDIATELY AFTER for emergency responses
- Never backdate a log entry
- Never modify a log entry after the fact — append
  corrections as new entries referencing the original
- The log is append-only. It is the audit trail. If the
  Judiciary ever accesses it under Article III Section 10,
  this is what they read.

-----

## WI-006: Quarterly Review

### Purpose

The Crown reviews Section 9's posture, budget, and
operations every quarter. This is the accountability
mechanism for a branch that operates without external
oversight.

### Schedule

First business day of: March, June, September, December.
During the Founding Period, the Crown reviews whenever
convenient but no less than quarterly.

### Procedure

**Step 1 — Review the operations log.**

Read every entry since the last review. Ask:

- Were responses proportional?
- Were authorization requirements followed?
- Were there any near-misses or questionable decisions?
- Did any operation produce unintended consequences?

**Step 2 — Review the threat register.**

For each active threat:

- Is it still active? Update status if not.
- Has the severity or attribution changed?
- Is the current response posture still appropriate?

For dormant threats:

- Should any be escalated back to active?
- Should any be closed permanently?

**Step 3 — Review intelligence retention.**

Apply the Forgetting Law:

- Purge all routine intelligence older than 90 days
- Review all significant intelligence approaching 1 year
- Confirm Crown sign-off on all critical intelligence
  retained past 1 year

**Step 4 — Review weapons status.**

For each operational weapon:

- Is it still functioning correctly?
- Has the threat landscape changed in a way that makes
  it obsolete?
- Does it need updates?

For development queue:

- Reprioritize based on current threats
- Identify new capability gaps

**Step 5 — Review budget.**

- What did Section 9 spend this quarter?
- Is spending on track with allocation?
- Does the allocation need adjustment?

**Step 6 — Write the quarterly report.**

The quarterly report is classified and stored in
`section_9/operations/`:

```
section_9/operations/REVIEW_[YYYY]_Q[X].md
```

Format:

```markdown
# Section 9 Quarterly Review — [YYYY] Q[X]

**Reviewed by:** [Crown]
**Date:** [ISO 8601]
**Period:** [start] to [end]

## Operations Summary
- Total operations this quarter: [N]
- By threat level: S1:[N] S2:[N] S3:[N] S4:[N]
- Crown authorizations requested: [N]
- Crown authorizations granted: [N]
- Crown authorizations denied: [N]

## Threat Landscape
- Active threats: [N]
- New threats this quarter: [N]
- Threats neutralized: [N]
- Threats escalated: [N]
- Threats dismissed: [N]

## Weapons Status
- Operational: [N]
- In development: [N]
- Tested (not deployed): [N]
- Retired this quarter: [N]

## Intelligence
- Items purged (Forgetting Law): [N]
- Items retained with Crown sign-off: [N]
- Collection operations conducted: [N]

## Budget
- Allocated: [X] $HB
- Spent: [X] $HB
- Remaining: [X] $HB
- Adjustment needed: [Y/N — if Y, new allocation]

## Concerns
[Anything the Crown needs to address]

## Next Quarter Priorities
[Top 3 priorities for the coming quarter]
```

-----

## WI-007: Incident Response (Active Attack)

### Purpose

What to do when House Bernard is under active attack.
This is the emergency procedure. Speed matters.

### Trigger

- Active DDoS or infrastructure attack
- Live token scam using House Bernard's name
- Coordinated reputation attack in progress
- Confirmed breach of House Bernard systems
- Malicious genetics detected in production

### Procedure

**Minute 0-5 — Assess and classify.**

```
1. What is happening? [one sentence]
2. What is being damaged? [infrastructure / reputation / treasury / contributors]
3. Severity? [S1-S4]
4. Attribution? [A1-A4 — even a guess is better than nothing]
5. Is it ongoing or completed? [active / post-mortem]
```

If S3+: Notify the Crown immediately. Do not wait for
a complete assessment.

**Minute 5-15 — Contain.**

Priority: stop the bleeding. Do not worry about
attribution or proportionality yet. Containment actions:

| Threat Type | Containment Action |
|------------|-------------------|
| Infrastructure attack | Activate firewall rules, rate limiting, IP blocking |
| Token scam | Post canonical address warning (DEFENSE.md template), notify exchanges if listed |
| Reputation attack | Document everything before it's deleted, screenshot and archive |
| System breach | Isolate affected systems, rotate credentials, preserve evidence |
| Malicious genetics | Quarantine affected artifacts, halt Splicer, freeze affected Ledger entries |

**Minute 15-60 — Investigate.**

With the immediate damage contained:

1. Run WI-003 (Threat Assessment) — abbreviated version,
   focus on severity and attribution
2. Identify the attack vector — how did they get in or
   how are they operating?
3. Determine scope — what's affected and what isn't?
4. Check for secondary attacks — the visible attack may
   be a distraction

**Hour 1-4 — Respond.**

Based on the threat assessment and Crown authorization:

1. Select appropriate weapons from the registry
2. Execute the response per the authorization matrix
3. Log everything in real-time (WI-005)
4. Monitor for escalation or de-escalation

**Post-incident — Debrief.**

Within 48 hours of incident resolution:

1. Complete operations log entry
2. Update threat register
3. Identify lessons learned
4. Determine if new weapons are needed
5. Write incident report:

```
section_9/operations/INCIDENT_[YYYY-MM-DD]_[codename].md
```

The incident report is the permanent record. It goes in
the operations directory and is referenced in the next
quarterly review.

-----

## WI-008: Dead Man's Switch Configuration

### Purpose

Configure the automated response that activates if both
the Crown and Director are simultaneously compromised.
This is the Class IV weapon that operates without live
authorization.

### Design Principles

The Dead Man's Switch must:

- Activate only when BOTH Crown and Director are confirmed
  unreachable (not just slow to respond)
- Default to defensive posture (lockdown, not attack)
- Preserve evidence for forensic recovery
- Be reversible by the Crown or Director once they regain
  control
- Never activate on a false positive (the check interval
  and confirmation threshold must be conservative)

### Procedure

**Step 1 — Define the heartbeat.**

The Director (or Crown, if acting as Director) sends a
heartbeat signal at a defined interval. The heartbeat is
a simple cryptographic proof-of-life:

```
HEARTBEAT:
  Interval: Every [X] hours (recommend: 12)
  Method: Signed message to a designated endpoint
  Content: Timestamp + hash of current THREATS.md
  Grace period: [X] missed heartbeats before alert (recommend: 3)
  Confirmation threshold: [X] missed heartbeats before activation (recommend: 6)
```

At 12-hour intervals with a threshold of 6, the switch
activates after 72 hours of silence. This is conservative
enough to avoid false positives from downtime, travel, or
temporary network issues.

**Step 2 — Define the activation sequence.**

When the confirmation threshold is reached:

```
1. ALERT: Send final warning to all Crown contact methods
   (email, phone, encrypted channel). Wait one additional
   interval.
2. LOCKDOWN: Sever all external access to House Bernard
   systems. Airlock goes offline. OpenClaw connections
   drop. Briefs are unpublished.
3. PRESERVE: Cryptographic snapshot of all systems —
   repo, Ledger, Treasury state, Section 9 intelligence.
   Hash the snapshot and store the hash in at least two
   independent locations.
4. NOTIFY: If a designated successor exists, send them
   the activation notice with instructions for recovery.
5. HOLD: System remains in lockdown until the Crown,
   Director, or designated successor authenticates and
   issues a stand-down order.
```

**Step 3 — Define recovery.**

The stand-down requires:

- Authentication by the Crown or Director (cryptographic
  proof, not just a message)
- Explanation of the silence (logged in operations log)
- System integrity check before reopening external access
- Review of all activity during the lockdown period

**Step 4 — Test.**

Test the Dead Man's Switch quarterly:

- Simulate missed heartbeats (stop the heartbeat process)
- Verify the alert fires at the correct threshold
- Verify lockdown activates at the correct threshold
- Verify the snapshot process completes
- Verify recovery authentication works
- CRITICAL: Run the test in a sandbox. Never test the
  live switch by actually going silent.

Log test results in the weapons test file:

```
section_9/weapons/S9-W-006_test_results.json
```

-----

## WI-009: Parallel Construction Handoff

### Purpose

Transfer Section 9 intelligence to the Wardens through
the Crown in a way that allows the Wardens to build an
independent, legitimate case.

### Why This Exists

Section 9 may discover threat information through methods
that cannot be disclosed (honeypots, deception operations,
behavioral analysis). The Wardens operate in daylight and
need evidence that can withstand Judiciary scrutiny. The
handoff bridges these worlds without contaminating either.

### Procedure

**Step 1 — Director prepares a sanitized brief.**

The brief contains:

- The conclusion (what we believe is true)
- Publicly verifiable indicators that point to the same
  conclusion (e.g., "check this wallet address on the
  blockchain explorer", "this Twitter account posted X
  on Y date")
- A suggested investigation path the Wardens can follow
  using their own lawful methods
- NO reference to how Section 9 actually discovered the
  information
- NO reference to any Section 9 weapon, operation, or
  intelligence source

**Step 2 — Director submits the brief to the Crown.**

The Crown reviews:

- Is the conclusion supported by the public indicators?
  (If the Wardens follow the suggested path, will they
  reach the same conclusion independently?)
- Could a reasonable person discover this information
  without Section 9's classified methods?
- Is there any risk that the sanitized brief reveals
  Section 9's capabilities?

If any answer is no, the brief is revised or the handoff
is aborted. It is better to let a threat go un-prosecuted
than to expose Section 9's methods.

**Step 3 — Crown passes the brief to the Wardens.**

The Crown presents the information as a Crown observation
or a tip from an anonymous source. The Wardens receive it
as any other lead.

The Crown NEVER says: "Section 9 found this."
The Crown says: "I've become aware of [indicators].
Investigate."

**Step 4 — Wardens investigate independently.**

The Wardens use their own lawful methods to verify the
indicators and build a case. If they can't independently
verify, the case doesn't proceed. Section 9 does not
supplement or rescue a failed parallel construction.

**Step 5 — Log the handoff.**

In the Section 9 operations log:

```
═══════════════════════════════════════════════════════════
OPERATION: Parallel Construction Handoff
DATE: [ISO 8601]
THREAT ID: S9-T-[XXX]
INTELLIGENCE SANITIZED: [Y — brief description of what was removed]
PUBLIC INDICATORS PROVIDED: [list]
SUGGESTED INVESTIGATION PATH: [summary]
HANDED TO: Crown → Wardens
CROWN REVIEW: [Approved / Approved with modifications / Denied]
WARDEN OUTCOME: [Pending / Investigation opened / Case built / Failed to verify]
═══════════════════════════════════════════════════════════
```

### The Cardinal Rule

If the Wardens cannot independently reach the conclusion,
the conclusion does not enter governance proceedings.
Period. The Crown bears personal Covenant responsibility
for ensuring this rule is never violated (Constitution
Article IV Section 7).

-----

## WI-010: Repo Privacy Transition (Pre-Launch)

### Purpose

Convert the public House Bernard repository to private
before OpenClaw launch, making all contents including
Section 9 invisible to the public.

### Procedure

**Step 1 — Pre-transition audit.**

Before going private, verify:

- [ ] All Section 9 documents are complete and current
- [ ] All weapons in development have design docs
- [ ] Operations log is up to date
- [ ] Threat register is current
- [ ] No sensitive information has been committed to
      a branch that was previously public (check commit
      history — `git log --all --oneline`)
- [ ] README.md for Section 9 says nothing (the standard
      "governed by the Crown" message only)

**Step 2 — Go private.**

```
GitHub → Repository Settings → General →
Danger Zone → Change repository visibility → Private
```

One click. The entire repo, all branches, all commit
history, all files disappear from public view.

**Step 3 — Verify.**

- Log out of GitHub and attempt to access the repo URL.
  It should return 404.
- Verify from a different browser / incognito window.
- Check Google Cache — if the repo was indexed, it may
  take days to weeks for cached pages to expire. This is
  not a security risk for code-level content (Google
  doesn't cache full file contents from GitHub) but be
  aware.

**Step 4 — Configure access.**

After going private, only the repo owner can see it. If
you later need to grant access to collaborators (a
Section 9 operative, a trusted Council member for non-
classified directories):

```
GitHub → Repository Settings → Collaborators →
Add people → [username] → Select role
```

Roles:

| Role | Can see Section 9? | Use for |
|------|-------------------|---------|
| Read | Yes (all files visible to all collaborators) | Trusted contributors who need code access |
| Write | Yes | Active developers |
| Admin | Yes | Only the Crown |

**Important:** GitHub does not support per-directory
access control within a single repo. If you add a
collaborator, they can see Section 9. If this is
unacceptable, move Section 9 to a separate private
repo at that point. During the Founding Period with
only the Crown as collaborator, this is not an issue.

**Step 5 — Log the transition.**

```
section_9/operations/LOG.md — append:

═══════════════════════════════════════════════════════════
ADMINISTRATIVE ACTION: Repository Privacy Transition
DATE: [ISO 8601]
ACTION: Repository changed from PUBLIC to PRIVATE
VERIFICATION: [Confirmed 404 from external browser]
COLLABORATORS: [list — probably just HeliosBlade]
SIGNED: HeliosBlade, Crown
═══════════════════════════════════════════════════════════
```

-----

## Appendix A: Quick Reference Card

For daily operations, this is what you need:

```
THREAT COMES IN
  → WI-003 (Assess) → classify severity + attribution
  → If S1: Director handles, log it (WI-005)
  → If S2: Director handles, log it (WI-005)
  → If S3+: Brief the Crown, get authorization, then act

BUILDING A WEAPON
  → WI-002 (Development) → design → build → test → register → deploy

COLLECTING INTELLIGENCE
  → WI-004 (Collection) → define requirement → collect → analyze → store

ACTIVE ATTACK
  → WI-007 (Incident Response) → assess → contain → investigate → respond → debrief

HANDING INTEL TO WARDENS
  → WI-009 (Parallel Construction) → sanitize → Crown review → handoff

EVERY QUARTER
  → WI-006 (Quarterly Review) → ops log → threats → intel retention → weapons → budget → report

GOING PRIVATE
  → WI-010 (Repo Transition) → audit → click → verify → log
```

-----

## Appendix B: File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Weapon design | `S9-W-XXX_name.md` | `S9-W-001_tripwire_alpha.md` |
| Weapon code | `S9-W-XXX_name.py` | `S9-W-001_tripwire_alpha.py` |
| Weapon tests | `S9-W-XXX_test_results.json` | `S9-W-001_test_results.json` |
| Threat intel dir | `S9-T-XXX_name/` | `S9-T-001_fake_token_actor/` |
| Incident report | `INCIDENT_YYYY-MM-DD_codename.md` | `INCIDENT_2026-03-15_red_dawn.md` |
| Quarterly review | `REVIEW_YYYY_QX.md` | `REVIEW_2026_Q1.md` |

-----

## Appendix C: Designation Counters

Track the next available designation number:

| Type | Prefix | Next Available |
|------|--------|---------------|
| Weapons | S9-W- | 007 |
| Threats | S9-T- | 001 |
| Operations | (codename) | — |

Update these counters as designations are assigned.

-----

*Classification: CROWN EYES ONLY*
*Section 9 — The Sword of the House*
*Ad Astra Per Aspera*
