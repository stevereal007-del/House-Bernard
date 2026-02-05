#!/usr/bin/env python3
"""
House Bernard - Splicer (Gene Extraction) v0.2

Deterministic extraction of allowlisted top-level functions from a python source file.
- Standard library only
- No execution
- No imports of candidate code
- Content-addressed storage (sha256 of resulting gene module)

Output:
  genes/<sha256>/gene.py
  genes/<sha256>/meta.json

Usage:
  python3 splicer.py --source /path/to/mutation.py --out ./genes --allow hb_ingest,hb_compact
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SPLICER_VERSION = "0.2"


# -----------------------------
# Utilities (deterministic I/O)
# -----------------------------

def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8", newline="\n")


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _rstrip_lines(s: str) -> str:
    lines = s.split("\n")
    lines = [ln.rstrip() for ln in lines]
    return "\n".join(lines).rstrip() + "\n"


# -----------------------------
# AST extraction (no execution)
# -----------------------------

@dataclass(frozen=True)
class ExtractResult:
    extracted_names: List[str]
    missing_names: List[str]
    gene_module_text: str


def _strip_function_docstring_in_ast(fn: ast.FunctionDef) -> ast.FunctionDef:
    """
    Remove function docstring if present as first statement.
    Done on a copied node reference (we mutate the node, but we never execute it).
    """
    if fn.body and isinstance(fn.body[0], ast.Expr):
        v = fn.body[0].value
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            fn.body = fn.body[1:]
    return fn


def _extract_src_segment(src: str, node: ast.AST) -> str:
    """
    Extract exact source segment using lineno/end_lineno if available.
    Deterministic (does not reformat code).
    """
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        raise ValueError("AST node missing location info; cannot extract.")

    lineno = getattr(node, "lineno", None)
    end_lineno = getattr(node, "end_lineno", None)
    if lineno is None or end_lineno is None:
        raise ValueError("AST node missing lineno/end_lineno; cannot extract.")

    lines = src.splitlines(True)  # keep line endings
    start_i = int(lineno) - 1
    end_i = int(end_lineno)       # slice end is exclusive
    segment = "".join(lines[start_i:end_i])

    # If end_col_offset exists, apply it to the last line deterministically
    end_col = getattr(node, "end_col_offset", None)
    if end_col is not None:
        seg_lines = segment.splitlines(True)
        if seg_lines:
            last = seg_lines[-1]
            # keep newline if present
            nl = "\n" if last.endswith("\n") else ""
            seg_lines[-1] = last[: int(end_col)] + nl
            segment = "".join(seg_lines)

    return segment


def _build_gene_module(function_sources: List[str]) -> str:
    header = (
        "# Auto-extracted by House Bernard Splicer v0.2\n"
        "# Deterministic gene capsule. Do not edit by hand.\n\n"
    )
    body = "\n".join(fs.rstrip() for fs in function_sources).rstrip() + "\n"
    return header + body


def extract_genes_from_source(src: str, allow: List[str]) -> ExtractResult:
    """
    Extract allowlisted TOP-LEVEL function defs from source text.
    - No nested extraction
    - No class method extraction
    """
    src = _normalize_newlines(src)
    tree = ast.parse(src, mode="exec")

    # Map top-level function name -> node
    top_level: Dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            top_level[node.name] = node

    extracted_names: List[str] = []
    missing_names: List[str] = []
    extracted_sources: List[str] = []

    for name in allow:
        fn = top_level.get(name)
        if fn is None:
            missing_names.append(name)
            continue

        # Remove docstring in AST (doesn't change offsets unless we regenerate;
        # we only use AST for docstring detection, but we still extract raw source range.)
        _strip_function_docstring_in_ast(fn)

        fn_src = _extract_src_segment(src, fn)
        fn_src = _rstrip_lines(_normalize_newlines(fn_src))

        extracted_names.append(name)
        extracted_sources.append(fn_src)

    gene_module_text = _build_gene_module(extracted_sources)
    gene_module_text = _rstrip_lines(_normalize_newlines(gene_module_text))

    return ExtractResult(
        extracted_names=extracted_names,
        missing_names=missing_names,
        gene_module_text=gene_module_text,
    )


# -----------------------------
# Storage (content-addressed)
# -----------------------------

def store_gene_module(out_dir: Path, gene_module_text: str, meta: dict) -> str:
    gene_bytes = gene_module_text.encode("utf-8")
    gene_hash = _sha256_hex(gene_bytes)

    gene_root = out_dir / gene_hash
    gene_py = gene_root / "gene.py"
    meta_json = gene_root / "meta.json"

    # Idempotent: if already exists, do not rewrite unless content differs
    gene_root.mkdir(parents=True, exist_ok=True)
    if gene_py.exists():
        existing = gene_py.read_text(encoding="utf-8")
        if existing != gene_module_text:
            # Same hash but different content should be impossible; fail-closed.
            raise RuntimeError("Hash collision or non-determinism detected: existing gene.py differs.")
    else:
        _write_text(gene_py, gene_module_text)

    # meta always re-written deterministically (sorted keys)
    meta_out = dict(meta)
    meta_out["gene_sha256"] = gene_hash
    meta_out["splicer_version"] = SPLICER_VERSION
    meta_out["size_bytes"] = len(gene_bytes)

    _write_json(meta_json, meta_out)
    return gene_hash


# -----------------------------
# CLI
# -----------------------------

def _parse_allowlist(s: str) -> List[str]:
    items = [x.strip() for x in s.split(",")]
    # preserve order, remove empties
    return [x for x in items if x]


def main() -> int:
    ap = argparse.ArgumentParser(description="House Bernard Splicer (Gene Extraction)")
    ap.add_argument("--source", required=True, help="Path to mutation.py (or any .py source file)")
    ap.add_argument("--out", required=True, help="Output directory for genes (content-addressed)")
    ap.add_argument("--allow", required=True, help="Comma-separated allowlist of function names")
    ap.add_argument("--require-nonempty", action="store_true",
                    help="Fail if no functions were extracted (recommended).")
    args = ap.parse_args()

    source_path = Path(args.source).resolve()
    out_dir = Path(args.out).resolve()
    allow = _parse_allowlist(args.allow)

    if not source_path.exists() or not source_path.is_file():
        raise SystemExit(f"Source not found: {source_path}")
    if not allow:
        raise SystemExit("Allowlist empty. Refusing to extract arbitrary code.")

    src = _read_text(source_path)
    result = extract_genes_from_source(src, allow)

    if args.require_nonempty and not result.extracted_names:
        raise SystemExit("No genes extracted (empty allowlist match). Fail-closed.")

    meta = {
        "source_file": str(source_path),
        "allowlist": allow,
        "extracted": result.extracted_names,
        "missing": result.missing_names,
    }

    gene_hash = store_gene_module(out_dir, result.gene_module_text, meta)

    # Public-safe stdout (no internal stack traces, no details useful to attackers)
    print(f"GENE_EXTRACTED sha256:{gene_hash}")
    if result.extracted_names:
        print("EXTRACTED: " + ",".join(result.extracted_names))
    else:
        print("EXTRACTED: (none)")
    if result.missing_names:
        print("MISSING: " + ",".join(result.missing_names))
    print(f"PATH: {out_dir / gene_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
