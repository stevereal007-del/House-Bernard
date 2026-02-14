"""Phase 0 authentication: citizen ID + HMAC token."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Optional

from . import config


def generate_secret() -> str:
    """Generate a random secret for a citizen."""
    return secrets.token_hex(32)


def generate_token(citizen_id: str, secret: str) -> str:
    """Create an HMAC-based bearer token.  Expires after TOKEN_EXPIRY_HOURS."""
    expires = int(time.time()) + config.TOKEN_EXPIRY_HOURS * 3600
    message = f"{citizen_id}:{expires}".encode()
    sig = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return f"{citizen_id}:{expires}:{sig}"


def verify_token(token: str, lookup_secret) -> Optional[str]:
    """Verify a bearer token.  *lookup_secret(citizen_id)* returns the
    stored secret or None.  Returns citizen_id on success, None on failure."""
    parts = token.split(":")
    if len(parts) != 3:
        return None
    citizen_id, expires_str, sig = parts
    try:
        expires = int(expires_str)
    except ValueError:
        return None
    if time.time() > expires:
        return None
    secret = lookup_secret(citizen_id)
    if secret is None:
        return None
    message = f"{citizen_id}:{expires_str}".encode()
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    return citizen_id
