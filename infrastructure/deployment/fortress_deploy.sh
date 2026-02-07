#!/bin/bash
###############################################################################
# House Bernard — Three-Layer Fortress Deployment
# Run this on the BEELINK after VPS is set up.
#
# Architecture:
#   Layer 1: 1984 Hosting VPS (Iceland) — intake_server.py, public submissions
#   Layer 2: Beelink EQ13 (home) — Labs, processing, Ollama models
#   Layer 3: GitHub — archive, version control, dead state
#
# Data flow:
#   Public → VPS intake → staging/ → [Tailscale] → Beelink inbox/
#   Beelink → Lab A/B processing → results/ → [Tailscale] → VPS results/
#   Beelink → git push → GitHub archive
#
# This script configures the Beelink side:
#   1. Cron job for periodic VPS sync
#   2. Systemd timer for git archive push
#   3. Integration with existing Airlock + Executioner
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HB_HOME="$HOME/.openclaw"
REPO_DIR="$HOME/House-Bernard"
LOG_DIR="$HB_HOME/logs"

echo "=== House Bernard Fortress Deployment (Beelink) ==="

# === 1. VERIFY PREREQUISITES ===
echo "[1/5] Checking prerequisites..."

check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        echo "MISSING: $1 — install it first"
        exit 1
    fi
}

check_cmd tailscale
check_cmd rsync
check_cmd docker
check_cmd git
check_cmd python3

# Check Tailscale is connected
if ! tailscale status &>/dev/null; then
    echo "ERROR: Tailscale not connected. Run: sudo tailscale up"
    exit 1
fi

echo "All prerequisites met."

# === 2. DIRECTORY STRUCTURE ===
echo "[2/5] Ensuring directory structure..."

mkdir -p "$HB_HOME"/{inbox,sandbox,logs}
mkdir -p "$HB_HOME"/lab_a/{larvae,results,survivors}
mkdir -p "$HB_HOME"/lab_b/{results}

echo "Directories ready."

# === 3. INSTALL VPS SYNC CRON ===
echo "[3/5] Installing VPS sync cron job..."

SYNC_SCRIPT="$REPO_DIR/infrastructure/vps/vps_sync.sh"

if [ ! -f "$SYNC_SCRIPT" ]; then
    echo "WARNING: vps_sync.sh not found at $SYNC_SCRIPT"
    echo "Copy it from the repo after git pull."
else
    chmod +x "$SYNC_SCRIPT"

    # Add cron job: pull every 15 minutes, push every 30 minutes
    CRON_PULL="*/15 * * * * $SYNC_SCRIPT pull >> $LOG_DIR/cron_sync.log 2>&1"
    CRON_PUSH="*/30 * * * * $SYNC_SCRIPT push >> $LOG_DIR/cron_sync.log 2>&1"

    # Install (idempotent)
    (crontab -l 2>/dev/null | grep -v "vps_sync.sh"; echo "$CRON_PULL"; echo "$CRON_PUSH") | crontab -

    echo "Cron jobs installed: pull/15min, push/30min."
fi

# === 4. GIT ARCHIVE TIMER ===
echo "[4/5] Installing git archive push timer..."

cat > "$HOME/.config/systemd/user/hb-git-archive.service" 2>/dev/null << EOF || true
[Unit]
Description=House Bernard Git Archive Push

[Service]
Type=oneshot
WorkingDirectory=$REPO_DIR
ExecStart=/bin/bash -c 'cd $REPO_DIR && git add -A && git diff --cached --quiet || git commit -m "auto-archive: \$(date -u +%%Y-%%m-%%dT%%H:%%M:%%SZ)" && git push origin main'
EOF

cat > "$HOME/.config/systemd/user/hb-git-archive.timer" 2>/dev/null << EOF || true
[Unit]
Description=House Bernard Git Archive Timer

[Timer]
OnCalendar=*-*-* 06:00:00
OnCalendar=*-*-* 18:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

mkdir -p "$HOME/.config/systemd/user/"
# Reinstall in case paths above failed
if [ -f "$HOME/.config/systemd/user/hb-git-archive.timer" ]; then
    systemctl --user daemon-reload
    systemctl --user enable hb-git-archive.timer
    systemctl --user start hb-git-archive.timer
    echo "Git archive timer: twice daily (06:00, 18:00 UTC)."
else
    echo "WARNING: Could not install systemd user timer. Set up manually."
fi

# === 5. STATUS CHECK ===
echo "[5/5] Status check..."
echo ""
echo "=== FORTRESS STATUS ==="
echo "Layer 1 (VPS):     Check with: ssh hb@<VPS_TAILSCALE_IP> 'systemctl status hb-intake'"
echo "Layer 2 (Beelink): Local processing ready"
echo "Layer 3 (GitHub):  Auto-archive timer $(systemctl --user is-active hb-git-archive.timer 2>/dev/null || echo 'NOT SET')"
echo ""
echo "Sync cron:"
crontab -l 2>/dev/null | grep "vps_sync" || echo "  Not installed"
echo ""
echo "Airlock:           $(pgrep -f airlock_monitor >/dev/null && echo 'RUNNING' || echo 'NOT RUNNING')"
echo "Docker:            $(docker info >/dev/null 2>&1 && echo 'READY' || echo 'NOT AVAILABLE')"
echo "Tailscale:         $(tailscale status >/dev/null 2>&1 && echo 'CONNECTED' || echo 'DISCONNECTED')"
echo ""
echo "=== DEPLOYMENT COMPLETE ==="
echo ""
echo "To activate full pipeline:"
echo "  1. Start airlock: cd $REPO_DIR/airlock && python3 airlock_monitor.py &"
echo "  2. Verify VPS:    curl http://<VPS_IP>:8443/health"
echo "  3. Test submit:   curl -X POST http://<VPS_IP>:8443/submit -d @test_artifact.zip"
echo "  4. Watch sync:    tail -f $LOG_DIR/cron_sync.log"
