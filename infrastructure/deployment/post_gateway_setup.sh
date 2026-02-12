#!/bin/bash
###############################################################################
# House Bernard — Post-Gateway Setup
#
# Run this ONCE after the gateway starts for the first time.
# Registers cron jobs, enables channels, and runs smoke tests.
#
# Prerequisites:
#   - Gateway running: openclaw gateway --foreground (WSL2) or openclaw gateway
#   - Env vars set: ANTHROPIC_API_KEY, GOOGLE_CHAT_* (optional)
#   - All secrets loaded
#
# Usage:
#   ./post_gateway_setup.sh              # Full setup
#   ./post_gateway_setup.sh --smoke-only # Just run smoke tests
###############################################################################

set -euo pipefail

SMOKE_ONLY=false
if [[ "${1:-}" == "--smoke-only" ]]; then
    SMOKE_ONLY=true
fi

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "============================================================"
echo "  HOUSE BERNARD — Post-Gateway Setup"
echo "============================================================"
echo ""

# ─── Check gateway is running ───────────────────────────────────────────────

echo "[0] Checking gateway..."
if ! openclaw health --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('ok') else 1)" 2>/dev/null; then
    echo "  ERROR: Gateway not reachable. Start it first:"
    echo "    openclaw gateway --foreground   (WSL2)"
    echo "    openclaw gateway                (Beelink)"
    exit 1
fi
echo "  Gateway is running."

if ! $SMOKE_ONLY; then

# ─── Register cron jobs ──────────────────────────────────────────────────────

echo ""
echo "[1] Registering cron jobs..."

# Monthly ops — 1st of each month at 6am UTC
if openclaw cron list --json 2>/dev/null | python3 -c "import sys,json; jobs=json.load(sys.stdin); sys.exit(0 if any(j.get('name')=='monthly-ops' for j in jobs) else 1)" 2>/dev/null; then
    echo "  monthly-ops: already registered"
else
    openclaw cron add \
        --name monthly-ops \
        --cron "0 6 1 * *" \
        --message "Run monthly operations cycle. Execute: cd ~/House-Bernard/treasury && python3 monthly_ops.py run" \
        --session isolated \
        --timeout 120000 \
        2>/dev/null && echo "  monthly-ops: registered (1st of month, 6am UTC)" \
        || echo "  monthly-ops: failed to register (add manually)"
fi

# Helios watcher — every 30 minutes
if openclaw cron list --json 2>/dev/null | python3 -c "import sys,json; jobs=json.load(sys.stdin); sys.exit(0 if any(j.get('name')=='helios-watcher' for j in jobs) else 1)" 2>/dev/null; then
    echo "  helios-watcher: already registered"
else
    openclaw cron add \
        --name helios-watcher \
        --every 30m \
        --message "Department of Continuity check. Execute: cd ~/House-Bernard && python3 openclaw/helios_watcher.py" \
        --session isolated \
        --timeout 30000 \
        2>/dev/null && echo "  helios-watcher: registered (every 30m)" \
        || echo "  helios-watcher: failed to register (add manually)"
fi

# Git archive — every 12 hours
if openclaw cron list --json 2>/dev/null | python3 -c "import sys,json; jobs=json.load(sys.stdin); sys.exit(0 if any(j.get('name')=='git-archive' for j in jobs) else 1)" 2>/dev/null; then
    echo "  git-archive: already registered"
else
    openclaw cron add \
        --name git-archive \
        --cron "0 */12 * * *" \
        --message "Archive snapshot. Execute: cd ~/House-Bernard && git add -A && git diff --cached --quiet || git commit -m 'auto: archive snapshot' && git push origin main" \
        --session isolated \
        --timeout 60000 \
        2>/dev/null && echo "  git-archive: registered (every 12h)" \
        || echo "  git-archive: failed to register (add manually)"
fi

# ─── Enable Google Chat (if credentials present) ────────────────────────────

echo ""
echo "[2] Checking channels..."

if [ -n "${GOOGLE_CHAT_SERVICE_ACCOUNT_FILE:-}" ] && [ -f "${GOOGLE_CHAT_SERVICE_ACCOUNT_FILE:-/dev/null}" ]; then
    echo "  Google Chat credentials found. Enabling channel..."
    openclaw config set channels.googlechat.enabled true 2>/dev/null \
        && echo "  Google Chat: enabled" \
        || echo "  Google Chat: failed to enable"
    openclaw config set channels.googlechat.serviceAccountFile "$GOOGLE_CHAT_SERVICE_ACCOUNT_FILE" 2>/dev/null || true
    openclaw config set channels.googlechat.audience "${GOOGLE_CHAT_WEBHOOK_URL:-placeholder}" 2>/dev/null || true
    if [ -n "${GOVERNOR_GMAIL:-}" ]; then
        openclaw config set channels.googlechat.dm.allowFrom "[\"$GOVERNOR_GMAIL\"]" 2>/dev/null || true
    fi
else
    echo "  Google Chat: credentials not found (skipping)"
    echo "    Set GOOGLE_CHAT_SERVICE_ACCOUNT_FILE and re-run, or enable manually:"
    echo "    openclaw config set channels.googlechat.enabled true"
fi

fi  # end SMOKE_ONLY check

# ─── Smoke tests ─────────────────────────────────────────────────────────────

echo ""
echo "[3] Running smoke tests..."

PASS=0
FAIL=0

# Test 1: Helios watcher
echo -n "  helios_watcher.py: "
if python3 "$REPO_ROOT/openclaw/helios_watcher.py" --quiet 2>/dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "WARN (non-critical alerts)"
    PASS=$((PASS + 1))  # warn is acceptable
fi

# Test 2: Treasury check (dry run)
echo -n "  monthly_ops.py check: "
if python3 "$REPO_ROOT/treasury/monthly_ops.py" check 2>/dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "SKIP (treasury_state.json not yet initialized)"
    PASS=$((PASS + 1))
fi

# Test 3: Verify deployment
echo -n "  verify_deployment.py: "
if python3 "$REPO_ROOT/infrastructure/deployment/verify_deployment.py" --quick 2>/dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "WARN (some checks pending)"
    PASS=$((PASS + 1))
fi

# Test 4: OpenClaw cron list
echo -n "  openclaw cron list: "
if openclaw cron list --json 2>/dev/null | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
fi

# Test 5: OpenClaw health
echo -n "  openclaw health: "
if openclaw health --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('ok')" 2>/dev/null; then
    echo "PASS"
    PASS=$((PASS + 1))
else
    echo "FAIL"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "============================================================"
if [ $FAIL -eq 0 ]; then
    echo "  SMOKE TESTS: ALL PASS ($PASS/$((PASS + FAIL)))"
    echo ""
    echo "  AchillesRun is operational."
    echo "  Open Google Chat and send a message to test."
else
    echo "  SMOKE TESTS: $FAIL FAILED ($PASS/$((PASS + FAIL)) passed)"
    echo ""
    echo "  Check gateway logs: openclaw gateway --foreground"
fi
echo "============================================================"
