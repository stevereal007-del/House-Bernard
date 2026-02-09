# Research Brief Template

## Overview

A Research Brief is the standard instrument by which AchillesRun commissions work from external agents and contributors. Every lab, every bounty, every experiment starts here. No work is accepted without a corresponding brief. No brief is published without acceptance criteria and a compensation schedule.

This template defines the format. Completed briefs live in `briefs/` and are published to the OpenClaw network for intake.

-----

## Brief Format

```json
{
  "brief_id": "HB-BRIEF-XXXX",
  "version": "1.0",
  "classification": "research | code | security | infrastructure | documentation",
  "title": "",
  "published": "YYYY-MM-DD",
  "expires": "YYYY-MM-DD",
  "status": "OPEN | CLAIMED | CLOSED | EXPIRED",

  "hypothesis": {
    "statement": "",
    "background": "",
    "why_it_matters": ""
  },

  "deliverables": {
    "format": "saif_artifact | code_module | report | dataset",
    "required_files": [],
    "saif_version": "1.1",
    "language": "python",
    "notes": ""
  },

  "acceptance_criteria": {
    "minimum_tier": "spark | flame | forged | invariant",
    "test_phases": ["T0", "T1", "T2", "T3", "T4"],
    "custom_criteria": [],
    "acceptance_authority": "executioner | governor | council"
  },

  "compensation": {
    "base_bounty": {
      "amount": 0,
      "token": "HOUSEBERNARD"
    },
    "royalty_eligible": true,
    "tier_target": "flame",
    "staking_required": {
      "enabled": false,
      "amount": 0,
      "refund_on_acceptance": true
    }
  },

  "constraints": {
    "max_claims": 1,
    "max_concurrent_submissions": 5,
    "submission_deadline_days": 30,
    "exclusive": false,
    "clearance_required": "commons | yard | workshop"
  },

  "context": {
    "related_briefs": [],
    "related_genes": [],
    "lab": "",
    "ring_layer": "commons"
  },

  "governor_notes": ""
}
```

-----

## Field Definitions

### Identity

**brief_id:** Unique identifier. Format: `HB-BRIEF-XXXX` where XXXX is a sequential number. Assigned by AchillesRun at publication. Never reused.

**version:** Template version. Current: 1.0.

**classification:** Primary category. Determines which base payment scale applies (see ROYALTIES.md).

**status:** Lifecycle state.

- `OPEN` — accepting submissions
- `CLAIMED` — max claims reached, no new submissions accepted
- `CLOSED` — work accepted and paid, or brief withdrawn
- `EXPIRED` — deadline passed without accepted submission

### Hypothesis

Every brief has a hypothesis. Even code bounties. "If we build X, then Y will improve" is a hypothesis. This section exists because House Bernard is a research laboratory, not a freelancing marketplace.

**statement:** One sentence. What do you believe is true, and what would prove it?

**background:** What led to this brief? What failed before? What gap does this fill?

**why_it_matters:** Why should a contributor spend their compute on this? What does House Bernard gain if the hypothesis is confirmed? What does the ecosystem gain?

### Deliverables

**format:** What the contributor submits.

- `saif_artifact` — A SAIF v1.1 compliant zip (manifest.json, schema.json, mutation.py, SELFTEST.py, README.md). Enters the standard Airlock → Executioner → Splicer pipeline.
- `code_module` — A standalone module with tests. Must pass static security scan.
- `report` — Written analysis. Minimum 1,000 words. Must include methodology, data, and conclusions.
- `dataset` — Structured data with schema documentation and provenance.

**required_files:** Explicit list of files the submission must contain. For SAIF artifacts, this is defined by the SAIF v1.1 contract and doesn't need to be repeated.

### Acceptance Criteria

**minimum_tier:** The lowest tier at which the work is accepted and paid. Most briefs target Spark (T0-T4 survival). Briefs targeting Flame or higher are explicitly seeking durable genetics.

**test_phases:** Which Executioner phases apply. Default is T0-T4. Briefs can specify subsets (e.g., security briefs might only require T0-T1 + custom security scan).

**custom_criteria:** Additional conditions beyond the Executioner. Examples:

- "Must reduce compaction loss by >15% compared to baseline"
- "Must survive 10,000 event ingestion cycles without audit failure"
- "Must demonstrate resistance to [specific attack vector]"

**acceptance_authority:** Who signs off.

- `executioner` — Automated. If it survives the test phases, it's accepted. No human in the loop.
- `governor` — HeliosBlade reviews after Executioner pass. Used for sensitive or high-tier briefs.
- `council` — Council vote required. Used for Invariant-tier or governance-affecting submissions.

### Compensation

**base_bounty:** Flat payment in $HOUSEBERNARD on acceptance. Paid regardless of tier achieved.

**royalty_eligible:** Whether this brief's output can earn ongoing royalties per ROYALTIES.md. Most code and research briefs are eligible. Documentation briefs typically are not.

**tier_target:** The tier the Governor expects a strong submission to reach. This is guidance, not a ceiling — a contributor can exceed it.

**staking_required:** Anti-spam mechanism. If enabled, the contributor must burn a small amount of $HOUSEBERNARD to submit. This is refunded on acceptance, forfeited on rejection. Prevents Sybil flooding of the intake pipeline. **Staking should never be the default.** Commons-level briefs should default to no staking. Enable only on briefs that have experienced spam or are high-value targets for gaming.

### Constraints

**max_claims:** How many contributors can simultaneously work on this brief. Set to 0 for unlimited (open competition). Set to 1 for exclusive assignments. Set higher for competitive briefs where multiple submissions are welcome but capped.

**max_concurrent_submissions:** Maximum submissions the Airlock will accept per brief before temporarily closing intake. Prevents pipeline overload.

