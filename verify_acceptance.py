"""Run the user's COST known answer and JPM missing-input probes on SEC data."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "warren-buffett-expert/scripts"))
from buffett import SEC, audit_memo, build, export, formatted, write_json


def verify_cost(report):
    expected = json.loads((HERE / "tests/cost_known_answer.json").read_text(encoding="utf-8"))
    fields = ("revenue", "net_income", "operating_cash_flow", "capital_spending", "equity", "roe_percent", "owner_earnings")
    checks = []
    for actual, row in zip(report["rows"], expected):
        checks.append({"period": row[0], "field": "FY end", "matches": actual["fiscal_year_end"] == row[0]})
        for key, target in zip(fields, row[1:]):
            target_text = f"{target:.1f}%" if key == "roe_percent" else f"{target:,}"
            actual_text = formatted(actual[key], "roe" if key == "roe_percent" else "money")
            checks.append({"period": row[0], "field": key, "expected": target_text, "actual": actual_text, "matches": actual_text == target_text})
    checks.append({"field": "Exactly five years", "matches": len(report["rows"]) == 5})
    checks.append({"field": "Three checks pass", "matches": list(report["checks"].values()) == ["pass"] * 3})
    return checks


def verify_jpm(report):
    return {"capital_spending_not_found": all(r["capital_spending"] == "not found" for r in report["rows"]), "owner_earnings_not_found": all(r["owner_earnings"] == "not found" for r in report["rows"]), "owner_checks_not_known": list(report["checks"].values())[1:] == ["not known", "not known"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--user-agent", default=os.getenv("SEC_USER_AGENT", ""))
    p.add_argument("--offline", action="store_true")
    p.add_argument("--asof", default=date.today().isoformat())
    a = p.parse_args()
    reports = {}
    for ticker in ("COST", "JPM"):
        client = SEC(HERE / "evidence/downloads", a.user_agent, offline=a.offline)
        reports[ticker] = build(client, ticker, a.asof)
        export(reports[ticker], HERE / "outputs" / ticker)
    cost_checks = verify_cost(reports["COST"])
    jpm_checks = verify_jpm(reports["JPM"])
    from buffett import print_report
    probe = audit_memo("ROE was 40.0%.", print_report(reports["COST"]))
    result = {"mode": "Saved SEC replay" if a.offline else "SEC download or explicitly dated cache", "cost": cost_checks, "jpm": jpm_checks, "unprinted_40_percent_flagged": "40.0%" in probe, "receipts": {t: r["receipts"] for t, r in reports.items()}}
    result["all_pass"] = all(x["matches"] for x in cost_checks) and all(jpm_checks.values()) and result["unprinted_40_percent_flagged"]
    write_json(HERE / "evidence/acceptance.json", result)
    print(json.dumps(result, indent=2))
    if not result["all_pass"]:
        raise SystemExit("Acceptance failed; investigate selection, periods, tags and units. Never paste known answers into the pipeline.")


if __name__ == "__main__":
    main()
