"""Citizen dashboard: profile, submissions, earnings."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from ..database import get_db

router = APIRouter()


@router.get("/citizen/{citizen_id}")
async def citizen_dashboard(request: Request, citizen_id: str):
    with get_db() as conn:
        profile = conn.execute(
            "SELECT * FROM citizens WHERE id = ?", (citizen_id,)
        ).fetchone()
        if not profile:
            return RedirectResponse("/", status_code=302)
        submissions = conn.execute(
            "SELECT * FROM submissions WHERE citizen_id = ? ORDER BY submitted_at DESC",
            (citizen_id,),
        ).fetchall()
    survived = sum(1 for s in submissions if s["status"] == "survived")
    return request.app.state.templates.TemplateResponse(
        "citizen_dashboard.html",
        {"request": request, "profile": dict(profile),
         "submissions": [dict(s) for s in submissions],
         "survived": survived, "citizen": request.state.citizen},
    )
