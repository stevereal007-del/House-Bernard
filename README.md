# HOUSE BERNARD: THE IMPERIAL LEDGER

> **MOTTO: AD ASTRA PER ASPERA**

## I. THE MISSION

To compound **Clarity**, **Capital**, and **Capability** in a strict dependency chain. We solve the physics of context rot to build an unstoppable capital engine.

## II. THE PRIME DIRECTIVES

1. **LAW OF ENTROPY:** Context rot is the enemy. Trust only the Card (SAIF v1.1 — see [spec](#v-saif-v11-contract)).
1. **LAW OF DENSITY:** No prose. No helpfulness theater. Truth is measured in density.
1. **LAW OF THE LATTICE:** Everything is connected. A signal is a mutation; a mutation is an evolution.

## III. THE SOVEREIGN DOMAINS

- **/airlock**: Intake monitoring and priority queuing.
- **/executioner**: The selection furnace. T0–T4 adversarial torture testing.
- **/splicer**: Genetic extraction via AST analysis.
- **/ledger**: The Master Genome. Immutable system logic.
- **/openclaw**: Agent specification, deployment configs, and behavioral directives.
- **/treasury**: Financial engine. Royalty decay, bond yields, emission enforcement.
- **/lab_b**: Security genetics laboratory. Adversarial harness for security-domain mutations.
- **/briefs**: Research brief pipeline. Active, closed, and draft briefs.

## IV. GOVERNANCE

House Bernard is a sovereign research institution.

- We seek **Invariants**, not consensus.
- We publish **Results**, never **Genetics**.
- We are a **Filter**, not a community.
- We maintain **The Bernard Guard** — a standing defense corps (see [DEFENSE.md](DEFENSE.md)).

Governance documents: [COVENANT.md](COVENANT.md) · [CONSTITUTION.md](CONSTITUTION.md) · [CROWN.md](CROWN.md) · [SUNSET_CLAUSE.md](SUNSET_CLAUSE.md) · [IDENTITY_INTEGRITY_ACT.md](IDENTITY_INTEGRITY_ACT.md) · [INTERNAL_SECURITY_ACT.md](INTERNAL_SECURITY_ACT.md) · [CITIZENSHIP.md](CITIZENSHIP.md) · [CITIZENSHIP_GUIDE.md](CITIZENSHIP_GUIDE.md) · [COUNCIL.md](COUNCIL.md) · [TREASURY.md](TREASURY.md) · [ROYALTIES.md](ROYALTIES.md) · [DEFENSE.md](DEFENSE.md) · [PHILOSOPHY.md](PHILOSOPHY.md) · [AGENTS_CODE.md](AGENTS_CODE.md) · [VISION.md](VISION.md) · [SOVEREIGN_ECONOMICS.md](SOVEREIGN_ECONOMICS.md) · [RESEARCH_BRIEF_TEMPLATE.md](RESEARCH_BRIEF_TEMPLATE.md) · [LAB_SCALING_MODEL.md](LAB_SCALING_MODEL.md)


## V. SAIF v1.1 CONTRACT

The **Sovereign Artifact Interface Format (SAIF) v1.1** defines the three mandatory functions every artifact must implement to survive the Executioner:

| Function | Signature | Purpose |
|----------|-----------|---------|
| `ingest` | `(event_payload: dict, state: dict) -> (new_state: dict, lineage_item: dict)` | Process an incoming event, return updated state and lineage record. |
| `compact` | `(state: dict, lineage: list, target_bytes: int) -> new_state: dict` | Compress state to fit within a byte budget without losing invariants. |
| `audit` | `(state: dict, lineage: list) -> "OK" or ("HALT", reason: str)` | Self-check. Returns OK or halts with a reason string. |

Artifacts are single-file Python modules. No external dependencies. No network access. No filesystem writes outside `/work`. The Executioner tests each artifact through five escalating tiers (T0–T4) and kills at first failure.

-----

[STATUS: GREEN | SIGNED: THE CROWN]
