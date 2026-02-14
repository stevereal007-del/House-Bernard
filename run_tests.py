#!/usr/bin/env python3
"""
House Bernard — Master Test Runner (Classified)
Runs all test suites and reports results.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent
SUITES = [
    ("Treasury Backend", [sys.executable, "test_backend.py"], REPO / "treasury"),
    ("Treasury Red Team", [sys.executable, "redteam_test.py"], REPO / "treasury"),
    ("Guild System", [sys.executable, "test_guild_system.py"], REPO / "guild"),
    ("ISD System", [sys.executable, "test_isd_system.py"], REPO / "isd"),
    ("CAA System", [sys.executable, "caa/test_caa.py"], REPO),
]

def main():
    print("=" * 60)
    print("  HOUSE BERNARD — MASTER TEST RUNNER (CLASSIFIED)")
    print("=" * 60)
    print()

    results = []
    for name, cmd, cwd in SUITES:
        print(f"  Running: {name}...")
        try:
            r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
            ok = r.returncode == 0
            results.append((name, ok, r.stdout, r.stderr))
            print(f"    {'✓' if ok else '✗'} {name}")
        except Exception as e:
            results.append((name, False, "", str(e)))
            print(f"    ✗ {name} — {e}")

    print()
    print("=" * 60)
    passed = sum(1 for _, ok, _, _ in results if ok)
    total = len(results)
    print(f"  SUITES: {passed}/{total} passed")
    print("=" * 60)

    if passed < total:
        print("\n  FAILURES:")
        for name, ok, stdout, stderr in results:
            if not ok:
                print(f"\n  --- {name} ---")
                if stderr:
                    print(f"  {stderr[:500]}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
