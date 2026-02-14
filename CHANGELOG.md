# Changelog

All notable changes to House Bernard are documented here.

## [0.3.0] — 2026-02-14

### Added
- `examples/sample_artifact/` — working SAIF v1.1 artifact (key-value counter) with selftest
- `hooks/pre-commit` — pre-commit hook checks for secrets, pycache, runs tests
- `deployment_config.template.json` — config template for wallet addresses and RPC endpoints
- `Makefile` — `make test`, `make build-site`, `make install-hooks`, `make clean`

### Changed
- All engines refactored to import from `hb_utils.py` instead of duplicating utility functions
- 19 duplicate function definitions eliminated across treasury, guild, and support modules

## [0.2.0] — 2026-02-14

### Added
- `hb_utils.py` — shared utility module
- `run_tests.py` — master test runner for all suites
- `CONTRIBUTING.md` — contributor guidelines
- `CHANGELOG.md`, `LICENSE`, `pyproject.toml`
- Missing `__init__.py` files for all Python packages

### Fixed
- All "Governor" references updated to "Crown"
- `__pycache__` directories removed from version control
- OpenClaw build script handles missing templates gracefully (v0.3)

### Changed
- README.md rewritten for clarity
- QUICKSTART.md updated with correct pip flags

## [0.1.0] — 2026-02-08

### Added
- Initial repository structure and full governance framework
- Treasury engine, guild system, OpenClaw site, Executioner pipeline
- Token metadata for $HOUSEBERNARD on Solana
