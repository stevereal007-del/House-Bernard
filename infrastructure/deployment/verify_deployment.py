#!/usr/bin/env python3
"""
House Bernard — Post-Deployment Verification

Checks that all components are installed, configured, and wired.
Run after deploy_achillesrun.sh to confirm operational readiness.

Usage:
    python3 verify_deployment.py          # Full check, output JSON
    python3 verify_deployment.py --quick  # Exit code only
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def is_wsl2() -> bool:
    """Detect if running inside WSL2."""
    try:
        version = Path("/proc/version").read_text().lower()
        return "microsoft" in version
    except Exception:
        return False


def has_systemd() -> bool:
    """Check if systemd is running (PID 1)."""
    try:
        return Path("/proc/1/comm").read_text().strip() == "systemd"
    except Exception:
        return False


def check(name: str, fn: callable) -> dict[str, Any]:
    """Run a check function and return structured result."""
    try:
        result = fn()
        return {"name": name, **result}
    except Exception as e:
        return {"name": name, "status": "error", "detail": str(e)}


def check_ollama() -> dict[str, Any]:
    if not shutil.which("ollama"):
        return {"status": "fail", "detail": "ollama not installed"}
    r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        return {"status": "fail", "detail": "ollama not responsive"}
    models = r.stdout.lower()
    required = ["llama3.2:3b", "mistral:7b", "llama3:8b"]
    missing = [m for m in required if m not in models]
    if missing:
        return {"status": "warn", "detail": f"missing models: {missing}"}
    return {"status": "pass", "detail": f"3/3 models available"}


def check_node() -> dict[str, Any]:
    if not shutil.which("node"):
        return {"status": "fail", "detail": "node not installed"}
    r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
    version = r.stdout.strip()
    major = int(version.lstrip("v").split(".")[0])
    if major < 22:
        return {"status": "fail", "detail": f"node {version} (need 22+)"}
    return {"status": "pass", "detail": f"node {version}"}


def check_openclaw() -> dict[str, Any]:
    if not shutil.which("openclaw"):
        return {"status": "fail", "detail": "openclaw not installed"}
    r = subprocess.run(["openclaw", "--version"], capture_output=True, text=True, timeout=15)
    return {"status": "pass", "detail": f"openclaw {r.stdout.strip()}"}


def check_config() -> dict[str, Any]:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        return {"status": "fail", "detail": "~/.openclaw/openclaw.json missing"}
    try:
        data = json.loads(config_path.read_text())
        mode = data.get("gateway", {}).get("mode", "unknown")
        port = data.get("gateway", {}).get("port", "unknown")
        auth = data.get("gateway", {}).get("auth", {}).get("mode", "none")
        return {"status": "pass", "detail": f"mode={mode} port={port} auth={auth}"}
    except json.JSONDecodeError:
        return {"status": "fail", "detail": "config is invalid JSON"}


def check_workspace() -> dict[str, Any]:
    base = Path.home() / ".openclaw" / "agents" / "achillesrun" / "workspace"
    required = ["commons", "yard", "workshop", "sanctum"]
    missing = [d for d in required if not (base / d).is_dir()]
    if not base.exists():
        return {"status": "fail", "detail": "workspace root missing"}
    if missing:
        return {"status": "warn", "detail": f"missing dirs: {missing}"}
    return {"status": "pass", "detail": f"all {len(required)} workspace dirs present"}


def check_skills() -> dict[str, Any]:
    # Try repo-relative path first, then ~/House-Bernard
    script_dir = Path(__file__).resolve().parent
    repo = script_dir.parent.parent / "openclaw" / "skills"
    if not repo.exists():
        repo = Path.home() / "House-Bernard" / "openclaw" / "skills"
    expected = ["house-bernard-airlock", "house-bernard-executioner", "house-bernard-treasury"]
    missing = [s for s in expected if not (repo / s / "SKILL.md").exists()]
    if missing:
        return {"status": "warn", "detail": f"missing skills: {missing}"}
    return {"status": "pass", "detail": f"{len(expected)}/{len(expected)} skills defined"}


def check_sanctum() -> dict[str, Any]:
    sanctum = Path.home() / ".openclaw" / "agents" / "achillesrun" / "workspace" / "sanctum"
    ledger = sanctum / "EVENT_LEDGER.jsonl"
    if not ledger.exists():
        return {"status": "warn", "detail": "EVENT_LEDGER.jsonl not initialized"}
    lines = ledger.read_text().strip().split("\n")
    return {"status": "pass", "detail": f"event ledger has {len(lines)} entries"}


def check_permissions() -> dict[str, Any]:
    oc_dir = Path.home() / ".openclaw"
    config = oc_dir / "openclaw.json"
    issues = []
    if oc_dir.exists():
        mode = oct(oc_dir.stat().st_mode)[-3:]
        if mode != "700":
            issues.append(f"~/.openclaw is {mode} (want 700)")
    if config.exists():
        mode = oct(config.stat().st_mode)[-3:]
        if mode != "600":
            issues.append(f"openclaw.json is {mode} (want 600)")
    if issues:
        return {"status": "warn", "detail": "; ".join(issues)}
    return {"status": "pass", "detail": "permissions secure"}


def check_env_vars() -> dict[str, Any]:
    required = ["ANTHROPIC_API_KEY"]
    optional = ["GOOGLE_CHAT_SERVICE_ACCOUNT_FILE", "GOOGLE_CHAT_WEBHOOK_URL", "GOVERNOR_GMAIL"]
    missing_required = [v for v in required if not os.environ.get(v)]
    missing_optional = [v for v in optional if not os.environ.get(v)]
    if missing_required:
        return {"status": "warn", "detail": f"missing required: {missing_required}; missing optional: {missing_optional}"}
    if missing_optional:
        return {"status": "info", "detail": f"required set; missing optional: {missing_optional}"}
    return {"status": "pass", "detail": "all env vars set"}


def check_docker() -> dict[str, Any]:
    if not shutil.which("docker"):
        return {"status": "warn", "detail": "docker not installed"}
    r = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
    if r.returncode != 0:
        return {"status": "warn", "detail": "docker installed but daemon not running"}
    docker_type = "Docker Desktop" if "docker-desktop" in r.stdout else "docker-ce"
    r2 = subprocess.run(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True, text=True, timeout=10
    )
    if "python:3.10.15-alpine" in r2.stdout:
        return {"status": "pass", "detail": f"{docker_type} running, sandbox image present"}
    return {"status": "warn", "detail": f"{docker_type} running but sandbox image not pulled"}


def check_wsl2_config() -> dict[str, Any]:
    """WSL2-specific: verify WSL2 environment is correctly configured."""
    if not is_wsl2():
        return {"status": "info", "detail": "not WSL2 (skipped)"}

    issues = []
    details = []

    # Check systemd status
    if has_systemd():
        details.append("systemd=yes")
    else:
        issues.append("systemd not enabled (add [boot] systemd=true to /etc/wsl.conf)")

    # Check available memory
    try:
        meminfo = Path("/proc/meminfo").read_text()
        for line in meminfo.split("\n"):
            if line.startswith("MemTotal:"):
                mem_kb = int(line.split()[1])
                mem_gb = mem_kb / (1024 * 1024)
                details.append(f"ram={mem_gb:.1f}GB")
                if mem_gb < 10:
                    issues.append(f"low memory ({mem_gb:.1f}GB, need 12-16GB for full model stack)")
                break
    except Exception:
        pass

    # Check startup script
    startup = Path.home() / ".openclaw" / "achillesrun_start.sh"
    if startup.exists():
        details.append("startup_script=yes")
    elif not has_systemd():
        issues.append("no startup script and no systemd")

    # Check log directory
    log_dir = Path.home() / ".openclaw" / "logs"
    if log_dir.exists():
        details.append("logs_dir=yes")

    detail_str = ", ".join(details)
    if issues:
        return {"status": "warn", "detail": f"WSL2 [{detail_str}]; issues: {'; '.join(issues)}"}
    return {"status": "pass", "detail": f"WSL2 [{detail_str}]"}


def check_services() -> dict[str, Any]:
    """Check that core services are running (Ollama, gateway)."""
    running = []
    stopped = []

    # Ollama
    r = subprocess.run(["pgrep", "-x", "ollama"], capture_output=True, timeout=5)
    if r.returncode == 0:
        running.append("ollama")
    else:
        stopped.append("ollama")

    # OpenClaw gateway
    try:
        r = subprocess.run(
            ["curl", "-sf", "http://127.0.0.1:18789/health"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            running.append("gateway")
        else:
            stopped.append("gateway")
    except Exception:
        stopped.append("gateway")

    if not stopped:
        return {"status": "pass", "detail": f"all running: {', '.join(running)}"}
    if not running:
        return {"status": "warn", "detail": f"all stopped: {', '.join(stopped)}"}
    return {"status": "warn", "detail": f"running: {', '.join(running)}; stopped: {', '.join(stopped)}"}


def main() -> None:
    quick = "--quick" in sys.argv

    checks = [
        check("ollama", check_ollama),
        check("node", check_node),
        check("openclaw", check_openclaw),
        check("config", check_config),
        check("workspace", check_workspace),
        check("skills", check_skills),
        check("sanctum", check_sanctum),
        check("permissions", check_permissions),
        check("env_vars", check_env_vars),
        check("docker", check_docker),
        check("services", check_services),
    ]
    if is_wsl2():
        checks.append(check("wsl2", check_wsl2_config))

    statuses = [c["status"] for c in checks]
    if "fail" in statuses:
        overall = "FAIL"
    elif "error" in statuses:
        overall = "ERROR"
    elif "warn" in statuses:
        overall = "WARN"
    else:
        overall = "PASS"

    if quick:
        sys.exit(0 if overall == "PASS" else 1)

    report = {"overall": overall, "checks": checks}
    print(json.dumps(report, indent=2))

    # Summary table
    env_label = "WSL2" if is_wsl2() else "Beelink/Server"
    print(f"\n{'='*60}")
    print(f"  DEPLOYMENT VERIFICATION: {overall}")
    print(f"  Environment: {env_label}")
    print(f"{'='*60}")
    for c in checks:
        icon = {"pass": "+", "warn": "~", "fail": "X", "error": "!", "info": "i"}
        print(f"  [{icon.get(c['status'], '?')}] {c['name']:15s} {c['detail']}")
    print(f"{'='*60}")

    sys.exit(0 if overall in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
