#!/usr/bin/env python3
"""
OpenClaw Static Site Builder (v0.3)
Reads ledger/HB_STATE.json and results/*/outcome.json.
Writes openclaw_site/ with dashboard, results, genes, denylist, about + assets.
Standard library only. No network. No untrusted code execution.

v0.3 changes:
  - Counts active briefs for {{active_briefs}} template variable
  - Handles missing templates gracefully (skip instead of crash)
  - Better error messages for missing data
"""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_DIR = REPO_ROOT / "ledger"
RESULTS_DIR = REPO_ROOT / "results"
BRIEFS_DIR = REPO_ROOT / "briefs" / "active"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
OUT_DIR = REPO_ROOT / "openclaw_site"
ASSETS = ["style.css", "theme.js"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8", newline="\n")


def load_state() -> Dict[str, Any]:
    state_path = LEDGER_DIR / "HB_STATE.json"
    if not state_path.exists():
        print(f"  Warning: {state_path} not found. Using defaults.")
        return {"project": "House Bernard"}
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


def count_active_briefs() -> int:
    """Count briefs in briefs/active/ directory."""
    if not BRIEFS_DIR.exists():
        return 0
    return sum(1 for f in BRIEFS_DIR.iterdir() if f.is_file() and f.suffix == ".md")


def render_template(name: str, context: Dict[str, Any]) -> str | None:
    tpl_path = TEMPLATES_DIR / name
    if not tpl_path.exists():
        print(f"  Warning: Template {name} not found, skipping.")
        return None
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
    active_briefs = count_active_briefs()
    context = {
        "project": state.get("project", "House Bernard"),
        "survived": counts["SURVIVED"], "culled": counts["CULLED"],
        "blacklisted": counts["BLACKLISTED"], "queued": counts["QUEUED"],
        "quarantined": counts["QUARANTINED"], "rejected": counts["REJECTED"],
        "active_briefs": active_briefs,
    }
    html = render_template("index.html", context)
    if html:
        write_text(OUT_DIR / "index.html", html)


def build_results(outcomes):
    rows = []
    for o in outcomes:
        rows.append(
            f"<tr><td>{o.get('artifact_id', '')}</td>"
            f"<td>{o.get('stage', '')}</td>"
            f"<td>{o.get('result', '')}</td>"
            f"<td>{','.join(o.get('classes', []))}</td>"
            f"<td>{o.get('fingerprint', '')}</td></tr>"
        )
    context = {"rows": "\n".join(rows) if rows else "<tr><td colspan='5'>No results yet.</td></tr>"}
    html = render_template("results.html", context)
    if html:
        write_text(OUT_DIR / "results.html", html)


def build_genes():
    context = {"rows": "<tr><td colspan='3'>Gene registry not yet published.</td></tr>"}
    html = render_template("genes.html", context)
    if html:
        write_text(OUT_DIR / "genes.html", html)


def build_denylist():
    context = {"rows": "<tr><td colspan='2'>Denylist not yet published.</td></tr>"}
    html = render_template("denylist.html", context)
    if html:
        write_text(OUT_DIR / "denylist.html", html)


def build_about():
    html = render_template("about.html", {})
    if html:
        write_text(OUT_DIR / "about.html", html)


def build_pages():
    """Build additional pages (briefs, pipeline, economics, governance) if templates exist."""
    for page in ["briefs.html", "pipeline.html", "economics.html", "governance.html"]:
        html = render_template(page, {})
        if html:
            write_text(OUT_DIR / page, html)


def main() -> int:
    print("OpenClaw Site Builder v0.3")
    state = load_state()
    outcomes = load_outcomes()
    active_briefs = count_active_briefs()
    print(f"  State: loaded | Outcomes: {len(outcomes)} | Active briefs: {active_briefs}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()
    build_index(state, outcomes)
    build_results(outcomes)
    build_genes()
    build_denylist()
    build_about()
    build_pages()
    print(f"  Site built at: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
