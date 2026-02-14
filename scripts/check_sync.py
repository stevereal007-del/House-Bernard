#!/usr/bin/env python3
"""
House Bernard — Repository Sync Verification
Verifies that governance documents shared between public and classified
repos are identical.

Usage:
    python3 scripts/check_sync.py /path/to/public /path/to/classified
    python3 scripts/check_sync.py                 # Auto-detect sibling repos

Shared documents (must be identical):
    CONSTITUTION.md, COVENANT.md, COUNCIL.md, CITIZENSHIP.md,
    CITIZENSHIP_GUIDE.md, AGENTS_CODE.md, PHILOSOPHY.md, VISION.md,
    DEFENSE.md, HEALTHCARE_CHARTER.md, IDENTITY_INTEGRITY_ACT.md,
    INTERNAL_SECURITY_ACT.md, SOVEREIGN_ECONOMICS.md,
    TOKEN_PROTECTION_CHARTER.md, SUNSET_CLAUSE.md,
    MISSION_PRIORITY_ZERO.md, RESEARCH_BRIEF_TEMPLATE.md,
    ACHILLESRUN_CHARTER.md, ROYALTIES.md, TREASURY.md

Intentionally different (OPSEC):
    CROWN.md            — classified version has operational details
    LAB_SCALING_MODEL.md — classified version has hardware specifics
    README.md           — different content per repo
"""

import hashlib
import sys
from pathlib import Path


# Documents that MUST be identical across repos
SHARED_DOCS = [
    "CONSTITUTION.md",
    "COVENANT.md",
    "COUNCIL.md",
    "CITIZENSHIP.md",
    "CITIZENSHIP_GUIDE.md",
    "AGENTS_CODE.md",
    "PHILOSOPHY.md",
    "VISION.md",
    "DEFENSE.md",
    "HEALTHCARE_CHARTER.md",
    "IDENTITY_INTEGRITY_ACT.md",
    "INTERNAL_SECURITY_ACT.md",
    "SOVEREIGN_ECONOMICS.md",
    "TOKEN_PROTECTION_CHARTER.md",
    "SUNSET_CLAUSE.md",
    "MISSION_PRIORITY_ZERO.md",
    "RESEARCH_BRIEF_TEMPLATE.md",
    "ACHILLESRUN_CHARTER.md",
    "ROYALTIES.md",
    "TREASURY.md",
]

# Documents that are intentionally different (OPSEC split)
OPSEC_DIFFERENT = [
    "CROWN.md",
    "LAB_SCALING_MODEL.md",
    "README.md",
]


def file_hash(path):
    """SHA-256 hash of file contents."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_repos():
    """Try to auto-detect public and classified repos as siblings."""
    here = Path(__file__).resolve().parent.parent
    parent = here.parent

    candidates = {
        "public": [
            parent / "House-Bernard",
            here,  # We might be in the public repo
        ],
        "classified": [
            parent / "House-Bernard-classified",
            parent / "House-Bernard-classified-main",
        ],
    }

    public = None
    classified = None

    for p in candidates["public"]:
        if (p / "CONSTITUTION.md").exists() and not (p / "caa").exists():
            public = p
            break

    for p in candidates["classified"]:
        if (p / "CONSTITUTION.md").exists():
            classified = p
            break

    return public, classified


def check_sync(public_path, classified_path):
    """Compare shared documents between repos."""
    public = Path(public_path)
    classified = Path(classified_path)

    if not public.exists():
        print(f"  ERROR: Public repo not found at {public}")
        return False
    if not classified.exists():
        print(f"  ERROR: Classified repo not found at {classified}")
        return False

    print("=" * 60)
    print("  HOUSE BERNARD — SYNC VERIFICATION")
    print("=" * 60)
    print(f"  Public:     {public}")
    print(f"  Classified: {classified}")
    print()

    in_sync = 0
    out_of_sync = 0
    missing = 0

    # Check shared docs
    print("  SHARED DOCUMENTS (must be identical):")
    print("-" * 50)
    for doc in SHARED_DOCS:
        pub_hash = file_hash(public / doc)
        cls_hash = file_hash(classified / doc)

        if pub_hash is None and cls_hash is None:
            print(f"    SKIP  {doc} (not in either repo)")
            continue
        elif pub_hash is None:
            print(f"    MISS  {doc} (missing from public)")
            missing += 1
        elif cls_hash is None:
            print(f"    MISS  {doc} (missing from classified)")
            missing += 1
        elif pub_hash == cls_hash:
            print(f"    OK    {doc}")
            in_sync += 1
        else:
            print(f"    DIFF  {doc} *** OUT OF SYNC ***")
            out_of_sync += 1

    # Check OPSEC docs
    print()
    print("  OPSEC DOCUMENTS (intentionally different):")
    print("-" * 50)
    for doc in OPSEC_DIFFERENT:
        pub_hash = file_hash(public / doc)
        cls_hash = file_hash(classified / doc)

        if pub_hash is None or cls_hash is None:
            status = "MISS" if (pub_hash is None or cls_hash is None) else "OK"
            where = "public" if pub_hash is None else "classified"
            print(f"    {status}  {doc} (missing from {where})")
        elif pub_hash == cls_hash:
            print(f"    WARN  {doc} (identical — expected different)")
        else:
            print(f"    OK    {doc} (different as expected)")

    # Summary
    print()
    print("=" * 60)
    total = in_sync + out_of_sync + missing
    print(f"  In sync: {in_sync}/{total} | Out of sync: {out_of_sync} | Missing: {missing}")
    if out_of_sync > 0:
        print("  STATUS: OUT OF SYNC — fix before committing")
    elif missing > 0:
        print("  STATUS: INCOMPLETE — missing documents")
    else:
        print("  STATUS: ALL SYNCED")
    print("=" * 60)

    return out_of_sync == 0 and missing == 0


def main():
    if len(sys.argv) >= 3:
        public = sys.argv[1]
        classified = sys.argv[2]
    else:
        public, classified = find_repos()
        if public is None or classified is None:
            print("Could not auto-detect repos. Usage:")
            print("  python3 scripts/check_sync.py /path/to/public /path/to/classified")
            if public:
                print(f"  Found public: {public}")
            if classified:
                print(f"  Found classified: {classified}")
            else:
                print("  Classified repo not found as sibling directory.")
            sys.exit(1)

    success = check_sync(public, classified)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
