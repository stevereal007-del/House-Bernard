#!/usr/bin/env python3
"""
House Bernard Treasury CLI
Run monthly reports, record payments, activate royalties and bonds.

Usage:
    python treasury_cli.py report                         # Monthly report
    python treasury_cli.py status                         # Quick emission status
    python treasury_cli.py pay HB-2026-001 alice 5000 1   # Base payment (task, who, amount, tier)
    python treasury_cli.py royalty GENE-001 alice 2        # Activate royalty (gene, who, tier)
    python treasury_cli.py bond BOND-001 alice builder 10000  # Activate bond
"""

import sys
import json
from pathlib import Path
from treasury_engine import TreasuryEngine, BOND_CONFIG


STATE_FILE = Path(__file__).parent / "treasury_state.json"


def cmd_report(engine):
    """Generate and display monthly treasury report."""
    report = engine.monthly_report()

    print("=" * 60)
    print("  HOUSE BERNARD TREASURY REPORT")
    print(f"  Date: {report['report_date']}")
    print("=" * 60)

    # Obligations
    ob = report["obligations"]
    print(f"\n{'─' * 40}")
    print("  OBLIGATIONS DUE")
    print(f"{'─' * 40}")

    if ob["royalties"]:
        print("\n  Royalties:")
        for r in ob["royalties"]:
            print(f"    {r['gene_id']} → {r['contributor_id']}")
            print(f"      Tier {r['tier']} ({r['tier_name']}) @ {r['current_rate']:.4f}")
            print(f"      Revenue: {r['attributed_revenue']:,.0f} → Owed: {r['amount_owed']:,.2f}")
            print(f"      {r['months_remaining']:.1f} months remaining")
    else:
        print("\n  Royalties: None active")

    if ob["bonds"]:
        print("\n  Bonds:")
        for b in ob["bonds"]:
            print(f"    {b['bond_id']} ({b['bond_type']}) → {b['holder_id']}")
            print(f"      Principal: {b['principal']:,.0f} | Yield due: {b['yield_due_now']:,.2f}")
            print(f"      Status: {b['status']} | {b['days_to_maturity']} days to maturity")
    else:
        print("\n  Bonds: None active")

    print(f"\n  TOTAL DUE THIS PERIOD: {ob['total_due']:,.2f} $HOUSEBERNARD")

    # Upcoming
    up = report["upcoming"]
    print(f"\n{'─' * 40}")
    print("  UPCOMING (LOOKAHEAD)")
    print(f"{'─' * 40}")

    if up["expiring_royalties_60d"]:
        print("\n  Royalties expiring within 60 days:")
        for e in up["expiring_royalties_60d"]:
            print(f"    {e['gene_id']} ({e['tier_name']}) → {e['days_until_expiry']:.0f} days")
    else:
        print("\n  No royalties expiring within 60 days")

    if up["maturing_bonds_90d"]:
        print("\n  Bonds maturing within 90 days:")
        for m in up["maturing_bonds_90d"]:
            print(f"    {m['bond_id']} ({m['bond_type']}) → {m['days_to_maturity']} days")
            print(f"      Principal: {m['principal']:,.0f} to return to {m['holder_id']}")
    else:
        print("\n  No bonds maturing within 90 days")

    # Emission
    em = report["emission"]
    print(f"\n{'─' * 40}")
    print("  EMISSION STATUS")
    print(f"{'─' * 40}")
    print(f"  Epoch {em['epoch']} ({em['epoch_label']})")
    print(f"  Cap: {em['epoch_cap']:,.0f} | Emitted: {em['epoch_emitted']:,.0f} | Headroom: {em['epoch_headroom']:,.0f}")
    print(f"  Utilization: {em['epoch_utilization_pct']}%")
    print(f"  Circulating: {em['total_circulating']:,.0f} | Burned: {em['total_burned']:,.0f}")
    if em["warnings"]:
        for w in em["warnings"]:
            print(f"  ⚠ {w}")

    # Lifecycle
    lc = report["lifecycle"]
    if lc["royalties_expired"] or lc["bonds_matured"]:
        print(f"\n{'─' * 40}")
        print("  LIFECYCLE CHANGES")
        print(f"{'─' * 40}")
        if lc["royalties_expired"]:
            print(f"  Royalties expired: {', '.join(lc['royalties_expired'])}")
        if lc["bonds_matured"]:
            print(f"  Bonds matured: {', '.join(lc['bonds_matured'])}")

    # Governor actions
    actions = report["governor_actions"]
    print(f"\n{'─' * 40}")
    print("  GOVERNOR ACTION ITEMS")
    print(f"{'─' * 40}")
    if actions:
        for a in actions:
            icon = {"INFO": "ℹ", "ACTION": "►", "WARNING": "⚠", "CRITICAL": "🛑"}.get(a["priority"], "•")
            print(f"  {icon} [{a['priority']}] {a['action']}")
            print(f"    → {a['requires']}")
    else:
        print("  No action items. Treasury is clean.")

    print(f"\n{'=' * 60}")
    print("  [AWAITING GOVERNOR SIGNATURE]")
    print(f"{'=' * 60}")

    # Save report
    report_path = Path(__file__).parent / "treasury_report.json"
    engine.save_report(report, report_path)
    print(f"\n  Report saved to {report_path}")


