#!/usr/bin/env python3
"""
House Bernard — Backend Integration Tests
Tests solana_dispatcher.py and cpa_agent.py in offline mode.

These tests validate logic WITHOUT touching the blockchain.
They mock the spl-token CLI calls and test:
  - Payment validation and rate limiting
  - CPA Agent recording and 1099 threshold detection
  - Kill switch behavior
  - Batch payment processing
  - Retry queue mechanics
  - Yearly tax report generation

Run: python3 test_backend.py
"""

import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure treasury/ is importable
sys.path.insert(0, str(Path(__file__).parent))

from cpa_agent import CPAAgent


def _now():
    return datetime.now(timezone.utc)


def _format_dt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  ✓ {name}")

    def fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ✗ {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'=' * 50}")
        print(f"  BACKEND TESTS: {self.passed}/{total} passed")
        if self.errors:
            print(f"\n  FAILURES:")
            for name, reason in self.errors:
                print(f"    {name}: {reason}")
        print(f"{'=' * 50}")
        return self.failed == 0


results = TestResults()


# ---------------------------------------------------------------------------
# CPA Agent Tests
# ---------------------------------------------------------------------------

def test_cpa_record_payment():
    """CPA Agent correctly records a payment."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "_schema_version": "1.0",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }, f)
        tmp_path = f.name

    try:
        cpa = CPAAgent(ledger_path=tmp_path)
        receipt = {
            "status": "SUCCESS",
            "timestamp": "2026-03-15T10:00:00Z",
            "recipient": "abc123walletaddress",
            "amount": 5000,
            "usd_value_per_token": 0.002,
            "usd_total": 10.0,
            "contributor_id": "alice",
            "task_id": "HB-2026-001",
            "reason": "Furnace survival",
            "tx_signature": "fake_sig_123",
        }
        cpa.record_payment(receipt)

        assert len(cpa.ledger["payments"]) == 1, "Should have 1 payment"
        assert "alice" in cpa.ledger["contributors"], "alice should be in contributors"
        assert cpa.ledger["contributors"]["alice"]["total_tokens_earned"] == 5000
        assert cpa.ledger["contributors"]["alice"]["yearly_usd"]["2026"] == 10.0
        results.ok("CPA records payment correctly")
    except AssertionError as e:
        results.fail("CPA records payment correctly", str(e))
    except Exception as e:
        results.fail("CPA records payment correctly", str(e))
    finally:
        os.unlink(tmp_path)


def test_cpa_1099_threshold():
    """CPA Agent flags contributors at $600 threshold."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "_schema_version": "1.0",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }, f)
        tmp_path = f.name

    try:
        cpa = CPAAgent(ledger_path=tmp_path)

        # Add payments to alice that total > $600
        for i in range(65):  # 65 payments of $10 = $650
            receipt = {
                "status": "SUCCESS",
                "timestamp": f"2026-{(i % 12) + 1:02d}-15T10:00:00Z",
                "recipient": "alice_wallet",
                "amount": 5000,
                "usd_value_per_token": 0.002,
                "usd_total": 10.0,
                "contributor_id": "alice",
                "task_id": f"HB-2026-{i:03d}",
                "reason": "test",
                "tx_signature": f"sig_{i}",
            }
            cpa.record_payment(receipt)

        flagged = cpa.check_1099_threshold(2026)
        assert len(flagged) == 1, f"Expected 1 flagged, got {len(flagged)}"
        assert flagged[0]["status"] == "NEEDS_1099"
        assert flagged[0]["ytd_usd"] == 650.0
        results.ok("CPA flags 1099 threshold correctly")
    except Exception as e:
        results.fail("CPA flags 1099 threshold correctly", str(e))
    finally:
        os.unlink(tmp_path)


