#!/usr/bin/env python3
"""
House Bernard — Lab B Harness: I1 Static Scan
Wraps security_scanner.py for pipeline integration.
Reads artifact, runs AST scan, writes result to INTENT_LOG.jsonl.

Usage:
    python3 i1_static_scan.py <artifact_dir>
"""

import json
import sys
import os
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Add parent directories to path for security scanner import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "security"))

from security_scanner import scan_file, scan_directory


RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
INTENT_LOG = RESULTS_DIR / "INTENT_LOG.jsonl"


def hash_directory(dirpath: str) -> str:
    """SHA256 hash of all .py files in directory, sorted."""
    h = hashlib.sha256()
    for path in sorted(Path(dirpath).rglob("*.py")):
        h.update(path.read_bytes())
    return h.hexdigest()


def run_i1(artifact_dir: str) -> dict:
    """Run I1 static scan on an artifact directory."""
    artifact_dir = str(artifact_dir)

    if not os.path.isdir(artifact_dir):
        return {
            "test": "I1",
            "artifact": artifact_dir,
            "status": "ERROR",
            "error": "Not a directory",
            "verdict": "REJECT",
        }

    # Hash the artifact
    artifact_hash = hash_directory(artifact_dir)

    # Scan all Python files
    results = scan_directory(artifact_dir)

    # Aggregate
    total_critical = sum(r["summary"]["critical"] for r in results if r["status"] == "SCANNED")
    total_high = sum(r["summary"]["high"] for r in results if r["status"] == "SCANNED")
    total_medium = sum(r["summary"]["medium"] for r in results if r["status"] == "SCANNED")
    total_low = sum(r["summary"]["low"] for r in results if r["status"] == "SCANNED")
    parse_errors = sum(1 for r in results if r["status"] == "PARSE_ERROR")

    # Verdict
    if total_critical > 0 or parse_errors > 0:
        verdict = "REJECT"
        intent = "HOSTILE" if total_critical > 2 else "SUSPICIOUS"
    elif total_high >= 2:
        verdict = "REJECT"
        intent = "SUSPICIOUS"
    elif total_high == 1:
        verdict = "QUARANTINE"
        intent = "PROBING"
    elif total_medium > 0:
        verdict = "FLAG"
        intent = "ACCIDENTAL"
    else:
        verdict = "PASS"
        intent = "CLEAN"

    record = {
        "test": "I1",
        "test_name": "STATIC_SCAN",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "artifact": os.path.basename(artifact_dir),
        "artifact_hash": artifact_hash,
        "files_scanned": len(results),
        "parse_errors": parse_errors,
        "findings": {
            "critical": total_critical,
            "high": total_high,
            "medium": total_medium,
            "low": total_low,
        },
        "intent_classification": intent,
        "verdict": verdict,
        "details": results,
    }

    return record


def log_result(record: dict):
    """Append result to INTENT_LOG.jsonl."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write without details for the log (keep it compact)
    log_entry = {k: v for k, v in record.items() if k != "details"}

    with open(INTENT_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <artifact_directory>")
        sys.exit(2)

    artifact_dir = sys.argv[1]
    record = run_i1(artifact_dir)

    # Log
    log_result(record)

    # Output
    print(json.dumps(record, indent=2))

    # Exit code
    if record["verdict"] == "REJECT":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
