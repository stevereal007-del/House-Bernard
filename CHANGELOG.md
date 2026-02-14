# Changelog (Classified)

All notable changes to House Bernard (classified repository) are documented here.

**CLASSIFICATION: CROWN EYES ONLY**

## [0.2.0] — 2026-02-14

### Added
- `hb_utils.py` — shared utility module eliminating code duplication
- `run_tests.py` — master test runner for all suites (5 suites, all passing)
- `CHANGELOG.md` — this file
- `pyproject.toml` — Python project configuration
- Missing `__init__.py` files for all Python packages

### Fixed
- All "Governor" references updated to "Crown" (code, docs, wallet paths, env vars)
- CAA test suite now runs standalone (`python3 caa/test_caa.py`)
- `__pycache__` directories removed from version control
- `.gitignore` updated with guild, ISD, and ledger runtime patterns
- OpenClaw build script upgraded to v0.3

### Changed
- README.md restructured with clear public/classified module separation
- QUICKSTART.md updated with correct pip flags and troubleshooting table
- `CROWN_DISCORD_ID` / `CROWN_GMAIL` env vars replace old Governor naming

## [0.1.0] — 2026-02-08

### Added
- Full classified repository with public-equivalent + classified-only modules
- CAA (Crown Authority Architecture) — 95 tests passing
- ISD (Internal Security Division) — 81 tests passing
- Section 9 offensive security framework
- Legal infrastructure (LLC agreement, token ToS, trademark guide)
- Infrastructure deployment scripts
- Security scanner and seccomp profiles