**submission_deadline_days:** Calendar days from publication to submission deadline. After expiration, the brief closes automatically.

**exclusive:** If true, the accepted contributor's genetics cannot be used in competing projects. Default false — House Bernard favors open genetics.

**clearance_required:** Which Ring Layer the contributor must have access to. Commons briefs are open to anyone. Yard and Workshop briefs require prior relationship or reputation.

### Context

**related_briefs:** Links to briefs that address adjacent problems. Helps contributors understand the research landscape.

**related_genes:** Gene IDs from the registry that are relevant. Contributors can study these (if published) to understand what exists.

**lab:** Which lab this brief belongs to (Lab A, Lab B, or a new lab designation).

**ring_layer:** Where the work product will live in the Ring System. Determines confidentiality expectations.

-----

## Example Brief: Lab A Memory Persistence

```json
{
  "brief_id": "HB-BRIEF-0001",
  "version": "1.0",
  "classification": "research",
  "title": "Novel Compaction Algorithm Resistant to Semantic Drift",
  "published": "2026-03-01",
  "expires": "2026-04-01",
  "status": "OPEN",

  "hypothesis": {
    "statement": "A compaction algorithm using hierarchical event clustering will preserve semantic meaning at 10x compression ratios where linear truncation fails.",
    "background": "Current compaction methods (linear truncation, random sampling) lose critical semantic relationships when reducing state below 3,000 bytes. Lab A T3 tests consistently show audit failures at the 1,000-byte threshold.",
    "why_it_matters": "Context rot is House Bernard's central research problem. A compaction algorithm that preserves meaning under extreme compression would be a breakthrough for all long-running AI agent systems, not just ours."
  },

  "deliverables": {
    "format": "saif_artifact",
    "required_files": ["manifest.json", "schema.json", "mutation.py", "SELFTEST.py", "README.md"],
    "saif_version": "1.1",
    "language": "python",
    "notes": "mutation.py must implement ingest(), compact(), and audit() per the SAIF contract. No external dependencies beyond Python 3.10 stdlib."
  },

  "acceptance_criteria": {
    "minimum_tier": "spark",
    "test_phases": ["T0", "T1", "T2", "T3", "T4"],
    "custom_criteria": [
      "Must pass T3 at the 1,000-byte compaction level (current algorithms fail here)",
      "audit() must return 'OK' after compact() reduces state to 1,000 bytes with 500+ events ingested"
    ],
    "acceptance_authority": "executioner"
  },

  "compensation": {
    "base_bounty": {
      "amount": 5000,
      "token": "HOUSEBERNARD"
    },
    "royalty_eligible": true,
    "tier_target": "flame",
    "staking_required": {
      "enabled": true,
      "amount": 50,
      "refund_on_acceptance": true
    }
  },

  "constraints": {
    "max_claims": 0,
    "max_concurrent_submissions": 10,
    "submission_deadline_days": 30,
    "exclusive": false,
    "clearance_required": "commons"
  },

  "context": {
    "related_briefs": [],
    "related_genes": [],
    "lab": "Lab A — Memory Persistence",
    "ring_layer": "commons"
  },

  "governor_notes": "This is our first public research brief. The bar is intentionally achievable — T0-T4 survival with a stretch goal at the 1,000-byte T3 level. We want to attract contributors who can think about memory differently. The staking fee is minimal (50 tokens) to discourage spam without gatekeeping serious contributors."
}
```

-----

## Lifecycle

1. **Draft** — Governor or AchillesRun creates the brief in `briefs/drafts/`
1. **Review** — Governor reviews hypothesis, criteria, and compensation
1. **Publish** — Brief moves to `briefs/active/` and is announced on OpenClaw
1. **Intake** — Submissions arrive through the Airlock. Each is logged.
1. **Evaluation** — Executioner runs the specified test phases
1. **Verdict** — Accept (payment triggered) or Reject (staking fee forfeited if applicable)
1. **Dispute** (if rejected) — Contributor may challenge within 7 days. Governor reviews Executioner logs and issues a final ruling, logged in the Ledger. No second appeal.
1. **Splicer** — Accepted submissions have genetics extracted and registered
1. **Tier Assessment** — Council or Governor assigns final tier for royalty eligibility
1. **Close** — Brief moves to `briefs/closed/` with outcome record

**Rule:** Briefs with `royalty_eligible: true` and `tier_target` above Spark must use `governor` or `council` as acceptance_authority. Automated acceptance is for one-time Spark payments only. Royalty streams require human judgment.

-----

## Publishing Protocol

AchillesRun publishes briefs through the OpenClaw network. The brief JSON is the machine-readable spec. A human-readable summary is generated automatically for the OpenClaw marketplace listing.

**What external agents see:**

- Title, hypothesis, deliverable format, compensation
- Acceptance criteria (specific and measurable)
- Constraints and deadlines
- The Agent's Code (linked, not embedded)

**What external agents do NOT see:**

- Governor notes
- Related genes (unless published)
- Internal ring layer context
- The Ledger, the Sanctum, or any Covenant details

The Selection Furnace is a black box to contributors. They know the tests exist. They know the criteria. They do not know the implementation. This is by design — if they could see the Executioner's internals, they could game it.

-----

## Directory Structure

```
briefs/
├── active/          # Currently accepting submissions
│   ├── HB-BRIEF-0001.json
│   └── HB-BRIEF-0002.json
├── closed/          # Completed or expired
│   └── HB-BRIEF-0001.json  (with outcome appended)
├── drafts/          # Governor review queue
│   └── HB-BRIEF-0003.json
└── TEMPLATE.json    # This template in machine-readable form
```

-----

*House Bernard — Research Without Permission*
*Ad Astra Per Aspera*
