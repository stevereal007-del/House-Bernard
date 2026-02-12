#!/bin/bash
###############################################################################
# House Bernard — AchillesRun Startup (WSL2)
#
# Starts all AchillesRun services in the correct order for WSL2
# environments that lack systemd. Designed to be idempotent — safe
# to run multiple times.
#
# Services started:
#   1. Docker daemon (if not running via Docker Desktop)
#   2. Ollama serve (local model inference)
#   3. OpenClaw gateway (foreground or background)
#
# Usage:
#   ./achillesrun_start.sh              # Interactive (gateway foreground)
#   ./achillesrun_start.sh --bg         # Background (all services daemonized)
#   ./achillesrun_start.sh --quiet      # Background, suppress output
#   ./achillesrun_start.sh --stop       # Stop all services
#   ./achillesrun_start.sh --status     # Check service status
###############################################################################

set -euo pipefail

MODE="foreground"
QUIET=false

for arg in "$@"; do
    case "$arg" in
        --bg)       MODE="background" ;;
        --quiet)    MODE="background"; QUIET=true ;;
        --stop)     MODE="stop" ;;
        --status)   MODE="status" ;;
        *)          echo "Unknown option: $arg"; exit 1 ;;
    esac
done

log() {
    if ! $QUIET; then
        echo "$@"
    fi
}

LOG_DIR="$HOME/.openclaw/logs"
mkdir -p "$LOG_DIR"

# ─── Status ──────────────────────────────────────────────────────────────────

status_check() {
    local name="$1"
    local check="$2"
    if eval "$check" &>/dev/null; then
        printf "  %-20s %s\n" "$name" "RUNNING"
    else
        printf "  %-20s %s\n" "$name" "STOPPED"
    fi
}

if [ "$MODE" = "status" ]; then
    echo "AchillesRun Service Status"
    echo "=========================="
    status_check "Docker" "docker info"
    status_check "Ollama" "pgrep -x ollama"
    status_check "OpenClaw Gateway" "curl -sf http://127.0.0.1:18789/health"
    echo ""
    echo "Logs: $LOG_DIR/"
    exit 0
fi

# ─── Stop ─────────────────────────────────────────────────────────────────────

if [ "$MODE" = "stop" ]; then
    log "Stopping AchillesRun services..."

    # Stop OpenClaw gateway
    if pkill -f "openclaw.*gateway" 2>/dev/null; then
        log "  OpenClaw gateway stopped."
    else
        log "  OpenClaw gateway: not running."
    fi

    # Stop Ollama
    if pkill -x ollama 2>/dev/null; then
        log "  Ollama stopped."
    else
        log "  Ollama: not running."
    fi

    # Don't stop Docker (other containers may depend on it)
    log "  Docker: left running (shared resource)."
    log "Done."
    exit 0
fi

# ─── Start ────────────────────────────────────────────────────────────────────

log "============================================================"
log "  HOUSE BERNARD — AchillesRun Startup (WSL2)"
log "============================================================"
log ""

# 1. Docker daemon
log "[1/3] Docker..."
if docker info &>/dev/null 2>&1; then
    log "  Docker already running."
else
    log "  Starting Docker daemon..."
    sudo dockerd >> "$LOG_DIR/docker.log" 2>&1 &
    # Wait for Docker to be ready (up to 30s)
    for i in $(seq 1 30); do
        if docker info &>/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    if docker info &>/dev/null 2>&1; then
        log "  Docker started."
    else
        log "  WARNING: Docker failed to start. Check $LOG_DIR/docker.log"
        log "  Continuing without Docker (Executioner sandbox unavailable)."
    fi
fi

# 2. Ollama
log "[2/3] Ollama..."
if pgrep -x ollama &>/dev/null; then
    log "  Ollama already running."
else
    log "  Starting Ollama..."
    ollama serve >> "$LOG_DIR/ollama.log" 2>&1 &
    sleep 3
    if pgrep -x ollama &>/dev/null; then
        log "  Ollama started."
    else
        log "  WARNING: Ollama failed to start. Check $LOG_DIR/ollama.log"
    fi
fi

# 3. OpenClaw gateway
log "[3/3] OpenClaw gateway..."
if curl -sf http://127.0.0.1:18789/health &>/dev/null; then
    log "  Gateway already running on :18789."
elif [ "$MODE" = "background" ]; then
    log "  Starting gateway (background)..."
    nohup openclaw gateway >> "$LOG_DIR/gateway.log" 2>&1 &
    sleep 3
    if curl -sf http://127.0.0.1:18789/health &>/dev/null; then
        log "  Gateway started on :18789."
    else
        log "  Gateway starting... check $LOG_DIR/gateway.log"
    fi
else
    log "  Starting gateway (foreground — Ctrl+C to stop)..."
    log ""
    openclaw gateway --foreground
fi

if [ "$MODE" = "background" ]; then
    log ""
    log "All services started. Logs: $LOG_DIR/"
    log "  Status:  ~/.openclaw/achillesrun_start.sh --status"
    log "  Stop:    ~/.openclaw/achillesrun_start.sh --stop"
fi
