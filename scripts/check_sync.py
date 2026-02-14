#!/usr/bin/env python3
"""
Checks that governance documents in classified match the public repo.
Run from the classified repo root with the public repo path as argument.

Usage:
    python3 scripts/check_sync.py ../House-Bernard
"""

import hashlib
import sys
from pathlib import Path

MUST_MATCH = [
    "CONSTITUTION.md", "COVENANT.md", "TREASURY.md", "ROYALTIES.md",
    "DEFENSE.md", "HEALTHCARE_CHARTER.md", "IDENTITY_INTEGRITY_ACT.md",
    "INTERNAL_SECURITY_ACT.md", "SUNSET_CLAUSE.md",
    "TOKEN_PROTECTION_CHARTER.md", "RESEARCH_BRIEF_TEMPLATE.md",
    "MISSION_PRIORITY_ZERO.md", "COUNCIL.md", ]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/check_sync.py <public-repo-path>")
        return 1

    public = Path(sys.argv[1])
    classified = Path(".")
    ok = True

    print("Checking governance document sync...")
    for f in MUST_MATCH:
        cp = classified / f
        pp = public / f
        if not cp.exists():
            print(f"  WARNING: {f} missing in classified")
            ok = False
            continue
        if not pp.exists():
            print(f"  WARNING: {f} missing in public")
            ok = False
            continue
        if file_hash(cp) == file_hash(pp):
            print(f"  OK: {f}")
        else:
            print(f"  MISMATCH: {f}")
            ok = False

    print()
    if ok:
        print("All governance documents in sync.")
    else:
        print("SYNC FAILURES — reconcile before committing.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
