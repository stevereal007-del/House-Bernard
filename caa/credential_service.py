#!/usr/bin/env python3
"""
CAA — Credential Service
Authority: CAA Specification v1.0, Part IV Section 9
Classification: CROWN EYES ONLY / ISD DIRECTOR

Core infrastructure service for session-scoped token management.
Issues ephemeral tokens at session start, validates mid-session,
revokes on compromise or session end. Maintains immutable audit trail.

The credential service is NOT an agent. It is a service hosted on
House Bernard's core infrastructure (Beelink EQ13). It never operates
on external systems.

Usage:
    from caa.credential_service import CredentialService
    svc = CredentialService("caa/caa_state.json")
    result = svc.issue_session_token("agent-001", "guild_head")
"""

from __future__ import annotations

import json
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from caa.compartments import get_compartment, get_credential_scope


# ── Token configuration ──────────────────────────────────────────

DEFAULT_SESSION_TTL_HOURS = 4        # matches openclaw 4-hour session max
ELEVATED_SESSION_TTL_HOURS = 1       # under elevated threat conditions
SECTION_9_SESSION_TTL_HOURS = 2      # shorter for high-tier operatives
TOKEN_HASH_ALGORITHM = "sha256"


# ── Utility ──────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if s is None:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _generate_token() -> str:
    """Generate a cryptographically random session token."""
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _hash_token(token: str) -> str:
    """Hash a token for storage (never store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Credential Service ───────────────────────────────────────────

class CredentialService:
    """
    Session-scoped credential management service.

    Issues ephemeral tokens, validates requests, revokes on compromise.
    Maintains an immutable audit trail. Never exposes master credentials.
    """

    def __init__(self, state_path: str = "caa/caa_state.json") -> None:
        self.state_path = Path(state_path)
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        try:
            content = self.state_path.read_text(encoding="utf-8")
            return json.loads(content)
        except (OSError, IOError, json.JSONDecodeError):
            return self._default_state()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "service": "credential_service",
            "version": "1.0",
            "active_sessions": [],
            "revoked_tokens": [],
            "audit_trail": [],
            "rotation_schedule": {
                "session_tokens": "per_session",
                "infrastructure_credentials": "isd_director_schedule",
            },
            "threat_posture": "nominal",
        }

    def save_state(self) -> Dict[str, Any]:
        """Persist state to disk. Returns confirmation."""
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(self.state, indent=2))
            return {"saved": True, "path": str(self.state_path)}
        except (OSError, IOError) as e:
            return {"saved": False, "error": str(e)}

    # ── Token issuance ───────────────────────────────────────

    def issue_session_token(
        self,
        agent_id: str,
        role: str,
        session_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue a session-scoped token for an authenticated agent.

        The token is valid only for the session duration. It cannot
        be renewed without re-authentication. It cannot be transferred.
        """
        compartment = get_compartment(role)
        if compartment is None:
            return {"error": "unknown_role", "role": role}

        ttl = self._compute_ttl(role)
        now = _now()
        token = _generate_token()
        token_hash = _hash_token(token)

        session = {
            "session_id": _generate_id("SES"),
            "agent_id": agent_id,
            "role": role,
            "token_hash": token_hash,
            "credential_scope": get_credential_scope(role),
            "issued_at": _format_dt(now),
            "expires_at": _format_dt(now + timedelta(hours=ttl)),
            "ttl_hours": ttl,
            "context": session_context,
            "status": "active",
            "revoked": False,
            "heartbeat_count": 0,
            "last_heartbeat": None,
        }

        self.state["active_sessions"].append(session)
        self._audit("token_issued", agent_id, role, session["session_id"])

        return {
            "session_id": session["session_id"],
            "token": token,
            "credential_scope": session["credential_scope"],
            "issued_at": session["issued_at"],
            "expires_at": session["expires_at"],
            "ttl_hours": ttl,
        }

    def _compute_ttl(self, role: str) -> int:
        """Compute session TTL based on role and threat posture."""
        posture = self.state.get("threat_posture", "nominal")
        if posture in ("elevated", "critical"):
            return ELEVATED_SESSION_TTL_HOURS
        if role in ("section_9_operative", "section_9_director"):
            return SECTION_9_SESSION_TTL_HOURS
        return DEFAULT_SESSION_TTL_HOURS

    # ── Token validation ─────────────────────────────────────

    def validate_token(
        self,
        session_id: str,
        token: str,
        requested_scope: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a session token. Checks expiry, revocation, and
        optionally whether the requested scope is authorized.
        """
        session = self._get_session(session_id)
        if session is None:
            return {"valid": False, "reason": "session_not_found"}

        if session.get("revoked"):
            return {"valid": False, "reason": "token_revoked"}

        token_hash = _hash_token(token)
        if token_hash != session.get("token_hash"):
            return {"valid": False, "reason": "token_mismatch"}

        expires = _parse_dt(session.get("expires_at"))
        if expires is not None and _now() >= expires:
            return {"valid": False, "reason": "token_expired"}

        if requested_scope is not None:
            if requested_scope not in session.get("credential_scope", []):
                return {
                    "valid": False,
                    "reason": "scope_not_authorized",
                    "requested": requested_scope,
                }

        return {
            "valid": True,
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "role": session["role"],
        }

    # ── Token revocation ─────────────────────────────────────

    def revoke_token(
        self,
        session_id: str,
        reason: str,
        revoked_by: str = "system",
    ) -> Dict[str, Any]:
        """
        Revoke a session token immediately. Used on compromise
        detection or session end.
        """
        session = self._get_session(session_id)
        if session is None:
            return {"error": "session_not_found"}

        if session.get("revoked"):
            return {"error": "already_revoked"}

        session["revoked"] = True
        session["status"] = "revoked"
        session["revoked_at"] = _format_dt(_now())
        session["revocation_reason"] = reason
        session["revoked_by"] = revoked_by

        self.state["revoked_tokens"].append({
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "revoked_at": session["revoked_at"],
            "reason": reason,
        })

        self._audit("token_revoked", session["agent_id"],
                     session["role"], session_id, reason)

        return {
            "revoked": True,
            "session_id": session_id,
            "agent_id": session["agent_id"],
            "reason": reason,
        }

    def revoke_all_for_agent(
        self,
        agent_id: str,
        reason: str,
        revoked_by: str = "system",
    ) -> Dict[str, Any]:
        """Revoke ALL active sessions for a given agent."""
        revoked = []
        for session in self.state.get("active_sessions", []):
            if session.get("agent_id") == agent_id and not session.get("revoked"):
                result = self.revoke_token(
                    session["session_id"], reason, revoked_by
                )
                if result.get("revoked"):
                    revoked.append(session["session_id"])

        return {
            "agent_id": agent_id,
            "sessions_revoked": len(revoked),
            "session_ids": revoked,
            "reason": reason,
        }

    # ── Silent credential rotation ───────────────────────────

    def rotate_credentials_for_contacts(
        self,
        compromised_agent_id: str,
    ) -> Dict[str, Any]:
        """
        Rotate credentials for all agents that shared operational
        context with the compromised agent. CAA Spec Part II, Section 2.
        """
        affected = []
        for session in self.state.get("active_sessions", []):
            if (session.get("agent_id") != compromised_agent_id
                    and not session.get("revoked")
                    and session.get("status") == "active"):
                affected.append({
                    "session_id": session["session_id"],
                    "agent_id": session["agent_id"],
                    "role": session["role"],
                    "rotation_required": True,
                })

        self._audit(
            "silent_rotation_triggered",
            compromised_agent_id,
            "unknown",
            "N/A",
            f"Affected agents: {len(affected)}",
        )

        return {
            "triggered_by": compromised_agent_id,
            "affected_agents": len(affected),
            "agents": affected,
            "timestamp": _format_dt(_now()),
        }

    # ── Session cleanup ──────────────────────────────────────

    def expire_sessions(self) -> Dict[str, Any]:
        """Expire all sessions past their TTL. Run periodically."""
        now = _now()
        expired = []
        for session in self.state.get("active_sessions", []):
            if session.get("revoked") or session.get("status") != "active":
                continue
            expires = _parse_dt(session.get("expires_at"))
            if expires is not None and now >= expires:
                session["status"] = "expired"
                session["revoked"] = True
                session["revoked_at"] = _format_dt(now)
                session["revocation_reason"] = "ttl_expired"
                expired.append(session["session_id"])

        return {
            "expired_count": len(expired),
            "session_ids": expired,
            "timestamp": _format_dt(now),
        }

    # ── Threat posture ───────────────────────────────────────

    def set_threat_posture(
        self,
        posture: str,
        set_by: str,
    ) -> Dict[str, Any]:
        """
        Update threat posture. Affects TTL computation for new sessions.
        Valid postures: nominal, heightened, elevated, critical
        """
        valid = {"nominal", "heightened", "elevated", "critical"}
        if posture not in valid:
            return {"error": "invalid_posture", "valid": sorted(valid)}

        old = self.state.get("threat_posture", "nominal")
        self.state["threat_posture"] = posture

        self._audit("threat_posture_changed", set_by, "system",
                     "N/A", f"{old} -> {posture}")

        return {
            "previous": old,
            "current": posture,
            "set_by": set_by,
            "timestamp": _format_dt(_now()),
        }

    # ── Status ───────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return credential service status summary."""
        active = [
            s for s in self.state.get("active_sessions", [])
            if s.get("status") == "active" and not s.get("revoked")
        ]
        return {
            "service": "credential_service",
            "version": "1.0",
            "active_sessions": len(active),
            "total_sessions": len(self.state.get("active_sessions", [])),
            "revoked_tokens": len(self.state.get("revoked_tokens", [])),
            "audit_entries": len(self.state.get("audit_trail", [])),
            "threat_posture": self.state.get("threat_posture", "nominal"),
            "timestamp": _format_dt(_now()),
        }

    # ── Private helpers ──────────────────────────────────────

    def _get_session(self, session_id: str) -> Optional[Dict]:
        for s in self.state.get("active_sessions", []):
            if s.get("session_id") == session_id:
                return s
        return None

    def _audit(
        self,
        action: str,
        agent_id: str,
        role: str,
        session_id: str,
        detail: Optional[str] = None,
    ) -> None:
        """Append to immutable audit trail."""
        entry = {
            "timestamp": _format_dt(_now()),
            "action": action,
            "agent_id": agent_id,
            "role": role,
            "session_id": session_id,
        }
        if detail:
            entry["detail"] = detail
        self.state.setdefault("audit_trail", []).append(entry)
