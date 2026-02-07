#!/bin/bash
###############################################################################
# House Bernard — 1984 Hosting VPS Setup
# Run this ONCE on a fresh 1984.hosting VPS (Ubuntu 24.04)
#
# What this does:
#   1. Creates 'hb' service user (no shell, limited permissions)
#   2. Sets up directory structure
#   3. Installs intake server as systemd service
#   4. Configures UFW firewall
#   5. Installs Tailscale for Beelink connectivity
#   6. Hardens SSH
#
# Usage:
#   scp vps_setup.sh root@<vps-ip>:~/
#   ssh root@<vps-ip> 'bash ~/vps_setup.sh'
#
# IMPORTANT: Review each section before running.
###############################################################################

set -euo pipefail

echo "=== House Bernard VPS Setup ==="
echo "Provider: 1984 Hosting (Iceland)"
echo "Purpose: Public shield wall / intake server"
echo ""

# === 1. SYSTEM UPDATE ===
echo "[1/6] System update..."
apt update && apt upgrade -y
apt install -y ufw fail2ban rsync python3 python3-pip

# === 2. SERVICE USER ===
echo "[2/6] Creating service user 'hb'..."
if id "hb" &>/dev/null; then
    echo "User 'hb' already exists. Skipping."
else
    useradd -r -m -d /opt/hb -s /usr/sbin/nologin hb
fi

# === 3. DIRECTORY STRUCTURE ===
echo "[3/6] Setting up directories..."
mkdir -p /opt/hb/{staging,results,logs}
chown -R hb:hb /opt/hb
chmod 750 /opt/hb
chmod 770 /opt/hb/staging  # writable by intake server
chmod 755 /opt/hb/results  # readable for result serving

# === 4. INTAKE SERVER ===
echo "[4/6] Installing intake server..."

# Copy intake_server.py to /opt/hb/
# (assumes you've already scp'd the file, or paste inline)
if [ ! -f /opt/hb/intake_server.py ]; then
    echo "WARNING: /opt/hb/intake_server.py not found."
    echo "Copy it manually: scp intake_server.py root@<vps>:/opt/hb/"
fi

# Systemd service
cat > /etc/systemd/system/hb-intake.service << 'EOF'
[Unit]
Description=House Bernard Intake Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=hb
Group=hb
WorkingDirectory=/opt/hb
ExecStart=/usr/bin/python3 /opt/hb/intake_server.py --port 8443 --bind 0.0.0.0 --staging-dir /opt/hb/staging --results-dir /opt/hb/results
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/hb/staging /opt/hb/results /opt/hb/logs
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictNamespaces=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hb-intake.service
# Don't start yet — wait for intake_server.py to be in place

# === 5. FIREWALL ===
echo "[5/6] Configuring UFW firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 8443/tcp comment "House Bernard Intake"
# Allow Tailscale
ufw allow in on tailscale0

echo "y" | ufw enable

# === 6. TAILSCALE ===
echo "[6/6] Installing Tailscale..."
if ! command -v tailscale &>/dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
    echo ""
    echo "Run 'sudo tailscale up' to authenticate."
    echo "Then note the Tailscale IP for vps_sync.sh on the Beelink."
else
    echo "Tailscale already installed."
fi

# === SSH HARDENING ===
echo "Hardening SSH..."
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl restart sshd

# === FAIL2BAN ===
echo "Configuring fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
maxretry = 3
bantime = 3600
findtime = 600

[hb-intake]
enabled = true
port = 8443
filter = hb-intake
maxretry = 10
bantime = 600
findtime = 60
EOF

# Custom filter for intake server abuse
cat > /etc/fail2ban/filter.d/hb-intake.conf << 'EOF'
[Definition]
failregex = ^.*"ip": "<HOST>".*"status": "RATE_LIMITED"
ignoreregex =
EOF

systemctl enable fail2ban
systemctl restart fail2ban

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Next steps:"
echo "  1. Copy intake_server.py to /opt/hb/"
echo "  2. Run: sudo tailscale up"
echo "  3. Run: sudo systemctl start hb-intake"
echo "  4. Test: curl http://localhost:8443/health"
echo "  5. Note Tailscale IP for Beelink vps_sync.sh"
echo ""
echo "VPS is now a shield wall. It stores but never processes."
