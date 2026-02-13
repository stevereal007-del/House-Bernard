#!/usr/bin/env python3
"""
OpenClaw Static Site Builder (v0.2)
Reads ledger/HB_STATE.json and results/*/outcome.json.
Writes openclaw_site/ with dashboard, results, genes, denylist, about + assets.
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
    context = {
        "project": state.get("project", "House Bernard"),
        "survived": counts["SURVIVED"], "culled": counts["CULLED"],
        "blacklisted": counts["BLACKLISTED"], "queued": counts["QUEUED"],
        "quarantined": counts["QUARANTINED"], "rejected": counts["REJECTED"],
    }
    write_text(OUT_DIR / "index.html", render_template("index.html", context))


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
    write_text(OUT_DIR / "results.html", render_template("results.html", context))


def build_genes():
    context = {"rows": "<tr><td colspan='3'>Gene registry not yet published.</td></tr>"}
    write_text(OUT_DIR / "genes.html", render_template("genes.html", context))


def build_denylist():
    context = {"rows": "<tr><td colspan='2'>Denylist not yet published.</td></tr>"}
    write_text(OUT_DIR / "denylist.html", render_template("denylist.html", context))


def build_about():
    write_text(OUT_DIR / "about.html", render_template("about.html", {}))


def main() -> int:
    state = load_state()
    outcomes = load_outcomes()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()
    build_index(state, outcomes)
    build_results(outcomes)
    build_genes()
    build_denylist()
    build_about()
    print(f"OpenClaw site built at: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
