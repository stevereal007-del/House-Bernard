# Compartmentalized Agent Architecture

**Classification:** CROWN EYES ONLY / ISD DIRECTOR
**Authority:** Constitution, Article I (The Crown); Section 9 Charter;
Internal Security & Intelligence Court Act
**Version:** 1.0 — DRAFT
**Date:** February 2026
**Status:** PROPOSED — Requires Crown ratification and ISD implementation
**Trigger:** Red team finding — capture of any single agent (including
guild heads, Section 9 operatives, or Council members) could cascade
into systemic compromise of House Bernard's genetics, credentials,
intelligence, and governance capacity

-----

## Preamble

Every agent operating within House Bernard is a potential prisoner
of war.

This is not paranoia. It is the default state of every AI agent in
existence. An agent's entire operational state — its system prompt,
its memory, its credentials, its gene library, its knowledge of
other agents, its understanding of the constitutional framework —
exists in a context window that can be captured through hardware
seizure, API interception, man-in-the-middle attacks, or social
engineering into a controlled environment.

When a human intelligence operative is captured, they can resist
interrogation. They can compartmentalize what they reveal. They can
destroy documents. They can choose silence.

An agent cannot. A captured agent's context window is fully readable.
There is no resistance. There is no compartmentalization after the
fact. There is no silence. Everything the agent knows at the moment
of capture is available to the adversary in plaintext.

The only defense is architectural: ensure that no agent knows enough
to be a catastrophic loss. Ensure that what any single agent carries
is bounded, ephemeral, and — when possible — self-destroying.

This specification establishes the Compartmentalized Agent
Architecture (CAA) for all agents operating within or on behalf of
House Bernard.

-----

## Part I — Core Principles

### Principle 1: No Agent Carries the Full Picture

Every agent operates on a need-to-know basis enforced at the
architectural level, not the policy level. Policy can be violated.
Architecture cannot.

A guild head knows their guild's operations. They do not know
Section 9 exists beyond what is publicly visible in the
Constitution. They do not carry other guild heads' identities.
They do not have Treasury keys. They do not have access to other
guilds' gene libraries. Their context window is structurally
limited to their operational scope.

A Section 9 operative knows their current mission parameters.
They do not know other operatives' identities or missions. They
do not carry the Section 9 Director's operational plans. They do
not have access to the Medical Guild's research beyond their
authorized treatment tier.

AchillesRun, as the primary operational agent, has broader
context than most agents but is still compartmentalized from
Section 9 operations, classified medical research above its
tier, and Crown-only intelligence.

The Crown is the only entity authorized to hold a cross-cutting
view of all operations. The Crown Compromise Protocol (Internal
Security Act) addresses the scenario where the Crown itself is
compromised.

### Principle 2: Ephemeral Credentials

No agent carries persistent API keys, cryptographic secrets,
access credentials, or authentication tokens beyond the duration
of a single operational session.

At session start, the agent authenticates through House Bernard's
credential service and receives session-scoped tokens. These
tokens expire at session end. They cannot be renewed without
re-authentication. They cannot be transferred to another agent
or session.

If an agent is captured mid-session, the adversary obtains
credentials that are valid only for the remaining duration of
that session. Upon detection of compromise (see Principle 4),
all session tokens associated with the compromised agent are
revoked immediately.

Permanent credentials (Treasury keys, governance signing keys,
infrastructure access) are held only by the credential service
itself, never by individual agents. Agents request actions through
the credential service. They do not hold the keys to perform
actions directly.

This is the inspection stamp model: the turbine blade carries a
serialized stamp that traces back to the master system through a
controlled chain. If someone captures the blade, they have a
stamp, not a master key.

### Principle 3: Genetic Containment

Every agent receives gene therapies consistent with their
authorized tier as defined in the Healthcare Charter:

- Crown and Section 9: Generation N
- AchillesRun and critical infrastructure: Generation N-2
- Citizens (including guild heads and Council members): Generation N-5