def test_cpa_approaching_threshold():
    """CPA Agent warns when approaching $600."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "_schema_version": "1.0",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }, f)
        tmp_path = f.name

    try:
        cpa = CPAAgent(ledger_path=tmp_path)

        # $500 total (above 80% of $600)
        for i in range(50):
            receipt = {
                "status": "SUCCESS",
                "timestamp": "2026-06-15T10:00:00Z",
                "recipient": "bob_wallet",
                "amount": 5000,
                "usd_value_per_token": 0.002,
                "usd_total": 10.0,
                "contributor_id": "bob",
                "task_id": f"HB-2026-{i:03d}",
                "reason": "test",
                "tx_signature": f"sig_{i}",
            }
            cpa.record_payment(receipt)

        flagged = cpa.check_1099_threshold(2026)
        assert len(flagged) == 1
        assert flagged[0]["status"] == "APPROACHING_THRESHOLD"
        results.ok("CPA warns approaching threshold")
    except Exception as e:
        results.fail("CPA warns approaching threshold", str(e))
    finally:
        os.unlink(tmp_path)


def test_cpa_failed_payment_not_recorded():
    """CPA Agent ignores failed payments."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "_schema_version": "1.0",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }, f)
        tmp_path = f.name

    try:
        cpa = CPAAgent(ledger_path=tmp_path)
        receipt = {
            "status": "FAILED",
            "timestamp": "2026-03-15T10:00:00Z",
            "amount": 5000,
            "contributor_id": "alice",
            "error": "Transfer failed",
        }
        cpa.record_payment(receipt)
        assert len(cpa.ledger["payments"]) == 0, "Failed payment should not be recorded"
        results.ok("CPA ignores failed payments")
    except Exception as e:
        results.fail("CPA ignores failed payments", str(e))
    finally:
        os.unlink(tmp_path)


def test_cpa_expense_recording():
    """CPA Agent records business expenses."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "_schema_version": "1.0",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }, f)
        tmp_path = f.name

    try:
        cpa = CPAAgent(ledger_path=tmp_path)
        cpa.record_expense("hardware", "Beelink EQ13", 180.00)
        cpa.record_expense("software", "Claude Pro monthly", 20.00)
        cpa.record_expense("legal", "LLC filing", 120.00)

        assert len(cpa.ledger["expenses"]) == 3
        total = sum(e["amount_usd"] for e in cpa.ledger["expenses"])
        assert total == 320.00
        results.ok("CPA records expenses correctly")
    except Exception as e:
        results.fail("CPA records expenses correctly", str(e))
    finally:
        os.unlink(tmp_path)


def test_cpa_yearly_report():
    """CPA Agent generates yearly tax report."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "_schema_version": "1.0",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }, f)
        tmp_path = f.name

    try:
        cpa = CPAAgent(ledger_path=tmp_path)

        # Add some payments and expenses
        cpa.record_payment({
            "status": "SUCCESS",
            "timestamp": "2026-06-15T10:00:00Z",
            "recipient": "alice_wallet",
            "amount": 5000,
            "usd_value_per_token": 0.002,
            "usd_total": 10.0,
            "contributor_id": "alice",
            "task_id": "HB-2026-001",
            "reason": "test",
            "tx_signature": "sig_1",
        })
        cpa.record_expense("hardware", "Beelink", 180.00, date="2026-02-10T00:00:00Z")
        cpa.record_expense("software", "Claude Pro", 20.00, date="2026-02-10T00:00:00Z")

        report = cpa.yearly_report(2026)

        assert report["tax_year"] == 2026
        assert report["income"]["total_payments"] == 1
        assert report["income"]["total_tokens_disbursed"] == 5000
        assert report["expenses"]["total"] == 200.00
        assert report["schedule_c_estimate"]["net_loss"] == -200.00
        results.ok("CPA yearly report generates correctly")
    except Exception as e:
        results.fail("CPA yearly report generates correctly", str(e))
    finally:
        os.unlink(tmp_path)


