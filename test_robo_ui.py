"""App interactions using the verified live snapshots (no extra downloads)."""
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import robo_app


class AppInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = Path(__file__).parent / "validation" / "robo"
        cls.payloads = {"french": (folder / "french.zip").read_bytes(),
                        "gs10": (folder / "gs10.csv").read_bytes()}

    def setUp(self):
        self.downloader = patch.object(robo_app, "download_sources", return_value=self.payloads)
        self.mock_download = self.downloader.start()
        self.addCleanup(self.downloader.stop)
        self.app = AppTest.from_string("import robo_app\nrobo_app.main()", default_timeout=30).run()
        self.assertEqual(len(self.app.exception), 0)

    def change(self, label, value):
        for widget in self.app.number_input:
            if widget.label == label:
                widget.set_value(value)
                return
        self.fail(f"Missing widget: {label}")

    def test_manual_default_and_live_fetch_on_rerun(self):
        self.app.checkbox[0].check().run()
        self.assertIn("50%", self.app.subheader[0].value)
        self.assertIn("RED FLAG", self.app.error[0].value)
        table = self.app.dataframe[0].value
        self.assertEqual(list(table["Percent"]), ["8.88%", "9.38%", "-28.40%", "-24.41%"])
        self.assertEqual(table.iloc[3]["Dollar equivalent on initial investment"], "−$24,415")
        count = self.mock_download.call_count
        self.app.run()
        self.assertEqual(self.mock_download.call_count, count + 1)

    def test_15_percent_loss_probes(self):
        self.app.checkbox[0].check().run()
        self.change("Maximum acceptable loss in any 12 months (%)", 15.)
        self.app.run()
        self.assertIn("no stock/bond mix passes", self.app.subheader[0].value)
        self.change("Stocks (%)", 30.)
        self.change("Bonds (%)", 50.)
        self.change("Cash (%)", 20.)
        self.app.run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(len(self.app.error), 0)
        self.assertIn("PASS", self.app.success[0].value)
        self.assertIn("30%", self.app.subheader[0].value)
        self.change("Bonds (%)", 60.)
        self.change("Cash (%)", 10.)
        self.app.run()
        self.assertIn("no stock/bond mix passes", self.app.subheader[0].value)

    def test_invalid_allocation_withholds_results(self):
        self.app.checkbox[0].check().run()
        self.change("Cash (%)", 10.)
        count = self.mock_download.call_count
        self.app.run()
        self.assertIn("sum to 100%", self.app.error[0].value)
        self.assertEqual(len(self.app.dataframe), 0)
        self.assertEqual(self.mock_download.call_count, count)

    def test_selected_rule_updates_with_questionnaire(self):
        summary = lambda: "\n".join(element.value for element in self.app.markdown)
        self.assertFalse(self.app.checkbox[0].value)
        self.assertIn("65% stocks / 25% bonds / 10% cash", summary())
        self.assertIn("Rule B selected by Sam", "\n".join(element.value for element in self.app.caption))
        self.change("Age", 60)
        self.app.run()
        self.assertIn("40% stocks / 50% bonds / 10% cash", summary())
        self.change("Time horizon (years)", 1)
        self.app.run()
        self.assertIn("0% stocks / 0% bonds / 100% cash", summary())
        self.assertIn("PASS", self.app.success[0].value)
        self.app.checkbox[0].check().run()
        self.assertIn("60% stocks / 40% bonds / 0% cash", summary())
        self.app.checkbox[0].uncheck().run()
        self.assertIn("0% stocks / 0% bonds / 100% cash", summary())

    def test_download_failure_withholds_results(self):
        import requests
        self.mock_download.side_effect = requests.ConnectionError("test source unavailable")
        self.app.run()
        self.assertIn("Results are withheld", self.app.error[0].value)
        self.assertEqual(len(self.app.dataframe), 0)


if __name__ == "__main__":
    unittest.main()
