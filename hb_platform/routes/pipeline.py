"""Pipeline: live view of submissions and agent status."""
from __future__ import annotations

import time

from fastapi import APIRouter, Request

from .. import config
from ..database import get_db

router = APIRouter()


def _agent_status() -> list[dict]:
    """Return status of all known agents based on heartbeat messages."""
    agents = []
    with get_db() as conn:
        for name in ("achillesrun", "warden", "treasurer", "magistrate"):
            row = conn.execute(
                "SELECT created_at FROM agent_messages "
                "WHERE from_agent = ? AND message_type = 'heartbeat' "
                "ORDER BY created_at DESC LIMIT 1",
                (name,),
            ).fetchone()
            last = row["created_at"] if row else None
            status = "offline"
            if last:
                # Simple check — if heartbeat within HEARTBEAT_TIMEOUT_S, online
                try:
                    from datetime import datetime, timezone
                    ts = datetime.fromisoformat(last)
                    age = (datetime.now(timezone.utc) - ts).total_seconds()
                    status = "online" if age < config.HEARTBEAT_TIMEOUT_S else "offline"
                except Exception:
                    pass
            agents.append({"name": name.title(), "last_heartbeat": last, "status": status})
    return agents


@router.get("/pipeline")
async def pipeline_view(request: Request):
    with get_db() as conn:
        submissions = [dict(r) for r in conn.execute(
            "SELECT * FROM submissions ORDER BY submitted_at DESC LIMIT 50"
        ).fetchall()]
        counts_row = conn.execute(
            "SELECT "
            "  COALESCE(SUM(status='survived'),0) AS survived, "
            "  COALESCE(SUM(status='culled'),0)    AS culled, "
            "  COALESCE(SUM(status='queued'),0)    AS queued, "
            "  COALESCE(SUM(status='testing'),0)   AS testing "
            "FROM submissions"
        ).fetchone()
    counts = dict(counts_row)
    agents = _agent_status()
    return request.app.state.templates.TemplateResponse(
        "pipeline.html",
        {"request": request, "submissions": submissions, "counts": counts,
         "agents": agents, "citizen": request.state.citizen},
    )
