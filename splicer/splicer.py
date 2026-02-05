#!/usr/bin/env python3
"""
House Bernard - Gene Splicer (v0.1)
Deterministic extraction of whitelisted function "genes" from mutation.py.

Standard library only.
No execution.
No network.
No time calls.

Usage:
  python3 splicer.py --source /path/to/mutation.py --out ./genes --allow hb_score,hb_compact,hb_ingest

Notes:
- This intentionally only extracts functions by *explicit allowlist*.
- No "search the whole AST for magic". That way lies madness.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, s: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8", newline="\n")


def write_json(path: Path, obj: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def strip_docstring_from_function(fn: ast.FunctionDef) -> ast.FunctionDef:
    """
    Remove the first statement if it's a docstring literal.
    Deterministic transformation.
    """
    if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(fn.body[0].value, ast.Constant):
        if isinstance(fn.body[0].value.value, str):
            fn.body = fn.body[1:]
    return fn


def extract_function_source(src: str, fn: ast.FunctionDef) -> str:
    """
    Extract the exact source for the function definition using node offsets.
    Requires end_lineno / end_col_offset (py3.8+).
    """
    lines = src.splitlines(True)  # keep line endings
    if fn.lineno is None or fn.end_lineno is None:
        raise ValueError("AST node missing line info; cannot extract deterministically.")
    start = fn.lineno - 1
    end = fn.end_lineno
    chunk = "".join(lines[start:end])

    # Trim to end_col_offset if available (rarely needed, but deterministic)
    if fn.end_col_offset is not None:
        # apply end_col_offset to the last line only
        chunk_lines = chunk.splitlines(True)
        if chunk_lines:
            chunk_lines[-1] = chunk_lines[-1][: fn.end_col_offset] + ("\n" if chunk_lines[-1].endswith("\n") else "")
            chunk = "".join(chunk_lines)

    return chunk.rstrip() + "\n"


def normalize_gene_source(fn_src: str) -> str:
    """
    Deterministic normalization:
    - normalize newlines
    - strip trailing whitespace per line
    - ensure final newline
    DOES NOT attempt semantic rewrites.
    """
    lines = fn_src.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [ln.rstrip() for ln in lines]
    return "\n".join(lines).rstrip() + "\n"


def build_gene_module(genes: List[str]) -> str:
    """
    Wrap extracted functions into a tiny module.
    """
    header = (
        "# Auto-extracted by House Bernard Splicer v0.1\n"
        "# Deterministic gene capsule. Do not edit by hand.\n\n"
    )
    return header + "\n".join(genes).rstrip() + "\n"


def splice(source_path: Path, out_dir: Path, allow: List[str]) -> Tuple[str, Dict]:
    src = read_text(source_path)

    tree = ast.parse(src, filename=str(source_path))
    # map function name -> FunctionDef
    fns: Dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            fns[node.name] = node

    extracted: List[str] = []
    extracted_names: List[str] = []
    missing: List[str] = []

    for name in allow:
        fn = fns.get(name)
        if fn is None:
            missing.append(name)
            continue

        # sanitize in-AST (docstring removal) but keep source extraction stable
        fn_clean = strip_docstring_from_function(fn)

        fn_src = extract_function_source(src, fn_clean)
        fn_src = normalize_gene_source(fn_src)

        extracted.append(fn_src)
        extracted_names.append(name)

    gene_module = build_gene_module(extracted).encode("utf-8")
    gene_hash = sha256_bytes(gene_module)

    meta = {
        "splicer_version": "0.1",
        "source_file": str(source_path),
        "allowlist": allow,
        "extracted": extracted_names,
        "missing": missing,
        "gene_sha256": gene_hash,
        "size_bytes": len(gene_module),
    }

    # store content-addressed
    gene_root = out_dir / gene_hash
    write_text(gene_root / "gene.py", gene_module.decode("utf-8"))
    write_json(gene_root / "meta.json", meta)

    return gene_hash, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="Path to mutation.py (or any python file)")
    ap.add_argument("--out", required=True, help="Genes output directory")
    ap.add_argument("--allow", required=True, help="Comma-separated list of allowed function names")
    args = ap.parse_args()

    source_path = Path(args.source).resolve()
    out_dir = Path(args.out).resolve()
    allow = [s.strip() for s in args.allow.split(",") if s.strip()]

    if not source_path.exists() or not source_path.is_file():
        raise SystemExit(f"Source not found: {source_path}")
    if not allow:
        raise SystemExit("Allowlist empty. Refusing to extract 'whatever looks cool'.")

    gene_hash, meta = splice(source_path, out_dir, allow)

    # Public-safe stdout (no stack traces, no internal details)
    print(f"GENE_EXTRACTED sha256:{gene_hash}")
    print(f"EXTRACTED: {','.join(meta['extracted']) if meta['extracted'] else '(none)'}")
    if meta["missing"]:
        print(f"MISSING: {','.join(meta['missing'])}")
    print(f"PATH: {out_dir / gene_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
