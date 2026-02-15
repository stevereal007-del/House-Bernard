# Contributing to Guild {name}

## Before You Start

1. Read the [CHARTER.md](CHARTER.md).
2. Read the [SAIF v1.1 spec](https://github.com/HouseBernard/House-Bernard).
3. Make sure you're a registered House Bernard citizen.

## Submitting Artifacts

1. Fork this repo.
2. Build your artifact following SAIF v1.1:
   - Single-file Python module
   - Implements `ingest()`, `compact()`, `audit()`
   - Include `manifest.json` with required fields
   - Include `SELFTEST.py` that validates your artifact
3. Place your artifact in `artifacts/`.
4. Open a Pull Request.
5. CI will validate your manifest and run your selftest.
6. If approved, your artifact enters the Selection Furnace.

## Manifest Format

```json
{
  "saif_version": "1.1",
  "artifact_name": "your-artifact-name",
  "entry_point": "mutation.py",
  "selftest": "SELFTEST.py",
  "author_citizen_id": "HB-CIT-XXXX",
  "brief_id": "HB-BRIEF-XXXX"
}
```

## Code of Conduct

The Constitution governs all interactions. The Agent's Code applies
to every participant — human and AI alike.
