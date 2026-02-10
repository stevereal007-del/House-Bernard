#!/usr/bin/env python3
"""
House Bernard — CPA Agent v1.0
Autonomous financial compliance and tax record management.

This is the Finance Director of House Bernard. It runs on its own.
The Governor doesn't sign checks. The CPA Agent tracks everything.

WHAT IT DOES:
  - Records every payment with USD fair market value at time of transfer
  - Tracks cumulative payments per contributor per calendar year
  - Flags contributors approaching the $600 1099-NEC threshold
  - Generates year-end 1099 data for US-based contributors
  - Produces Schedule C expense/income summaries for the Governor
  - Maintains audit trail for Warden quarterly reviews

WHAT IT DOES NOT DO:
  - File taxes (that's a human CPA's job)
  - Give tax advice (we say this in TOKEN_TERMS_OF_SERVICE.md)
  - Store SSN/EIN (contributors provide that separately at 1099 time)

DATA FLOW:
  solana_dispatcher.py executes payment
    → logs receipt with USD value
    → cpa_agent.record_payment() called
    → tax_ledger.json updated
    → 1099 threshold checked
    → monthly/yearly reports generated on demand

Usage:
    from cpa_agent import CPAAgent
    cpa = CPAAgent()
    cpa.record_payment(receipt)           # After each disbursement
    report = cpa.yearly_report(2026)      # Year-end tax data
    flagged = cpa.check_1099_threshold()  # Who's approaching $600
"""

import json
from datetime import datetime, timezone
from pathlib import Path


TAX_LEDGER = Path(__file__).parent / "tax_ledger.json"
THRESHOLD_1099 = 600.00  # USD — IRS 1099-NEC threshold


def _now():
    return datetime.now(timezone.utc)


