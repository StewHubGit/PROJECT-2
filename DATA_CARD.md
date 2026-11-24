# DGS10: point-in-time decision for Project 2

Verified on **29 October 2026**, using public FRED and ALFRED CSV downloads. Built with AI help.

**Admit:** DGS10 is a daily market rate with about one business day of observed publication lag and **zero revisions** in the September 30-versus-today comparison. Project 2 may use it only as known before each decision, using the eligible ALFRED vintage; today's historical values with an assumed fixed lag are not sufficient proof of availability. **Change to quarantine** if a required vintage is unavailable or the signal's availability before the trade cannot be verified; admit again once that evidence is established. No evidence currently warrants rejecting the series outright.

The selected universe is SGOV, IEF, BND, and VT. Treasury yields are relevant to IEF and BND interest-rate exposure and equity discount rates. This is an economic hypothesis, not a demonstrated forecasting result.

## Data card

| Field | Detail |
|---|---|
| ID | DGS10 |
| Name | Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis |
| What it measures | The market yield on U.S. Treasury securities adjusted to a constant 10-year maturity, quoted on an investment basis. It is a yield, not an ETF price or total return. |
| Source and link | Board of Governors of the Federal Reserve System, H.15 Selected Interest Rates; Treasury constant-maturity data originate with the U.S. Treasury. Distributed by the Federal Reserve Bank of St. Louis through [FRED](https://fred.stlouisfed.org/series/DGS10) and historical [ALFRED vintages](https://alfred.stlouisfed.org/series?seid=DGS10). |
| Units | Percent, not seasonally adjusted |
| Frequency | Daily |
| Release | H.15 Selected Interest Rates |
| Publication lag | Almost no lag for a daily market rate: about **one business day in the checked ALFRED vintages**. On 30 September the last available measurement is 29 September. Earlier checked evidence shows 31 March's measurement first present in the 1 April vintage. This is observed date-level availability, not proof of an exact intraday release time. Holidays and database update timing matter. |
| Revisions | **0 revised values** on shared nonmissing measurement dates when comparing the 30 September 2026 vintage with today's full download. DGS10 behaves as an unrevised daily market rate in this check; this is not a guarantee against future corrections. |
| Download date | **29 October 2026**, about 13:56 America/Indianapolis (UTC−04:00). Exact timestamps and request URLs are saved in the comparison JSON. |
| Missing values and transformations | A `.` is missing. No filling or interpolation; latest dates and counts exclude missing values. Raw percent levels are compared. Chart start date is 1 January 2020; table counts cover the complete downloaded histories. |

**Finding: DGS10 is a daily market rate with almost no publication lag and no revisions in the tested comparison.** Its short lag still matters for a trade on the measurement date. The yield can move substantially without any historical values being revised.

## Last month-end versus today

I entered **DGS10** in the extra-ID box; since it is already selected, the app correctly kept one DGS10 chart. I then set **As known on** to **30 September 2026**, the last day of last month, and then to **29 October 2026**, today, using Streamlit's test runner. The app's browser automation host remains unavailable, so these are verified app-control changes rather than a claim of visual inspection.

| As known on | Last date measured and available | Value (%) | Today's later observations | Revised shared observations |
|---|---|---:|---:|---:|
| 30 September 2026 | 29 September 2026 | 5.26 | 19 | 0 |
| 29 October 2026 | 27 October 2026 | 4.99 | 0 | 0 |

The **19 values that disappear** at the September cutoff were not in that day's ALFRED information set. They run from **30 September (5.29%) through 27 October (4.99%)**. September 30's measurement illustrates the publication lag; the October observations describe periods after the cutoff. They are later arrivals, not revisions of the values already known on September 30. Today's latest measured date is October 27, not the download date.

The complete downloads and [comparison evidence](evidence/asof_dgs10/month_end_comparison.json) are preserved in `evidence/asof_dgs10/`:

- [Current FRED data](evidence/asof_dgs10/DGS10_today.csv)
- [ALFRED vintage for 30 September](evidence/asof_dgs10/DGS10_asof_2026-09-30.csv)
- [ALFRED vintage for today](evidence/asof_dgs10/DGS10_asof_2026-10-29.csv)

## Three values read against the FRED page

On **29 October 2026**, three direct page readings were checked with AI assistance from the observation list on the [FRED DGS10 page](https://fred.stlouisfed.org/series/DGS10), then compared each with the downloaded CSV. All three match:

| Measurement date | FRED page (%) | Download (%) | Result |
|---|---:|---:|---|
| 27 October 2026 | 4.99 | 4.99 | Match |
| 26 October 2026 | 5.00 | 5.00 | Match |
| 23 October 2026 | 5.00 | 5.00 | Match |

The page states that the series was updated on **28 October 2026 at 3:16 PM CDT**. These checks verify the series, units, dates, and downloaded values; they do not by themselves certify past trading-time availability.

## Actual availability evidence

| ALFRED vintage date | Latest nonmissing measurement date | Yield (%) |
|---|---|---:|
| 31 March 2026 | 30 March 2026 | 4.35 |
| 1 April 2026 | 31 March 2026 | 4.30 |
| 5 October 2026 | 2 October 2026 | 5.28 |

Thus **31 March's 4.30% was not in the 31 March ALFRED information set**, although its measurement date is 31 March. The next day's vintage contains it. A month-end trade using that day's measured yield would leak information under the ALFRED date convention. Zero revisions in the checked DGS10 histories does not remove this publication-lag problem.

For each trade, select the ALFRED vintage dated the previous calendar day and use only that vintage's nonmissing observations. Trade in the next actual trading session after the vintage date. For example, the 31 March vintage permits 30 March's 4.35% for an April 1 trade; it does not permit 31 March's 4.30%. Computing changes requires both observations to be present in the same eligible vintage. Keep measurement date, vintage date, downloaded-at timestamp, and trade date with the signal; save the downloaded vintage used for a reproducible backtest.

ALFRED dates do not establish an exact intraday release time. The previous-day cutoff is a conservative date-level rule. ALFRED also documents that source releases and database updates can differ, and that observations are typically added within one business day. If the required vintage is unavailable, skip the signal rather than substitute today's data. The app compares two information sets; it does not audit every trade in the Project 2 history. No claim that every Project 2 signal was knowable has been established, and the existing portfolio model has not been changed to consume DGS10.

## Acceptance checks

The app's 5 October 2026 vintage matches all supplied expectations: September BAA **6.47**, September FEDFUNDS **3.75**, 2 October DGS10 **5.28**, and 1 October MORTGAGE30US **7.28**. Monthly measurement dates are represented as the first day of the month in the downloads; that is not their publication date.

The independent revision probe adds PAYEMS and uses **15 January 2025**. December 2024 is **159,536 thousand persons** in that vintage and **158,316** in today's download. **381** nonmissing shared measurement dates have changed across the complete history, and today's download has **21** nonmissing values after the vintage's last measurement date. Counts use the full downloads, independently of the chart start date. The app includes a column for today's value on the last date known then, so this revision is visible directly.

Streamlit AppTest verified the four default individual charts plus their overlay, today's default cutoff, both supplied historical checks, five individual charts plus an overlay with PAYEMS, a separate PAYEMS axis, isolation of an unknown ID, missing-value treatment, addition/revision counts, and cached downloads when changing only the chart start date. Results: [validation JSON](evidence/VALIDATION.json). The computer/browser automation hosts were unavailable, so visual browser inspection could not be performed.

## Run

From this extracted submission folder, after installing requirements:

```powershell
python -m streamlit run asof_app.py --server.address 127.0.0.1 --server.port 8503 --server.headless false --server.showEmailPrompt false --browser.gatherUsageStats false
```

The base address opens four rates with today's cutoff. The PAYEMS probe is also available at:

http://127.0.0.1:8503/?asof=2025-01-15&extra=PAYEMS

## Sources

- [DGS10 metadata](https://fred.stlouisfed.org/series/DGS10)
- [ALFRED availability and vintage conventions](https://alfred.stlouisfed.org/help)
- [PAYEMS metadata: thousands of persons, seasonally adjusted, monthly; Employment Situation](https://fred.stlouisfed.org/series/PAYEMS)
- Current CSV: `https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIES`
- Historical CSV: `https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=SERIES&vintage_date=YYYY-MM-DD`