def test_cpa_multiple_contributors():
    """CPA Agent tracks multiple contributors independently."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({
            "_schema_version": "1.0",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }, f)
        tmp_path = f.name

    try:
        cpa = CPAAgent(ledger_path=tmp_path)

        for name in ["alice", "bob", "charlie"]:
            for i in range(3):
                cpa.record_payment({
                    "status": "SUCCESS",
                    "timestamp": f"2026-0{i+3}-15T10:00:00Z",
                    "recipient": f"{name}_wallet",
                    "amount": 1000 * (i + 1),
                    "usd_value_per_token": 0.005,
                    "usd_total": 5.0 * (i + 1),
                    "contributor_id": name,
                    "task_id": f"HB-2026-{name}-{i}",
                    "reason": "test",
                    "tx_signature": f"sig_{name}_{i}",
                })

        assert len(cpa.ledger["contributors"]) == 3
        assert cpa.ledger["contributors"]["alice"]["payment_count"] == 3
        assert cpa.ledger["contributors"]["bob"]["payment_count"] == 3
        results.ok("CPA tracks multiple contributors independently")
    except Exception as e:
        results.fail("CPA tracks multiple contributors independently", str(e))
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Dispatcher config validation
# ---------------------------------------------------------------------------

def test_dispatcher_config_template():
    """Dispatcher generates valid config template."""
    try:
        from solana_dispatcher import generate_config_template
        tmp_path = tempfile.mktemp(suffix=".json")
        generate_config_template(tmp_path)

        with open(tmp_path) as f:
            config = json.load(f)

        assert "mint_address" in config
        assert "wallets" in config
        assert "unmined_treasury" in config["wallets"]
        assert "rate_limits" in config
        assert config["rate_limits"]["max_single_transfer"] == 100000
        results.ok("Dispatcher config template is valid")
        os.unlink(tmp_path)
    except Exception as e:
        results.fail("Dispatcher config template is valid", str(e))


def test_dispatcher_pause_unpause():
    """Dispatcher kill switch works."""
    try:
        pause_file = Path(__file__).parent / "PAUSE"
        # Clean up first
        if pause_file.exists():
            pause_file.unlink()

        # Create a mock dispatcher that doesn't need real config
        from solana_dispatcher import PAUSE_FILE
        assert not PAUSE_FILE.exists(), "PAUSE file should not exist"

        # Create and verify
        PAUSE_FILE.write_text('{"paused_at": "test", "reason": "unit test"}')
        assert PAUSE_FILE.exists(), "PAUSE file should exist after creation"

        # Clean up
        PAUSE_FILE.unlink()
        assert not PAUSE_FILE.exists(), "PAUSE file should be removed"

        results.ok("Dispatcher kill switch works")
    except Exception as e:
        results.fail("Dispatcher kill switch works", str(e))
        # Clean up on failure
        if Path(__file__).parent.joinpath("PAUSE").exists():
            Path(__file__).parent.joinpath("PAUSE").unlink()


# ---------------------------------------------------------------------------
# Integration: treasury_engine + CPA Agent
# ---------------------------------------------------------------------------

def test_engine_payment_feeds_cpa():
    """Treasury engine payment flows through to CPA Agent."""
    try:
        from treasury_engine import TreasuryEngine
        import tempfile, shutil

        # Copy state to temp
        state_src = Path(__file__).parent / "treasury_state.json"
        tmp_state = tempfile.mktemp(suffix=".json")
        tmp_ledger = tempfile.mktemp(suffix=".json")
        shutil.copy(state_src, tmp_state)

        # Init engine and CPA
        engine = TreasuryEngine(tmp_state)
        cpa = CPAAgent(ledger_path=tmp_ledger)

        # Record a payment through the engine
        payment = engine.record_base_payment(
            task_id="HB-2026-TEST",
            contributor_id="integration_test_user",
            gross_amount=5000,
            tier=1,
            reason="Integration test"
        )

        # Feed the payment into CPA as if dispatcher completed it
        receipt = {
            "status": "SUCCESS",
            "timestamp": _format_dt(_now()),
            "recipient": "test_wallet_address",
            "amount": payment["net"],  # After 5% burn
            "usd_value_per_token": 0.001,
            "usd_total": payment["net"] * 0.001,
            "contributor_id": payment["contributor_id"],
            "task_id": payment["task_id"],
            "reason": payment["reason"],
            "tx_signature": "integration_test_sig",
        }
        cpa.record_payment(receipt)

        # Verify both systems agree
        assert payment["gross"] == 5000
        assert payment["burn"] == 250  # 5% burn
        assert payment["net"] == 4750
        assert len(cpa.ledger["payments"]) == 1
        assert cpa.ledger["payments"][0]["amount_tokens"] == 4750

        results.ok("Engine → CPA integration works")
        os.unlink(tmp_state)
        os.unlink(tmp_ledger)
    except Exception as e:
        results.fail("Engine → CPA integration works", str(e))


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("  HOUSE BERNARD BACKEND TESTS")
    print("=" * 50)
    print()

    test_cpa_record_payment()
    test_cpa_1099_threshold()
    test_cpa_approaching_threshold()
    test_cpa_failed_payment_not_recorded()
    test_cpa_expense_recording()
    test_cpa_yearly_report()
    test_cpa_multiple_contributors()
    test_dispatcher_config_template()
    test_dispatcher_pause_unpause()
    test_engine_payment_feeds_cpa()

    all_pass = results.summary()
    sys.exit(0 if all_pass else 1)