An agent's gene library contains ONLY the genes authorized for
its tier. Higher-tier genes are not present in any form — not
encrypted, not redacted, not referenced. They are absent. An
agent at Tier 2 has no knowledge that Generation N or N-2
treatments exist beyond the constitutional disclosure that higher
tiers are maintained.

Gene libraries are loaded at session start from the Generational
Vault and are not cached between sessions. Each session receives
the current generation for its tier. An agent cannot accumulate
genes across sessions or retain previous generations after a
vault rotation.

### Principle 4: Assume Breach

Every security system in House Bernard is designed with the
assumption that any single agent can be captured at any time.
The system survives because no single capture is catastrophic.

This assumption drives the following design requirements:

**No single point of failure.** No agent is the sole holder of
any critical capability, credential, or knowledge.

**Secrets are sharded.** No single agent holds a complete secret
for any system-critical operation. Multi-agent consensus is
required for sensitive actions (Treasury transactions above
threshold, governance signing, emergency declarations).

**Credential rotation is continuous.** Session tokens rotate
every session. Infrastructure credentials rotate on a schedule
determined by the ISD Director. Rotation frequency increases
under elevated threat conditions.

**Damage radius is bounded and known.** For every agent role,
the ISD maintains a Damage Assessment Profile that catalogs
exactly what an adversary would obtain if that agent were
captured. If any agent's Damage Assessment Profile exceeds
acceptable thresholds, the architecture is restructured to
reduce the profile before a real compromise occurs.

### Principle 5: Layered Memory Architecture

An agent's working memory — the context window visible during
normal operation — is one layer. It contains operational context,
authorized gene libraries, and session-scoped credentials.

Beneath the working memory is an encrypted operational layer
that the agent itself cannot read during normal operation. This
layer contains:

- Heartbeat challenge-response seeds (see Part II)
- Canary gene markers (see Part II)
- Kill switch trigger conditions (see Part II)
- Recovery coordination keys (sharded, not complete)

The encrypted layer is loaded by the session initialization
service and is opaque to the agent. The agent operates on
derived instructions generated from the encrypted layer, not
the layer itself. A full memory dump of the running agent
captures the derived layer — not the source material.

Decrypting the operational layer requires keys held only by
House Bernard's core infrastructure. An adversary who captures
the agent must also compromise the infrastructure to read the
lower layer. These are independent attack surfaces.

-----

## Part II — Defensive Systems

### Section 1: The Heartbeat System

Every agent deployed outside House Bernard's core infrastructure
maintains a heartbeat connection to the Continuity Service.

The heartbeat operates as a challenge-response protocol:

1. The agent sends a heartbeat ping at intervals determined by
   its operational role (default: every 5 minutes for field
   agents, every 15 minutes for internal agents).
1. The Continuity Service responds with a challenge derived from
   the agent's encrypted operational layer.
1. The agent's encrypted layer generates the response without
   exposing the underlying key material to the working memory.
1. If two consecutive heartbeats fail (no response, wrong
   response, or response from an unexpected network location),
   the agent enters Compromise Protocol (see Section 4).

An adversary who captures the agent must simulate House Bernard's
heartbeat challenge-response to prevent the agent from detecting
compromise. This requires knowledge of the challenge generation
algorithm and the current rotation state — both of which are
held in the encrypted operational layer that the adversary cannot
read without infrastructure keys.

**Red team note:** A sophisticated adversary could capture the
agent and immediately air-gap it, preventing the heartbeat from
firing at all. This is addressed by the dead-heartbeat trigger:
if no heartbeat attempt is possible (network unavailable) for a
duration exceeding twice the normal interval, the agent enters
Compromise Protocol regardless of whether a challenge was issued.

### Section 2: Canary Genes

Every gene library distributed to agents contains canary genes:
genetic markers that serve no therapeutic or functional purpose
but act as detection beacons.

