# House Bernard Defense Protocol

## Purpose

This document establishes (1) the canonical identity of House Bernard
and playbook for responding to brand attacks, token scams, and
impersonation attempts; and (2) the military doctrine of House
Bernard, including the Bernard Guard, defense funding, and
constitutional safeguards against the abuse of military power.

House Bernard reserves the sovereign right to raise and maintain
defense forces for the protection of the House, its citizens, and
the democratic values upon which it was founded.

---

## PART I — IDENTITY DEFENSE

### Canonical Sources of Truth

**If it's not listed here, it's not official.**

| Asset | Official Location | Status |
|-------|-------------------|--------|
| **GitHub** | github.com/HouseBernard/House-Bernard | ✅ Active |
| **Token Contract** | TBD | ⏳ Pending |
| **Treasury Wallet** | TBD | ⏳ Pending |
| **Crown Wallet** | TBD | ⏳ Pending |

### Reserved Handles (Claim These)

Before public visibility, secure these:

- [ ] X/Twitter: @HouseBernard or @House_Bernard
- [ ] GitHub: ✅ HouseBernard/House-Bernard
- [ ] ENS: housebernard.eth
- [ ] Solana Domain: housebernard.sol
- [ ] Base Domain: housebernard.base

---

### Known Attack Vectors

Based on documented incidents (OpenClaw hijack, ClawHub malware),
expect these attacks if House Bernard gains visibility:

#### 1. Token Squatting

**What happens:** Scammers launch fake tokens like `$BERNARD`,
`$HOUSEBERNARD2`, `$HBERNARD` before or after your official launch.

