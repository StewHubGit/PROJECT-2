"""Behavioral and live acceptance checks for the rates app."""
from datetime import date, datetime
import importlib.util
import json
import hashlib
import requests
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rates_app", ROOT / "asof_app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

# The comparison must distinguish additions, revisions, and missing days.
old = app.parse_csv("observation_date,X_20250115\n2025-01-01,10\n2025-01-02,.\n2025-01-03,11\n", "X")
new = app.parse_csv("observation_date,X\n2025-01-01,9\n2025-01-02,.\n2025-01-03,11\n2025-01-06,12\n", "X")
comparison = app.compare_series(new, old)
assert comparison["Revised values on shared dates"] == 1
assert comparison["Values after last known date"] == 1
assert app.compare_series(new, None)["Revised values on shared dates"] is None
assert old.isna().sum() == 1


receipts = []
raw_dir = ROOT / "evidence" / "downloads"
raw_dir.mkdir(parents=True, exist_ok=True)
original_get = requests.get

def record_get(url, **kwargs):
    response = original_get(url, **kwargs)
    params = kwargs.get("params", {})
    sid = params.get("id", "unknown")
    provider = "ALFRED" if "alfred" in url else "FRED"
    vintage = params.get("vintage_date", date.today().isoformat())
    filename = f"{sid}_{provider}_{vintage}.csv"
    receipt = {"series": sid, "provider": provider, "vintage": vintage,
               "url": response.url, "status": response.status_code,
               "downloaded_at": datetime.now().astimezone().isoformat()}
    if response.ok and response.text.startswith("observation_date,"):
        (raw_dir / filename).write_text(response.text, encoding="utf-8")
        receipt["saved_csv"] = "downloads/" + filename
    receipts.append(receipt)
    return response

recorder = patch("requests.get", side_effect=record_get)
recorder.start()
result = {"synthetic_comparison": comparison}

at = AppTest.from_file(str(ROOT / "asof_app.py"), default_timeout=180).run()
assert not at.exception, str(at.exception)
assert not at.error, [e.value for e in at.error]
assert len(at.get("vega_lite_chart")) == 5
overlay = json.loads(at.get("vega_lite_chart")[0].proto.spec)
assert overlay["encoding"]["color"]["scale"]["domain"] == list(app.SERIES)
assert len(at.dataframe[0].value) == 4
assert at.date_input[0].value == date(2020, 1, 1)
assert at.date_input[1].value == date.today()
result["default_today"] = at.dataframe[0].value.to_dict("records")
print("PASS: four individual rate charts, overlay and four table rows", flush=True)

at.date_input[1].set_value(date(2026, 10, 5)).run()
assert not at.exception and not at.error
expected = {
    "BAA": ("2026-09-01", 6.47),
    "FEDFUNDS": ("2026-09-01", 3.75),
    "DGS10": ("2026-10-02", 5.28),
    "MORTGAGE30US": ("2026-10-01", 7.28),
}
rows = at.dataframe[0].value.to_dict("records")
for row in rows:
    sid = row["Series"].rsplit("/", 1)[-1]
    assert (row["Last measured date known then"], row["Value known then"]) == expected[sid], row
result["october_5_acceptance"] = rows
print("PASS: October 5 matches all four supplied values", flush=True)

at.date_input[1].set_value(date(2025, 1, 15))
at.text_input[0].set_value("PAYEMS").run()
assert not at.exception and not at.error
assert len(at.get("vega_lite_chart")) == 6
overlay = json.loads(at.get("vega_lite_chart")[0].proto.spec)
assert overlay["resolve"]["scale"]["y"] == "independent"
assert len(overlay["layer"]) == 2
rows = at.dataframe[0].value.to_dict("records")
payems = next(row for row in rows if row["Series"].endswith("/PAYEMS"))
assert payems["Last measured date known then"] == "2024-12-01", payems
assert payems["Value known then"] == 159536, payems
assert payems["Today's value on last known date"] < 159536, payems
assert payems["Revised values on shared dates"] > 100, payems
result["january_15_payroll_probe"] = rows
current_december = payems["Today's value on last known date"]
print("PASS: PAYEMS historical value 159536; current December value "
      f"{current_december}; "
      f"{payems['Revised values on shared dates']} revised observations", flush=True)

# Invalid real ID may fail both endpoints but must leave the four rates usable.
at.text_input[0].set_value("ZZZINVALIDFREDSERIES987654321").run()
assert not at.exception
assert len(at.error) >= 1
assert len(at.get("vega_lite_chart")) == 5
assert len(at.dataframe[0].value) == 5
assert at.dataframe[0].value.iloc[-1]["Status"] != "OK"
result["unknown_id_isolated"] = True
print("PASS: invalid ID isolated; four rate charts survive", flush=True)

# Verify a historical trade cutoff for DGS10; record exactly what was available.
dgs_today, _ = app.download_today("DGS10", date.today())
result["dgs10_availability_examples"] = {}
for cutoff in (date(2026, 3, 31), date(2026, 4, 1)):
    vintage, stamp = app.download_asof("DGS10", cutoff, date.today())
    result["dgs10_availability_examples"][str(cutoff)] = {
        **app.compare_series(dgs_today, vintage), "downloaded_at": stamp,
    }

# Cache hits must avoid network, including changes to only the chart start date.
at.text_input[0].set_value("PAYEMS").run()
with patch("requests.get", side_effect=AssertionError("unexpected repeat request")):
    at.date_input[0].set_value(date(2022, 1, 1)).run()
    assert not at.exception and not at.error
result["start_date_reuses_cached_downloads"] = True
result["verified_on"] = date.today().isoformat()

recorder.stop()
result["download_receipts"] = receipts
result["app_sha256"] = hashlib.sha256((ROOT / "asof_app.py").read_bytes()).hexdigest()
result["overlay_checked"] = {"default_individual_charts": 4, "default_overlays": 1,
                            "PAYEMS_individual_charts": 5, "PAYEMS_overlays": 1,
                            "separate_PAYEMS_axis": True}
output = ROOT / "evidence" / "VALIDATION.json"

output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
print(f"PASS: cache reuse; saved {output}", flush=True)
