"""Run deterministic tests: python -m unittest test_robo_app -v.

Run live acceptance checks: python test_robo_app.py --live.
The latter saves download receipts/results under tmp/robo_validation.
"""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile
from dataclasses import replace

import numpy as np
import pandas as pd

import robo_app as app


def zipped(text):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("factors.csv", text)
    return stream.getvalue()


class CalculationTests(unittest.TestCase):
    def test_age_rule_bounds_and_bond_remainder(self):
        client = app.Client(35, 10, "5–10 years", True, 20., "Hold", 100000.)
        for age, expected in [(0, [.8, .1, .1]), (20, [.8, .1, .1]),
                              (35, [.65, .25, .1]), (100, [0, .9, .1]), (120, [0, .9, .1])]:
            with self.subTest(age=age):
                result = app.questionnaire_allocation(replace(client, age=age))
                np.testing.assert_allclose(result, expected)
                app.validate_weights(result)

    def test_rule_cash_and_reaction_adjustments(self):
        client = app.Client(35, 10, "5–10 years", True, 20., "Hold", 100000.)
        cases = [({"emergency_fund": False}, [.65, .15, .2]),
                 ({"money_needed": "1–3 years"}, [.65, .15, .2]),
                 ({"reaction_to_fall": "Sell all"}, [.2, .7, .1]),
                 ({"reaction_to_fall": "Sell some"}, [.4, .5, .1]),
                 ({"reaction_to_fall": "Buy more"}, [.65, .25, .1]),
                 ({"age": 85, "reaction_to_fall": "Sell all"}, [.15, .75, .1]),
                 ({"age": 20, "emergency_fund": False}, [.8, 0, .2])]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                result = app.questionnaire_allocation(replace(client, **changes))
                np.testing.assert_allclose(result, expected)
                app.validate_weights(result)

    def test_near_term_cash_override_has_priority(self):
        client = app.Client(20, 10, "5–10 years", True, 20., "Buy more", 100000.)
        for changes in [{"horizon_years": 0}, {"horizon_years": 1},
                        {"money_needed": "Within 1 year"}]:
            self.assertEqual(app.questionnaire_allocation(replace(client, **changes)), (0., 0., 1.))
        self.assertEqual(app.questionnaire_allocation(replace(client, horizon_years=2)), (.8, .1, .1))

    def test_loss_limit_and_investment_do_not_retune_rule(self):
        client = app.Client(35, 10, "5–10 years", True, 20., "Hold", 100000.)
        expected = app.questionnaire_allocation(client)
        self.assertEqual(app.questionnaire_allocation(replace(client, max_loss_pct=5.)), expected)
        self.assertEqual(app.questionnaire_allocation(replace(client, initial_investment=5000.)), expected)

    def test_monthly_parser_excludes_annual_rows_and_adds_rf(self):
        data = app.parse_french(zipped("Description\n,Mkt-RF,SMB,HML,RF\n199001,1,0,0,0.5\n199002,-2,0,0,0.4\n Annual Factors\n,Mkt-RF,SMB,HML,RF\n1990,100,0,0,20\n"))
        self.assertEqual(len(data), 2)
        np.testing.assert_allclose(data["Stocks"], [.015, -.016])
        np.testing.assert_allclose(data["Cash"], [.005, .004])

    def test_french_missing_marker_rejected(self):
        with self.assertRaises(ValueError):
            app.parse_french(zipped(",Mkt-RF,SMB,HML,RF\n199001,-99.99,0,0,0.5\n"))

    def test_bond_flat_yield_returns_coupon_only(self):
        yields = pd.Series(.06, index=pd.period_range("1989-12", "2025-12", freq="M"))
        np.testing.assert_allclose(app.bond_returns(yields), .005, atol=1e-12)

    def test_bond_formula_and_december_seed(self):
        yields = pd.Series(.06, index=pd.period_range("1989-12", "2025-12", freq="M"))
        yields.iloc[0] = .08
        yields.iloc[1] = .07
        n = 2 * (10 - 1 / 12)
        discount = (1 + .07 / 2) ** -n
        expected = (.08 / .07) * (1 - discount) + discount - 1 + .08 / 12
        self.assertAlmostEqual(app.bond_returns(yields).iloc[0], expected)
        with self.assertRaises(ValueError):
            app.bond_returns(yields.iloc[1:])

    def test_zero_yield_limit(self):
        yields = pd.Series(0., index=pd.period_range("1989-12", "2025-12", freq="M"))
        yields.iloc[0] = .02
        self.assertAlmostEqual(app.bond_returns(yields).iloc[0], .02 * (10 - 1 / 12) + .02 / 12)

    def test_drawdown_includes_initial_capital(self):
        returns = pd.Series([-.2] + [0.] * 11, index=pd.period_range("2000-01", periods=12, freq="M"))
        stats = app.performance(returns)
        self.assertAlmostEqual(stats["max_drawdown"], -.2)
        self.assertAlmostEqual(stats["cagr"], -.2)
        self.assertAlmostEqual(stats["worst_12m"], -.2)
        self.assertEqual(str(stats["worst_12m_end"]), "2000-12")
        self.assertAlmostEqual(stats["volatility"], returns.std(ddof=1) * np.sqrt(12))

    def test_monthly_rebalancing(self):
        frame = pd.DataFrame({"Stocks": [.1, -.1], "Bonds": [0., .1], "Cash": [0., 0.]})
        np.testing.assert_allclose(app.portfolio_returns(frame, [.6, .4, 0]), [.06, -.02])

    def test_weights_and_loss_boundaries(self):
        for weights in ([.6, .5, 0], [-.1, .5, .6], [np.nan, 0, 1]):
            with self.assertRaises(ValueError):
                app.validate_weights(weights)
        self.assertTrue(app.alignment_passes(-.2, 20))
        self.assertFalse(app.alignment_passes(-.2001, 20))
        self.assertTrue(app.alignment_passes(.01, 0))

    def test_grid_checks_all_candidates_without_assuming_monotonicity(self):
        # Only the 30% and 70% candidates pass: select the largest.
        def fake_performance(series):
            return {"worst_12m": -.1 if series.iloc[0] in (.3, .7) else -.3,
                    "worst_12m_end": pd.Period("2000-12")}
        frame = pd.DataFrame({"Stocks": [1.], "Bonds": [0.], "Cash": [0.]})
        with patch.object(app, "performance", side_effect=fake_performance):
            self.assertEqual(app.largest_stock_share(frame, .2, 15), .7)
            self.assertIsNone(app.largest_stock_share(frame, .2, 5))

    def test_missing_months_fail_instead_of_truncating(self):
        french = zipped(",Mkt-RF,SMB,HML,RF\n199001,1,0,0,0.5\n")
        yields = "observation_date,GS10\n" + "\n".join(f"{p}-01,6" for p in pd.period_range("1989-12", "2025-12", freq="M"))
        with self.assertRaises(ValueError):
            app.build_returns(french, yields.encode())


