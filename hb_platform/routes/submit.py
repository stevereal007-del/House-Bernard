"""Artifact submission: upload zip → inbox → status tracking."""
from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse

from .. import config
from ..database import get_db

router = APIRouter()


@router.get("/submit")
async def submit_form(request: Request):
    citizen = request.state.citizen
    submissions = []
    open_briefs = []
    if citizen:
        with get_db() as conn:
            submissions = [dict(r) for r in conn.execute(
                "SELECT * FROM submissions WHERE citizen_id = ? ORDER BY submitted_at DESC",
                (citizen["id"],),
            ).fetchall()]
            open_briefs = [dict(r) for r in conn.execute(
                "SELECT * FROM briefs WHERE status = 'open' ORDER BY created_at DESC"
            ).fetchall()]
    return request.app.state.templates.TemplateResponse(
        "submit.html",
        {"request": request, "citizen": citizen, "submissions": submissions,
         "open_briefs": open_briefs},
    )


@router.post("/submit")
async def submit_artifact(request: Request,
                          artifact: UploadFile = File(...),
                          brief_id: str = Form("")):
    citizen = request.state.citizen
    if not citizen:
        return RedirectResponse("/login", status_code=302)

    if not artifact.filename or not artifact.filename.endswith(".zip"):
        return RedirectResponse("/submit", status_code=302)

    # Read and hash the artifact
    contents = await artifact.read()
    artifact_hash = "sha256:" + hashlib.sha256(contents).hexdigest()

    # Write to inbox for the airlock monitor
    inbox = config.INBOX_DIR
    inbox.mkdir(parents=True, exist_ok=True)
    dest = inbox / artifact.filename
    dest.write_bytes(contents)

    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO submissions (brief_id, citizen_id, artifact_hash, status, submitted_at) "
            "VALUES (?, ?, ?, 'queued', ?)",
            (brief_id or None, citizen["id"], artifact_hash, now),
        )

    return RedirectResponse("/submit", status_code=302)
