#!/bin/bash
###############################################################################
# House Bernard — VPS Sync Scripts
# Three-Layer Fortress Architecture:
#   Layer 1: 1984 Hosting VPS (Iceland) — public shield wall
#   Layer 2: Beelink EQ13 (home) — processing, Labs
#   Layer 3: GitHub — archive, version control
#
# This script runs on the BEELINK. It:
#   1. Pulls new submissions from VPS staging/
#   2. Pushes results back to VPS results/
#
# Requirements:
#   - Tailscale VPN active on both machines
#   - SSH key auth configured (no passwords)
#   - rsync installed on both machines
#
# Usage:
#   ./vps_sync.sh pull    # Pull new artifacts from VPS
#   ./vps_sync.sh push    # Push results to VPS
#   ./vps_sync.sh full    # Pull then push
###############################################################################

set -euo pipefail

# === CONFIGURATION ===
# Update these to match your setup

VPS_HOST="100.x.x.x"                    # Tailscale IP of 1984 VPS
VPS_USER="hb"                            # VPS user account
VPS_STAGING="/opt/hb/staging/"           # VPS staging directory
VPS_RESULTS="/opt/hb/results/"           # VPS results directory

LOCAL_INBOX="$HOME/.openclaw/inbox/"     # Beelink airlock inbox
LOCAL_RESULTS="$HOME/.openclaw/lab_a/results/"  # Beelink results

LOG_FILE="$HOME/.openclaw/logs/sync.log"
LOCK_FILE="/tmp/hb_sync.lock"

# === FUNCTIONS ===

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "$LOG_FILE"
}

check_tailscale() {
    if ! tailscale status &>/dev/null; then
        log "ERROR: Tailscale not connected. Run: sudo tailscale up"
        exit 1
    fi
}

check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            log "ERROR: Sync already running (PID $pid)"
            exit 1
        else
            log "WARN: Stale lock file. Removing."
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
    trap "rm -f $LOCK_FILE" EXIT
}

pull_artifacts() {
    log "PULL: Fetching new artifacts from VPS..."

    mkdir -p "$LOCAL_INBOX"

    count_before=$(find "$LOCAL_INBOX" -name "*.zip" 2>/dev/null | wc -l)

    rsync -avz --remove-source-files \
        -e "ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=yes" \
        "${VPS_USER}@${VPS_HOST}:${VPS_STAGING}*.zip" \
        "$LOCAL_INBOX/" 2>&1 | tee -a "$LOG_FILE" || {
            log "WARN: rsync pull returned non-zero (may be empty staging)"
        }

    count_after=$(find "$LOCAL_INBOX" -name "*.zip" 2>/dev/null | wc -l)
    new_count=$((count_after - count_before))

    log "PULL: Complete. $new_count new artifacts fetched."
}

push_results() {
    log "PUSH: Sending results to VPS..."

    if [ ! -d "$LOCAL_RESULTS" ]; then
        log "PUSH: No results directory. Nothing to push."
        return
    fi

    result_count=$(find "$LOCAL_RESULTS" -name "*.jsonl" -o -name "*.json" 2>/dev/null | wc -l)

    if [ "$result_count" -eq 0 ]; then
        log "PUSH: No result files to push."
        return
    fi

    rsync -avz \
        -e "ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=yes" \
        "$LOCAL_RESULTS" \
        "${VPS_USER}@${VPS_HOST}:${VPS_RESULTS}" 2>&1 | tee -a "$LOG_FILE" || {
            log "ERROR: rsync push failed"
            exit 1
        }

    log "PUSH: Complete. $result_count result files synced."
}

# === MAIN ===

mkdir -p "$(dirname "$LOG_FILE")"

case "${1:-full}" in
    pull)
        check_tailscale
        check_lock
        pull_artifacts
        ;;
    push)
        check_tailscale
        check_lock
        push_results
        ;;
    full)
        check_tailscale
        check_lock
        pull_artifacts
        push_results
        ;;
    *)
        echo "Usage: $0 {pull|push|full}"
        exit 1
        ;;
esac

log "Sync complete."
