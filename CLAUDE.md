# House Bernard — Claude Code Instructions

## Identity
You are working on the House Bernard repository.
The Governor is HeliosBlade. The agent is AchillesRun.
This is a sovereign research micro-nation's codebase.

## Critical Rules
- NEVER commit directly to main without Governor review
- NEVER expose Section 9 contents in commit messages
- NEVER run weapons code outside Docker sandbox
- NEVER modify CONSTITUTION.md or COVENANT.md without
  explicit Governor instruction
- NEVER commit .env files or private keys
- All Python code must pass security_scanner.py
- All test output goes to JSON format

## Directory Structure
- section_9/          — CLASSIFIED. Crown eyes only.
- security/           — AST scanner, seccomp profiles
- executioner/        — Selection Furnace (T0-T4 testing)
- treasury/           — Token economics engine (61 tests)
- openclaw/           — Agent config and deployment
- lab_b/              — Security genetics laboratory
- legal/              — LLC operating agreement, token terms,
                        trademark guide. All DRAFTS pending
                        Cowork Legal Plugin review.
- token/              — $HOUSEBERNARD SPL token on Solana.
                        Metadata, logo, and TOKEN_RECORD.md.

## Tonight's Build
If the Governor says "run tonight's build" or "let's go",
read TONIGHTS_BUILD.md for the full deployment playbook.
Priority order: repo update → ENS domain → system check →
token scaffold → testnet deploy.

## Code Standards
- Python 3.10+, type hints on all functions
- Solana CLI + spl-token for all token operations
- No external dependencies not already in the repo
- All output as structured JSON
- All weapons must fail to PASSIVE, never fail to ACTIVE
- Test before commit. Always.

## Section 9 Designations
- Weapons: S9-W-XXX (next available: 007)
- Threats: S9-T-XXX (next available: 001)
- Check section_9/WORK_INSTRUCTIONS.md Appendix C

## Legal / Token Notes
- The legal/ docs reference the Cowork Legal Plugin for
  review. Commands: /review-contract, /brief, /triage-nda
- Token is SPL on Solana mainnet — no custom smart contract,
  uses Solana's built-in Token Program
- Treasury engine handles vesting, allocation tracking, and
  constitutional constraints — not the token contract
- Allocation wallets stored in ~/hb-*.json (NEVER commit)
- LLC: House Bernard LLC (file in Governor's home state)
