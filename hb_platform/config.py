"""Platform configuration. All paths resolve relative to the repo root."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Paths ──────────────────────────────────────────
DB_PATH = REPO_ROOT / "ledger" / "platform.db"
LEDGER_DIR = REPO_ROOT / "ledger"
RESULTS_DIR = REPO_ROOT / "results"
BRIEFS_DIR = REPO_ROOT / "briefs"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent / "static"
INBOX_DIR = Path.home() / ".openclaw" / "inbox"
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"

# ── Auth ───────────────────────────────────────────
SECRET_KEY = "hb-dev-secret-change-in-production"
TOKEN_EXPIRY_HOURS = 24

# ── Agents ─────────────────────────────────────────
HEARTBEAT_INTERVAL_S = 60
HEARTBEAT_TIMEOUT_S = 300          # 5 min before considered dead
ESCALATION_TIMEOUT_S = 900         # 15 min before Crown alert

# ── Model router ───────────────────────────────────
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral:7b"
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
