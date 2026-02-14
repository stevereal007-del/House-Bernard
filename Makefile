.PHONY: test build-site install-hooks clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

test: ## Run all test suites
	python3 run_tests.py

build-site: ## Build the OpenClaw static site
	python3 openclaw/build.py

install-hooks: ## Install git pre-commit hook
	cp hooks/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed."

sample-test: ## Run the sample SAIF artifact self-test
	cd examples/sample_artifact && python3 SELFTEST.py

clean: ## Remove build artifacts and caches
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf openclaw_site/
	@echo "Cleaned."
