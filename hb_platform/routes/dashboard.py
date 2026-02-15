"""GET / — main dashboard with live stats."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..database import get_db

router = APIRouter()


def _get_stats() -> dict:
    with get_db() as conn:
        row = conn.execute(
            "SELECT "
            "  COALESCE(SUM(status='survived'),0) AS survived, "
            "  COALESCE(SUM(status='culled'),0)    AS culled, "
            "  COALESCE(SUM(status='queued'),0)    AS queued "
            "FROM submissions"
        ).fetchone()
        briefs_count = conn.execute(
            "SELECT COUNT(*) FROM briefs WHERE status='open'"
        ).fetchone()[0]
        citizens_count = conn.execute(
            "SELECT COUNT(*) FROM citizens"
        ).fetchone()[0]
    return {
        "survived": row["survived"],
        "culled": row["culled"],
        "queued": row["queued"],
        "active_briefs": briefs_count,
        "total_citizens": citizens_count,
        "agents_online": 0,
    }


@router.get("/")
async def index(request: Request):
    stats = _get_stats()
    return request.app.state.templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": stats, "citizen": request.state.citizen},
    )
