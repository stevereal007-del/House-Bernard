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
