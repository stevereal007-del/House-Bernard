#!/usr/bin/env python3
"""
OpenClaw Static Site Builder (v0.3)
Reads ledger/HB_STATE.json and results/*/outcome.json.
Writes openclaw_site/ with dashboard, results, genes, denylist, about + assets.
Standard library only. No network. No untrusted code execution.

Changes v0.3:
- Added active_briefs count from briefs/active/
- Graceful fallback for missing templates
- Added governance and economics pages
- Better error messages
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
PAGES = ["index.html", "briefs.html", "pipeline.html",
         "economics.html", "governance.html", "about.html"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8", newline="\n")


def load_state() -> Dict[str, Any]:
    state_path = LEDGER_DIR / "HB_STATE.json"
    if not state_path.exists():
        print(f"Warning: {state_path} not found, using defaults")
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
    if not BRIEFS_DIR.exists():
        return 0
    return sum(1 for f in BRIEFS_DIR.iterdir()
               if f.is_file() and f.suffix in (".md", ".json"))


def render_template(name: str, context: Dict[str, Any]) -> str:
    tpl_path = TEMPLATES_DIR / name
    if not tpl_path.exists():
        print(f"  Skipping {name} (template not found)")
        return ""
    tpl = tpl_path.read_text(encoding="utf-8")
    for k, v in context.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl


def copy_assets() -> None:
    for asset in ASSETS:
        src = TEMPLATES_DIR / asset
        if src.exists():
            shutil.copy2(src, OUT_DIR / asset)


def build_all(state, outcomes):
    counts = {"SURVIVED": 0, "CULLED": 0, "BLACKLISTED": 0,
              "QUEUED": 0, "QUARANTINED": 0, "REJECTED": 0}
    for o in outcomes:
        r = o.get("result", "UNKNOWN")
        if r in counts:
            counts[r] += 1

    context = {
        "project": state.get("project", "House Bernard"),
        "survived": counts["SURVIVED"],
        "culled": counts["CULLED"],
        "blacklisted": counts["BLACKLISTED"],
        "queued": counts["QUEUED"],
        "quarantined": counts["QUARANTINED"],
        "rejected": counts["REJECTED"],
        "active_briefs": count_active_briefs(),
    }

    for page in PAGES:
        html = render_template(page, context)
        if html:
            write_text(OUT_DIR / page, html)
            print(f"  Built {page}")


def main() -> int:
    state = load_state()
    outcomes = load_outcomes()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()
    print(f"Building OpenClaw site...")
    build_all(state, outcomes)
    print(f"Done → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
