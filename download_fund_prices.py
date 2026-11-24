"""Download and validate monthly adjusted closes for the Meridian lab.

Run with this project's interpreter: .venv/Scripts/python.exe download_fund_prices.py
Raw daily Yahoo responses and retrieval metadata are retained for audit.
"""

import csv
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TICKERS = ["SGOV", "IEF", "BND", "VT"]
START = date(2021, 9, 1)
END_EXCLUSIVE = date(2026, 10, 1)
ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent / "outputs" / "fund_prices_sources"


def fetch():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    sources = []
    series = {}
    for ticker in TICKERS:
        params = urlencode({
            "period1": int(datetime.combine(START, datetime.min.time(), timezone.utc).timestamp()),
            "period2": int(datetime.combine(END_EXCLUSIVE, datetime.min.time(), timezone.utc).timestamp()),
            "interval": "1d", "events": "div,splits", "includeAdjustedClose": "true",
        })
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?{params}"
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=60) as response:
            raw = response.read()
        retrieved = datetime.now(timezone.utc).isoformat()
        (EVIDENCE / f"{ticker}_daily.json").write_bytes(raw)
        payload = json.loads(raw)
        if payload["chart"].get("error"):
            raise ValueError(f"{ticker}: {payload['chart']['error']}")
        result = payload["chart"]["result"][0]
        if result["meta"]["symbol"].upper() != ticker:
            raise ValueError(f"Unexpected ticker for {ticker}")
        adjusted = result["indicators"]["adjclose"][0]["adjclose"]
        timestamps = result["timestamp"]
        if len(adjusted) != len(timestamps):
            raise ValueError(f"{ticker}: timestamps and prices have different lengths")
        monthly = {}
        for stamp, value in zip(timestamps, adjusted):
            trading_date = datetime.fromtimestamp(stamp, ZoneInfo("America/New_York")).date()
            if not START <= trading_date < END_EXCLUSIVE:
                continue
            if value is None or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{ticker}: missing or invalid price at {trading_date}")
            month = trading_date.strftime("%Y-%m")
            previous = monthly.get(month)
            if previous is None or trading_date > previous[0]:
                monthly[month] = (trading_date, value)
        expected = [f"{year}-{month:02d}" for year in range(2021, 2027)
                    for month in range(1, 13)
                    if "2021-09" <= f"{year}-{month:02d}" <= "2026-09"]
        if sorted(monthly) != expected:
            raise ValueError(f"{ticker}: incomplete monthly coverage: {sorted(monthly)}")
        series[ticker] = monthly
        sources.append({
            "ticker": ticker, "source": "Yahoo Finance chart API", "url": url,
            "history_url": f"https://finance.yahoo.com/quote/{ticker}/history/",
            "downloaded_at_utc": retrieved,
            "downloaded_date_indianapolis": datetime.fromisoformat(retrieved).astimezone(
                ZoneInfo("America/Indiana/Indianapolis")).date().isoformat(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "field": "indicators.adjclose[0].adjclose", "interval_downloaded": "1d",
            "monthly_observations": len(monthly),
            "first_trading_date": str(monthly[expected[0]][0]),
            "last_trading_date": str(monthly[expected[-1]][0]),
        })
        print(f"{ticker}: {len(monthly)} complete month-end adjusted prices", flush=True)
    rows = []
    for month in expected:
        trading_dates = {series[ticker][month][0] for ticker in TICKERS}
        if len(trading_dates) != 1:
            raise ValueError(f"Tickers have differing month-end dates in {month}")
        rows.append([str(trading_dates.pop()), *[series[ticker][month][1] for ticker in TICKERS]])
    # JSON is the validated intermediate consumed by the CSV authoring step.
    (EVIDENCE / "monthly_prices.json").write_text(
        json.dumps({"columns": ["Date", *TICKERS], "rows": rows}, indent=2), encoding="utf-8")
    (EVIDENCE / "sources.json").write_text(json.dumps(sources, indent=2), encoding="utf-8")
    print("Validated: 61 monthly prices per fund, supplying 60 monthly returns.")


if __name__ == "__main__":
    fetch()
