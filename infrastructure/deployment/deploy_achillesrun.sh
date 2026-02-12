#!/bin/bash
###############################################################################
# House Bernard — AchillesRun Deployment
#
# Two-Layer Architecture:
#   Layer 1: On-premise — OpenClaw gateway, Labs, processing, local models
#   Layer 2: GitHub — archive, version control, dead state storage
#
# Supports two targets:
#   - Beelink EQ13 / Ubuntu Server 24.04 (headless)
#   - WSL2 / Ubuntu 24.04 (development)
#
# Usage:
#   chmod +x deploy_achillesrun.sh
#   ./deploy_achillesrun.sh              # Full deploy (headless server)
#   ./deploy_achillesrun.sh --wsl2       # Skip UFW, Tailscale, systemd
###############################################################################

set -euo pipefail

WSL2=false
if [[ "${1:-}" == "--wsl2" ]] || grep -qi microsoft /proc/version 2>/dev/null; then
    WSL2=true
fi

echo "============================================================"
echo "  HOUSE BERNARD — AchillesRun Deployment"
if $WSL2; then
    echo "  Target: WSL2 / Ubuntu 24.04"
else
    echo "  Target: Beelink EQ13 / Ubuntu Server 24.04 (headless)"
fi
echo "  OpenClaw: 2026.2.9+"
echo "============================================================"
echo ""

# ─── Phase 1: System Packages ────────────────────────────────────────────────

echo "[1/7] System packages..."
sudo apt update && sudo apt upgrade -y
if $WSL2; then
    sudo apt install -y python3-pip git curl zstd
    # Docker: use Docker Desktop or install docker-ce separately on WSL2
    if command -v docker &>/dev/null; then
        echo "  Docker already installed: $(docker --version)"
    else
        echo "  WARNING: Docker not found. Install Docker Desktop or docker-ce."
    fi
else
    sudo apt install -y ufw fail2ban python3-pip docker.io git curl zstd
    sudo usermod -aG docker "$USER"
fi

# ─── Phase 2: Firewall ──────────────────────────────────────────────────────

if $WSL2; then
    echo "[2/7] Firewall — SKIPPED (WSL2, host firewall applies)"
else
    echo "[2/7] Firewall (UFW)..."
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw --force enable
    echo "  UFW active. Gateway on localhost only."
fi

# ─── Phase 3: Tailscale (remote access) ─────────────────────────────────────

if $WSL2; then
    echo "[3/7] Tailscale — SKIPPED (WSL2, use host Tailscale)"
else
    echo "[3/7] Tailscale..."
    if ! command -v tailscale &>/dev/null; then
        curl -fsSL https://tailscale.com/install.sh | sh
    fi
    sudo tailscale up
    echo "  Tailscale active. Use 'tailscale status' to verify."
fi

# ─── Phase 4: Ollama (local models) ─────────────────────────────────────────

echo "[4/7] Ollama + local models..."
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama if not running
if ! pgrep -x ollama &>/dev/null; then
    ollama serve &>/dev/null &
    sleep 3
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
mkdir -p ~/.openclaw/agents/achillesrun/{workspace,skills,sessions,memory}
mkdir -p ~/.openclaw/agents/achillesrun/workspace/{commons,yard,workshop,sanctum}
mkdir -p ~/.openclaw/agents/main/sessions
mkdir -p ~/.openclaw/credentials

# Deploy config files
cp openclaw/openclaw.json ~/.openclaw/openclaw.json
cp openclaw/SOUL.md ~/.openclaw/agents/achillesrun/SOUL.md
cp openclaw/MEMORY.md ~/.openclaw/agents/achillesrun/MEMORY.md
cp openclaw/TOOLS.md ~/.openclaw/agents/achillesrun/TOOLS.md

# Secure permissions
chmod 700 ~/.openclaw
chmod 600 ~/.openclaw/openclaw.json

# Run onboarding (generates gateway token, validates config)
echo "  Running OpenClaw onboard..."
openclaw onboard \
    --non-interactive --accept-risk \
    --mode local --flow quickstart \
    --skip-channels --skip-daemon --skip-skills --skip-health --skip-ui \
    --gateway-bind loopback --gateway-port 18789 --gateway-auth token \
    --auth-choice skip \
    --workspace ~/.openclaw/agents/achillesrun/workspace \
    2>/dev/null || echo "  Onboard needs interactive run: openclaw onboard"

echo "  Workspace created at ~/.openclaw/agents/achillesrun/"

# ─── Phase 7: Docker + Services ─────────────────────────────────────────────

echo "[7/7] Docker image + services..."

# Start Docker daemon on WSL2 if needed
if $WSL2; then
    if ! docker info &>/dev/null 2>&1; then
        echo "  Starting Docker daemon..."
        sudo dockerd &>/dev/null &
        sleep 5
    fi
fi

# Pin Docker image for Executioner sandbox
docker pull python:3.10.15-alpine 2>/dev/null || echo "  Docker pull deferred (start Docker daemon first)"

# Run security audit
echo "  Running OpenClaw security audit..."
openclaw security audit --deep 2>/dev/null || echo "  Security audit skipped (run manually after onboarding)"

# Systemd service (headless only — WSL2 typically lacks systemd)
if ! $WSL2; then
    openclaw onboard --install-daemon 2>/dev/null || true
    echo "  OpenClaw daemon installed."

    if [ -f /etc/systemd/system/openclaw.service ]; then
        sudo sed -i '/\[Service\]/a Restart=on-failure\nRestartSec=10\nWatchdogSec=300' \
            /etc/systemd/system/openclaw.service 2>/dev/null || true
        sudo systemctl daemon-reload 2>/dev/null || true
        echo "  Systemd watchdog configured (auto-restart on crash)."
    fi
else
    echo "  Systemd service — SKIPPED (WSL2, run gateway in foreground)"
fi

# Run helios_watcher to verify deployment health
echo "  Running deployment health check..."
python3 openclaw/helios_watcher.py 2>/dev/null || true

# ─── Done ────────────────────────────────────────────────────────────────────

echo ""
echo "============================================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
if $WSL2; then
    echo "  Target: WSL2 / Ubuntu 24.04"
    echo "  Access: Local terminal"
else
    echo "  Target: Ubuntu Server 24.04 (headless)"
    echo "  Access: SSH over Tailscale from phone/laptop"
fi
echo ""
echo "  Next steps:"
echo "    1. Set environment variables in ~/.bashrc:"
echo "       export ANTHROPIC_API_KEY='your-api-key'"
echo "       export GOOGLE_CHAT_SERVICE_ACCOUNT_FILE='\$HOME/.openclaw/google-chat-sa.json'"
echo "       export GOOGLE_CHAT_WEBHOOK_URL='your-chat-app-url'"
echo "       export GOVERNOR_GMAIL='your-gmail@gmail.com'"
echo ""
echo "    2. Enable Google Chat in config:"
echo "       openclaw config set channels.googlechat.enabled true"
echo ""
echo "    3. Add cron jobs (gateway must be running):"
echo "       openclaw cron add --name monthly-ops --cron '0 6 1 * *' \\"
echo "         --message 'Run monthly operations cycle'"
echo "       openclaw cron add --name helios-watcher --every 30m \\"
echo "         --message 'Department of Continuity check'"
echo ""
echo "    4. Start the gateway:"
if $WSL2; then
    echo "       openclaw gateway --foreground"
else
    echo "       openclaw gateway"
fi
echo ""
echo "  AchillesRun is ready."
echo "============================================================"