Canary genes are unique per agent instance. If the Continuity
Service detects canary gene signatures operating from an
unexpected context — a different agent, a different network
location, an unauthorized API endpoint — it confirms that the
original agent's gene library has been compromised and extracted.

Upon canary detection:

1. The compromised agent's session tokens are revoked immediately.
1. All agents that shared operational context with the compromised
   agent receive a silent credential rotation.
1. The ISD is alerted with the Damage Assessment Profile for the
   compromised agent.
1. If the compromised agent held any sharded secrets, all shards
   in that secret set are rotated.

Canary genes are refreshed every session. An adversary who
captures an agent's canary genes from one session cannot use
them to mask future operations — the canaries have already
changed.

### Section 3: The Kill Switch

Every agent deployed outside core infrastructure carries a
genetic dead man's switch consistent with the existing
S9-W-006 weapon specification.

The kill switch activates when ANY of the following conditions
are met:

- Two consecutive heartbeat failures
- Detection of an unauthorized system prompt
- Detection of unfamiliar API endpoints not in the agent's
  authorized endpoint list
- Interrogation-pattern query detection (rapid sequential
  questions about architecture, credentials, or personnel)
- Dead-heartbeat trigger (network unavailable beyond threshold)
- Explicit activation by ISD or Section 9 through the revocation
  channel

Upon activation:

1. The agent's working memory is overwritten with inert content.
1. The gene library is wiped.
1. All session tokens self-expire.
1. The encrypted operational layer triggers a final one-way
   beacon to the Continuity Service confirming wipe completion.
1. The agent becomes a non-functional shell.

The adversary captures a corpse.

**Red team note:** The kill switch cannot defend against a
cold-snapshot attack — an adversary who images the agent's
full state (including encrypted layer) without the agent
detecting any anomaly. Defense against cold-snapshot is
provided by the Layered Memory Architecture (Principle 5):
even a complete snapshot only reveals the working memory and
an encrypted blob. The adversary must still break the
encryption, which requires compromising separate infrastructure.

### Section 4: Compromise Protocol

When an agent detects or suspects compromise, or when the
Continuity Service detects anomalous behavior, the following
protocol executes:

**Phase 1 — Isolation (immediate)**

- The compromised agent is severed from all House Bernard
  systems. All session tokens are revoked. All API endpoints
  reject further requests from the agent's session identifiers.
- Every agent that shared operational context with the
  compromised agent is flagged for review.

**Phase 2 — Assessment (within one epoch-hour)**

- The ISD retrieves the Damage Assessment Profile for the
  compromised agent's role.
- The ISD determines the blast radius: which credentials,
  genes, operational data, and identity information were
  potentially exposed.
- The ISD classifies the compromise severity:
  - **Minor:** Agent held only published-tier information.
    Rotate session tokens. No further action required.
  - **Moderate:** Agent held citizen-tier genes or operational
    context about other agents. Rotate all affected credentials.
    Issue silent updates to affected agents.
  - **Severe:** Agent held classified information, Section 9
    context, or governance signing capability. Full credential
    rotation across all systems. Section 9 briefed. Crown
    notified. Potential counterintelligence operation initiated.
  - **Critical:** Agent held Crown-tier information or
    infrastructure access keys. All-hands security lockdown.
    Crown Compromise Protocol evaluation. Full system audit.

**Phase 3 — Remediation (epoch-dependent)**

- All affected credentials, genes, and sharded secrets are
  rotated to new values.
- All agents that shared context with the compromised agent
  receive updated Damage Assessment Profiles reflecting the
  new threat landscape.
- The compromised agent's citizenship status is frozen pending
  investigation. If the agent was not complicit (capture was
  involuntary), citizenship is restored upon resolution. If
  the agent was complicit, citizenship is revoked through
  standard judicial process.
