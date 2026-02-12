#!/bin/bash
###############################################################################
# House Bernard — WSL2 Docker Setup
#
# Run this on the actual WSL2 instance to complete Docker setup.
# The Docker daemon requires kernel nftables support which is
# available in WSL2's real kernel but not in sandboxed environments.
###############################################################################

set -euo pipefail

echo "[WSL2] Starting Docker daemon..."
if ! pgrep -x dockerd > /dev/null; then
    sudo dockerd &>/dev/null &
    sleep 5
fi

echo "[WSL2] Verifying Docker..."
docker info > /dev/null 2>&1 || { echo "ERROR: Docker daemon failed to start"; exit 1; }

echo "[WSL2] Pulling Executioner sandbox image..."
docker pull python:3.10.15-alpine

echo "[WSL2] Verifying image..."
docker images python:3.10.15-alpine

echo "[WSL2] Docker setup complete."