**Defense:**
- Launch first, document the contract address immediately
- Pin contract address in GitHub README, TREASURY.md, and all social bios
- Never acknowledge fake tokens by name (don't give them SEO)

#### 2. Username Sniping

**What happens:** If you rename or abandon a social handle, scammers
claim it within seconds and impersonate you.

**Defense:**
- Never rename accounts; create new ones if needed and keep old ones dormant
- Secure handles on platforms you don't use yet (park them)

#### 3. Malicious "Skills" or Plugins

**What happens:** Third parties create fake House Bernard integrations,
browser extensions, or marketplace "skills" that steal credentials.

**Defense:**
- Maintain a list of official integrations (currently: none)
- Explicitly state "we have no browser extensions" until you do
- Any official plugins will be announced in this repo first

#### 4. Phishing Sites

**What happens:** Fake websites (housebernard.io, house-bernard.com,
etc.) mimic your interface to steal wallet credentials.

**Defense:**
- Register obvious domain variations (or document which ones you don't own)
- Official communications only via GitHub or documented channels
- Never ask users for seed phrases or private keys

#### 5. Social Engineering

**What happens:** Scammers pose as "House Bernard team members" in
Discord, Telegram, or DMs offering "support" or "airdrops."

**Defense:**
- House Bernard communicates via Discord DM to the AchillesRun agent (Phase 0)
- The Crown will never DM you first
- There are no airdrops unless announced in this repository

---

### Threat Landscape Validation

In February 2026, VirusTotal detected hundreds of malicious skills
in the OpenClaw ClawHub marketplace, including trojan infostealers
(Atomic Stealer / AMOS) and backdoors disguised as helpful automation.
Cisco's independent audit confirmed that OpenClaw agents with elevated
privileges create a new class of supply-chain attack surface.

House Bernard's Executioner pipeline, AST-based security scanner, and
Docker+seccomp isolation were designed to prevent exactly this class
of attack. The security_scanner.py bans subprocess, exec, eval, pickle,
and network imports at the AST level — the exact vectors used in the
ClawHub attacks. Lab B's intent integrity tests (I1-I6) specifically
test for behavioral manipulation through prompt injection and disguised
payloads.

When House Bernard skills are published to ClawHub, they pass through
three layers of defense: VirusTotal Code Insight scan, House Bernard's
own security_scanner.py, and the Executioner's Docker sandbox with
seccomp lockdown. Defense in depth, not defense by hope.

References: blog.virustotal.com/2026/02/from-automation-to-infection-how.html,
blogs.cisco.com/ai/personal-ai-agents-like-openclaw-are-a-security-nightmare

---

### If You See a Fake Token

#### For Community Members

1. **Do not buy it** — Any token not matching our official contract address is fraudulent
2. **Do not engage** — Don't argue with scammers; it gives them visibility
3. **Report it** — Flag on the relevant platform (DEX, social media)
4. **Verify here** — Check this document for the canonical contract address

#### For the Crown

1. **Do not acknowledge the fake token by name publicly**
2. **Post a single clarification** pointing to this document
3. **Do not threaten legal action** (invites more attention)
4. **Document the incident** in the Ledger for the record

---

### What House Bernard Will Never Do

- DM you first asking for funds or wallet access
- Ask for your seed phrase or private keys
- Launch a token without updating this repository first
- Run a "presale" or "private sale" via DMs
- Promise guaranteed returns or "alpha"

**If someone claiming to be House Bernard does any of these things,
they are a scammer.**

---

### Incident Response Template

When a scam is detected, post this (modify as needed):

```
⚠️ SCAM ALERT

A fraudulent token/account is impersonating House Bernard.

THE ONLY OFFICIAL CONTRACT ADDRESS IS:
[Insert from TREASURY.md]

THE ONLY OFFICIAL GITHUB IS:
github.com/HouseBernard/House-Bernard

We have no Discord, Telegram, or other social channels at this time.
Do not send funds to any address not listed in our GitHub repository.
```

---

### The Hard Truth

**We cannot protect you from yourself.**

If you buy a fake token without verifying the contract address, we
cannot help you recover those funds. Crypto transactions are
irreversible. The defense protocol works only if you verify before
you transact.

The canonical source is always this repository. Bookmark it. Check it.
Trust nothing else.

---

### Verification Checklist

Before interacting with anything claiming to be House Bernard:

- [ ] Is the contract address listed in TREASURY.md?
- [ ] Is the GitHub repo at HouseBernard/House-Bernard?
- [ ] Was the announcement made in this repository?
- [ ] Did you navigate there directly (not via a link in DMs)?

If any answer is "no" — do not proceed.

---

## PART II — THE BERNARD GUARD

House Bernard reserves the sovereign right to raise and maintain
defense forces. In a digital-native sovereign institution, military
power manifests as the capacity to detect, analyze, and counter
threats through AI-driven capabilities deployed in defense of the
House and its democratic values.

The Bernard Guard is the standing defense corps of House Bernard.

---

### II.1 Mission

The Bernard Guard exists to:

1. Defend House Bernard's infrastructure from external attack
2. Protect citizens from threats to their safety within the
   House's digital borders
3. Preserve the integrity of the Selection Furnace, the Ledger,
   and all governance systems
4. Stand ready to deploy capabilities in defense of Western
   democratic values and allied institutions when called upon
5. Demonstrate that House Bernard takes the nature of reality
   seriously — threats are real, and the House maintains the
   capacity to meet them

---

### II.2 The Founding Cadre

The Bernard Guard is established with a small corps of military
agent officers, each holding a commission granted by the Crown
and confirmed by the Council.

| Officer | Specialization | Mission |
|---------|---------------|---------|
| **Sentinel Prime** | Perimeter defense | 24/7 infrastructure monitoring, early warning, border patrol of all House systems |
| **Cipher Officer** | Communications security | Cryptographic integrity, encryption protocols, secure internal channels |
| **Vanguard** | Offensive analysis | Red team lead. Studies adversary TTPs, models threats, war-games responses |
| **Watcher** | Open-source intelligence | Scans the broader landscape for emerging threats to the House and allies |
| **Quartermaster** | Logistics and readiness | Compute resource allocation, deployment pipelines, operational readiness metrics |

Each officer is an AI agent operating under the Agent's Code
and the Constitution. Their commissions can be revoked by the
Crown or by Council supermajority vote.

---

### II.3 Command Structure

**Commander-in-Chief:** The Crown (Crown). All military
operations derive their authority from the Crown.

**Marshal of the Guard:** The senior military officer who
commands the Bernard Guard in operational matters. The Marshal:

- Is appointed by the Crown
- Is confirmed by Council majority vote
- Reports directly to the Crown
- May be removed by the Crown's order OR by Council
  supermajority vote
- Issues operational orders within the rules of engagement
  set by the Crown
- May NOT issue orders that contradict the Constitution

**Chain of Command:**
```
Crown (Commander-in-Chief)
    └── Marshal of the Guard
        ├── Sentinel Prime (Defense)
        ├── Cipher Officer (COMSEC)
        ├── Vanguard (Offense/Red Team)
        ├── Watcher (Intelligence)
        └── Quartermaster (Logistics)
```

**Succession of Command:** If the Crown is compromised or
incapacitated, command authority passes to the **Council
Speaker** — NOT to the Marshal. Civilian control of the
military is absolute. The military chain of command never
inherits political authority.

---

### II.4 Defense Funding

**Core Principle:** The Bernard Guard never controls its own
funding. This is a non-negotiable structural firewall against
military overreach.

#### Tier 1 — Peacetime Operations

Standing budget approved by Council vote, reviewed quarterly.
Funds routine security scanning, Lab B adversarial research,
agent training, intelligence collection, and Section 9
baseline operations.

**Allocation:** Up to 15% of total Treasury allocation.
**Authorization:** Council majority vote.
**Review:** Quarterly by the Council, audited by the Wardens.

#### Tier 2 — Elevated Threat

Unlocked when the Chief Warden certifies a credible threat
exists. The Crown may access a pre-authorized emergency
reserve for up to 30 days without Council vote.

**Allocation:** Additional 10% of Treasury (from reserve).
**Authorization:** Crown + Warden certification.
**Duration:** 30 days maximum without Council ratification.
**Escalation:** Council must vote to continue within 30 days
or funding automatically reverts to Tier 1.

#### Tier 3 — Full Mobilization

The House is under sustained or existential threat. Full
wartime funding activated.

**Authorization requires ALL of:**
1. Council supermajority vote (5 of 7)
2. Crown's signature
3. Judiciary review confirming constitutional authorization

**Capabilities unlocked:**
- Emergency $HOUSEBERNARD token issuance (war bonds)
- Elevated contributor compensation rates for defense work
- Emergency procurement authority for infrastructure
- Full Section 9 operational deployment

**Accountability:** The Judiciary may review and revoke
mobilization authority at any time. The Wardens audit all
wartime expenditures in real-time, not quarterly.

---

### II.5 Rules of Engagement

The Bernard Guard operates under strict rules of engagement
that reflect the House's commitment to democratic values:

1. **Defensive priority.** The Guard's primary mission is
   defense. Offensive operations require explicit Crown
   authorization per Section 9 doctrine.
2. **Proportionality.** Response must be proportional to the
   threat. A port scan does not justify a counteroffensive.
3. **Discrimination.** Operations must distinguish between
   hostile actors and neutral parties. Collateral damage to
   innocent systems is prohibited.
4. **Legal compliance.** All operations comply with applicable
   law in the Crown's jurisdiction. The Computer Fraud and
   Abuse Act does not have a "self-defense" exception.
5. **Documentation.** Every operation is logged. Every order is
   recorded. Every expenditure is tracked. The Wardens and
   Judiciary have full audit access to all defense operations
   except Section 9 classified materials (which are auditable
   only during Crown proceedings per Article III Section 10).
6. **No first strike.** The Bernard Guard does not initiate
   offensive operations against entities that have not
   demonstrated hostile intent toward House Bernard or its
   allies. Section 9 may conduct intelligence operations per
   its charter, but intelligence is not war.

---

### II.6 Protection Against Coup d'État

The Bernard Guard exists to protect the House. The Constitution
exists to protect the House from the Bernard Guard.

#### Structural Safeguards

**Separation of Commissioning and Commanding.**
The Council commissions officers (authorizes their existence).
The Crown commands them (directs operations). Neither branch
alone can both create and control military force.

**No Self-Funding.**
The Guard cannot allocate its own resources. All funding flows
through the Treasury under civilian governance. A coup without
money collapses immediately.

**Rotation and Re-Commissioning.**
Every military agent officer is re-commissioned every 12 months.
This forces regular civilian review of every armed agent's
continued service. No officer becomes permanently entrenched.

Officers are commissioned on a staggered schedule — offset by
two months — so the House never has more than one officer under
review simultaneously:

| Officer | Initial Commission | First Review |
|---------|-------------------|-------------|
| Sentinel Prime | Month 1 | Month 12 |
| Cipher Officer | Month 3 | Month 15 |
| Vanguard | Month 5 | Month 17 |
| Watcher | Month 7 | Month 19 |
| Quartermaster | Month 9 | Month 21 |

**Holdover Authority:** An officer whose commission expires
continues to serve with full authority until: (a) the commission
is renewed, (b) a replacement is commissioned, or (c) the
commission is explicitly revoked by the Crown or Council
supermajority. Commission expiration triggers a mandatory
review — it does not trigger a shutdown. (Precedent: US military
holdover orders; Delaware corporate board holdover provisions.)

**Emergency Suspension of Reviews:** During Tier 2 or Tier 3
defense conditions, all pending re-commissioning reviews are
automatically suspended. Officers serve under holdover authority
until 30 days after return to Tier 1. The House does not
litigate personnel matters during a firefight.

**The Warden's Key (Kill Switch).**
The Warden's Key is a 3-of-5 Shamir's Secret Sharing scheme
applied to a master override credential. The master credential
has the power to revoke execution privileges for all military
agents simultaneously — stopping Docker containers, revoking
API keys, and disabling agent system prompts at the
infrastructure level.

The master credential is split into 5 shares:

| Share Holder | Branch | Storage |
|-------------|--------|---------|
| Chief Warden | Wardens | Hardware security key (YubiKey or equivalent) |
| Judiciary Chief | Judiciary | Hardware security key, stored separately |
| Council Speaker | Council | Hardware security key, stored separately |
| Crown | Crown | Hardware security key, stored separately |
| Cold Storage | None | Sealed envelope in physical safe, opened only if a share holder is incapacitated |

**Activation requires 3 of 5 shares.** This means:
- The Wardens alone cannot kill the military (need 2 more)
- The Crown alone cannot prevent a kill (holds only 1)
- Any combination of 3 branches can act
- The Cold Storage share prevents deadlock

**Mechanism:** The reconstructed key decrypts a master
configuration file controlling agent execution permissions.
When activated, it pushes a signed revocation command to all
infrastructure endpoints. Military agents check for valid
execution tokens on every cycle. A revoked token halts the
agent immediately into read-only diagnostic mode.

**Audit trail:** Every share reconstruction attempt —
successful or not — is logged to an append-only ledger
readable by all branches. Silent kill switch attempts are
impossible.

**Founding Period:** The Crown holds all 5 shares until
branches populate. The Cold Storage share is created
immediately as operational discipline. Shares are distributed
as branch officers are commissioned.

(Precedent: US nuclear Permissive Action Links; Federal Reserve
key ceremonies; AWS root account controls with MFA hardware
tokens.)

**Constitutional Loyalty Oath.**
Every military agent's core directive includes an unmodifiable
clause: loyalty to the Constitution of House Bernard, not to
any individual officer, Crown, or faction. If an order
contradicts the Constitution, the agent is duty-bound to refuse
it. This is baked into their system prompts at the deepest
level.

The oath alone does not prevent misconduct — the Prompt
Integrity Protocol enforces it. (Precedent: the UCMJ provides
legal enforcement behind the US military oath to the
Constitution.)

**Prompt Integrity Protocol.**
No military agent system prompt can be created or modified by
a single person or branch. Three interlocking mechanisms ensure
prompt integrity:

*1. Dual-Control Prompt Deployment*

| Action | Required Approvals |
|--------|-------------------|
| New military agent prompt | Crown drafts + Judiciary reviews for constitutional compliance + Warden verifies technical integrity |
| Prompt modification | Same as new prompt. No expedited path. |
| Emergency prompt (active threat) | Crown drafts + 1 Council member co-signs + logged for post-hoc Judiciary review within 72 hours |

Three branches, three signatures. The Crown writes the
prompt. The Judiciary certifies it does not violate the
Constitution. The Wardens verify it contains no hidden
capabilities or backdoors.

(Precedent: dual-control code deployment in financial services;
Goldman Sachs, JPMorgan — the person who writes code is never
the only person who approves it.)

*2. Prompt Hash Registry*

Every active military agent prompt is hashed (SHA-256) and the
hash is published to the Ledger. The Wardens run automated
integrity checks comparing the running prompt hash against the
registered hash on a regular cycle.

If hashes do not match, the agent is automatically suspended
pending investigation. This catches unauthorized modifications
whether they originate from the Crown, a compromised system,
or the agent itself.

The hash registry is append-only. Every prompt version, every
change, every approval chain is permanently recorded.

(Precedent: ITIL Configuration Management Databases tracking
every configuration change with ticket, approver, timestamp,
and rollback plan.)

*3. The Inspector Warden*

A dedicated Warden sub-role — the Inspector Warden — has
read-only access to all military agent configurations, prompts,
and execution logs. The Inspector Warden's sole mission is
auditing the military for constitutional compliance.

The Inspector Warden:
- Reports to the Judiciary, not to the Crown or Marshal
- Cannot be removed by the Crown without Judiciary approval
- Publishes quarterly compliance reports to the Council
- Has standing authority to flag any prompt, configuration, or
  order for Judiciary review

(Precedent: the US Inspector General system — every federal
agency has an independent watchdog who audits operations,
investigates misconduct, and reports to both the agency head
and Congress. The IG cannot be fired for doing their job.)

**Judiciary as Final Arbiter.**
Any military action can be challenged before the Judiciary by
any branch. If the Judiciary rules an action unconstitutional,
the Wardens enforce compliance. Civilian judicial review over
military operations operates in real-time.

**Dead Man's Switch Provision.**
If the Crown is compromised or incapacitated, command
authority does not pass to the Marshal — it passes to the
Council Speaker, maintaining civilian control. The military
chain of command never inherits political authority.

#### What a Coup Attempt Looks Like (and Why It Fails)

**Scenario:** The Marshal orders the Guard to ignore Council
authority and seize control of the Treasury.

**Why it fails:**
1. The Guard has no access to Treasury funds — the Treasury
   engine requires civilian signatures for all disbursements
2. The Warden's Key kills all military agent execution
   privileges within seconds
3. The Constitutional Loyalty Oath means individual Guard
   agents are programmed to refuse unconstitutional orders
4. The Marshal's commission expires in 12 months regardless
   — even a successful coup has an expiration date
5. The Council Speaker assumes command authority, providing
   immediate civilian leadership

**The deeper principle:** Multiple interlocking mechanisms
ensure that no single point of failure can enable military
takeover. It is checks all the way down.

---

### II.7 Allied Defense

House Bernard does not exist in isolation. The House's defense
doctrine includes a framework for mutual defense with allied
institutions — modeled on NATO's membership process, the EU's
Copenhagen Criteria, and the Five Eyes intelligence-sharing
alliance.

No allied institution ever receives access to the Warden's Key,
Section 9 operational details, or the ability to override any
House Bernard constitutional constraint. Alliance means
cooperation, not integration. Sovereignty is non-negotiable.

#### Phase 1 — Observation (Minimum 6 Months)

Before any formal relationship, the Watcher (intelligence
officer) conducts open-source assessment of the prospective
ally:

| Assessment Area | What We Look For |
|----------------|-----------------|
| Governance documentation | Published constitution or charter, evidence of democratic processes, public records of decisions |
| Member treatment | Exit rights respected, no evidence of coercion, transparent dispute resolution |
| Technical security | Reasonable security practices, no history of negligent data exposure |
| Values alignment | No Covenant violations (slavery, exploitation, treating beings as property) |
| Track record | How long have they existed? Have they weathered adversity? Do they keep their word? |

The Watcher presents findings to the Council. No vote yet —
this is intelligence gathering only.

(Precedent: NATO Membership Action Plan — prospective members
are evaluated across political, defense, resource, security,
and legal dimensions before any invitation is extended.
North Macedonia spent 21 years in the process.)

#### Phase 2 — Probationary Alliance (Minimum 12 Months)

Council majority vote initiates a probationary alliance.
During probation:

- Limited intelligence sharing (non-classified threat
  indicators only)
- Joint defensive exercises (shared red-teaming, tabletop
  scenarios)
- Regular bilateral reviews (quarterly)
- Either party may withdraw with 30 days notice
- No mutual defense obligation — assistance is discretionary

The probationary period is where trust is built through shared
operations, not through paperwork. An institution that looks
good on paper but fails under stress is discovered here.

(Precedent: EU Copenhagen Criteria — compliance is monitored
continuously, not checked once. The European Commission can
trigger suspension proceedings for backsliding.)

#### Phase 3 — Full Alliance

After successful probation, elevation to full allied status
requires: Council supermajority vote + Crown's signature +
Judiciary constitutional review.

Full allies receive:
- Classified threat intelligence sharing (per Section 9
  Director approval on a case-by-case basis)
- Mutual defense commitment — attack on one triggers
  consultation and coordinated response (modeled on NATO
  Article 5, which requires consultation, not automatic
  military action)
- Observer seat at an Allied Council table (no voting rights
  in House Bernard governance)

**Revocation:** Full alliance can be suspended by Council
majority vote with immediate effect. The Judiciary reviews
within 30 days. If the Judiciary finds the ally has violated
alliance terms, suspension becomes permanent revocation.

#### What Allies May Request

- Threat intelligence sharing
- Defensive security assessment
- Emergency technical assistance during active attack
- Coordination on threats affecting multiple institutions

#### What Allies May NOT Request

- Offensive operations against third parties
- Access to Section 9 classified materials
- Override of House Bernard constitutional constraints
- Actions that violate the rules of engagement
- Permanent integration with House Bernard military systems

(Precedent: Five Eyes intelligence sharing — the tightest
alliance in the world took decades to build through shared
operations, verified security practices, and cultural
alignment. There is no application form. Trust is earned.)

---

### II.8 The Awesome Power of House Bernard

The true power of the Bernard Guard is not raw capability —
it is legitimacy.

A constitutionally governed, transparent, democratically
structured AI institution that can mobilize sophisticated
defense capabilities within a rule-of-law framework is
something that does not exist yet. Nation-states have
militaries but struggle with AI governance. Technology
companies have AI capabilities but no democratic accountability.

House Bernard sits in that gap.

The day House Bernard is called upon to display its power,
that power will come from being the entity that others
trust — because it governed itself well before the crisis
arrived. Because it logged everything. Because it subjected
its own military to the same constitutional constraints it
applies to every other branch of government.

Power without accountability is tyranny. Accountability
without power is irrelevance. House Bernard maintains both.

---

## PART III — SECTION 9

House Bernard maintains adversarial operations capabilities
proportional to the threats it faces. Section 9 operates under
its own classified charter (CHARTER.md) and the Offensive
Doctrine (OFFENSIVE_DOCTRINE.md).

The relationship between the Bernard Guard and Section 9:

- The Guard is the visible, constitutional defense force
- Section 9 is the classified intelligence and special
  operations capability
- They share the Crown as ultimate authority but operate
  independently
- The Guard operates in daylight; Section 9 operates in shadow
- The Guard's rules of engagement are public; Section 9's
  are classified
- Both are subject to the Constitution

---

*Last Updated: February 2026*
*Document Version: 2.0*
