r"""FRED rates and the historical information set, without an API key.

Run: .\.venv\Scripts\python.exe -m streamlit run asof_app.py
Each cache miss makes one CSV request per series to each provider.
"""

from datetime import date, datetime
from io import StringIO
import re

import altair as alt
import pandas as pd
import requests
import streamlit as st


SERIES = {
    "BAA": "Moody's Baa corporate bond yield",
    "FEDFUNDS": "federal funds rate",
    "DGS10": "10-year Treasury yield",
    "MORTGAGE30US": "30-year mortgage rate",
}
ID_PATTERN = re.compile(r"[A-Z][A-Z0-9_]{0,79}\Z")


def parse_csv(text: str, series_id: str) -> pd.Series:
    """ALFRED adds a vintage suffix to its value header; use column position.

    Keep missing observations as gaps. Never interpolate or fill them.
    Reject HTML/error pages and malformed data instead of plotting them.
    """
    frame = pd.read_csv(StringIO(text), na_values=["."], keep_default_na=True)
    if len(frame.columns) != 2 or frame.columns[0].lower() not in {
        "observation_date", "date"
    }:
        raise ValueError("The download did not contain a two-column FRED CSV.")
    if not re.fullmatch(re.escape(series_id) + r"(?:_\d{8})?", frame.columns[1]):
        raise ValueError("The CSV value column does not match the requested series.")
    dates = pd.to_datetime(frame.iloc[:, 0], format="%Y-%m-%d", errors="raise")
    values = pd.to_numeric(frame.iloc[:, 1], errors="raise").astype(float)
    if dates.isna().any() or dates.duplicated().any():
        raise ValueError("The CSV contains missing or repeated observation dates.")
    if values.isin([float("inf"), float("-inf")]).any():
        raise ValueError("The CSV contains a non-finite value.")
    return pd.Series(values.to_numpy(), index=dates, name=series_id).sort_index()


@st.cache_data(ttl=3600, max_entries=256, show_spinner=False)
def download_today(series_id: str, download_day: date) -> tuple[pd.Series, str]:
    """One public FRED CSV request; day in cache key prevents overnight reuse."""
    response = requests.get(
        "https://fred.stlouisfed.org/graph/fredgraph.csv",
        params={"id": series_id}, timeout=(10, 40),
    )
    response.raise_for_status()
    return parse_csv(response.text, series_id), datetime.now().astimezone().isoformat()


@st.cache_data(ttl=3600, max_entries=512, show_spinner=False)
def download_asof(
    series_id: str, vintage_date: date, download_day: date,
) -> tuple[pd.Series, str]:
    """One public ALFRED CSV request for the requested historical vintage."""
    response = requests.get(
        "https://alfred.stlouisfed.org/graph/alfredgraph.csv",
        params={"id": series_id, "vintage_date": vintage_date.isoformat()},
        timeout=(10, 40),
    )
    response.raise_for_status()
    values = parse_csv(response.text, series_id)
    if (values.dropna().index > pd.Timestamp(vintage_date)).any():
        raise ValueError("ALFRED returned observations beyond the requested vintage.")
    return values, datetime.now().astimezone().isoformat()


def compare_series(current: pd.Series | None, vintage: pd.Series | None) -> dict:
    """Compare nonmissing observations over the complete downloaded history."""
    now = current.dropna() if current is not None else pd.Series(dtype=float)
    then = vintage.dropna() if vintage is not None else pd.Series(dtype=float)
    row = {
        "Last measured date known then": None,
        "Value known then": None,
        "Today's value on last known date": None,
        "Last measured date today": None,
        "Value today": None,
        "Values after last known date": None,
        "Revised values on shared dates": None,
    }
    if not then.empty:
        row.update({"Last measured date known then": then.index[-1].strftime("%Y-%m-%d"),
                    "Value known then": float(then.iloc[-1])})
    if not now.empty:
        row.update({"Last measured date today": now.index[-1].strftime("%Y-%m-%d"),
                    "Value today": float(now.iloc[-1])})
    if current is not None and vintage is not None:
        if not then.empty and then.index[-1] in now.index:
            row["Today's value on last known date"] = float(now.loc[then.index[-1]])
        shared = now.index.intersection(then.index)
        # CSV decimal levels are compared, not computed returns; ignore float noise.
        row["Revised values on shared dates"] = int(
            ((now.loc[shared] - then.loc[shared]).abs() > 1e-10).sum()
        )
        if not then.empty:
            row["Values after last known date"] = int((now.index > then.index[-1]).sum())
    return row


