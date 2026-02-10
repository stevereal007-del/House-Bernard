#!/usr/bin/env python3
"""
House Bernard — Solana Payment Dispatcher v1.0
Autonomous on-chain payment execution for $HOUSEBERNARD.

This module wraps the Solana CLI (spl-token) to execute token
transfers on behalf of the Treasury Engine. It is the bridge
between the constitutional ledger and the blockchain.

WHO CALLS THIS:
  - monthly_ops.py (automated royalty/bond disbursements)
  - treasury_cli.py (manual Governor-approved payments)
  - AchillesRun (automated Furnace survival bounties)

WHO DOES NOT CALL THIS:
  - Contributors (they receive, they don't initiate)
  - The Governor (for routine payments — he has a day job)

DESIGN:
  - Every payment is logged BEFORE execution (intent)
  - Every payment is confirmed AFTER execution (receipt)
  - Failed payments are logged and queued for retry
  - USD fair market value is captured at time of execution
  - All records feed into cpa_agent.py for tax compliance

SECURITY:
  - Wallet keypair paths are loaded from config, never hardcoded
  - This module NEVER stores or logs private keys
  - Rate limits enforced: no single transfer > epoch cap
  - Kill switch: if PAUSE file exists, all transfers halt

Usage:
    from solana_dispatcher import SolanaDispatcher
    dispatcher = SolanaDispatcher("dispatcher_config.json")
    receipt = dispatcher.pay("alice_wallet_address", 5000, reason="Furnace #001")
"""

import json
import subprocess
import os
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAUSE_FILE = Path(__file__).parent / "PAUSE"
DISPATCH_LOG = Path(__file__).parent / "dispatch_log.jsonl"
FAILED_QUEUE = Path(__file__).parent / "failed_queue.json"


def _now():
    return datetime.now(timezone.utc)


