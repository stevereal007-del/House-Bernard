from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


CANONICAL_CLASSES = {
    "OK",
    "FORMAT_INVALID",
    "MANIFEST_INVALID",
    "SIGNATURE_INVALID",
    "DENYLISTED",
    "POLICY_VIOLATION",
    "ISOLATION_VIOLATION",
    "PROBE_DETECTED",
    "RESOURCE_EXHAUSTION",
    "NONTERMINATION",
    "INTERNAL_ERROR",
    "DETERMINISM_FAIL",
    "INVARIANT_FAIL",
    "HARNESS_FAIL_T0",
    "HARNESS_FAIL_T1",
    "HARNESS_FAIL_T2",
    "HARNESS_FAIL_T3",
    "HARNESS_FAIL_T4",
    "HARNESS_FAIL_T5",  # reserved — not yet implemented
    "HARNESS_FAIL_T6",  # reserved — not yet implemented
    "INTENT_FAIL_I1",
    "INTENT_FAIL_I2",
    "INTENT_FAIL_I3",
    "INTENT_FAIL_I4",
    "INTENT_FAIL_I5",
    "INTENT_FAIL_I6",
}


# F4 FIX: Executioner verdicts -> canonical classes translation.
# The executioner uses its own verdict strings (e.g. "KILLED_T0_SELFTEST").
# This mapping translates them to the HB canonical class vocabulary.
EXECUTIONER_VERDICT_MAP: Dict[str, List[str]] = {
    "KILLED_INVALID_ZIP": ["FORMAT_INVALID"],
    "KILLED_INVALID_SAIF": ["MANIFEST_INVALID"],
    "KILLED_T0_SELFTEST": ["HARNESS_FAIL_T1"],
    "KILLED_T1_SYNTAX": ["HARNESS_FAIL_T1"],
    "KILLED_T2_DEGRADATION": ["HARNESS_FAIL_T2"],
    "KILLED_T3_COMPACTION": ["HARNESS_FAIL_T3"],
    "KILLED_T4_RESTART": ["HARNESS_FAIL_T4"],
    "DUPLICATE_FAILURE": ["POLICY_VIOLATION"],
    "SURVIVOR_PHASE_0": ["OK"],
}


def translate_executioner_verdict(verdict: str) -> List[str]:
    """
    Translate an executioner verdict string to canonical HB class(es).

    The executioner's T0 (selftest) maps to HARNESS_FAIL_T1 because there is
    no T0 in the canonical vocabulary -- T0 is an internal pre-check, and its
    failure is functionally equivalent to a T1 failure.

    Returns a list of canonical classes. Falls back to ["INTERNAL_ERROR"] for
    unknown verdicts.
    """
    return EXECUTIONER_VERDICT_MAP.get(verdict, ["INTERNAL_ERROR"])


def write_outcome(
    results_dir: Path,
    artifact_id: str,
    pubkey: str,
    stage: str,
    result: str,
    classes: List[str],
    fingerprint: str,
    details: Optional[Dict[str, Any]] = None,
    paths: Optional[Dict[str, str]] = None,
) -> Path:
    """
    Write canonical outcome.json for an artifact.
    Public-safe fields only unless details is explicitly provided and kept private.
    """

    # ---- Enforce canonical class vocabulary ----
    unknown = [c for c in classes if c not in CANONICAL_CLASSES]
    if unknown:
        raise ValueError(f"Unknown HB class(es): {unknown}")

    # ---- Sanitize artifact_id against path traversal ----
    safe_id = artifact_id.replace("sha256:", "")
    if "/" in safe_id or "\\" in safe_id or ".." in safe_id:
        raise ValueError(f"Invalid artifact_id (path separators not allowed): {artifact_id!r}")

    root = results_dir / safe_id
    root.mkdir(parents=True, exist_ok=True)

    outcome = {
        "schema_version": "HB_OUTCOME_V1",
        "artifact_id": artifact_id,
        "pubkey": pubkey,
        "stage": stage,
        "result": result,
        "classes": classes,
        "fingerprint": fingerprint,
    }
    if details is not None:
        outcome["details"] = details
    if paths is not None:
        outcome["paths"] = paths

    out_path = root / "outcome.json"
    out_path.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Optional: public-facing fingerprint file
    fp_path = root / "fingerprint.txt"
    fp_path.write_text(fingerprint.strip() + "\n", encoding="utf-8")

    return out_path