def comparison_chart(series: dict[str, pd.Series]) -> alt.Chart | alt.LayerChart:
    """Overlay actual observation dates; keep rate and other units distinct."""
    frames = []
    for series_id, values in series.items():
        units = ("Percent" if series_id in SERIES else
                 "Thousands of persons" if series_id == "PAYEMS" else "Native series units")
        frames.append(pd.DataFrame({"Date measured": values.index,
                                    "Value": values.to_numpy(),
                                    "Series": series_id, "Units": units}))
    data = pd.concat(frames, ignore_index=True)
    colors = alt.Scale(domain=list(series), scheme="tableau10")

    def lines(frame: pd.DataFrame, title: str, orient: str = "left") -> alt.Chart:
        return alt.Chart(frame).mark_line().encode(
            x=alt.X("Date measured:T", title="Date measured"),
            y=alt.Y("Value:Q", title=title, scale=alt.Scale(zero=False),
                    axis=alt.Axis(orient=orient)),
            color=alt.Color("Series:N", scale=colors, title="Series"),
            tooltip=[alt.Tooltip("Series:N"),
                     alt.Tooltip("Date measured:T", format="%Y-%m-%d"),
                     alt.Tooltip("Value:Q", format=",.4f"), alt.Tooltip("Units:N")],
        )

    rates = data.loc[data["Series"].isin(SERIES)]
    other = data.loc[~data["Series"].isin(SERIES)]
    if rates.empty:
        return lines(other, str(other["Units"].iloc[0])).properties(height=340).interactive()
    rate_lines = lines(rates, "Percent")
    if other.empty:
        return rate_lines.properties(height=340).interactive()
    other_label = f"{', '.join(other['Series'].unique())} · {other['Units'].iloc[0]}"
    return alt.layer(rate_lines, lines(other, other_label, "right")).resolve_scale(
        y="independent", color="shared"
    ).properties(height=340).interactive()


