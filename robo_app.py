"""Live, key-free educational robo-advisor. Run: streamlit run robo_app.py.

Allocation and historical alignment are pure Python functions. No repository,
LLM, credentials, local data fallback, or cached download is used.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import requests


FRENCH_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
GS10_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GS10"
MONTHS = pd.period_range("1990-01", "2025-12", freq="M")
ASSETS = ["Stocks", "Bonds", "Cash"]
FOOTER = "Design after matvix90/ai-robo-advisor (MIT). Data: Ken French Data Library; FRED, Federal Reserve Bank of St. Louis. Education, not investment advice."
MONEY_NEEDED_OPTIONS = ["Within 1 year", "1–3 years", "3–5 years", "5–10 years", "More than 10 years"]
REACTION_OPTIONS = ["Sell all", "Sell some", "Hold", "Buy more"]
RULE_DESCRIPTION = (
    "B — stocks = min(80%, max(0%, 100 − age)); cash = 20% without an emergency "
    "fund or if money may be needed within 3 years, otherwise 10%; sell all/some "
    "caps stocks at 20%/40%; bonds = remainder. Horizon ≤1 year or money needed "
    "within 1 year overrides everything to 100% cash."
)


@dataclass(frozen=True)
class Client:
    age: int
    horizon_years: int
    money_needed: str
    emergency_fund: bool
    max_loss_pct: float
    reaction_to_fall: str
    initial_investment: float


def questionnaire_allocation(client: Client) -> tuple[float, float, float]:
    """Sam-selected option B, returned as Stocks/Bonds/Cash fractions.

    The one-year cash override has priority. Loss tolerance is independently
    checked against historical returns; it does not retune this allocation.
    Investment size scales dollars without changing allocation percentages.
    """
    if not 0 <= client.age <= 120 or not 0 <= client.horizon_years <= 100:
        raise ValueError("Age must be 0–120 and the horizon must be 0–100 years.")
    if client.money_needed not in MONEY_NEEDED_OPTIONS or client.reaction_to_fall not in REACTION_OPTIONS:
        raise ValueError("Choose one of the questionnaire's money-needed and reaction options.")
    if client.horizon_years <= 1 or client.money_needed == "Within 1 year":
        return (0.0, 0.0, 1.0)
    cash_pct = 20 if not client.emergency_fund or client.money_needed == "1–3 years" else 10
    stocks_pct = min(80, max(0, 100 - client.age))
    reaction_cap = {"Sell all": 20, "Sell some": 40, "Hold": 80, "Buy more": 80}
    stocks_pct = min(stocks_pct, reaction_cap[client.reaction_to_fall])
    bonds_pct = 100 - stocks_pct - cash_pct
    return (stocks_pct / 100, bonds_pct / 100, cash_pct / 100)


def validate_weights(weights) -> np.ndarray:
    values = np.asarray(weights, dtype=float)
    if values.shape != (3,) or not np.isfinite(values).all():
        raise ValueError("Enter three finite allocation weights.")
    if (values < 0).any() or (values > 1).any() or not np.isclose(values.sum(), 1, atol=1e-10, rtol=0):
        raise ValueError("Stocks, bonds and cash must be nonnegative and sum to 100%.")
    return values


def parse_french(payload: bytes) -> pd.DataFrame:
    """Read only six-digit monthly records, explicitly excluding annual rows."""
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError("Expected one French factor CSV in the ZIP.")
        source = archive.read(names[0]).decode("utf-8-sig")
    header = None
    records = []
    for row in csv.reader(io.StringIO(source, newline=None)):
        row = [value.strip() for value in row]
        if "Mkt-RF" in row and "RF" in row:
            header = row
            continue
        if not row or not re.fullmatch(r"\d{6}", row[0]):
            continue
        if header is None or len(row) != len(header):
            raise ValueError("Malformed French monthly record.")
        period = pd.Period(pd.to_datetime(row[0], format="%Y%m"), freq="M")
        market_excess, cash = float(row[header.index("Mkt-RF")]), float(row[header.index("RF")])
        if market_excess in (-99.99, -999) or cash in (-99.99, -999):
            raise ValueError(f"French missing-value marker in {period}.")
        records.append((period, (market_excess + cash) / 100, cash / 100))
    if not records:
        raise ValueError("No French monthly records found.")
    result = pd.DataFrame(records, columns=["Month", "Stocks", "Cash"]).set_index("Month").sort_index()
    if result.index.has_duplicates or not np.isfinite(result.to_numpy()).all():
        raise ValueError("Duplicate or nonfinite French observations.")
    return result


def parse_gs10(payload: bytes) -> pd.Series:
    frame = pd.read_csv(io.BytesIO(payload), dtype=str)
    if "GS10" not in frame or len(frame.columns) != 2:
        raise ValueError("Expected a date column and GS10 in the FRED CSV.")
    dates = pd.to_datetime(frame.iloc[:, 0], errors="raise").dt.to_period("M")
    values = pd.to_numeric(frame["GS10"], errors="coerce").to_numpy(dtype=float) / 100
    result = pd.Series(values, index=pd.PeriodIndex(dates), name="GS10").sort_index()
    if result.index.has_duplicates:
        raise ValueError("Duplicate GS10 months.")
    return result


def bond_returns(yields: pd.Series) -> pd.Series:
    """Monthly constant-ten-year par-bond approximation specified in the brief."""
    required = pd.period_range("1989-12", "2025-12", freq="M")
    y = yields.reindex(required)
    if not np.isfinite(y.to_numpy()).all() or (y < 0).any():
        raise ValueError("GS10 must supply every month from December 1989 to December 2025.")
    y0 = y.iloc[:-1].to_numpy()
    y1 = y.iloc[1:].to_numpy()
    n = 2 * (10 - 1 / 12)
    discount = (1 + y1 / 2) ** (-n)
    # Stable zero-yield limit of (1 - discount) / y1 is n/2.
    annuity = np.full_like(y1, n / 2)
    np.divide(-np.expm1(-n * np.log1p(y1 / 2)), y1, out=annuity, where=y1 != 0)
    price = y0 * annuity + discount
    return pd.Series(price - 1 + y0 / 12, index=MONTHS, name="Bonds")


def build_returns(french_zip: bytes, gs10_csv: bytes) -> pd.DataFrame:
    french = parse_french(french_zip).reindex(MONTHS)
    returns = french.join(bond_returns(parse_gs10(gs10_csv)))[ASSETS]
    if len(returns) != 432 or not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any().any():
        raise ValueError("Expected 432 complete, valid monthly returns: January 1990–December 2025.")
    return returns


def download_sources() -> dict[str, bytes]:
    """Fresh HTTP requests on every call; deliberately no Streamlit caching."""
    def fetch(url):
        response = requests.get(url, timeout=(10, 45), headers={"Cache-Control": "no-cache"})
        response.raise_for_status()
        return response.content

    with ThreadPoolExecutor(max_workers=2) as pool:
        french = pool.submit(fetch, FRENCH_URL)
        gs10 = pool.submit(fetch, GS10_URL)
        return {"french": french.result(), "gs10": gs10.result()}


def portfolio_returns(returns: pd.DataFrame, weights) -> pd.Series:
    """Fixed weights applied every month imply monthly rebalancing."""
    return returns[ASSETS].dot(validate_weights(weights)).rename("Portfolio")


def wealth_path(returns: pd.Series | pd.DataFrame):
    """Include the initial wealth of 1 before January's return."""
    start = returns.index[0] - 1
    if isinstance(returns, pd.DataFrame):
        initial = pd.DataFrame(1.0, index=pd.PeriodIndex([start]), columns=returns.columns)
    else:
        initial = pd.Series([1.0], index=pd.PeriodIndex([start]), name=returns.name)
    return pd.concat([initial, (1 + returns).cumprod()])


