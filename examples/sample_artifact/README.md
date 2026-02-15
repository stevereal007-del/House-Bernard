# Sample SAIF v1.1 Artifact: Key-Value Counter

A working example of a SAIF v1.1 compliant artifact for House Bernard's
Selection Furnace (Executioner).

## What It Does

Maintains a key-value store that counts write frequency per key.
On compaction, drops least-written keys to fit the byte budget
while preserving the `total_events` invariant.

## Files

| File | Purpose |
|------|---------|
| `mutation.py` | The artifact — implements `ingest`, `compact`, `audit` |
| `SELFTEST.py` | Self-test that the Executioner runs at T0 |
| `manifest.json` | Artifact metadata |
| `schema.json` | State schema |
| `README.md` | This file |

## How to Submit

```bash
cd examples/sample_artifact
zip -r kv_counter.zip mutation.py SELFTEST.py manifest.json schema.json README.md
cp kv_counter.zip ~/.openclaw/inbox/
```

## How to Test Locally

```bash
cd examples/sample_artifact
python3 SELFTEST.py
```
