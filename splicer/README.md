# Splicer - Gene Extraction v0.2

Deterministic extraction of allowlisted top-level functions from Python source files.

## Status

**v0.2:** Production-ready for Phase 0 and Phase 1 extraction.

## What It Does

The splicer takes a Python source file (typically a survivor's `mutation.py`) and extracts specific named functions into a content-addressed gene capsule.

### Key Properties

- **Standard library only** - no external dependencies
- **No execution** - uses AST parsing, never imports or runs candidate code
- **Deterministic** - same input always produces same output
- **Content-addressed** - output stored by SHA-256 hash of the gene module
- **Allowlist-only** - you must explicitly name which functions to extract

### Output Structure

```
genes/<sha256>/gene.py    # Extracted functions (docstrings stripped)
genes/<sha256>/meta.json  # Metadata: source, allowlist, extracted/missing names
```

## Usage

```bash
python3 splicer.py --source /path/to/mutation.py --out ./genes --allow hb_ingest,hb_compact
```

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--source` | Yes | Path to the Python source file |
| `--out` | Yes | Output directory for gene capsules |
| `--allow` | Yes | Comma-separated list of function names to extract |
| `--require-nonempty` | No | Fail if no functions matched the allowlist |

## How It Works

1. Reads source file as text (UTF-8)
2. Normalizes newlines
3. Parses AST (no execution)
4. Finds top-level `def` nodes matching the allowlist
5. Extracts exact source segments using line numbers
6. Strips docstrings from extracted functions
7. Builds gene module with header comment
8. Hashes the result (SHA-256)
9. Writes `gene.py` and `meta.json` to `genes/<hash>/`

### What It Does NOT Do

- Extract nested functions or class methods
- Execute or import candidate code
- Reformat or modify extracted code (preserves original formatting)
- Extract anything not on the allowlist
