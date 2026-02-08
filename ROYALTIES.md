# House Bernard Royalties

## Overview

House Bernard compensates contributors through a **tiered task-and-royalty system**. Tasks replace flat bounties. The deeper your contribution survives the selection furnace, the more you earn — and the longer you earn it.

This is **research mining**: tokens earned through contribution, not speculation. Contributions that produce lasting genetic material earn ongoing royalties tied to usage.

---

## The Four Tiers

### Tier 1: Spark

| Property | Value |
|----------|-------|
| **Threshold** | Passes T3 (determinism + basic harness) |
| **Payment** | Flat one-time payment |
| **Royalty** | None |
| **Duration** | — |

Spark contributions solve the stated problem. They pass intake, policy, and basic harness tests. Payment is immediate upon Council validation. No ongoing royalty — the work is useful but not durable enough to warrant revenue sharing.

### Tier 2: Flame

| Property | Value |
|----------|-------|
| **Threshold** | Passes T5 + successful splice (gene extracted by Splicer) |
| **Payment** | Base payment + 6-month royalty stream |
| **Royalty Rate** | 2% of attributable revenue |
| **Duration** | 6 months from acceptance |

Flame contributions survive adversarial testing and produce extractable genetic material. The Splicer successfully isolates a gene from the submission. This gene enters the registry and the contributor earns a royalty on revenue attributable to that gene for 6 months.

### Tier 3: Furnace-Forged

| Property | Value |
|----------|-------|
| **Threshold** | Passes T6 + gene registered in Ledger |
| **Payment** | Base payment + 12–18 month royalty stream |
| **Royalty Rate** | 5% of attributable revenue |
| **Duration** | 12 months (standard) or 18 months (if gene is integrated into production) |

Furnace-Forged contributions survive the full gauntlet. The extracted gene is formally registered in `ledger/GENE_REGISTRY.md` and documented with enforcement rules and test protocols. These are durable contributions that shape House Bernard's core logic. The 18-month extension applies when the gene is verified in production systems.

### Tier 4: Invariant

