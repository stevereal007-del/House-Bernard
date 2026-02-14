# Quick Start Guide

Get House Bernard running locally in under five minutes.

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10+ | `python3 --version` |
| Git | any | `git --version` |
| pip | any | `pip3 --version` |

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/HouseBernard/House-Bernard.git
cd House-Bernard

# 2. (Optional) Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dev dependencies (if needed)
pip3 install --break-system-packages ruff  # Linter (optional)
```

No external Python packages are required. House Bernard uses the standard library only.

## Run Tests

```bash
# Run all test suites
python3 run_tests.py

# Run with verbose output
python3 run_tests.py -v

# Run individual suites
python3 -m unittest guild/test_guild_system.py -v
python3 treasury/redteam_test.py
python3 treasury/redteam_monthly_ops.py
python3 treasury/test_backend.py
```

## Build the Website

```bash
python3 openclaw/build.py
# Output: openclaw_site/
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run from repo root: `cd House-Bernard` |
| `pip install` fails on Ubuntu 24+ | Add `--break-system-packages` flag |
| Tests fail with import errors | Ensure Python 3.10+: `python3 --version` |
| `openclaw/build.py` fails | Ensure `ledger/HB_STATE.json` exists |

## Project Layout

```
House-Bernard/
  run_tests.py          <- Master test runner
  hb_utils.py           <- Shared utilities
  pyproject.toml        <- Project metadata
  treasury/             <- Financial engine + tests
  guild/                <- Guild system + tests
  airlock/              <- Intake monitoring
  splicer/              <- Gene extraction
  ledger/               <- Outcome records
  openclaw/             <- Agent spec + site builder
  briefs/               <- Research briefs
  token/                <- Token metadata
```

## Next Steps

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the submission process
2. Browse [`briefs/active/`](briefs/active/) for open research problems
3. Read the [CONSTITUTION.md](CONSTITUTION.md) and [COVENANT.md](COVENANT.md)
4. Study the [RESEARCH_BRIEF_TEMPLATE.md](RESEARCH_BRIEF_TEMPLATE.md)

---

*Ad Astra Per Aspera*