def performance(returns: pd.Series) -> dict:
    if len(returns) < 12 or not np.isfinite(returns.to_numpy()).all() or (returns <= -1).any():
        raise ValueError("Performance requires at least 12 valid monthly returns.")
    wealth = wealth_path(returns)
    rolling = (1 + returns).rolling(12, min_periods=12).apply(np.prod, raw=True) - 1
    return {
        "months": len(returns),
        "cagr": float(wealth.iloc[-1] ** (12 / len(returns)) - 1),
        "volatility": float(returns.std(ddof=1) * np.sqrt(12)),
        "max_drawdown": float((wealth / wealth.cummax() - 1).min()),
        "worst_12m": float(rolling.min()),
        "worst_12m_end": rolling.idxmin(),
    }


def alignment_passes(worst_return: float, max_loss_pct: float) -> bool:
    if not np.isfinite([worst_return, max_loss_pct]).all() or not 0 <= max_loss_pct <= 100:
        raise ValueError("Maximum acceptable loss must be between 0% and 100%.")
    return worst_return >= -max_loss_pct / 100 - 1e-12


def stock_grid(returns: pd.DataFrame, cash_share: float, max_loss_pct: float) -> pd.DataFrame:
    validate_weights([0, 1 - cash_share, cash_share])
    rows = []
    for tenth in range(11):
        stocks = tenth / 10
        if stocks + cash_share > 1 + 1e-12:
            continue
        bonds = max(0.0, 1 - cash_share - stocks)
        stats = performance(portfolio_returns(returns, [stocks, bonds, cash_share]))
        rows.append({"Stocks": stocks, "Bonds": bonds, "Cash": cash_share,
                     "Worst 12 months": stats["worst_12m"], "Ended": str(stats["worst_12m_end"]),
                     "Pass": alignment_passes(stats["worst_12m"], max_loss_pct)})
    return pd.DataFrame(rows)


