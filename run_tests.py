#!/usr/bin/env python3
"""Unified test runner for House Bernard.

Discovers and runs all test suites across the repo.
Exit code 0 = all passed, non-zero = failures.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

SUITES = [
    # (description, command)
    ("Guild tests",
     [sys.executable, "-m", "pytest", "guild/test_guild_system.py", "-v"]),
    ("Treasury backend tests",
     [sys.executable, "treasury/test_backend.py"]),
    ("Treasury red-team tests",
     [sys.executable, "treasury/redteam_test.py"]),
    ("Platform tests",
     [sys.executable, "-m", "pytest", "hb_platform/test_platform.py", "-v"]),
    ("Site build",
     [sys.executable, "openclaw/build.py"]),
]


def main() -> int:
    failures = []
    for name, cmd in SUITES:
        print(f"\n{'='*60}")
        print(f"  {name}")
        print(f"{'='*60}\n")
        result = subprocess.run(cmd, cwd=str(REPO_ROOT))
        if result.returncode != 0:
            failures.append(name)
            print(f"\n  FAILED: {name}\n")
        else:
            print(f"\n  PASSED: {name}\n")

    print(f"\n{'='*60}")
    if failures:
        print(f"  {len(failures)} suite(s) FAILED: {', '.join(failures)}")
        return 1
    print(f"  All {len(SUITES)} suites PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