def main() -> None:
    st.set_page_config(page_title="Rates | FRED & ALFRED", page_icon="📈", layout="wide")
    today = date.today()
    # Optional shareable view; a plain launch still defaults to today / four rates.
    try:
        initial_asof = date.fromisoformat(st.query_params.get("asof", today.isoformat()))
        if not date(1776, 1, 1) <= initial_asof <= today:
            initial_asof = today
    except ValueError:
        initial_asof = today
    st.title("Interest rates: what was known when?")
    st.caption(
        "Data from [FRED](https://fred.stlouisfed.org/) and "
        "[ALFRED](https://alfred.stlouisfed.org/), Federal Reserve Bank of St. Louis, "
        f"downloaded today ({today:%Y-%m-%d}); built with AI help, "
        "a learning demonstration, not investment advice."
    )
    with st.sidebar:
        st.header("Explore rates")
        selected = st.multiselect(
            "Series", list(SERIES), default=list(SERIES),
            key="selected_series",
            format_func=lambda item: f"{item} ({SERIES[item]})",
        )
        extra = st.text_input("Add another FRED series ID", value=st.query_params.get("extra", ""),
                              key="extra_series", placeholder="e.g. PAYEMS").strip().upper()
        start = st.date_input("Start date", value=date(2020, 1, 1),
                              min_value=date(1776, 1, 1), max_value=today, key="chart_start")
        asof = st.date_input('As known on', value=initial_asof,
                             min_value=date(1776, 1, 1), max_value=today, key="as_known_on")
        st.caption("Dates identify measurement periods. ALFRED vintages identify the information set.")
        st.caption("Cached for one hour. Changing the chart start date reuses the downloads.")
    st.query_params["asof"] = asof.isoformat()
    if extra:
        st.query_params["extra"] = extra
    elif "extra" in st.query_params:
        del st.query_params["extra"]

    if extra:
        if not ID_PATTERN.fullmatch(extra):
            st.error("Extra series ID: enter letters, numbers, or underscores, starting with a letter.")
        elif extra not in selected:
            selected.append(extra)
    if not selected:
        st.info("Select a series or enter a FRED series ID in the sidebar.")
        return

    overlay = st.container()
    overlay_series = {}
    rows = []
    receipts = []
    for series_id in selected:
        st.subheader(f"{series_id} · {SERIES.get(series_id, 'Additional FRED series')}")
        current = vintage = None
        errors = []
        # Fetch independently so a missing vintage cannot suppress today's chart.
        with st.spinner(f"Loading {series_id} from FRED and ALFRED…"):
            for label, fetch in (
                ("FRED", lambda: download_today(series_id, today)),
                ("ALFRED", lambda: download_asof(series_id, asof, today)),
            ):
                try:
                    values, timestamp = fetch()
                    if label == "FRED":
                        current = values
                    else:
                        vintage = values
                    receipts.append({"Series": series_id, "Source": label,
                                     "Downloaded at": timestamp})
                except (requests.RequestException, ValueError, pd.errors.ParserError) as exc:
                    errors.append(f"{label}: {exc}")
                    st.error(f"{series_id} — {label} download failed. Check the ID, date, or connection. {exc}")

        if current is not None:
            chart = current.loc[current.index >= pd.Timestamp(start)]
            if chart.dropna().empty:
                st.info("No measured values on or after the selected start date.")
            else:
                overlay_series[series_id] = chart
                st.line_chart(chart.to_frame(), height=240,
                              y_label="Percent" if series_id in SERIES else "Native series units",
                              x_label="Date measured")

        summary = compare_series(current, vintage)
        last_known = summary["Last measured date known then"]
        if last_known:
            st.caption(f"As known on {asof:%Y-%m-%d}: last measured date available = {last_known}; "
                       f"value = {summary['Value known then']:g}.")
        elif vintage is not None:
            st.caption(f"As known on {asof:%Y-%m-%d}: no nonmissing observations available.")
        else:
            st.caption(f"As known on {asof:%Y-%m-%d}: availability could not be verified.")
        rows.append({"Series": f"https://fred.stlouisfed.org/series/{series_id}", **summary,
                     "Status": "; ".join(errors) if errors else
                     ("No observations in vintage" if not last_known else "OK")})

    with overlay:
        st.subheader("All selected series · comparison")
        if overlay_series:
            st.altair_chart(comparison_chart(overlay_series), width="stretch")
            st.caption(
                "Today's downloaded values from the selected start date. "
                "Colors identify each series; hover for dates and values. "
                "Rates share the percent axis. An additional series in other units "
                "uses a separate axis on the right; compare its direction, not its "
                "height against the rates. Monthly, weekly, and daily observations "
                "retain their own measurement dates."
            )
        else:
            st.info("No series has values to compare in the selected date range.")

    st.subheader(f"Known on {asof:%Y-%m-%d} versus today's data")
    st.dataframe(
        pd.DataFrame(rows), hide_index=True, width="stretch",
        column_config={
            "Series": st.column_config.LinkColumn("Series", display_text=r"/series/(.*)$"),
            "Value known then": st.column_config.NumberColumn(format="%.4f"),
            "Value today": st.column_config.NumberColumn(format="%.4f"),
            "Today's value on last known date": st.column_config.NumberColumn(format="%.4f"),
            "Values after last known date": st.column_config.NumberColumn(format="%d"),
            "Revised values on shared dates": st.column_config.NumberColumn(format="%d"),
        },
    )
    st.caption(
        "Last dates and counts use the complete downloads; the start date only crops charts. "
        "Counts exclude missing values ('.'). Revisions compare nonmissing values on shared "
        "measurement dates. A dash means unavailable, not zero. Today's values means the "
        "latest downloaded vintage, not necessarily measurements made today."
    )
    with st.expander("May Project 2 use DGS10?", expanded=True):
        st.markdown(
            "**Admit, with a dated information rule.** DGS10 has about one business day "
            "of observed publication lag and zero revisions in the checked month-end "
            "comparison. It is the selected "
            "driver for SGOV, IEF, BND, and VT. Rising Treasury yields can lower IEF and "
            "BND prices and affect VT valuations.\n\n"
            "**The observation date is not proof of availability.** For every simulated "
            "trade, use the ALFRED vintage from the previous calendar day and only its "
            "nonmissing observations. Execute on the next actual trading session after "
            "that vintage date. This avoids assuming that data released later during a "
            "trading day were available at the trade. Preserve the vintage and download "
            "date with each signal.\n\n"
            "**Today's historical CSV is not approved as a historical trading signal.** "
            "This two-vintage comparison checks the chosen date; it does not certify all "
            "historical trades or exact intraday availability. An unavailable vintage "
            "means quarantine the signal until its availability can be established.\n\n"
            "[DGS10 and H.15 release](https://fred.stlouisfed.org/series/DGS10) · "
            "[ALFRED availability conventions](https://alfred.stlouisfed.org/help)"
        )
    with st.expander("Download receipts"):
        st.dataframe(pd.DataFrame(receipts), hide_index=True, width="stretch")


if __name__ == "__main__":
    main()