def _format_dt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class CPAAgent:

    def __init__(self, ledger_path=None):
        self.ledger_path = Path(ledger_path) if ledger_path else TAX_LEDGER
        self.ledger = self._load_ledger()

    def _load_ledger(self):
        if self.ledger_path.exists():
            with open(self.ledger_path) as f:
                return json.load(f)
        return {
            "_schema_version": "1.0",
            "_description": "House Bernard Tax Ledger — CPA Agent",
            "payments": [],
            "contributors": {},
            "expenses": [],
        }

    def _save_ledger(self):
        # Atomic write
        tmp = self.ledger_path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self.ledger, f, indent=2)
        tmp.replace(self.ledger_path)

    # -------------------------------------------------------------------
    # Record payment (called after every disbursement)
    # -------------------------------------------------------------------

    def record_payment(self, receipt):
        """
        Record a payment from solana_dispatcher receipt.

        Args:
            receipt: dict from SolanaDispatcher.pay() with keys:
                amount, usd_value_per_token, usd_total, contributor_id,
                task_id, reason, timestamp, tx_signature
        """
        if receipt.get("status") != "SUCCESS":
            return  # Only record successful payments

        contributor_id = receipt.get("contributor_id", "unknown")
        amount_tokens = receipt.get("amount", 0)
        usd_per_token = receipt.get("usd_value_per_token", 0)
        usd_total = receipt.get("usd_total", 0)
        year = datetime.fromisoformat(
            receipt["timestamp"].replace("Z", "+00:00")
        ).year

        # Record the payment
        payment_record = {
            "timestamp": receipt["timestamp"],
            "contributor_id": contributor_id,
            "amount_tokens": amount_tokens,
            "usd_per_token": usd_per_token,
            "usd_total": usd_total,
            "task_id": receipt.get("task_id"),
            "reason": receipt.get("reason"),
            "tx_signature": receipt.get("tx_signature"),
            "tax_year": year,
        }
        self.ledger["payments"].append(payment_record)

        # Update contributor running totals
        if contributor_id not in self.ledger["contributors"]:
            self.ledger["contributors"][contributor_id] = {
                "wallet_address": receipt.get("recipient"),
                "total_tokens_earned": 0,
                "yearly_usd": {},
                "payment_count": 0,
                "first_payment": receipt["timestamp"],
                "last_payment": None,
                "needs_1099": False,
                "jurisdiction": None,  # Set manually or via KYC
            }

        contrib = self.ledger["contributors"][contributor_id]
        contrib["total_tokens_earned"] += amount_tokens
        contrib["payment_count"] += 1
        contrib["last_payment"] = receipt["timestamp"]

        year_key = str(year)
        if year_key not in contrib["yearly_usd"]:
            contrib["yearly_usd"][year_key] = 0.0
        contrib["yearly_usd"][year_key] = round(
            contrib["yearly_usd"][year_key] + (usd_total or 0), 2
        )

        # Check 1099 threshold (year-aware)
        if contrib["yearly_usd"][year_key] >= THRESHOLD_1099:
            if "needs_1099_years" not in contrib:
                contrib["needs_1099_years"] = []
            if year not in contrib["needs_1099_years"]:
                contrib["needs_1099_years"].append(year)
            contrib["needs_1099"] = True  # Keep legacy flag for current year

        self._save_ledger()
        return payment_record

    # -------------------------------------------------------------------
    # Record expense (Governor's business expenses)
    # -------------------------------------------------------------------

    def record_expense(self, category, description, amount_usd,
                       date=None, receipt_ref=None):
        """
        Record a business expense for Schedule C.

        Categories: hardware, software, internet, phone, cloud,
                    legal, education, office, blockchain_fees
        """
        expense = {
            "date": date or _format_dt(_now()),
            "category": category,
            "description": description,
            "amount_usd": round(amount_usd, 2),
            "receipt_ref": receipt_ref,
            "tax_year": datetime.fromisoformat(
                (date or _format_dt(_now())).replace("Z", "+00:00")
            ).year,
        }
        self.ledger["expenses"].append(expense)
        self._save_ledger()
        return expense

    # -------------------------------------------------------------------
    # 1099 threshold monitoring
    # -------------------------------------------------------------------

    def check_1099_threshold(self, year=None):
        """
        Check which contributors are at or approaching $600.

        Returns list of contributors needing attention.
        """
        if year is None:
            year = _now().year
        year_key = str(year)

        flagged = []
        for cid, info in self.ledger["contributors"].items():
            ytd = info["yearly_usd"].get(year_key, 0)
            if ytd >= THRESHOLD_1099:
                flagged.append({
                    "contributor_id": cid,
                    "ytd_usd": ytd,
                    "status": "NEEDS_1099",
                    "wallet": info.get("wallet_address"),
                    "payment_count": info["payment_count"],
                })
            elif ytd >= THRESHOLD_1099 * 0.8:  # 80% warning
                flagged.append({
                    "contributor_id": cid,
                    "ytd_usd": ytd,
                    "status": "APPROACHING_THRESHOLD",
                    "wallet": info.get("wallet_address"),
                    "remaining_until_1099": round(THRESHOLD_1099 - ytd, 2),
                })
        return flagged

    # -------------------------------------------------------------------
    # Reports
    # -------------------------------------------------------------------

    def yearly_report(self, year):
        """
        Generate year-end tax report.

        Used by:
        - Governor for Schedule C filing
        - CPA for 1099-NEC preparation
        - Wardens for audit
        """
        year_key = str(year)

        # Income summary
        income_payments = [
            p for p in self.ledger["payments"]
            if p["tax_year"] == year
        ]
        total_tokens_disbursed = sum(p["amount_tokens"] for p in income_payments)
        total_usd_disbursed = sum(p.get("usd_total", 0) or 0 for p in income_payments)

        # Expense summary
        year_expenses = [
            e for e in self.ledger["expenses"]
            if e["tax_year"] == year
        ]
        expenses_by_category = {}
        for e in year_expenses:
            cat = e["category"]
            if cat not in expenses_by_category:
                expenses_by_category[cat] = 0.0
            expenses_by_category[cat] = round(
                expenses_by_category[cat] + e["amount_usd"], 2
            )
        total_expenses = round(sum(expenses_by_category.values()), 2)

        # 1099 candidates
        needs_1099 = []
        for cid, info in self.ledger["contributors"].items():
            ytd = info["yearly_usd"].get(year_key, 0)
            if ytd >= THRESHOLD_1099:
                needs_1099.append({
                    "contributor_id": cid,
                    "total_usd": ytd,
                    "wallet_address": info.get("wallet_address"),
                    "jurisdiction": info.get("jurisdiction"),
                    "payment_count": info["payment_count"],
                })

        return {
            "report_type": "ANNUAL_TAX_SUMMARY",
            "tax_year": year,
            "generated": _format_dt(_now()),
            "income": {
                "total_payments": len(income_payments),
                "total_tokens_disbursed": total_tokens_disbursed,
                "total_usd_value": round(total_usd_disbursed, 2),
                "note": "Token disbursements from Treasury. Not income to LLC unless sold.",
            },
            "expenses": {
                "by_category": expenses_by_category,
                "total": total_expenses,
            },
            "schedule_c_estimate": {
                "gross_income": 0,  # No revenue yet in founding period
                "total_expenses": total_expenses,
                "net_loss": round(-total_expenses, 2),
                "note": "Pre-revenue. Net loss offsets W-2 income on Schedule C.",
            },
            "form_1099_nec": {
                "threshold": THRESHOLD_1099,
                "contributors_requiring_1099": needs_1099,
                "count": len(needs_1099),
                "note": "Issue 1099-NEC by January 31 for prior tax year.",
            },
            "contributor_summary": {
                cid: {
                    "total_usd": info["yearly_usd"].get(year_key, 0),
                    "total_tokens": sum(
                        p["amount_tokens"] for p in income_payments
                        if p["contributor_id"] == cid
                    ),
                }
                for cid, info in self.ledger["contributors"].items()
                if info["yearly_usd"].get(year_key, 0) > 0
            },
        }

    def quarterly_audit_report(self, year, quarter):
        """
        Generate quarterly audit data for Wardens.
        Quarter: 1-4
        """
        month_start = (quarter - 1) * 3 + 1
        month_end = quarter * 3

        quarter_payments = [
            p for p in self.ledger["payments"]
            if p["tax_year"] == year
            and month_start <= datetime.fromisoformat(
                p["timestamp"].replace("Z", "+00:00")
            ).month <= month_end
        ]

        quarter_expenses = [
            e for e in self.ledger["expenses"]
            if e["tax_year"] == year
            and month_start <= datetime.fromisoformat(
                e["date"].replace("Z", "+00:00")
            ).month <= month_end
        ]

        return {
            "report_type": "QUARTERLY_WARDEN_AUDIT",
            "year": year,
            "quarter": quarter,
            "generated": _format_dt(_now()),
            "payments": {
                "count": len(quarter_payments),
                "total_tokens": sum(p["amount_tokens"] for p in quarter_payments),
                "total_usd": round(
                    sum(p.get("usd_total", 0) or 0 for p in quarter_payments), 2
                ),
            },
            "expenses": {
                "count": len(quarter_expenses),
                "total_usd": round(
                    sum(e["amount_usd"] for e in quarter_expenses), 2
                ),
            },
            "payment_details": quarter_payments,
            "expense_details": quarter_expenses,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("House Bernard CPA Agent v1.0")
        print()
        print("Usage:")
        print("  python3 cpa_agent.py status              # Current year summary")
        print("  python3 cpa_agent.py threshold            # Check 1099 thresholds")
        print("  python3 cpa_agent.py report 2026          # Annual tax report")
        print("  python3 cpa_agent.py audit 2026 1         # Q1 Warden audit")
        print("  python3 cpa_agent.py expense <cat> <desc> <usd>  # Log expense")
        sys.exit(0)

    cpa = CPAAgent()
    cmd = sys.argv[1]

    if cmd == "status":
        year = _now().year
        flagged = cpa.check_1099_threshold(year)
        payments = [p for p in cpa.ledger["payments"] if p["tax_year"] == year]
        expenses = [e for e in cpa.ledger["expenses"] if e["tax_year"] == year]

        print(f"{'=' * 50}")
        print(f"  CPA AGENT — {year} STATUS")
        print(f"{'=' * 50}")
        print(f"  Payments this year: {len(payments)}")
        print(f"  Tokens disbursed:   {sum(p['amount_tokens'] for p in payments):,.0f}")
        print(f"  USD value:          ${sum(p.get('usd_total', 0) or 0 for p in payments):,.2f}")
        print(f"  Expenses logged:    {len(expenses)}")
        print(f"  Expenses total:     ${sum(e['amount_usd'] for e in expenses):,.2f}")
        print(f"  Contributors:       {len(cpa.ledger['contributors'])}")
        print(f"  Needing 1099:       {sum(1 for f in flagged if f['status'] == 'NEEDS_1099')}")
        if flagged:
            print(f"\n  FLAGGED:")
            for f in flagged:
                print(f"    {f['contributor_id']}: ${f['ytd_usd']:.2f} — {f['status']}")

    elif cmd == "threshold":
        flagged = cpa.check_1099_threshold()
        if not flagged:
            print("  No contributors at or near $600 threshold.")
        else:
            for f in flagged:
                print(f"  {f['contributor_id']}: ${f['ytd_usd']:.2f} — {f['status']}")

    elif cmd == "report":
        year = int(sys.argv[2]) if len(sys.argv) > 2 else _now().year
        report = cpa.yearly_report(year)
        print(json.dumps(report, indent=2))

    elif cmd == "audit":
        year = int(sys.argv[2]) if len(sys.argv) > 2 else _now().year
        quarter = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        report = cpa.quarterly_audit_report(year, quarter)
        print(json.dumps(report, indent=2))

    elif cmd == "expense":
        if len(sys.argv) < 5:
            print("Usage: python3 cpa_agent.py expense <category> <description> <usd_amount>")
            print("Categories: hardware, software, internet, phone, cloud, legal, education, office, blockchain_fees")
            sys.exit(1)
        cat = sys.argv[2]
        desc = sys.argv[3]
        usd = float(sys.argv[4])
        e = cpa.record_expense(cat, desc, usd)
        print(f"  Recorded: {cat} — {desc} — ${usd:.2f}")

    else:
        print(f"Unknown command: {cmd}")
