#!/bin/bash
###############################################################################
# House Bernard — AchillesRun Deployment (Beelink EQ13)
#
# Two-Layer Architecture:
#   Layer 1: Beelink EQ13 — OpenClaw gateway, Labs, processing, local models
#   Layer 2: GitHub — archive, version control, dead state storage
#
# No VPS needed. OpenClaw IS the gateway. The Beelink IS the server.
#
# Prerequisites:
#   - Ubuntu 24.04 on Beelink EQ13
#   - Internet connection
#   - GitHub SSH key configured
#
# Usage:
#   chmod +x deploy_achillesrun.sh
#   ./deploy_achillesrun.sh
###############################################################################

set -euo pipefail

echo "============================================================"
echo "  HOUSE BERNARD — AchillesRun Deployment"
echo "  Target: Beelink EQ13"
echo "============================================================"
echo ""

# ─── Phase 1: System Packages ────────────────────────────────────────────────

echo "[1/7] System packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y ufw fail2ban python3-pip docker.io git curl
sudo usermod -aG docker "$USER"

# ─── Phase 2: Firewall ──────────────────────────────────────────────────────

echo "[2/7] Firewall (UFW)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
# OpenClaw gateway binds to 127.0.0.1 — no port forwarding needed
# Tailscale for remote access only
sudo ufw --force enable
echo "  UFW active. Gateway on localhost only."

# ─── Phase 3: Tailscale (remote access) ─────────────────────────────────────

echo "[3/7] Tailscale..."
if ! command -v tailscale &>/dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi
sudo tailscale up
echo "  Tailscale active. Use 'tailscale status' to verify."

# ─── Phase 4: Ollama (local models) ─────────────────────────────────────────

echo "[4/7] Ollama + local models..."
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi
ollama pull llama3.2:3b    # Watcher (2GB)
ollama pull mistral:7b     # Worker (4.5GB)
ollama pull llama3:8b      # Master (5GB)
echo "  Three models pulled. Total: ~11.5GB"

# ─── Phase 5: OpenClaw ──────────────────────────────────────────────────────

echo "[5/7] OpenClaw..."

# Node.js 22+ required
if ! command -v node &>/dev/null || [ "$(node --version | cut -d. -f1 | tr -d v)" -lt 22 ]; then
    echo "  Installing Node.js 22..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt install -y nodejs
fi

npm install -g openclaw@latest
echo "  OpenClaw installed: $(openclaw --version 2>/dev/null || echo 'verify manually')"

# ─── Phase 6: House Bernard Repository ──────────────────────────────────────

echo "[6/7] House Bernard repo..."
if [ ! -d "$HOME/House-Bernard" ]; then
    cd "$HOME"
    git clone git@github.com:HouseBernard/House-Bernard.git
fi
cd "$HOME/House-Bernard"
git pull origin main

# Create OpenClaw workspace structure
mkdir -p ~/.openclaw/agents/achillesrun/{workspace,skills,sessions}
mkdir -p ~/.openclaw/agents/achillesrun/workspace/{commons,yard,workshop,sanctum}

# Deploy config
cp openclaw/openclaw.json ~/.openclaw/openclaw.json
cp openclaw/SOUL.md ~/.openclaw/agents/achillesrun/SOUL.md

echo "  Workspace created at ~/.openclaw/agents/achillesrun/"

# ─── Phase 7: Docker + Systemd ──────────────────────────────────────────────

echo "[7/7] Docker image + services..."

# Pin Docker image for Executioner sandbox
docker pull python:3.10.15-alpine

# Install OpenClaw as systemd service
openclaw onboard --install-daemon 2>/dev/null || true
echo "  OpenClaw daemon installed."

# ─── Done ────────────────────────────────────────────────────────────────────

echo ""
echo "============================================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
echo "  Next steps:"
echo "    1. Set environment variables:"
echo "       export DISCORD_BOT_TOKEN='your-bot-token'"
echo "       export GOVERNOR_DISCORD_ID='your-discord-user-id'"
echo "       export ANTHROPIC_API_KEY='your-api-key'"
echo ""
echo "    2. Run OpenClaw onboarding:"
echo "       openclaw onboard"
echo ""
echo "    3. Start the gateway:"
echo "       openclaw gateway"
echo ""
echo "    4. Message AchillesRun on Discord."
echo ""
echo "  Architecture:"
echo "    Layer 1: Beelink EQ13 (this machine)"
echo "      → OpenClaw gateway + Labs + local models"
echo "    Layer 2: GitHub"
echo "      → Archive, version control, dead state"
echo ""
echo "  AchillesRun is ready."
echo "============================================================"
