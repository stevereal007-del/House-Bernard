"""GitHub webhook handler: PR events → AchillesRun delegation.

GitHub sends POST /webhooks/github with event payloads.
We validate the signature, parse the event, and route to the
appropriate agent via the message bus.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional

from fastapi import APIRouter, Header, Request, Response

from .. import config
from ..agents import message_bus

router = APIRouter(prefix="/webhooks")

# Set via environment or config — the GitHub webhook secret
WEBHOOK_SECRET: Optional[str] = None


def _verify_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    if not WEBHOOK_SECRET:
        return True  # No secret configured — accept all (dev mode)
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header("", alias="X-Hub-Signature-256"),
    x_github_event: str = Header("", alias="X-GitHub-Event"),
):
    body = await request.body()

    if not _verify_signature(body, x_hub_signature_256):
        return Response(status_code=403, content="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return Response(status_code=400, content="Invalid JSON")

    action = payload.get("action", "")

    if x_github_event == "pull_request":
        return _handle_pr(payload, action)
    elif x_github_event == "issue_comment":
        return _handle_comment(payload, action)

    return {"status": "ignored", "event": x_github_event}


def _handle_pr(payload: dict, action: str) -> dict:
    """Handle pull_request events."""
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {}).get("full_name", "")
    pr_number = pr.get("number")
    author = pr.get("user", {}).get("login", "")
    title = pr.get("title", "")

    if action == "opened":
        # New PR — check if it contains an artifact submission
        files_url = pr.get("url", "") + "/files"
        message_bus.send(
            "webhook", "achillesrun", "alert",
            {
                "event": "pr_opened",
                "repo": repo,
                "pr_number": pr_number,
                "author": author,
                "title": title,
                "severity": "low",
            },
        )

        # If it looks like a SAIF submission (has manifest.json in changed files),
        # delegate to warden for scanning
        changed_files = [f.get("filename", "") for f in pr.get("files", [])]
        if any("manifest.json" in f for f in changed_files):
            message_bus.send(
                "achillesrun", "warden", "task",
                {
                    "action": "evaluate_artifact",
                    "repo": repo,
                    "pr_number": pr_number,
                    "author": author,
                },
            )

        return {"status": "pr_opened", "pr": pr_number}

    elif action == "closed" and pr.get("merged"):
        # PR merged — if it was an artifact, trigger post-merge processing
        message_bus.send(
            "webhook", "achillesrun", "alert",
            {
                "event": "pr_merged",
                "repo": repo,
                "pr_number": pr_number,
                "author": author,
                "severity": "low",
            },
        )
        return {"status": "pr_merged", "pr": pr_number}

    return {"status": "pr_ignored", "action": action}


def _handle_comment(payload: dict, action: str) -> dict:
    """Handle issue_comment events — brief claiming via PR comments."""
    if action != "created":
        return {"status": "comment_ignored"}

    comment = payload.get("comment", {})
    body = comment.get("body", "").strip()
    author = comment.get("user", {}).get("login", "")
    issue = payload.get("issue", {})

    # Check for brief claim command: "/claim HB-CIT-XXXX"
    if body.startswith("/claim "):
        citizen_id = body.split(" ", 1)[1].strip()
        message_bus.send(
            "webhook", "achillesrun", "task",
            {
                "action": "brief_claim",
                "citizen_id": citizen_id,
                "github_user": author,
                "issue_number": issue.get("number"),
                "repo": payload.get("repository", {}).get("full_name", ""),
            },
        )
        return {"status": "claim_submitted", "citizen_id": citizen_id}

    return {"status": "comment_ignored"}