def largest_stock_share(returns: pd.DataFrame, cash_share: float, max_loss_pct: float) -> float | None:
    grid = stock_grid(returns, cash_share, max_loss_pct)
    passing = grid.loc[grid["Pass"], "Stocks"]
    return None if passing.empty else float(passing.max())


def main():
    import streamlit as st

    st.set_page_config(page_title="My robo-advisor", page_icon="📊", layout="wide")
    st.title("My robo-advisor")
    st.write("Answer the questionnaire, review the allocation, and test its historical loss against your limit.")
    st.caption("Allocation and alignment checks run in testable Python code. Explanations describe the calculated results.")

    with st.sidebar:
        st.header("Your questionnaire")
        age = st.number_input("Age", min_value=0, max_value=120, value=35)
        horizon = st.number_input("Time horizon (years)", min_value=0, max_value=100, value=10)
        needed = st.selectbox("When might you need this money?", MONEY_NEEDED_OPTIONS, index=3)
        emergency = st.radio("Do you have an emergency fund?", ["Yes", "No"])
        loss = st.number_input("Maximum acceptable loss in any 12 months (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
        reaction = st.selectbox("Your reaction to a 20% market fall", REACTION_OPTIONS, index=2)
        initial = st.number_input("Initial investment ($)", min_value=1.0, value=100000.0, step=1000.0)

    client = Client(age, horizon, needed, emergency == "Yes", loss, reaction, initial)
    suggested = questionnaire_allocation(client)
    st.caption("Rule B selected by Sam from AI-proposed options; implemented with Codex assistance.")
    override = st.checkbox("Override allocation by hand", value=False)
    manual = None
    if override:
        cols = st.columns(3)
        manual = [cols[i].number_input(f"{asset} (%)", min_value=0.0, max_value=100.0,
                                     value=value, step=1.0, key=f"manual_{asset}")
                  for i, (asset, value) in enumerate(zip(ASSETS, [60.0, 40.0, 0.0]))]
    try:
        weights = validate_weights(np.asarray(manual) / 100 if override else suggested)
    except ValueError as exc:
        st.error(str(exc))
        st.caption(FOOTER)
        st.stop()
    rule = f"Manual override; questionnaire rule: {RULE_DESCRIPTION}" if override else RULE_DESCRIPTION
    st.write(f"**Allocation:** {weights[0] * 100:g}% stocks / {weights[1] * 100:g}% bonds / {weights[2] * 100:g}% cash · **Rule:** {rule}")
    st.caption("Maximum acceptable loss is tested independently below. Initial investment scales dollars; neither changes Rule B's weights.")
    st.button("Refresh live data")

    try:
        with st.spinner("Downloading fresh French factors and FRED GS10…"):
            payloads = download_sources()
            returns = build_returns(payloads["french"], payloads["gs10"])
    except (requests.RequestException, ValueError, KeyError, zipfile.BadZipFile, UnicodeError) as exc:
        st.error(f"Live data unavailable or invalid: {exc}. Results are withheld; retry the download.")
        st.caption(FOOTER)
        st.stop()

    retrieved = datetime.now(timezone.utc).isoformat(timespec="seconds")
    st.caption(f"{len(returns)} months · January 1990–December 2025 · rebalanced monthly · downloaded {retrieved}")
    series = portfolio_returns(returns, weights)
    stats = performance(series)
    metrics = pd.DataFrame([
        ["CAGR", stats["cagr"], "Annual compound growth rate"],
        ["Volatility", stats["volatility"], "Sample monthly standard deviation × √12"],
        ["Max drawdown", stats["max_drawdown"], "Largest peak-to-trough decline, including initial wealth of 1"],
        ["Worst 12 months", stats["worst_12m"], f"12 months ended {stats['worst_12m_end'].strftime('%B %Y')}"],
    ], columns=["Metric", "Percent", "Meaning"])
    metrics["Dollar equivalent on initial investment"] = metrics["Percent"] * initial
    metrics["Percent"] = metrics["Percent"].map(lambda x: f"{x:.2%}")
    metrics["Dollar equivalent on initial investment"] = metrics["Dollar equivalent on initial investment"].map(lambda x: f"{'−' if x < 0 else ''}${abs(x):,.0f}")
    st.dataframe(metrics, hide_index=True, width="stretch")
    st.caption("Dollar equivalents multiply each statistic by your initial investment; volatility is a dispersion measure. Drawdown dollars are scaled to initial capital, not the historical peak balance. Returns exclude trading costs, taxes and advisory fees.")

    if alignment_passes(stats["worst_12m"], loss):
        st.success(f"Historical alignment check: PASS. Worst 12-month loss {max(0, -stats['worst_12m']):.2%} stays within your {loss:g}% limit.")
    else:
        st.error(f"RED FLAG: worst 12 months returned {stats['worst_12m']:.2%} (−${-stats['worst_12m'] * initial:,.0f}), exceeding your maximum acceptable loss of {loss:g}%.")
    grid = stock_grid(returns, weights[2], loss)
    passing = grid.loc[grid["Pass"], "Stocks"]
    answer = "no stock/bond mix passes" if passing.empty else f"{passing.max():.0%}"
    st.subheader(f"Largest stock share within this client's max loss: {answer}")
    st.write(f"The code tests every feasible 10% stock step with cash fixed at {weights[2] * 100:g}%; bonds take the rest. This is an in-sample historical screen, not a guarantee of future losses or a complete suitability assessment.")
    with st.expander("Inspect every allocation tested"):
        display_grid = grid.copy()
        for column in ["Stocks", "Bonds", "Cash", "Worst 12 months"]:
            display_grid[column] = display_grid[column].map(lambda x: f"{x:.2%}")
        st.dataframe(display_grid, hide_index=True, width="stretch")

    st.subheader("Growth of $1")
    paths = wealth_path(returns.assign(Portfolio=series))
    paths.index = paths.index.to_timestamp(how="end").normalize()
    st.line_chart(paths, width="stretch")
    with st.expander("Data and calculation details"):
        st.markdown(f"[French monthly factors]({FRENCH_URL}) · [FRED GS10]({GS10_URL})")
        st.write("Stocks = (Mkt-RF + RF) / 100. Cash = RF / 100. Only six-digit YYYYMM French rows are admitted; annual records are excluded. The stock proxy is the US market.")
        st.write("GS10 is a nominal Treasury yield. The bond return is an approximation from real observed yields, not a published bond index or an inflation-adjusted yield series. December 1989 supplies January 1990's starting yield.")
        st.code("y0 = previous GS10 / 100; y1 = current GS10 / 100\nn = 2 * (10 - 1/12)\nP = (y0/y1) * (1 - (1 + y1/2)**(-n)) + (1 + y1/2)**(-n)\nbond_return = P - 1 + y0/12")
        st.write("Historical source revisions can change the results. Every Streamlit rerun downloads both sources again; no data cache or offline fallback is used.")
        st.json({name + "_sha256": hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()})
        st.download_button("Download monthly returns CSV", returns.assign(Portfolio=series).to_csv(index_label="Month"), "robo_monthly_returns.csv", "text/csv")
    st.caption(FOOTER)


if __name__ == "__main__":
    main()