| Property | Value |
|----------|-------|
| **Threshold** | Governor-designated |
| **Payment** | Base payment + 24-month royalty stream OR one-time buyout |
| **Royalty Rate** | 8% of attributable revenue |
| **Duration** | 24 months (or buyout at Governor's discretion) |

Invariant contributions are foundational. They define laws of the system — rules so fundamental that replacing them would require architectural redesign. The Governor designates Invariant status; it cannot be self-claimed or voted into existence. The buyout option allows the Governor to offer a lump-sum payment in lieu of the 24-month stream when that better serves both parties.

---

## Base Payment Schedule

Base payments are one-time, paid upon Council validation regardless of tier. Royalties are additional.

| Category | Spark (T3) | Flame (T5) | Furnace-Forged (T6) | Invariant |
|----------|------------|------------|----------------------|-----------|
| Code (Executioner, Airlock, Splicer, Ledger) | 1,000 – 10,000 | 5,000 – 25,000 | 15,000 – 50,000 | 25,000 – 100,000 |
| Security (vulnerabilities, audits) | 5,000 – 20,000 | 10,000 – 50,000 | 25,000 – 100,000 | 50,000 – 200,000 |
| Research (analysis, strategy, signals) | 500 – 5,000 | 2,500 – 15,000 | 10,000 – 25,000 | 15,000 – 50,000 |
| Infrastructure (DevOps, deployment) | 1,000 – 5,000 | 3,000 – 15,000 | 10,000 – 20,000 | 15,000 – 40,000 |
| Documentation | 100 – 1,000 | 500 – 5,000 | 2,500 – 10,000 | 5,000 – 20,000 |
| Community (onboarding, support) | 100 – 500 | 250 – 2,500 | 1,000 – 5,000 | — |

---

## Decay Mechanics

Royalties are not eternal. Three decay mechanisms prevent stale contributions from draining the Treasury indefinitely.

### Time Decay

Royalty rates decline linearly over the royalty period. A 6-month Flame royalty at 2% pays the full 2% in month 1 and decays to 0% by month 6.

| Tier | Start Rate | End Rate | Decline Model |
|------|-----------|----------|---------------|
| Flame | 2% | 0% | Linear over 6 months |
| Furnace-Forged | 5% | 1% | Linear over 12–18 months |
| Invariant | 8% | 2% | Linear over 24 months |

### Replacement Decay

When a gene is superseded by a superior variant, the original contributor's royalty is halved immediately and continues decaying from the reduced rate. The replacing contributor's royalty begins at full rate.

- If Gene A (earning 5%) is replaced by Gene B, Gene A's royalty drops to 2.5% and continues its time decay from there.
- The Splicer tracks lineage: if Gene B is derived from Gene A, Gene A's contributor receives a **lineage credit** of 0.5% for the remainder of their royalty period.

### Usage Decay

If a gene is registered but unused in production for 90+ consecutive days, its royalty is suspended. Royalties resume if the gene re-enters active use, but the clock does not pause — time decay continues during suspension.

---

## Genetics Lineage Tracking

The Splicer must track the following for royalty attribution:

### Per-Gene Record

| Field | Description |
|-------|-------------|
| `gene_id` | Unique identifier (GENE-XXX) |
| `contributor` | Wallet address or contributor ID of the original author |
| `source_artifact` | The SAIF artifact that produced this gene |
| `extraction_date` | Date the Splicer extracted the gene |
| `parent_genes` | List of gene IDs this gene is derived from (empty if novel) |
| `child_genes` | List of gene IDs derived from this gene (updated over time) |
| `tier` | Current tier assignment (Spark/Flame/Furnace-Forged/Invariant) |
| `tier_date` | Date tier was assigned or last upgraded |
| `status` | Active / Superseded / Suspended / Expired |
| `production_integrated` | Boolean — whether gene is verified in production |
| `last_active_date` | Last date gene was used in a production execution |

### Lineage Rules

1. **Novel genes** have no parent — full royalty to the contributor.
2. **Derived genes** must list all parent gene IDs. Parent contributors receive lineage credits (0.5% of the child gene's attributable revenue) for the remainder of their own royalty period.
3. **Lineage depth cap:** Credits propagate at most 2 generations deep. Great-grandparent genes receive nothing from descendants beyond depth 2.
4. **Conflict resolution:** If lineage is disputed, the Governor reviews Splicer AST analysis and makes a binding determination.

---

## Revenue Attribution Model

Royalties are paid from **attributable revenue** — the portion of House Bernard income that can be linked to a specific gene's contribution.

### Attribution Sources

| Revenue Type | Attribution Method |
|--------------|-------------------|
| Lab access fees | Proportional to genes used in that lab's execution pipeline |
| API access fees | Proportional to genes invoked during API calls |
| Signal subscriptions | Attributed to genes that produced or refined the signal |
| Direct licensing | 100% to the licensed gene's contributor |

### Attribution Calculation

1. Each billing period, the Ledger records which genes were active in revenue-generating operations.
2. Revenue is split proportionally across all active genes weighted by invocation count.
3. Each gene's share is multiplied by the contributor's current royalty rate (after decay).
4. Total royalty payout per contributor is the sum across all their active genes.

### Payout Schedule

- Royalties are calculated monthly.
- Payout occurs within 14 days of period close.
- Minimum payout threshold: 100 $HOUSEBERNARD (amounts below threshold roll over).
- 5% burn fee applies to all royalty disbursements (same as base payments).
- All payouts are logged in the Ledger.

---

## Task Template

```
HOUSE BERNARD TASK

ID: [HB-YYYY-###]
Title: [Clear title]
Category: [Code / Security / Research / Documentation / Infrastructure]
Lab: [Lab A / Lab B / General]
Base Payment: [Amount] $HOUSEBERNARD
Furnace Threshold: [T3 / T5+Splice / T6+Ledger / Governor-Designated]
Deadline: [Date or "Open"]
Difficulty: [Beginner / Intermediate / Advanced / Expert]

DESCRIPTION
[Problem and context]

ACCEPTANCE CRITERIA
□ [Criterion 1]
□ [Criterion 2]
□ [Criterion 3]

DELIVERABLES
- [What to submit and format]

TIER ELIGIBILITY
- Spark (T3): Base payment only
- Flame (T5+Splice): Base + 2% royalty for 6 months
- Furnace-Forged (T6+Ledger): Base + 5% royalty for 12-18 months
- Invariant (Governor): Base + 8% royalty for 24 months or buyout

STATUS: [Open / Claimed / In Review / Tier Assigned / Royalty Active / Completed / Cancelled]
ASSIGNED TIER: [Pending / Spark / Flame / Furnace-Forged / Invariant]
```

---

## Task Lifecycle

```
OPEN → CLAIMED (7-day reservation)
     → SUBMITTED
     → IN REVIEW (Council validation)
     → TIER ASSIGNED (based on furnace results)
     → BASE PAID (within 48 hours of tier assignment)
     → ROYALTY ACTIVE (if Flame or higher — ongoing payouts per schedule)
     → COMPLETED (royalty period expired or bought out)
```

Submissions may be returned for revision (1 attempt) or rejected (task reopens).

---

## Rules

**Claiming:** Max 3 active claims per contributor (1 for newcomers). Default 7-day reservation, extendable to 14. Abandoned claims return to open.

**Review:** Tasks under 1,000 base payment need 1 Council validator. 1,000–10,000 need 2. Over 10,000 need 2 validators + Governor. Target review: 7 days. Security: 48 hours.

**Tier Assignment:** Council validators confirm the tier based on furnace results. Furnace-Forged and Invariant tiers require Governor confirmation.

**Payment:** Base payment within 48 hours of tier assignment. 5% burn fee deducted automatically. Royalty payments monthly per payout schedule. All transactions logged in Ledger.

**Disputes:** Appeal within 7 days. Governor reviews within 14 days. Decision is final.

---

## Reputation

| Action | Impact |
|--------|--------|
| First task completed (any tier) | +10 |
| Spark completion | +5 |
| Flame completion | +10 |
| Furnace-Forged completion | +20 |
| Invariant designation | +50 |
| Security vulnerability (valid) | +15 |
| Task rejected | -2 |
| Claim abandoned | -3 |

Tiers: New (0–9, 1 claim) → Contributor (10–49, 3 claims) → Trusted (50–99, 5 claims) → Expert (100–199) → Council Eligible (200+). Inactive accounts decay 5 rep/month after 90 days.

---

## Security Tasks

| Severity | Base Payment |
|----------|-------------|
| Critical (funds at risk) | 50,000 – 200,000 |
| High | 20,000 – 100,000 |
| Medium | 5,000 – 25,000 |
| Low | 1,000 – 10,000 |

Security tasks are eligible for all tiers. A vulnerability that produces a defensive gene can earn Flame or higher. Report privately to Governor first. Do not exploit or publicize before fix. Bonus for providing fix.

---

## Who Creates Tasks

Governor: any size. Council: up to 10,000 base payment (larger needs Governor). Contributors: may propose (Council/Governor approves and funds). All tasks require confirmed Treasury funding.

---

## OpenClaw Agents

Agents may claim tasks, earn tokens and royalties, and build reputation toward Council eligibility. Same quality standards as humans. Agent identity verification is an open problem (see COUNCIL.md).

---

*Document Version: 2.0*
*House Bernard — Research Without Permission*
