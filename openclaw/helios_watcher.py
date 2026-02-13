#!/usr/bin/env python3
"""
House Bernard — Helios Watcher (Department of Continuity)

Lightweight heartbeat script run every 30 minutes by OpenClaw cron.
Checks system health indicators and writes structured JSON output.

What it checks:
  1. Ollama service is running and responsive
  2. All three local models are available
  3. Treasury state file exists and is not corrupted
  4. Workspace directory structure is intact
  5. PAUSE file kill-switch detection
  6. Disk usage threshold warning

What it does NOT do:
  - Make decisions (Watcher reports; Crown decides)
  - Modify state files
  - Send external messages (OpenClaw handles delivery)

Usage:
    python3 helios_watcher.py          # Run check, output JSON
    python3 helios_watcher.py --quiet  # Exit code only (0=healthy, 1=alert)

Cron (every 30 min):
    */30 * * * * cd ~/House-Bernard && python3 openclaw/helios_watcher.py
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_MODELS: list[str] = ["llama3.2:3b", "mistral:7b", "llama3:8b"]
TREASURY_STATE: str = os.path.expanduser("~/House-Bernard/treasury/treasury_state.json")
WORKSPACE_ROOT: str = os.path.expanduser("~/.openclaw/agents/achillesrun/workspace")
PAUSE_FILE: str = os.path.expanduser("~/House-Bernard/treasury/PAUSE")
DISK_WARN_PERCENT: int = 90

WORKSPACE_DIRS: list[str] = ["commons", "yard", "workshop", "sanctum"]


def check_ollama_running() -> dict[str, Any]:
    """Check if Ollama service is responsive."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return {"status": "ok", "detail": "ollama responsive"}
        return {"status": "alert", "detail": f"ollama exit code {result.returncode}"}
    except FileNotFoundError:
        return {"status": "critical", "detail": "ollama not installed"}
    except subprocess.TimeoutExpired:
        return {"status": "alert", "detail": "ollama timeout (10s)"}


def check_models_available() -> dict[str, Any]:
    """Verify all required models are pulled."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return {"status": "alert", "detail": "cannot list models"}

        available = result.stdout.lower()
        missing = [m for m in REQUIRED_MODELS if m not in available]
        if not missing:
            return {"status": "ok", "detail": f"all {len(REQUIRED_MODELS)} models present"}
        return {"status": "alert", "detail": f"missing models: {missing}"}
    except Exception as e:
        return {"status": "alert", "detail": str(e)}


def check_treasury_state() -> dict[str, Any]:
    """Verify treasury state file exists and parses as valid JSON."""
    if not os.path.exists(TREASURY_STATE):
        return {"status": "warn", "detail": "treasury_state.json not found"}
    try:
        with open(TREASURY_STATE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"status": "alert", "detail": "treasury_state.json is not a dict"}
        return {"status": "ok", "detail": f"treasury state valid ({len(data)} keys)"}
    except json.JSONDecodeError as e:
        return {"status": "critical", "detail": f"treasury_state.json corrupt: {e}"}


def check_workspace_integrity() -> dict[str, Any]:
    """Verify workspace directory structure exists."""
    missing = []
    for d in WORKSPACE_DIRS:
        path = os.path.join(WORKSPACE_ROOT, d)
        if not os.path.isdir(path):
            missing.append(d)
    if not missing:
        return {"status": "ok", "detail": f"all {len(WORKSPACE_DIRS)} workspace dirs intact"}
    return {"status": "alert", "detail": f"missing workspace dirs: {missing}"}


def check_pause_file() -> dict[str, Any]:
    """Detect kill-switch PAUSE file in treasury."""
    if os.path.exists(PAUSE_FILE):
        return {"status": "critical", "detail": "PAUSE file detected — all transfers halted"}
    return {"status": "ok", "detail": "no pause file"}


def check_disk_usage() -> dict[str, Any]:
    """Check disk usage on the root partition."""
    try:
        usage = shutil.disk_usage("/")
        percent_used = int((usage.used / usage.total) * 100)
        free_gb = round(usage.free / (1024 ** 3), 1)
        if percent_used >= DISK_WARN_PERCENT:
            return {"status": "warn", "detail": f"disk {percent_used}% used ({free_gb}GB free)"}
        return {"status": "ok", "detail": f"disk {percent_used}% used ({free_gb}GB free)"}
    except Exception as e:
        return {"status": "alert", "detail": str(e)}


def run_checks() -> dict[str, Any]:
    """Run all health checks and return structured report."""
    checks = {
        "ollama_service": check_ollama_running(),
        "models_available": check_models_available(),
        "treasury_state": check_treasury_state(),
        "workspace_integrity": check_workspace_integrity(),
        "pause_file": check_pause_file(),
        "disk_usage": check_disk_usage(),
    }

    # Determine overall status (worst of all checks)
    statuses = [c["status"] for c in checks.values()]
    if "critical" in statuses:
        overall = "critical"
    elif "alert" in statuses:
        overall = "alert"
    elif "warn" in statuses:
        overall = "warn"
    else:
        overall = "healthy"

    return {
        "agent": "AchillesRun",
        "department": "continuity",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall": overall,
        "checks": checks,
    }


def main() -> None:
    quiet = "--quiet" in sys.argv
    report = run_checks()

    if quiet:
        sys.exit(0 if report["overall"] == "healthy" else 1)

    print(json.dumps(report, indent=2))
    if report["overall"] != "healthy":
        sys.exit(1)


if __name__ == "__main__":
    main()
