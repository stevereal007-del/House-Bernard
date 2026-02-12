#!/bin/bash
###############################################################################
# House Bernard — WSL2 Docker Setup
#
# Handles Docker installation and configuration for WSL2 environments.
# Supports two modes:
#   1. Docker Desktop integration (Windows-side, recommended for GUI users)
#   2. docker-ce native install (Linux-side, recommended for headless/server)
#
# Run this on the actual WSL2 instance. The Docker daemon requires kernel
# nftables support available in WSL2's real kernel.
#
# Usage:
#   ./wsl2_docker_setup.sh              # Auto-detect and configure
#   ./wsl2_docker_setup.sh --native     # Force docker-ce install
###############################################################################

set -euo pipefail

FORCE_NATIVE=false
if [[ "${1:-}" == "--native" ]]; then
    FORCE_NATIVE=true
fi

echo "============================================================"
echo "  HOUSE BERNARD — WSL2 Docker Setup"
echo "============================================================"
echo ""

# ─── Detect existing Docker installation ──────────────────────────────────────

DOCKER_TYPE="none"
if command -v docker &>/dev/null; then
    if docker info 2>/dev/null | grep -q "docker-desktop"; then
        DOCKER_TYPE="desktop"
    elif docker info &>/dev/null; then
        DOCKER_TYPE="native"
    else
        DOCKER_TYPE="installed-not-running"
    fi
fi

echo "[1/4] Docker detection..."
echo "  Current: $DOCKER_TYPE"

# ─── Install docker-ce if needed ──────────────────────────────────────────────

if [ "$DOCKER_TYPE" = "none" ] || $FORCE_NATIVE; then
    echo ""
    echo "[2/4] Installing docker-ce..."
    sudo apt update
    sudo apt install -y ca-certificates curl gnupg

    sudo install -m 0755 -d /etc/apt/keyrings
    if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
    fi

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io

    sudo usermod -aG docker "$USER"
    echo "  docker-ce installed. You may need to 'newgrp docker' or re-login."
    DOCKER_TYPE="native"
elif [ "$DOCKER_TYPE" = "desktop" ]; then
    echo "[2/4] Docker Desktop detected — skipping install."
else
    echo "[2/4] Docker already installed — skipping install."
fi

# ─── Start Docker daemon ─────────────────────────────────────────────────────

echo ""
echo "[3/4] Starting Docker daemon..."

if [ "$DOCKER_TYPE" = "desktop" ]; then
    echo "  Docker Desktop manages its own daemon."
    if ! docker info &>/dev/null 2>&1; then
        echo "  WARNING: Docker Desktop not running. Start it from Windows."
    else
        echo "  Docker Desktop daemon is running."
    fi
else
    # Check if systemd is managing Docker
    if pidof systemd &>/dev/null && systemctl is-active docker &>/dev/null 2>&1; then
        echo "  Docker running via systemd."
    elif docker info &>/dev/null 2>&1; then
        echo "  Docker daemon already running."
    else
        echo "  Starting Docker daemon manually..."
        sudo dockerd &>/dev/null &
        # Wait for daemon (up to 30s)
        for i in $(seq 1 30); do
            if docker info &>/dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        if docker info &>/dev/null 2>&1; then
            echo "  Docker daemon started."
        else
            echo "  ERROR: Docker daemon failed to start."
            echo "  Check: sudo dockerd (run manually to see errors)"
            exit 1
        fi
    fi

    # Enable via systemd if available
    if pidof systemd &>/dev/null; then
        sudo systemctl enable docker 2>/dev/null || true
        sudo systemctl start docker 2>/dev/null || true
        echo "  Docker enabled in systemd (will auto-start)."
    fi
fi

# ─── Pull sandbox image ──────────────────────────────────────────────────────

echo ""
echo "[4/4] Pulling Executioner sandbox image..."
if docker pull python:3.10.15-alpine; then
    echo "  Sandbox image ready."
    docker images python:3.10.15-alpine --format "  {{.Repository}}:{{.Tag}} ({{.Size}})"
else
    echo "  WARNING: Failed to pull image. Will retry on first Executioner run."
fi

# ─── Verify ──────────────────────────────────────────────────────────────────

echo ""
echo "============================================================"
echo "  WSL2 Docker Setup: COMPLETE"
echo "  Type: $DOCKER_TYPE"
echo "  Daemon: $(docker info --format '{{.ServerVersion}}' 2>/dev/null || echo 'not running')"
echo "  Sandbox: $(docker images python:3.10.15-alpine --format '{{.Size}}' 2>/dev/null || echo 'not pulled')"
echo "============================================================"
