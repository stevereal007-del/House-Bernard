#!/usr/bin/env python3
"""
OpenClaw Static Site Builder (v0.1)

Reads:
  - ledger/HB_STATE.json
  - results/*/outcome.json
  - (optional later) ledger/gene_registry.json, ledger/HB_DENYLIST_V1.json

Writes:
  - openclaw_site/index.html
  - openclaw_site/results.html
  - openclaw_site/genes.html
  - openclaw_site/denylist.html
  - openclaw_site/about.html

Standard library only. No network. No execution of untrusted code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_DIR = REPO_ROOT / "ledger"
RESULTS_DIR = REPO_ROOT / "results"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
OUT_DIR = REPO_ROOT / "openclaw_site"


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
            data = read_json(out_path)
            outcomes.append(data)
        except Exception:
            # If one file is corrupt, skip it. OpenClaw is a viewer, not a judge.
            continue
    return outcomes


def render_template(name: str, context: Dict[str, Any]) -> str:
    tpl_path = TEMPLATES_DIR / name
    if not tpl_path.exists():
        raise SystemExit(f"Missing template: {tpl_path}")

    tpl = tpl_path.read_text(encoding="utf-8")

    # Ultra-dumb templating: {{key}} replacement only.
    # This is intentional. Complexity breeds bugs and leaks.
    for k, v in context.items():
        tpl = tpl.replace("{{" + k + "}}", str(v))
    return tpl


def build_index(state: Dict[str, Any], outcomes: List[Dict[str, Any]]) -> None:
    counts = {
        "SURVIVED": 0,
        "CULLED": 0,
        "BLACKLISTED": 0,
        "QUEUED": 0,
        "QUARANTINED": 0,
        "REJECTED": 0,
    }

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
    }

    html = render_template("index.html", context)
    write_text(OUT_DIR / "index.html", html)


def build_results(outcomes: List[Dict[str, Any]]) -> None:
    rows = []
    for o in outcomes:
        artifact = o.get("artifact_id", "")
        stage = o.get("stage", "")
        result = o.get("result", "")
        classes = ",".join(o.get("classes", []))
        fingerprint = o.get("fingerprint", "")

        rows.append(
            f"<tr>"
            f"<td>{artifact}</td>"
            f"<td>{stage}</td>"
            f"<td>{result}</td>"
            f"<td>{classes}</td>"
            f"<td>{fingerprint}</td>"
            f"</tr>"
        )

    context = {
        "rows": "\n".join(rows) if rows else "<tr><td colspan='5'>No results yet.</td></tr>"
    }

    html = render_template("results.html", context)
    write_text(OUT_DIR / "results.html", html)


def build_genes() -> None:
    # Phase 0: placeholder until gene_registry.json exists
    context = {
        "rows": "<tr><td colspan='3'>Gene registry not yet published.</td></tr>"
    }
    html = render_template("genes.html", context)
    write_text(OUT_DIR / "genes.html", html)


def build_denylist() -> None:
    # Phase 0: placeholder until HB_DENYLIST_V1.json exists
    context = {
        "rows": "<tr><td colspan='2'>Denylist not yet published.</td></tr>"
    }
    html = render_template("denylist.html", context)
    write_text(OUT_DIR / "denylist.html", html)


def build_about() -> None:
    html = render_template("about.html", {})
    write_text(OUT_DIR / "about.html", html)


def main() -> int:
    state = load_state()
    outcomes = load_outcomes()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    build_index(state, outcomes)
    build_results(outcomes)
    build_genes()
    build_denylist()
    build_about()

    print(f"OpenClaw site built at: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