def live_acceptance():
    payloads = app.download_sources()
    output = Path(__file__).parent / "tmp" / "robo_validation"
    output.mkdir(parents=True, exist_ok=True)
    (output / "french.zip").write_bytes(payloads["french"])
    (output / "gs10.csv").write_bytes(payloads["gs10"])
    return verify_payloads(payloads, output)


def verify_payloads(payloads, output):
    import hashlib
    from datetime import datetime, timezone

    returns = app.build_returns(payloads["french"], payloads["gs10"])
    stats = app.performance(app.portfolio_returns(returns, [.6, .4, 0]))
    checks = {"432_months": len(returns) == 432,
              "start": str(returns.index[0]) == "1990-01",
              "end": str(returns.index[-1]) == "2025-12"}
    for key, expected in {"cagr": .0888, "volatility": .0938, "max_drawdown": -.2840, "worst_12m": -.2441}.items():
        checks[key] = abs(stats[key] - expected) <= .001
    checks["worst_end"] = str(stats["worst_12m_end"]) == "2009-02"
    probes = {}
    for cash, limit, expected in [(0, 20, .5), (0, 15, None), (.2, 15, .3), (.1, 15, None)]:
        actual = app.largest_stock_share(returns, cash, limit)
        name = f"cash_{cash:.0%}_loss_{limit}%"
        probes[name] = actual
        checks[name] = actual == expected
    bonds = app.performance(returns["Bonds"])
    checks["bonds_worst"] = abs(bonds["worst_12m"] + .1687) <= .001
    checks["bonds_worst_end"] = str(bonds["worst_12m_end"]) == "2022-10"
    stats["worst_12m_end"] = str(stats["worst_12m_end"])
    report = {"verified_utc": datetime.now(timezone.utc).isoformat(), "60_40_0": stats,
              "worst_12m_dollars_on_100000": stats["worst_12m"] * 100000,
              "bonds_worst_12m": bonds["worst_12m"], "bonds_worst_end": str(bonds["worst_12m_end"]),
              "probes": probes, "checks": checks,
              "sources": {k: {"sha256": hashlib.sha256(v).hexdigest(), "bytes": len(v)} for k, v in payloads.items()}}
    (output / "acceptance.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise AssertionError("Acceptance mismatch; see the report.")
    return report


if __name__ == "__main__":
    if "--live" in sys.argv:
        live_acceptance()
    else:
        unittest.main()
