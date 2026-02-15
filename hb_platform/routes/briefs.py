"""Brief marketplace: browse, detail, claim."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..database import get_db

router = APIRouter(prefix="/briefs")


@router.get("")
async def list_briefs(request: Request):
    with get_db() as conn:
        active = conn.execute(
            "SELECT * FROM briefs WHERE status = 'open' ORDER BY created_at DESC"
        ).fetchall()
        closed = conn.execute(
            "SELECT * FROM briefs WHERE status = 'closed' ORDER BY created_at DESC"
        ).fetchall()
    return request.app.state.templates.TemplateResponse(
        "briefs_list.html",
        {"request": request, "active_briefs": [dict(r) for r in active],
         "closed_briefs": [dict(r) for r in closed],
         "citizen": request.state.citizen},
    )


@router.get("/{brief_id}")
async def brief_detail(request: Request, brief_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM briefs WHERE id = ?", (brief_id,)).fetchone()
    if not row:
        return RedirectResponse("/briefs", status_code=302)
    return request.app.state.templates.TemplateResponse(
        "brief_detail.html",
        {"request": request, "brief": dict(row), "citizen": request.state.citizen},
    )


@router.post("/{brief_id}/claim")
async def claim_brief(request: Request, brief_id: str):
    citizen = request.state.citizen
    if not citizen:
        return RedirectResponse("/login", status_code=302)
    with get_db() as conn:
        row = conn.execute("SELECT status FROM briefs WHERE id = ?", (brief_id,)).fetchone()
        if not row or row["status"] != "open":
            return RedirectResponse(f"/briefs/{brief_id}", status_code=302)
        conn.execute(
            "UPDATE briefs SET status = 'claimed', claimed_by = ? WHERE id = ?",
            (citizen["id"], brief_id),
        )
    return RedirectResponse(f"/briefs/{brief_id}", status_code=302)
