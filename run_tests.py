#!/usr/bin/env python3
"""
House Bernard — Master Test Runner
Runs all test suites and reports results.

Usage:
    python3 run_tests.py          # Run all suites
    python3 run_tests.py -v       # Verbose output

Suites (public repo):
    1. Guild System          — guild/test_guild_system.py      (unittest)
    2. Treasury Red Team     — treasury/redteam_test.py        (custom)
    3. Monthly Ops Red Team  — treasury/redteam_monthly_ops.py (custom)
    4. Backend Integration   — treasury/test_backend.py        (custom)
"""

import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

SUITES = [
    {
        "name": "Guild System",
        "path": REPO_ROOT / "guild" / "test_guild_system.py",
        "runner": "unittest",
    },
    {
        "name": "Treasury Red Team",
        "path": REPO_ROOT / "treasury" / "redteam_test.py",
        "runner": "script",
    },
    {
        "name": "Monthly Ops Red Team",
        "path": REPO_ROOT / "treasury" / "redteam_monthly_ops.py",
        "runner": "script",
    },
    {
        "name": "Backend Integration",
        "path": REPO_ROOT / "treasury" / "test_backend.py",
        "runner": "script",
    },
]


def run_suite(suite, verbose=False):
    """Run a single test suite and return (name, success, output)."""
    path = suite["path"]
    if not path.exists():
        return suite["name"], False, f"File not found: {path}"

    env = None  # inherit environment
    cwd = str(path.parent)

    if suite["runner"] == "unittest":
        cmd = [sys.executable, "-m", "unittest", str(path.name)]
        if verbose:
            cmd.insert(3, "-v")
    else:
        cmd = [sys.executable, str(path)]

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return suite["name"], success, output
    except subprocess.TimeoutExpired:
        return suite["name"], False, "TIMEOUT (120s)"
    except Exception as e:
        return suite["name"], False, str(e)


def main():
    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    print("=" * 60)
    print("  HOUSE BERNARD — MASTER TEST RUNNER")
    print("=" * 60)
    print()

    results = []
    total_start = time.time()

    for suite in SUITES:
        print(f"  [{suite['name']}]", end=" ", flush=True)
        start = time.time()
        name, success, output = run_suite(suite, verbose)
        elapsed = time.time() - start
        status = "PASS" if success else "FAIL"
        print(f"... {status} ({elapsed:.1f}s)")
        results.append((name, success, output, elapsed))

    total_elapsed = time.time() - total_start

    # Summary
    passed = sum(1 for _, s, _, _ in results if s)
    failed = sum(1 for _, s, _, _ in results if not s)

    print()
    print("=" * 60)
    print(f"  RESULTS: {passed}/{len(results)} suites passed ({total_elapsed:.1f}s)")
    print("=" * 60)

    # Show failures
    if failed > 0:
        print()
        for name, success, output, _ in results:
            if not success:
                print(f"  FAILED: {name}")
                print("-" * 40)
                # Show last 30 lines of output
                lines = output.strip().split("\n")
                for line in lines[-30:]:
                    print(f"    {line}")
                print()

    if verbose:
        print()
        for name, success, output, _ in results:
            if success:
                print(f"  --- {name} ---")
                print(output)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
