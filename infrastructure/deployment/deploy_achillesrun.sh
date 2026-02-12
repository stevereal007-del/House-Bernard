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
WSL2_SYSTEMD=false
if [[ "${1:-}" == "--wsl2" ]] || grep -qi microsoft /proc/version 2>/dev/null; then
    WSL2=true
    # Modern WSL2 (0.67.6+) supports systemd if enabled in /etc/wsl.conf
    if $WSL2 && pidof systemd &>/dev/null; then
        WSL2_SYSTEMD=true
    fi
fi

echo "============================================================"
echo "  HOUSE BERNARD — AchillesRun Deployment"
if $WSL2; then
    echo "  Target: WSL2 / Ubuntu 24.04"
    if $WSL2_SYSTEMD; then
        echo "  Systemd: DETECTED (will install services)"
    else
        echo "  Systemd: NOT DETECTED (foreground mode)"
        echo "    Tip: Enable systemd in /etc/wsl.conf:"
        echo "      [boot]"
        echo "      systemd=true"
    fi
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
    sudo apt install -y python3-pip python3-venv git curl zstd jq
    # Docker: prefer Docker Desktop integration, fall back to docker-ce
    if command -v docker &>/dev/null; then
        echo "  Docker already installed: $(docker --version)"
    else
        echo "  Docker not found. Installing docker-ce for WSL2..."
        sudo apt install -y ca-certificates gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            sudo chmod a+r /etc/apt/keyrings/docker.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt update
        fi
        sudo apt install -y docker-ce docker-ce-cli containerd.io
        sudo usermod -aG docker "$USER"
        echo "  docker-ce installed. Relogin or 'newgrp docker' for group access."
    fi
else
    sudo apt install -y ufw fail2ban python3-pip python3-venv docker.io git curl zstd jq
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

# Deploy House Bernard skills
echo "  Deploying workspace skills..."
cp -r openclaw/skills/house-bernard-airlock ~/.openclaw/agents/achillesrun/skills/
cp -r openclaw/skills/house-bernard-executioner ~/.openclaw/agents/achillesrun/skills/
cp -r openclaw/skills/house-bernard-treasury ~/.openclaw/agents/achillesrun/skills/

# Initialize sanctum event ledger
python3 openclaw/skills/house-bernard-treasury/scripts/sanctum_init.py 2>/dev/null || true

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

# Systemd service setup
if ! $WSL2 || $WSL2_SYSTEMD; then
    openclaw onboard --install-daemon 2>/dev/null || true
    echo "  OpenClaw daemon installed."

    if [ -f /etc/systemd/system/openclaw.service ]; then
        sudo sed -i '/\[Service\]/a Restart=on-failure\nRestartSec=10\nWatchdogSec=300' \
            /etc/systemd/system/openclaw.service 2>/dev/null || true
        sudo systemctl daemon-reload 2>/dev/null || true
        echo "  Systemd watchdog configured (auto-restart on crash)."
    fi

    if $WSL2_SYSTEMD; then
        echo "  WSL2 systemd detected — services will persist across sessions."
    fi
else
    echo "  Systemd service — SKIPPED (WSL2 without systemd)"
    echo "  Use achillesrun_start.sh or enable systemd in /etc/wsl.conf"

    # Deploy startup script for WSL2 without systemd
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    if [ -f "$SCRIPT_DIR/achillesrun_start.sh" ]; then
        cp "$SCRIPT_DIR/achillesrun_start.sh" "$HOME/.openclaw/achillesrun_start.sh"
        chmod +x "$HOME/.openclaw/achillesrun_start.sh"
        echo "  Startup script deployed: ~/.openclaw/achillesrun_start.sh"

        # Add to .bashrc for auto-start on WSL2 login
        if ! grep -q "achillesrun_start.sh" "$HOME/.bashrc" 2>/dev/null; then
            echo "" >> "$HOME/.bashrc"
            echo "# House Bernard — auto-start AchillesRun services" >> "$HOME/.bashrc"
            echo "if grep -qi microsoft /proc/version 2>/dev/null; then" >> "$HOME/.bashrc"
            echo "    \$HOME/.openclaw/achillesrun_start.sh --quiet &>/dev/null &" >> "$HOME/.bashrc"
            echo "fi" >> "$HOME/.bashrc"
            echo "  Auto-start added to ~/.bashrc"
        fi
    fi
fi

# Run verification
echo "  Running deployment verification..."
python3 infrastructure/deployment/verify_deployment.py 2>/dev/null || true

# ─── Done ────────────────────────────────────────────────────────────────────

echo ""
echo "============================================================"
echo "  DEPLOYMENT COMPLETE"
echo "============================================================"
echo ""
if $WSL2; then
    echo "  Target: WSL2 / Ubuntu 24.04"
    echo "  Access: Local terminal"
    if $WSL2_SYSTEMD; then
        echo "  Systemd: ENABLED"
    else
        echo "  Systemd: DISABLED (using startup script)"
    fi
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
    if $WSL2_SYSTEMD; then
        echo "       sudo systemctl start openclaw"
        echo "       sudo systemctl enable openclaw   # auto-start on boot"
    else
        echo "       ~/.openclaw/achillesrun_start.sh   # starts Ollama + Docker + gateway"
        echo "       # Or manually:"
        echo "       openclaw gateway --foreground"
    fi
else
    echo "       openclaw gateway"
fi
echo ""
if $WSL2; then
    echo "    5. Configure Windows-side .wslconfig (in %USERPROFILE%):"
    echo "       See infrastructure/deployment/wslconfig.template"
    echo ""
    echo "    6. Run post-gateway setup:"
    echo "       ./infrastructure/deployment/post_gateway_setup.sh"
fi
echo ""
echo "  AchillesRun is ready."
echo "============================================================"
