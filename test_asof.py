"""Behavior checks for the known answer, removal order and row accountability."""

from decimal import Decimal
import unittest

from Project2_Portfolio.asof import DATA, analyze, known_answer, load_rows


def row(number, series, month, value, published):
    return {"row_number": str(number), "source_record": number,
            "raw": {"series": series, "month_measured": month,
                    "value": value, "published_on": published}}


class PointInTimeTests(unittest.TestCase):
    def test_supplied_known_answer(self):
        self.assertTrue(all(known_answer().values()))

    def test_three_dates(self):
        rows = load_rows(DATA / "training.csv")
        feb = analyze(rows, "2026-02-28")
        march = analyze(rows, "2026-03-31")
        april = analyze(rows, "2026-04-30")
        self.assertEqual([r["row_number"] for r in feb["panel"]], ["1"])
        self.assertIsNone(feb["signals"]["AAA"]["asof"]["signal_percent"])
        self.assertEqual([r["row_number"] for r in march["panel"]], ["1", "3"])
        self.assertEqual([r["row_number"] for r in april["panel"]], ["1", "3", "4"])
        self.assertEqual(april["signals"]["AAA"]["leak_percentage_points"], 0)

    def test_cutoff_inclusive_and_old_value_until_revision_day(self):
        rows = load_rows(DATA / "training.csv")
        for day, expected_ids in (("2026-03-09", ["1"]),
                                  ("2026-03-10", ["1", "2"]),
                                  ("2026-03-24", ["1", "2"]),
                                  ("2026-03-25", ["1", "3"]),
                                  ("2026-04-09", ["1", "3"]),
                                  ("2026-04-10", ["1", "3", "4"])):
            with self.subTest(day=day):
                self.assertEqual([r["row_number"] for r in analyze(rows, day)["panel"]], expected_ids)

    def test_all_four_stages_and_row_numbers(self):
        rows = [row(11, "AAA", "2026-01", "101", "2026-02-10"),
                row(24, "AAA", "2026-02", "104", "2026-03-10"),
                row(25, "AAA", "2026-02", "103", "2026-03-25"),
                row(31, "AAA", "2026-03", "109", "2026-04-10"),
                row(40, "AAA", "2026-03", "109.0", "2026-04-10"),
                row(55, "BAD", "2026-01", "NaN", "2026-02-10"),
                row(56, "BAD", "2026-01", "NaN", "2026-02-10"),
                row(70, "CCC", "2026-01", "80", ""),
                row(71, "CCC", "2026-02", "81", "2026-03-10")]
        result = analyze(rows, "2026-03-31")
        self.assertEqual(result["funnel"], {"quarantine": 4, "duplicate": 1,
                         "late_publication": 1, "superseded_revision": 1, "retained": 2})
        self.assertEqual([r["row_number"] for r in result["audit"]],
                         ["11", "24", "25", "31", "40", "55", "56", "70", "71"])
        # The duplicated late row is removed as a duplicate, before the late stage.
        self.assertEqual(result["audit"][4]["status"], "duplicate")
        # Invalid duplicates are quarantined first; they are not counted as duplicates.
        self.assertEqual(result["audit"][6]["status"], "quarantine")
        self.assertEqual(result["audit"][8]["status"], "quarantine")
        self.assertEqual(sum(result["funnel"].values()), len(rows))
        self.assertEqual(rows[0]["raw"]["value"], "101")
        self.assertNotIn("status", rows[0])

    def test_late_revision_cannot_erase_known_value(self):
        rows = load_rows(DATA / "training.csv")
        rows.append(row(99, "AAA", "2026-02", "500", "2026-05-01"))
        result = analyze(rows, "2026-03-31")
        self.assertEqual([r["row_number"] for r in result["panel"]], ["1", "3"])
        self.assertEqual(result["audit"][-1]["status"], "late_publication")

    def test_unordered_input_does_not_change_selection(self):
        rows = load_rows(DATA / "training.csv")
        result = analyze(list(reversed(rows)), "2026-03-31")
        self.assertEqual([r["row_number"] for r in result["panel"]], ["1", "3"])

    def test_missing_invalid_dates_quarantine_entire_series(self):
        for published in ("", "2026-02-30", "20260301", "2026-2-10"):
            with self.subTest(published=published):
                rows = [row(1, "AAA", "2026-01", "101", published),
                        row(2, "AAA", "2026-02", "103", "2026-03-10")]
                result = analyze(rows, "2026-03-31")
                self.assertEqual(result["funnel"]["quarantine"], 2)
                self.assertEqual(result["panel"], [])

    def test_same_day_conflicts_are_not_resolved_by_file_order(self):
        rows = [row(1, "AAA", "2026-01", "101", "2026-02-10"),
                row(2, "AAA", "2026-01", "102", "2026-02-10")]
        self.assertEqual(analyze(rows, "2026-03-31")["funnel"]["quarantine"], 2)

    def test_missing_preceding_month_does_not_backfill(self):
        rows = [row(1, "AAA", "2026-01", "101", "2026-02-10"),
                row(2, "AAA", "2026-03", "109", "2026-04-10")]
        comp = analyze(rows, "2026-04-30")["signals"]["AAA"]
        self.assertIsNone(comp["asof"]["signal_percent"])
        self.assertIn("gap", comp["asof"]["reason"])

    def test_future_period_excluded_from_naive(self):
        result = analyze(load_rows(DATA / "training.csv"), "2026-02-28")
        self.assertNotIn("4", [r["row_number"] for r in result["naive_panel"]])

    def test_bad_levels_and_dates_quarantined(self):
        rows = [row(1, "AAA", "2026-01", "Infinity", "2026-02-10"),
                row(2, "BBB", "2026-01", "0", "2026-02-10"),
                row(3, "CCC", "2026-15", "100", "2026-02-10"),
                row(4, "DDD", "2026-02", "100", "2026-02-01")]
        self.assertEqual(analyze(rows, "2026-03-31")["funnel"]["quarantine"], 4)

    def test_real_series_release_dates_and_quarterly_ratio(self):
        rows = load_rows(DATA / "own_gdp.csv")
        for day, value, row_id in (("2011-04-29", "15006.4", "2"),
                                    ("2011-05-31", "15010.3", "3"),
                                    ("2011-06-30", "15018.1", "4")):
            with self.subTest(day=day):
                result = analyze(rows, day, "quarterly")
                self.assertEqual(result["panel"][-1]["row_number"], row_id)
                self.assertEqual(result["signals"]["US_NOMINAL_GDP"]["asof"]["signal_percent"],
                                 (Decimal(value) / Decimal("14871.4") - 1) * 100)


if __name__ == "__main__":
    unittest.main()
