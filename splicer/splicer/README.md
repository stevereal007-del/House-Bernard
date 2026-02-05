# Splicer - Gene Extraction

Analyzes survivors to extract memory genes.

## Status

**Phase 0:** Manual extraction  
**Phase 1:** Automated AST analysis

## Phase 0 Process

When a survivor is found:

1. Open `~/.openclaw/lab_a/survivors/survivor.zip`
2. Extract `mutation.py`
3. Read the code
4. Identify the core pattern:
   - How does it handle restart?
   - What's the reconstruction protocol?
   - What makes it survive?

5. Document as gene:
```markdown
## GENE: [NAME]

**Source:** survivor_xyz.zip  
**Discovered:** 2026-02-XX  
**Harness Result:** SURVIVOR_PHASE_0

**Rule:** [Core invariant]

**Enforcement:** [How to implement]

**Example:**
[Code snippet]
```

6. Add to `ledger/GENE_REGISTRY.md`

## Phase 1 (Future)

Automated extraction using AST analysis:
- Parse mutation.py syntax tree
- Detect patterns (ledger files, state reconstruction)
- Extract invariants automatically
- Generate gene documentation

## Coming Soon

`splicer_auto.py` - Automated gene extraction
