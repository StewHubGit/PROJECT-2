# SPY monthly price upload

Prepared October 22, 2026, from the daily SPY history pasted in this conversation.

| Ticker | Fund | Role | Indicated source | Date received |
|---|---|---|---|---|
| SPY | SPDR S&P 500 ETF Trust | U.S. large-cap equity | User-pasted [Yahoo Finance historical data](https://finance.yahoo.com/quote/SPY/history/) | 2026-10-22 |

The user's original download date was not supplied. This file records the date the table was received, rather than claiming an independent download.

`spy_prices.csv` contains only `Date,SPY`, sorted oldest first. SPY values come from the **Adj Close** column at the last supplied trading day in each completed month. Dividend-event rows are omitted because distributions are already reflected in adjusted prices. No missing prices were filled and no new price observations were invented.

The file contains **60 completed monthly price observations**, September 2021 through August 2026, dated **2021-09-30 through 2026-08-31**. This produces **59 monthly returns**. The pasted September 2026 data stops at **2026-09-29** and lacks September 30, so that partial month is excluded. To obtain 60 completed monthly returns over the intended five-year interval ending September 2026, add September 30, 2026's adjusted close from the same adjustment basis. Alternatively, obtain an August 2021 opening observation to accompany the current 60 completed months.

The monthly selections and excluded partial observation are preserved in `outputs/spy_sources/pasted_monthly_selection.json`. The original four-fund `prices.csv` remains separate.

## Upload to the app

1. Open [the portfolio app](http://127.0.0.1:8502).
2. In the sidebar, select **Upload prices.csv**, then choose `spy_prices.csv`.
3. For a SPY-only demonstration, set **Reserve minimum (%)** to **0** and leave SPY's reserve-eligible box unticked. SPY is the equity sleeve. The original 3% reserve requirement cannot be met with SPY alone; meeting that mandate requires a combined file including an eligible reserve fund.
4. Keep the return objective unchanged. Read the all-month answer, then enable **Last 36 months only**.

With a single fund the only fully invested allocation is 100% SPY, so each window either passes the modeled return threshold or reports "no mix meets the objective." Return estimates describe history, not forecasts. A single-fund demonstration does not replace the assignment's three-to-six-fund universe.
