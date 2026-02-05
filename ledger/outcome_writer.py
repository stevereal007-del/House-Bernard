from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


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
    root = results_dir / artifact_id.replace("sha256:", "")
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
