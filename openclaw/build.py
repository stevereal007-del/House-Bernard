#!/usr/bin/env python3
"""
OpenClaw Static Site Builder (v0.3)
Reads ledger/HB_STATE.json and results/*/outcome.json.
Writes docs/ (GitHub Pages) from openclaw/templates/.
Standard library only. No network. No untrusted code execution.
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_DIR = REPO_ROOT / "ledger"
RESULTS_DIR = REPO_ROOT / "results"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
OUT_DIR = REPO_ROOT / "docs"
BRIEFS_DIR = REPO_ROOT / "briefs"
ASSETS = ["style.css", "theme.js"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8", newline="\n")


def load_state() -> Dict[str, Any]:
    state_path = LEDGER_DIR / "HB_STATE.json"
    if not state_path.exists():
        raise SystemExit("Missing ledger/HB_STATE.json")
    return read_json(state_path)


def load_outcomes() -> List[Dict[str, Any]]:
    outcomes: List[Dict[str, Any]] = []
    if not RESULTS_DIR.exists():
        return outcomes
    for artifact_dir in sorted(RESULTS_DIR.iterdir()):
        if not artifact_dir.is_dir():
            continue
        out_path = artifact_dir / "outcome.json"
        if not out_path.exists():
            continue
        try:
            outcomes.append(read_json(out_path))
        except Exception:
            continue
    return outcomes


def render_template(name: str, context: Dict[str, Any]) -> str:
    tpl_path = TEMPLATES_DIR / name
    if not tpl_path.exists():
        raise SystemExit(f"Missing template: {tpl_path}")
    tpl = tpl_path.read_text(encoding="utf-8")
    for k, v in context.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl


def copy_assets() -> None:
    for asset in ASSETS:
        src = TEMPLATES_DIR / asset
        if src.exists():
            shutil.copy2(src, OUT_DIR / asset)


def build_index(state, outcomes):
    counts = {"SURVIVED": 0, "CULLED": 0, "BLACKLISTED": 0,
              "QUEUED": 0, "QUARANTINED": 0, "REJECTED": 0}
    for o in outcomes:
        r = o.get("result", "UNKNOWN")
        if r in counts:
            counts[r] += 1
    active_briefs = 0
    active_dir = BRIEFS_DIR / "active"
    if active_dir.exists():
        active_briefs = sum(1 for f in active_dir.iterdir() if f.suffix in (".md", ".json"))
    context = {
        "project": state.get("project", "House Bernard"),
        "survived": counts["SURVIVED"], "culled": counts["CULLED"],
        "blacklisted": counts["BLACKLISTED"], "queued": counts["QUEUED"],
        "quarantined": counts["QUARANTINED"], "rejected": counts["REJECTED"],
        "active_briefs": active_briefs,
    }
    write_text(OUT_DIR / "index.html", render_template("index.html", context))


STATIC_PAGES = ["about.html", "economics.html", "governance.html"]


def build_static_pages():
    for page in STATIC_PAGES:
        tpl_path = TEMPLATES_DIR / page
        if tpl_path.exists():
            write_text(OUT_DIR / page, render_template(page, {}))


def build_pipeline(outcomes):
    counts = {"SURVIVED": 0, "CULLED": 0, "BLACKLISTED": 0,
              "QUARANTINED": 0}
    for o in outcomes:
        r = o.get("result", "UNKNOWN")
        if r in counts:
            counts[r] += 1
    result_rows = []
    for o in outcomes:
        result_rows.append(
            f"<tr><td>{o.get('artifact_id', '')}</td>"
            f"<td>{o.get('stage', '')}</td>"
            f"<td>{o.get('result', '')}</td>"
            f"<td>{','.join(o.get('classes', []))}</td>"
            f"<td>{o.get('fingerprint', '')}</td></tr>"
        )
    context = {
        "survived": counts["SURVIVED"],
        "culled": counts["CULLED"],
        "blacklisted": counts["BLACKLISTED"],
        "quarantined": counts["QUARANTINED"],
        "result_rows": "\n".join(result_rows) if result_rows
            else "<tr><td colspan='5'>No results yet.</td></tr>",
        "gene_rows": "<tr><td colspan='3'>Gene registry not yet published.</td></tr>",
        "denylist_rows": "<tr><td colspan='2'>No entries.</td></tr>",
    }
    write_text(OUT_DIR / "pipeline.html", render_template("pipeline.html", context))


def build_briefs():
    def brief_card(path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("_", " ").replace("-", " ").title()
        for line in text.splitlines():
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break
        return (f'<div class="card"><div class="card-title">{title}</div>'
                f'<div class="card-text">{path.name}</div></div>')

    active_rows: List[str] = []
    closed_rows: List[str] = []
    active_dir = BRIEFS_DIR / "active"
    closed_dir = BRIEFS_DIR / "closed"
    if active_dir.exists():
        for f in sorted(active_dir.iterdir()):
            if f.suffix in (".md", ".json"):
                active_rows.append(brief_card(f))
    if closed_dir.exists():
        for f in sorted(closed_dir.iterdir()):
            if f.suffix in (".md", ".json"):
                closed_rows.append(brief_card(f))
    context = {
        "active_brief_rows": "\n".join(active_rows) if active_rows
            else '<div class="section-body"><p>No active briefs at this time.</p></div>',
        "closed_brief_rows": "\n".join(closed_rows) if closed_rows
            else '<div class="section-body"><p>No closed briefs yet.</p></div>',
    }
    write_text(OUT_DIR / "briefs.html", render_template("briefs.html", context))


def main() -> int:
    state = load_state()
    outcomes = load_outcomes()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()
    build_index(state, outcomes)
    build_pipeline(outcomes)
    build_briefs()
    build_static_pages()
    print(f"OpenClaw site built at: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
