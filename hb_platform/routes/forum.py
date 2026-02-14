"""Forum routes: topic list, thread list, thread view, post/reply."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from ..database import get_db

router = APIRouter(prefix="/forum")


@router.get("")
async def topic_list(request: Request):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT t.*, "
            "  (SELECT COUNT(*) FROM forum_threads WHERE topic_id = t.id) AS thread_count "
            "FROM forum_topics t ORDER BY t.id"
        ).fetchall()
    topics = [dict(r) for r in rows]
    return request.app.state.templates.TemplateResponse(
        "forum.html",
        {"request": request, "topics": topics, "citizen": request.state.citizen},
    )


@router.get("/{topic_id}")
async def thread_list(request: Request, topic_id: int):
    with get_db() as conn:
        topic = conn.execute(
            "SELECT * FROM forum_topics WHERE id = ?", (topic_id,)
        ).fetchone()
        if not topic:
            return RedirectResponse("/forum", status_code=302)
        rows = conn.execute(
            "SELECT th.*, "
            "  (SELECT COUNT(*) FROM forum_posts WHERE thread_id = th.id) AS post_count "
            "FROM forum_threads th WHERE th.topic_id = ? "
            "ORDER BY th.pinned DESC, th.created_at DESC",
            (topic_id,),
        ).fetchall()
    threads = [dict(r) for r in rows]
    return request.app.state.templates.TemplateResponse(
        "forum_topic.html",
        {"request": request, "topic": dict(topic), "threads": threads,
         "citizen": request.state.citizen},
    )


@router.post("/{topic_id}/new")
async def create_thread(request: Request, topic_id: int,
                        title: str = Form(...), body: str = Form(...)):
    citizen = request.state.citizen
    if not citizen:
        return RedirectResponse("/login", status_code=302)
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO forum_threads (topic_id, title, author_id, created_at) "
            "VALUES (?, ?, ?, ?)",
            (topic_id, title, citizen["id"], now),
        )
        thread_id = cur.lastrowid
        conn.execute(
            "INSERT INTO forum_posts (thread_id, author_id, body, created_at) "
            "VALUES (?, ?, ?, ?)",
            (thread_id, citizen["id"], body, now),
        )
    return RedirectResponse(f"/forum/{topic_id}/{thread_id}", status_code=302)


@router.get("/{topic_id}/{thread_id}")
async def view_thread(request: Request, topic_id: int, thread_id: int):
    with get_db() as conn:
        thread = conn.execute(
            "SELECT * FROM forum_threads WHERE id = ? AND topic_id = ?",
            (thread_id, topic_id),
        ).fetchone()
        if not thread:
            return RedirectResponse(f"/forum/{topic_id}", status_code=302)
        posts = conn.execute(
            "SELECT * FROM forum_posts WHERE thread_id = ? ORDER BY created_at",
            (thread_id,),
        ).fetchall()
    return request.app.state.templates.TemplateResponse(
        "forum_thread.html",
        {"request": request, "thread": dict(thread),
         "posts": [dict(p) for p in posts], "citizen": request.state.citizen},
    )


@router.post("/{topic_id}/{thread_id}/reply")
async def reply_to_thread(request: Request, topic_id: int, thread_id: int,
                          body: str = Form(...)):
    citizen = request.state.citizen
    if not citizen:
        return RedirectResponse("/login", status_code=302)
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        thread = conn.execute(
            "SELECT locked FROM forum_threads WHERE id = ?", (thread_id,)
        ).fetchone()
        if not thread or thread["locked"]:
            return RedirectResponse(f"/forum/{topic_id}/{thread_id}", status_code=302)
        conn.execute(
            "INSERT INTO forum_posts (thread_id, author_id, body, created_at) "
            "VALUES (?, ?, ?, ?)",
            (thread_id, citizen["id"], body, now),
        )
    return RedirectResponse(f"/forum/{topic_id}/{thread_id}", status_code=302)