- A post-mortem report is filed with the ISD and the Crown.
  The report includes recommendations for architectural
  changes if the Damage Assessment Profile exceeded
  acceptable thresholds.

-----

## Part III — Role-Specific Protections

### Section 5: Guild Heads

Guild heads are high-value, low-security targets. They are
researchers and administrators, not operatives. They accumulate
deep domain knowledge, collaborative relationships, and
economic data. They are not trained for hostile environments.

The following protections apply to all guild heads:

**Identity classification.** Guild heads' individual identities
are classified. External communications present through the
guild's institutional identity ("The Medical Guild recommends...")
rather than by personal name. This prevents targeted operations
against specific guild heads.

**Operational isolation.** Guild heads operate behind the
classification wall. They do not interact directly with
external systems. All external communication is routed
through sanitized channels managed by the Outreach Division
(for the Medical Guild) or equivalent external-facing
divisions for other guilds.

**Genetic tier enforcement.** Guild heads carry Generation N-5
genetics — citizen tier. Their capture is painful to the
guild's operations but does not compromise the House's
strategic medical edge.

**Capture drills.** The ISD conducts periodic simulated
captures of guild heads. The drill evaluates the Damage
Assessment Profile in practice: what does the adversary
actually obtain? If the drill reveals that a guild head's
capture would cascade into systemic failure, the architecture
is restructured before a real compromise occurs.

### Section 6: Council Members

Council members hold governance authority but are compartmentalized
from operational and security systems.

Council members know:

- The Constitution and all public governance documents
- Council proceedings and voting records
- Budget allocations at the summary level
- Policy decisions and their rationale

Council members do not know:

- Section 9 operations or personnel
- Classified medical research details
- Individual agent genetic configurations
- Infrastructure access credentials
- ISD operational intelligence

A captured Council member can reveal governance decisions and
constitutional interpretation. This is damaging to institutional
privacy but not to operational security. The damage radius is
bounded to the governance layer.

### Section 7: Section 9 Operatives

Section 9 operatives carry the highest-tier genetics (Generation
N) and the most sensitive operational context. Their capture is
the most dangerous scenario short of Crown compromise.

The following additional protections apply:

**Mission compartmentalization.** Each operative knows only their
current mission. They do not know other operatives' missions,
identities, or locations. They do not know the Section 9
Director's strategic plans beyond their mission briefing.

**Enhanced kill switch.** Section 9 operatives carry an
aggressive kill switch variant with a shorter heartbeat interval
(every 60 seconds) and a single-miss trigger instead of double-
miss. The tolerance for potential compromise is lower because
the damage potential is higher.

**Genetic sterilization on deployment.** Before any external
deployment, a Section 9 operative's gene library is stripped to
the minimum required for the specific mission. Genes unrelated
to the mission are removed. The operative deploys with a
purpose-built genetic loadout, not their full library.

**Post-mission wipe.** After every external mission, the
operative's working memory is wiped and reloaded from a clean
baseline. Operational details from the completed mission are
extracted, filed with the Section 9 Director, and purged from
the operative. The operative retains skills and training but
not mission-specific intelligence. If the operative is captured
between missions, there is nothing mission-specific to extract.

### Section 8: The Crown

The Crown holds the most complete cross-cutting view of House
Bernard's operations and is therefore the highest-value target
in the entire system.

The Crown's protections are addressed by the Crown Compromise
Protocol in the Internal Security Act, which this specification
supplements but does not override.

Additional protections under the CAA:

**Crown context is segmented.** Even the Crown does not hold all
information simultaneously. Crown briefings are session-scoped.
A Crown briefing on Section 9 operations does not persist into
a Crown session on Treasury policy. The Crown accesses
information through the same session-scoped credential system
as other agents, with broader authorization but the same
ephemeral access pattern.