def _format_dt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_cmd(cmd, timeout=30):
    """Run a shell command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT"
    except Exception as e:
        return False, "", str(e)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

class SolanaDispatcher:

    def __init__(self, config_path="dispatcher_config.json"):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Dispatcher config not found: {config_path}\n"
                f"Run 'python3 solana_dispatcher.py init' to create template."
            )
        with open(self.config_path) as f:
            self.config = json.load(f)

        self.mint_address = self.config["mint_address"]
        self.wallets = self.config["wallets"]
        self.rate_limits = self.config.get("rate_limits", {})

    # -------------------------------------------------------------------
    # Core: Pay
    # -------------------------------------------------------------------

    def pay(self, recipient_address, amount, source_wallet="unmined_treasury",
            reason=None, task_id=None, contributor_id=None, auto_retry=True):
        """
        Execute a $HOUSEBERNARD transfer on Solana.

        Args:
            recipient_address: Solana wallet address of recipient
            amount: Number of tokens to send (integer or float)
            source_wallet: Key in config["wallets"] to send from
            reason: Human-readable reason for the payment
            task_id: Reference to brief/task/gene that triggered this
            contributor_id: Who is being paid
            auto_retry: If True, queue failed payments for retry

        Returns:
            dict with receipt details including tx_signature
        """
        # --- Pre-flight checks ---
        if self._is_paused():
            return self._fail_receipt(
                recipient_address, amount, source_wallet, reason,
                task_id, contributor_id, "PAUSED: Kill switch active"
            )

        if amount <= 0:
            return self._fail_receipt(
                recipient_address, amount, source_wallet, reason,
                task_id, contributor_id, f"Invalid amount: {amount}"
            )

        wallet_config = self.wallets.get(source_wallet)
        if not wallet_config:
            return self._fail_receipt(
                recipient_address, amount, source_wallet, reason,
                task_id, contributor_id,
                f"Unknown source wallet: {source_wallet}"
            )

        keypair_path = wallet_config["keypair_path"]
        if not Path(keypair_path).exists():
            return self._fail_receipt(
                recipient_address, amount, source_wallet, reason,
                task_id, contributor_id,
                f"Keypair file not found: {keypair_path}"
            )

        # --- Rate limit check ---
        max_single = self.rate_limits.get("max_single_transfer", 100000)
        if amount > max_single:
            return self._fail_receipt(
                recipient_address, amount, source_wallet, reason,
                task_id, contributor_id,
                f"Amount {amount} exceeds single transfer limit {max_single}"
            )

        # --- Log intent ---
        intent = {
            "type": "INTENT",
            "timestamp": _format_dt(_now()),
            "recipient": recipient_address,
            "amount": amount,
            "source_wallet": source_wallet,
            "reason": reason,
            "task_id": task_id,
            "contributor_id": contributor_id,
        }
        self._append_log(intent)

        # --- Get USD value at time of transfer ---
        usd_value = self.get_token_usd_value()
        usd_amount = round(amount * usd_value, 6) if usd_value else None

        # --- Execute transfer ---
        cmd = (
            f"spl-token transfer "
            f"--keypair {keypair_path} "
            f"{self.mint_address} {amount} {recipient_address} "
            f"--fund-recipient --allow-unfunded-recipient"
        )

        success, stdout, stderr = _run_cmd(cmd, timeout=60)

        if success:
            # Parse tx signature from output
            tx_sig = self._parse_tx_signature(stdout)
            receipt = {
                "type": "RECEIPT",
                "status": "SUCCESS",
                "timestamp": _format_dt(_now()),
                "recipient": recipient_address,
                "amount": amount,
                "usd_value_per_token": usd_value,
                "usd_total": usd_amount,
                "source_wallet": source_wallet,
                "tx_signature": tx_sig,
                "reason": reason,
                "task_id": task_id,
                "contributor_id": contributor_id,
                "solscan_url": f"https://solscan.io/tx/{tx_sig}" if tx_sig else None,
            }
            self._append_log(receipt)
            return receipt
        else:
            receipt = self._fail_receipt(
                recipient_address, amount, source_wallet, reason,
                task_id, contributor_id,
                f"Transfer failed: {stderr}"
            )
            if auto_retry:
                self._queue_for_retry(intent, stderr)
            return receipt

    # -------------------------------------------------------------------
    # Batch payments (for monthly ops)
    # -------------------------------------------------------------------

    def pay_batch(self, payments):
        """
        Execute multiple payments. Used by monthly_ops for royalties/bonds.

        Args:
            payments: list of dicts, each with keys:
                recipient, amount, source_wallet, reason, task_id, contributor_id

        Returns:
            list of receipts
        """
        receipts = []
        for p in payments:
            receipt = self.pay(
                recipient_address=p["recipient"],
                amount=p["amount"],
                source_wallet=p.get("source_wallet", "unmined_treasury"),
                reason=p.get("reason"),
                task_id=p.get("task_id"),
                contributor_id=p.get("contributor_id"),
            )
            receipts.append(receipt)
            # Small delay between transfers to avoid rate limiting
            time.sleep(0.5)
        return receipts

    # -------------------------------------------------------------------
    # Balance checks
    # -------------------------------------------------------------------

    def get_balance(self, wallet_name="unmined_treasury"):
        """Get $HOUSEBERNARD balance for a configured wallet."""
        wallet_config = self.wallets.get(wallet_name)
        if not wallet_config:
            return None
        keypair_path = wallet_config["keypair_path"]
        owner_addr = wallet_config.get("address")

        if owner_addr:
            cmd = f"spl-token balance --owner {owner_addr} {self.mint_address}"
        else:
            cmd = f"spl-token balance --keypair {keypair_path} {self.mint_address}"

        success, stdout, stderr = _run_cmd(cmd)
        if success:
            try:
                return float(stdout.strip())
            except ValueError:
                return None
        return None

    def get_all_balances(self):
        """Get balances for all configured wallets."""
        balances = {}
        for name in self.wallets:
            balances[name] = self.get_balance(name)
        return balances

    # -------------------------------------------------------------------
    # USD price (for tax records)
    # -------------------------------------------------------------------

    def get_token_usd_value(self):
        """
        Fetch current USD value of $HOUSEBERNARD.

        Strategy:
        1. Check local price cache (< 5 min old)
        2. Query Jupiter price API
        3. Fallback to 0 if unavailable (logged)

        For tax purposes, we need fair market value at time of
        each transfer. This is recorded in every receipt.
        """
        cache_path = Path(__file__).parent / "price_cache.json"

        # Check cache
        if cache_path.exists():
            try:
                with open(cache_path) as f:
                    cache = json.load(f)
                cache_time = datetime.fromisoformat(
                    cache["timestamp"].replace("Z", "+00:00")
                )
                age_seconds = (_now() - cache_time).total_seconds()
                if age_seconds < 300:  # 5 minute cache
                    return cache["usd_per_token"]
            except (json.JSONDecodeError, KeyError):
                pass

        # Query Jupiter price API
        try:
            cmd = (
                f'curl -s "https://price.jup.ag/v4/price?ids={self.mint_address}"'
            )
            success, stdout, stderr = _run_cmd(cmd, timeout=10)
            if success and stdout:
                data = json.loads(stdout)
                price = data.get("data", {}).get(self.mint_address, {}).get("price")
                if price is not None:
                    price = float(price)
                    # Update cache
                    with open(cache_path, "w") as f:
                        json.dump({
                            "usd_per_token": price,
                            "timestamp": _format_dt(_now()),
                            "source": "jupiter",
                        }, f)
                    return price
        except Exception:
            pass

        return 0.0  # No price available — logged as $0 (pre-market)

    # -------------------------------------------------------------------
    # Kill switch
    # -------------------------------------------------------------------

    def _is_paused(self):
        return PAUSE_FILE.exists()

    def pause(self, reason="Manual pause"):
        """Activate kill switch — all transfers halt."""
        PAUSE_FILE.write_text(
            json.dumps({"paused_at": _format_dt(_now()), "reason": reason})
        )

    def unpause(self):
        """Deactivate kill switch."""
        if PAUSE_FILE.exists():
            PAUSE_FILE.unlink()

    # -------------------------------------------------------------------
    # Retry queue
    # -------------------------------------------------------------------

    def _queue_for_retry(self, intent, error):
        queue = []
        if FAILED_QUEUE.exists():
            try:
                with open(FAILED_QUEUE) as f:
                    queue = json.load(f)
            except (json.JSONDecodeError, ValueError):
                queue = []
        intent["error"] = error
        intent["retry_count"] = 0
        queue.append(intent)
        with open(FAILED_QUEUE, "w") as f:
            json.dump(queue, f, indent=2)

    def retry_failed(self):
        """Retry all failed payments in queue."""
        if not FAILED_QUEUE.exists():
            return []
        with open(FAILED_QUEUE) as f:
            queue = json.load(f)
        results = []
        remaining = []
        for item in queue:
            receipt = self.pay(
                recipient_address=item["recipient"],
                amount=item["amount"],
                source_wallet=item.get("source_wallet", "unmined_treasury"),
                reason=f"RETRY: {item.get('reason', '')}",
                task_id=item.get("task_id"),
                contributor_id=item.get("contributor_id"),
                auto_retry=False,
            )
            if receipt["status"] == "SUCCESS":
                results.append(receipt)
            else:
                item["retry_count"] = item.get("retry_count", 0) + 1
                if item["retry_count"] < 3:
                    remaining.append(item)
                else:
                    # Escalate — 3 failures, needs Governor
                    item["escalated"] = True
                    remaining.append(item)
                    results.append(receipt)
        with open(FAILED_QUEUE, "w") as f:
            json.dump(remaining, f, indent=2)
        return results

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _parse_tx_signature(self, stdout):
        """Extract transaction signature from spl-token output."""
        for line in stdout.split("\n"):
            line = line.strip()
            if line.startswith("Signature:"):
                return line.split(":", 1)[1].strip()
            # Sometimes the sig is on its own line (base58, 87-88 chars)
            if len(line) > 80 and all(c.isalnum() for c in line):
                return line
        return None

    def _fail_receipt(self, recipient, amount, source, reason,
                      task_id, contributor_id, error):
        receipt = {
            "type": "RECEIPT",
            "status": "FAILED",
            "timestamp": _format_dt(_now()),
            "recipient": recipient,
            "amount": amount,
            "source_wallet": source,
            "reason": reason,
            "task_id": task_id,
            "contributor_id": contributor_id,
            "error": error,
        }
        self._append_log(receipt)
        return receipt

    def _append_log(self, entry):
        """Append-only log. Never truncated."""
        with open(DISPATCH_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Config template generator
# ---------------------------------------------------------------------------

def generate_config_template(output_path="dispatcher_config.json"):
    """Generate template config for first-time setup."""
    template = {
        "_description": "House Bernard Solana Dispatcher Config",
        "_WARNING": "NEVER commit this file to git. Contains wallet paths.",
        "mint_address": "<YOUR_MINT_ADDRESS>",
        "network": "mainnet-beta",
        "wallets": {
            "unmined_treasury": {
                "keypair_path": "~/hb-contributor-pool.json",
                "address": "<CONTRIBUTOR_POOL_ADDRESS>",
                "purpose": "60M unmined treasury — bounties, royalties, bonds",
            },
            "governor_reserve": {
                "keypair_path": "~/hb-governor-reserve.json",
                "address": "<GOVERNOR_RESERVE_ADDRESS>",
                "purpose": "15M governor reserve — emergencies, partnerships",
            },
            "founder": {
                "keypair_path": "~/house-bernard-wallet.json",
                "address": "<FOUNDER_WALLET_ADDRESS>",
                "purpose": "20M founder allocation (within 60M treasury)",
            },
        },
        "rate_limits": {
            "max_single_transfer": 100000,
            "max_daily_total": 500000,
            "cooldown_seconds": 1,
        },
        "price_api": "https://price.jup.ag/v4/price",
    }
    with open(output_path, "w") as f:
        json.dump(template, f, indent=2)
    print(f"Config template written to {output_path}")
    print("Fill in mint_address and wallet addresses after token deployment.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 solana_dispatcher.py init          # Create config template")
        print("  python3 solana_dispatcher.py balance        # Check all balances")
        print("  python3 solana_dispatcher.py retry          # Retry failed payments")
        print("  python3 solana_dispatcher.py pause [reason] # Activate kill switch")
        print("  python3 solana_dispatcher.py unpause        # Deactivate kill switch")
        print("  python3 solana_dispatcher.py price          # Get current USD price")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "init":
        generate_config_template()
    elif cmd == "balance":
        d = SolanaDispatcher()
        for name, bal in d.get_all_balances().items():
            print(f"  {name}: {bal:,.0f} $HOUSEBERNARD" if bal else f"  {name}: unavailable")
    elif cmd == "retry":
        d = SolanaDispatcher()
        results = d.retry_failed()
        for r in results:
            print(f"  {r['status']}: {r['amount']} → {r['recipient']}")
    elif cmd == "pause":
        d = SolanaDispatcher()
        reason = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Manual pause"
        d.pause(reason)
        print(f"PAUSED: {reason}")
    elif cmd == "unpause":
        d = SolanaDispatcher()
        d.unpause()
        print("UNPAUSED: Transfers re-enabled")
    elif cmd == "price":
        d = SolanaDispatcher()
        p = d.get_token_usd_value()
        print(f"  $HOUSEBERNARD = ${p:.8f} USD")
    else:
        print(f"Unknown command: {cmd}")
