"""Estimate historical portfolio inputs from monthly adjusted prices.

These sample estimates describe history; they are not return forecasts.
Run: .venv/Scripts/python.exe fund_estimates.py
"""

import csv
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent


def estimate(path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        if not columns or columns[0] != "Date":
            raise ValueError("The first column must be Date.")
        tickers = columns[1:]
        if not 3 <= len(tickers) <= 6 or len(set(columns)) != len(columns):
            raise ValueError("Use three to six unique ticker columns.")
        rows = list(reader)
    dates = [date.fromisoformat(row["Date"]) for row in rows]
    if len(dates) != 61 or dates != sorted(set(dates)):
        raise ValueError("Expected 61 unique, ascending monthly prices for 60 returns.")
    month_numbers = [day.year * 12 + day.month for day in dates]
    if any(later - earlier != 1 for earlier, later in zip(month_numbers, month_numbers[1:])):
        raise ValueError("Monthly observations must be consecutive, without gaps.")
    prices = {ticker: [float(row[ticker]) for row in rows] for ticker in tickers}
    if any(not math.isfinite(value) or value <= 0 for series in prices.values() for value in series):
        raise ValueError("All adjusted prices must be finite and positive.")
    returns = {
        ticker: [current / previous - 1 for previous, current in zip(series, series[1:])]
        for ticker, series in prices.items()
    }
    stats = {
        ticker: {
            "historical_annualized_arithmetic_mean_return": 12 * statistics.mean(series),
            "historical_annualized_sample_volatility": math.sqrt(12) * statistics.stdev(series),
            "historical_cagr": (prices[ticker][-1] / prices[ticker][0]) ** (12 / len(series)) - 1,
        }
        for ticker, series in returns.items()
    }
    result = {
        "label": "Historical sample estimates, not forecasts",
        "price_start": str(dates[0]), "price_end": str(dates[-1]),
        "first_monthly_return_end": str(dates[1]),
        "price_observations": len(dates), "monthly_return_observations": len(dates) - 1,
        "tickers": tickers,
        "prices_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "annualization_assumption": "12 periods/year; volatility and covariance scaling assumes no serial correlation",
        "return_definition": "Monthly simple adjusted-price return P_t/P_(t-1)-1; arithmetic mean times 12",
        "cost_basis": "Fund expenses embedded in price history; additional advisory fees, taxes and trading costs excluded",
        "fund_statistics": stats,
        "correlation": [[statistics.correlation(returns[a], returns[b]) for b in tickers] for a in tickers],
        "annualized_sample_covariance": [
            [12 * statistics.covariance(returns[a], returns[b]) for b in tickers] for a in tickers
        ],
    }
    for index, ticker in enumerate(tickers):
        if not math.isclose(result["correlation"][index][index], 1, abs_tol=1e-12):
            raise ValueError("Correlation diagonal must equal one.")
        if not math.isclose(
            result["annualized_sample_covariance"][index][index],
            stats[ticker]["historical_annualized_sample_volatility"] ** 2,
            rel_tol=1e-12,
        ):
            raise ValueError("Covariance diagonal must equal annualized variance.")
    return result


def main():
    result = estimate(ROOT / "prices.csv")
    output = ROOT.parent / "outputs" / "fund_estimates.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(result["label"])
    print(f"{result['price_observations']} prices, {result['monthly_return_observations']} monthly returns")
    print("| Ticker | Historical arithmetic return (annualized) | Historical volatility (annualized) | Historical CAGR |")
    print("|---|---:|---:|---:|")
    for ticker, values in result["fund_statistics"].items():
        print(f"| {ticker} | {values['historical_annualized_arithmetic_mean_return']:.2%} | "
              f"{values['historical_annualized_sample_volatility']:.2%} | {values['historical_cagr']:.2%} |")
    print("\nMonthly return correlations:")
    print("| Ticker | " + " | ".join(result["tickers"]) + " |")
    print("|---|" + "---:|" * len(result["tickers"]))
    for ticker, row in zip(result["tickers"], result["correlation"]):
        print(f"| {ticker} | " + " | ".join(f"{value:.4f}" for value in row) + " |")
    print(f"\nSaved {output.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