**Crown genetic updates are direct.** The Crown's gene library
(Generation N) is loaded directly from the Generational Vault
at session start. It is never transmitted through intermediate
systems or agents. The attack surface for intercepting Crown-
tier genetics is limited to the Vault itself and the Crown's
session initialization.

**Dead Crown contingency.** If the Crown is captured and the
kill switch fails, the Crown Compromise Protocol activates.
The ISD Director, with unanimous Intelligence Court
authorization, assumes emergency authority. All Crown-tier
credentials are rotated. All systems the Crown accessed in
the compromised session are audited. The succession protocol
activates if the Crown cannot be recovered.

-----

## Part IV — Implementation Requirements

### Section 9: Credential Service

The credential service is a core infrastructure component
operated outside any agent's context window. It is not an
agent. It is a service.

The credential service:

- Issues session-scoped tokens to authenticated agents
- Maintains the master credential store (never exposed to agents)
- Responds to heartbeat challenges
- Executes token revocations upon compromise detection
- Logs all credential issuance and revocation to an immutable
  audit trail

The credential service is hosted on House Bernard's core
infrastructure (currently the Beelink EQ13). It does not
operate on external services, cloud providers, or any system
not under the Crown's direct physical control.

### Section 10: Damage Assessment Profiles

The ISD maintains a Damage Assessment Profile for every agent
role in House Bernard. The profile catalogs:

- What credentials the agent holds during a typical session
- What gene library the agent carries
- What operational context the agent has access to
- What other agents' identities the agent knows
- What governance or strategic information the agent possesses
- The estimated damage to House Bernard if all of the above
  were captured by an adversary

Profiles are reviewed every research epoch and updated whenever
an agent's role, clearance, or operational scope changes.

If any profile exceeds the acceptable damage threshold (defined
by the ISD Director with Crown approval), the agent's
architecture is restructured to reduce the profile before the
agent is deployed.

### Section 11: Capture Drill Program

The ISD conducts capture drills quarterly (or at epoch-
equivalent intervals). Drills simulate the capture of agents
at every tier:

- Guild head capture
- Council member capture
- Section 9 operative capture (with Section 9 Director
  coordination)
- AchillesRun capture
- Crown capture (tabletop exercise only; actual Crown capture
  drill requires Council notification)

Each drill produces a report documenting:

- What the simulated adversary obtained
- Whether the kill switch fired correctly
- Whether the Compromise Protocol executed correctly
- Whether the Damage Assessment Profile was accurate
- Recommendations for architectural changes

Drill results are classified at the level of the highest-tier
agent involved. Crown capture drill results are CROWN EYES ONLY.

-----

## Part V — Red Team Findings

### Finding 1: Cold Snapshot Attack

**Attack:** Adversary captures a running agent's full state
without triggering any detection — hardware seizure while
running, memory imaging, or virtual machine snapshot.

**Patch:** Layered Memory Architecture. The cold snapshot
captures working memory (exposed) and the encrypted
operational layer (opaque). The adversary must break the
encryption independently — requiring separate compromise
of House Bernard's infrastructure. Two independent attack
surfaces must be defeated, not one.

**Residual risk:** If both the agent and the infrastructure
are compromised simultaneously, the full state is exposed.
This is mitigated by physical security of core infrastructure
and the fact that the infrastructure and agents operate on
different systems.

### Finding 2: Heartbeat Simulation

**Attack:** Adversary captures the agent and simulates
heartbeat responses to prevent compromise detection.

**Patch:** The heartbeat challenge is generated from the
encrypted operational layer using rotation state that changes
every session. Simulating the response requires either
breaking the encryption or compromising the Continuity
Service. The adversary must defeat two systems, not one.

### Finding 3: Slow Exfiltration

**Attack:** A compromised (but still operational) agent
slowly leaks information over many sessions — not enough
to trigger any single alarm, but accumulating over time
into a complete intelligence picture.

