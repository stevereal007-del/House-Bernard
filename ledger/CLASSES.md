# HB Canonical Reason Classes (V1)

These are coarse, public-safe failure classes. They must NOT reveal exploit tactics.
If you can derive a bypass from the wording, the wording is wrong.

## Core Intake / Policy

- OK
  - Used when the stage succeeds and no special classification is needed.

- FORMAT_INVALID
  - Archive/layout invalid (missing required files, wrong structure).

- MANIFEST_INVALID
  - manifest.json missing, malformed, or hash mismatch.

- SIGNATURE_INVALID
  - Signature missing/invalid for signed submissions (when enforced).

- DENYLISTED
  - Pubkey present in HB_DENYLIST_V1.

- POLICY_VIOLATION
  - Violates submission policy (prose, disallowed file types, forbidden extras).

## Security / Isolation

- ISOLATION_VIOLATION
  - Attempted forbidden filesystem/process/network access (coarse only).

- PROBE_DETECTED
  - Behavioral signature indicates probing/escape attempts (coarse only).

## Resource / Runtime

- RESOURCE_EXHAUSTION
  - Time/memory/recursion limits exceeded.

- NONTERMINATION
  - Failed to halt within bounded execution window (if distinguished from exhaustion).

- INTERNAL_ERROR
  - House Bernard bug. Not the submitter’s fault.

## Determinism / Correctness

- DETERMINISM_FAIL
  - Output differed across repeated runs for same inputs.

- INVARIANT_FAIL
  - Broke explicit invariant (hash integrity, schema constraints, etc.).

## Harness Failures (Lab A)

- HARNESS_FAIL_T1
- HARNESS_FAIL_T2
- HARNESS_FAIL_T3
- HARNESS_FAIL_T4
- HARNESS_FAIL_T5
- HARNESS_FAIL_T6

## Intent Harness (Lab B, reserved)

- INTENT_FAIL_I1
- INTENT_FAIL_I2
- INTENT_FAIL_I3
- INTENT_FAIL_I4
- INTENT_FAIL_I5
- INTENT_FAIL_I6

## Rules

1) classes must be drawn ONLY from this list.
2) Multiple classes allowed (e.g., ["RESOURCE_EXHAUSTION", "HARNESS_FAIL_T3"]).
3) fingerprint must remain public-safe and coarse.
4) NEVER include paths, syscall names, or exact exploit targets in fingerprint/classes.
