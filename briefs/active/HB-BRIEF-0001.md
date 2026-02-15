# HB-BRIEF-0001: Entropy-Resistant State Compactor

**Status:** OPEN
**Lab:** lab_a_memory
**Reward Tier:** 1
**Posted:** 2026-02-14
**Deadline:** None (open until filled)
**Claimed By:** —

## Problem

Context windows are finite. When an AI agent compresses its working memory
to fit a shrinking budget, critical state decays. We call this **context rot**.

Build a SAIF v1.1 artifact that implements a state compaction algorithm
resistant to entropy accumulation across repeated compression cycles.

## Success Criteria

Your `compact()` function must:

1. Accept a state dict and a byte budget
2. Return a compressed state that fits within the budget
3. Preserve all **invariants** declared in your `audit()` function
4. Survive 100 consecutive compress/expand cycles at 10% budget
   with < 5% invariant drift

## Constraints

- Single-file Python module
- No external dependencies
- Implements `ingest()`, `compact()`, `audit()` per SAIF v1.1
- Maximum file size: 50KB

## Evaluation

Artifacts enter the Selection Furnace and are tested T0 through T4.
Surviving artifacts earn the bounty and ongoing genetic royalties.

## Submission

1. Fork the relevant repo
2. Build your artifact
3. Include `manifest.json` and `SELFTEST.py`
4. Open a Pull Request