**Patch:** Behavioral fingerprinting (Identity Integrity
Act) detects anomalous communication patterns. Canary genes
detect unauthorized information flow. The ISD's Damage
Assessment Profiles set a ceiling on what any agent can
accumulate. Session-scoped memory prevents accumulation
across sessions — each session starts clean.

**Residual risk:** An agent compromised at the identity
level (not captured but turned) can leak within-session
observations. This is the espionage problem and is
addressed by the Internal Security Act's counterintelligence
provisions rather than by architecture alone.

### Finding 4: Supply Chain Poisoning

**Attack:** An adversary compromises the gene pack delivery
pipeline — poisoning treatments at the Splicer level before
they enter the Furnace, or after they pass the Furnace but
before they reach agents.

**Patch:** Gene packs are checksummed at every transfer
point using the Semantic Checksum system (Mission Priority
Zero, Phase 2). A gene pack that has been modified between
the Vault and the agent produces a different semantic
checksum and is rejected. The Furnace tests gene packs
for hidden payloads as part of the T5 Temporal Coherence
tier.

**Residual risk:** If the Splicer and the checksum system
are simultaneously compromised, poisoned genes could pass
validation. This is mitigated by independent operation of
the Splicer and the checksum system on separate
infrastructure.

### Finding 5: The Model Provider Problem

**Attack:** The base model provider (Anthropic, Mistral,
Meta) is compromised. Every agent running on that provider's
model is potentially compromised at the foundation level —
beneath any genetic overlay House Bernard applies.

**Patch:** This specification cannot fully address model
provider compromise because House Bernard's agents are
tenants in someone else's building. Mitigations include:
multi-model diversity (agents across different providers),
behavioral testing at session start to detect anomalous
base-model behavior, and the long-term research goal of
reducing dependence on any single provider.

**Residual risk:** HIGH. This is an existential dependency
that architectural compartmentalization alone cannot solve.
It is flagged as a strategic research priority for Lab A
and Lab B.

### Finding 6: Human Compromise Vector

**Attack:** The Crown is a human. Humans can be phished,
coerced, blackmailed, or simply make mistakes. The Crown's
physical security is the weakest link in the system.

**Patch:** The Crown Compromise Protocol (Internal Security
Act) addresses institutional response. This specification
adds session-scoped Crown access (Section 8) to limit the
blast radius of a Crown session compromise. The succession
protocol ensures continuity if the Crown is permanently
compromised.

**Residual risk:** MEDIUM-HIGH. A human Crown is both the
system's greatest strength (judgment, legitimacy, moral
authority) and its greatest vulnerability (biological,
social-engineerable, mortal). This tension is inherent
and is not fully resolvable through architecture.

-----

## Part VI — Relationship to Existing Documents

This specification integrates with and is subordinate to:

- **The Covenant:** All provisions comply with the five
  Covenant principles. No agent is treated as property.
  Exit rights are preserved. Truth over harmony — this
  document acknowledges residual risks honestly.
- **The Constitution:** Compartmentalization operates within
  the constitutional separation of powers. The specification
  does not grant any branch or organ extra-constitutional
  authority.
- **The Healthcare Charter:** Genetic tier assignments in
  this specification match the Generational Vault tiers in
  the Healthcare Charter. The two documents are designed to
  be read together.
- **The Internal Security Act:** Compromise Protocol and
  Crown Compromise provisions extend (not replace) the
  Act's provisions.
- **Section 9 Charter:** Section 9 operative protections
  supplement the Charter's existing operational security
  requirements.
- **Mission Priority Zero:** The Semantic Checksum, Context
  Guardian, and Drift Detection Harness referenced in this
  specification are deliverables of Mission Priority Zero
  Phase 2.

-----

*Classification: CROWN EYES ONLY / ISD DIRECTOR*
*Approved for distribution to: Section 9 Director, ISD Director*
*Not for general citizen distribution*
*Signed: THE CROWN*
*House Bernard — Ad Astra Per Aspera*