def cmd_status(engine):
    """Quick emission status check."""
    em = engine.emission_status()
    active_royalties = sum(1 for r in engine.state["royalties"] if r["status"] == "active")
    active_bonds = sum(1 for b in engine.state["bonds"] if b["status"] == "active")

    print(f"Epoch {em['epoch']} ({em['epoch_label']}) — {em['epoch_utilization_pct']}% utilized")
    print(f"Emitted: {em['epoch_emitted']:,.0f} / {em['epoch_cap']:,.0f}")
    print(f"Circulating: {em['total_circulating']:,.0f} | Burned: {em['total_burned']:,.0f}")
    print(f"Active royalties: {active_royalties} | Active bonds: {active_bonds}")
    print(f"Total payments recorded: {len(engine.state['base_payments'])}")


def cmd_pay(engine, args):
    """Record a base payment."""
    if len(args) < 4:
        print("Usage: treasury_cli.py pay <task_id> <contributor_id> <amount> <tier> [gene_id]")
        sys.exit(1)

    task_id = args[0]
    contributor_id = args[1]
    amount = float(args[2])
    tier = int(args[3])
    gene_id = args[4] if len(args) > 4 else None

    try:
        payment = engine.record_base_payment(task_id, contributor_id, amount, tier, gene_id)
        engine.save()
        print(f"Payment recorded:")
        print(f"  Task: {task_id} → {contributor_id}")
        print(f"  Gross: {payment['gross']:,.2f} | Burn: {payment['burn']:,.2f} | Net: {payment['net']:,.2f}")
        print(f"  Tier: {tier}")
        print(f"  State saved.")
    except ValueError as e:
        print(f"REJECTED: {e}")
        sys.exit(1)


def cmd_royalty(engine, args):
    """Activate a royalty stream."""
    if len(args) < 3:
        print("Usage: treasury_cli.py royalty <gene_id> <contributor_id> <tier>")
        sys.exit(1)

    gene_id = args[0]
    contributor_id = args[1]
    tier = int(args[2])

    try:
        royalty = engine.activate_royalty(gene_id, contributor_id, tier)
        engine.save()
        print(f"Royalty activated:")
        print(f"  Gene: {gene_id} → {contributor_id}")
        print(f"  Tier: {tier} ({royalty['tier_name']})")
        print(f"  Window: {royalty['window_months']} months")
        print(f"  Rate: {royalty['rate_start']*100:.1f}% → {royalty['rate_end']*100:.1f}%")
        print(f"  State saved.")
    except ValueError as e:
        print(f"REJECTED: {e}")
        sys.exit(1)


def cmd_bond(engine, args):
    """Activate a bond."""
    if len(args) < 4:
        print("Usage: treasury_cli.py bond <bond_id> <holder_id> <type> <principal>")
        print("  Types: contributor, builder, founder")
        sys.exit(1)

    bond_id = args[0]
    holder_id = args[1]
    bond_type = args[2]
    principal = float(args[3])

    try:
        bond = engine.activate_bond(bond_id, holder_id, bond_type, principal)
        engine.save()
        print(f"Bond activated:")
        print(f"  {bond_id} → {holder_id}")
        print(f"  Type: {bond['bond_label']}")
        print(f"  Principal: {principal:,.0f} locked for {BOND_CONFIG[bond_type]['lock_months']} months")
        print(f"  Yield: {bond['yield_rate']*100:.0f}% at maturity")
        print(f"  Maturity: {bond['maturity_date']}")
        print(f"  State saved.")
    except ValueError as e:
        print(f"REJECTED: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    engine = TreasuryEngine(STATE_FILE)
    cmd = sys.argv[1]

    if cmd == "report":
        cmd_report(engine)
    elif cmd == "status":
        cmd_status(engine)
    elif cmd == "pay":
        cmd_pay(engine, sys.argv[2:])
    elif cmd == "royalty":
        cmd_royalty(engine, sys.argv[2:])
    elif cmd == "bond":
        cmd_bond(engine, sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
