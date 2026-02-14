# Changelog

All notable changes to House Bernard are documented here.

## [0.2.0] — 2026-02-14

### Added
- `hb_utils.py` — shared utility module (datetime helpers, atomic save)
- `run_tests.py` — master test runner for all suites
- `CONTRIBUTING.md` — contributor guide with SAIF v1.1 requirements
- `QUICKSTART.md` — setup and troubleshooting guide
- `CHANGELOG.md` — this file
- `pyproject.toml` — Python project metadata with pytest and ruff config
- `LICENSE` — proprietary license
- `__init__.py` for treasury, splicer, airlock, and ledger packages

### Changed
- Replaced all "GOVERNOR" references with "CROWN" terminology
  - `treasury_cli.py`: "GOVERNOR ACTION ITEMS" → "CROWN ACTION ITEMS"
  - `monthly_ops.py`: "GOVERNOR ACTION REQUIRED" → "CROWN ACTION REQUIRED"
  - `solana_dispatcher.py`: `GOVERNOR_RESERVE_ADDRESS` → `CROWN_RESERVE_ADDRESS`
  - `.gitignore`: `GOVERNORS_BRIEFING.md` → `CROWNS_BRIEFING.md`
- Rewrote `README.md` with clearer structure and directory table
- Upgraded `openclaw/build.py` to v0.3 (active brief counting, graceful template handling)
- Updated `.gitignore` with guild, ISD, and ledger backup patterns

### Fixed
- Guild `__init__.py` already existed but was minimal — kept as-is

## [0.1.0] — 2026-02-13

### Added
- Initial public repository with clean single-commit history
- Full governance framework (Constitution, Covenant, Crown, 20+ documents)
- Treasury engine with royalty decay, bond yields, emission enforcement
- Guild system with formation, governance, financial incentives, advocates, magistrate court
- Splicer for deterministic gene extraction via AST analysis
- Airlock intake monitor with security scanning
- Ledger outcome writer with canonical classification
- Solana dispatcher for on-chain payments with kill switch
- CPA Agent for tax compliance and 1099 monitoring
- OpenClaw site builder and agent specification
- Red team test suites for treasury and monthly ops (18 findings resolved)
- Backend integration tests for dispatcher and CPA agent
- Guild system test suite (full unittest coverage)
- OpenClaw website with Apple-inspired dark/light theme
- GitHub Pages deployment at housebernard.github.io/House-Bernard/

---

*Ad Astra Per Aspera*
