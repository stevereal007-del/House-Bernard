"""Static content pages: governance, economics, about.

These serve the existing openclaw/templates HTML directly via Jinja2,
wrapped in the platform's base template for consistent nav/footer.
The content sections are extracted from the static files and placed
inside {% block content %} at render time.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

# Read the raw static HTML from openclaw/templates — we serve them as-is
# since they already contain full page markup and match the design language.
_OPENCLAW_TPL = Path(__file__).resolve().parents[2] / "openclaw" / "templates"


def _serve_static(name: str) -> str:
    """Return full HTML from an openclaw template file."""
    path = _OPENCLAW_TPL / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "<h1>Page not found</h1>"


@router.get("/governance")
async def governance(request: Request):
    return HTMLResponse(_serve_static("governance.html"))


@router.get("/economics")
async def economics(request: Request):
    return HTMLResponse(_serve_static("economics.html"))


@router.get("/about")
async def about(request: Request):
    return HTMLResponse(_serve_static("about.html"))
