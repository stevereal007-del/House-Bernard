"""House Bernard Platform — FastAPI application entry point."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from . import config
from .auth import generate_token, verify_token
from .database import get_db, init_db
from .routes import briefs, citizen, dashboard, forum, governance, pipeline, submit, webhooks

app = FastAPI(title="House Bernard", docs_url=None, redoc_url=None)

# ── Static files & templates ───────────────────────
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")
app.state.templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))


# ── Auth middleware ─────────────────────────────────

class AuthMiddleware(BaseHTTPMiddleware):
    """Attach request.state.citizen from cookie token."""

    async def dispatch(self, request: Request, call_next):
        request.state.citizen = None
        token = request.cookies.get("hb_token")
        if token:
            def lookup_secret(cid: str):
                with get_db() as conn:
                    row = conn.execute(
                        "SELECT secret FROM citizen_secrets WHERE citizen_id = ?",
                        (cid,),
                    ).fetchone()
                    return row["secret"] if row else None
            citizen_id = verify_token(token, lookup_secret)
            if citizen_id:
                with get_db() as conn:
                    row = conn.execute(
                        "SELECT * FROM citizens WHERE id = ?", (citizen_id,)
                    ).fetchone()
                    if row:
                        request.state.citizen = dict(row)
        return await call_next(request)


app.add_middleware(AuthMiddleware)


# ── Routes ─────────────────────────────────────────

app.include_router(dashboard.router)
app.include_router(forum.router)
app.include_router(briefs.router)
app.include_router(submit.router)
app.include_router(citizen.router)
app.include_router(pipeline.router)
app.include_router(governance.router)
app.include_router(webhooks.router)


@app.get("/login")
async def login_page(request: Request):
    return app.state.templates.TemplateResponse(
        "login.html",
        {"request": request, "citizen": None, "error": None},
    )


@app.post("/login")
async def login_submit(request: Request):
    form = await request.form()
    citizen_id = form.get("citizen_id", "")
    secret = form.get("secret", "")

    with get_db() as conn:
        row = conn.execute(
            "SELECT secret FROM citizen_secrets WHERE citizen_id = ?",
            (citizen_id,),
        ).fetchone()

    if not row or row["secret"] != secret:
        return app.state.templates.TemplateResponse(
            "login.html",
            {"request": request, "citizen": None, "error": "Invalid credentials."},
        )

    token = generate_token(citizen_id, secret)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("hb_token", token, httponly=True, samesite="lax",
                        max_age=config.TOKEN_EXPIRY_HOURS * 3600)
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("hb_token")
    return response


# ── Startup ────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    init_db()
    # Ensure citizen_secrets table exists (supplements main migration)
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS citizen_secrets ("
            "  citizen_id TEXT PRIMARY KEY REFERENCES citizens(id),"
            "  secret TEXT NOT NULL"
            ")"
        )
