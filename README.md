# Lab 17 — FRED/ALFRED: what was known when?

**Sam Stewart · 29 October 2026 · Project 2 series: DGS10**

This submission includes a working Streamlit interest-rate app, the four known answers, a PAYEMS revision probe, a DGS10 data card and source checks, an evidence-backed fresh-eyes response, and an admission decision with an as-of rule. The app was built with AI assistance. It downloads public CSVs without an API key or account. It is a learning demonstration, not investment advice.

## What to submit

Submit the entire `Lab17_FRED_AsOf` folder, or its companion ZIP. Keep the evidence files with the app and documents.

| File | Purpose |
|---|---|
| [asof_app.py](asof_app.py) | Final live app: individual charts, comparison overlay, vintage table, sources and Project 2 call. |
| [DATA_CARD.md](DATA_CARD.md) | Source, measure, units, lag, revisions, acquisition date, three direct page checks and the decision rule. |
| [requirements.txt](requirements.txt) | Exact dependency versions used for the submitted run. |
| [verify_lab17.py](verify_lab17.py) | Reproducible live acceptance checks; expected answers are confined to this validator, not the app. |
| [evidence/VALIDATION.json](evidence/VALIDATION.json) | Actual app results, validation checks, download receipts and app SHA-256. |
| [evidence/downloads/](evidence/downloads/) | Raw public CSVs captured during the submission validation, including PAYEMS and both known-answer vintages. |
| [evidence/asof_dgs10/month_end_comparison.json](evidence/asof_dgs10/month_end_comparison.json) | September 30 versus October 29 evidence and the three source-value comparisons. |
| [MANIFEST.json](MANIFEST.json) | Inventory and SHA-256 checksums of the submission files. |

## Run the app

Extract the ZIP first. In a terminal opened in `Lab17_FRED_AsOf`, run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run asof_app.py --server.headless false --server.showEmailPrompt false --browser.gatherUsageStats false
```

The browser opens at the address printed in the terminal, normally `http://localhost:8501`. Internet access is required. No credentials are required. Press `Ctrl+C` in the server terminal to stop it.

On the original AIFinance2026 workspace, the installed environment can run the submitted copy directly:

```powershell
.\.venv\Scripts\python.exe -m streamlit run .\Lab17_FRED_AsOf\asof_app.py --server.address 127.0.0.1 --server.port 8504 --server.headless false --server.showEmailPrompt false --browser.gatherUsageStats false
```

The submitted version was tested with **Python 3.14.7**, Streamlit **1.66.1**, pandas **3.1.0**, requests **2.34.2**, and Altair **6.3.0**. An existing compatible environment does not need a second installation.

## 1. Known answer reproduced

Select the four default series. Set **As known on** to **5 October 2026**. These were computed from ALFRED's CSVs, not entered into the app:

| Series | Last measurement available in that vintage | Value (%) | Result |
|---|---|---:|---|
| [BAA](https://fred.stlouisfed.org/series/BAA) | September 2026 | 6.47 | Matches supplied answer |
| [FEDFUNDS](https://fred.stlouisfed.org/series/FEDFUNDS) | September 2026 | 3.75 | Matches supplied answer |
| [DGS10](https://fred.stlouisfed.org/series/DGS10) | 2 October 2026 | 5.28 | Matches supplied answer |
| [MORTGAGE30US](https://fred.stlouisfed.org/series/MORTGAGE30US) | 1 October 2026 | 7.28 | Matches supplied answer |

The monthly CSV dates are `2026-09-01`, which identifies the measured month. That is not a claim that September's average was published on September 1.

For the independent probe, type **PAYEMS** in the extra-ID box and set **As known on** to **15 January 2025**:

| PAYEMS check | Actual result from 29 October 2026 downloads |
|---|---:|
| Latest measured month available then | December 2024 |
| December 2024 value known then | 159,536 thousand persons |
| Today's December 2024 value | 158,316 thousand persons |
| Change to that same measured month | −1,220 thousand persons |
| Revised nonmissing observations on shared dates, full history | 381 |
| Today's observations after the vintage's last measured date | 21 |

The table column **Today's value on last known date** makes the December revision visible. **Value today** has a different meaning: it is the latest measured period in today's full download. The two must not be confused.

Evidence: `october_5_acceptance` and `january_15_payroll_probe` in [VALIDATION.json](evidence/VALIDATION.json), plus the saved [CSV downloads](evidence/downloads/).

## 2. The app

- BAA, FEDFUNDS, DGS10 and MORTGAGE30US are selected on a fresh launch; a typed FRED ID adds another series. Typing DGS10 does not duplicate it.
- The start date defaults to **1 January 2020**; **As known on** defaults to the computer's current date. Shareable URL parameters can initialize a different view.
- Each series has an individual chart of today's downloaded values. A comparison overlay adds color-coded lines, a legend and hover details. Rates share a percent axis; an extra series such as PAYEMS has a separate axis for its different units.
- Each individual chart is followed by the last measurement date available in the selected vintage.
- A single table links each ID to its FRED page and shows the last measurement/value known then, the last measurement/value today, later-observation counts, revision counts, and today's value on the last date known then.
- Current and historical downloads are in two cached functions. Each cache miss makes one request per series to the respective provider. Changing only the chart start date reuses those downloads.
- A `.` is missing, not zero. Counts exclude missing observations; nothing is filled or interpolated. Counts use complete histories, while the start date crops charts.
- An unknown ID produces its own error while the other charts and rows remain usable. A failed vintage is not silently replaced with today's data.
- FRED and ALFRED are linked under the title. The table, data card and Project 2 explanation supply additional source links and provenance.

Public download patterns:

```text
https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIES
https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=SERIES&vintage_date=YYYY-MM-DD
```

The app contains no hard-coded economic observations or known-answer results. The validator contains explicit expected values so it can detect errors in the app's downloaded results.

## 3. Data card and three source checks

The complete [DGS10 data card](DATA_CARD.md) names the Federal Reserve Board's H.15 release, links FRED and ALFRED, describes the 10-year constant-maturity Treasury yield, states percent units and daily frequency, and records the observed publication lag, revisions and download date.

Three observations were read directly from the [FRED page's observation list](https://fred.stlouisfed.org/series/DGS10) with AI assistance and then compared with the CSV:

| Measured date | FRED page (%) | Download (%) |
|---|---:|---:|
| 27 October 2026 | 4.99 | 4.99 |
| 26 October 2026 | 5.00 | 5.00 |
| 23 October 2026 | 5.00 | 5.00 |

All three match. These are direct page spot checks, not a claim that the student performed an unaided check. The source comparison and exact request timestamps are preserved in [the month-end evidence](evidence/asof_dgs10/month_end_comparison.json).

## 4. Fresh eyes — attack and evidence-backed answer

**Attack supplied in the lab conversation:** Add PAYEMS and use January 15, 2025. December 2024 should read 159,536 then and lower today. If the revised count is zero, the app probably read today's data twice.

**Answer:** The app returned **159,536** in the historical information set, **158,316** for that same month in today's data, and **381** revised shared observations. This directly answers the attack: the historical and current downloads differ, and the comparison detects those differences. The request receipts identify separate FRED and ALFRED URLs; the raw CSVs and app-generated table rows are in the evidence folder.

**Additional timing attack:** If DGS10 has no revisions, may today's value simply be assigned to its measurement day?

**Answer:** No. The **30 September 2026** vintage ends on **29 September at 5.26%**. Today's CSV has **30 September at 5.29%**, but that measurement was absent from the September 30 vintage. Today's download has **19** later observations and **0** revised shared values. Zero revisions therefore does not establish same-day availability. Earlier app checks independently show that March 31's **4.30%** is absent from the March 31 vintage and present on April 1. Evidence: the [month-end JSON and CSVs](evidence/asof_dgs10/month_end_comparison.json) and `dgs10_availability_examples` in [VALIDATION.json](evidence/VALIDATION.json).

**Attribution:** The PAYEMS attack was supplied by the user in this conversation. No separate partner identity or independently completed partner review was supplied; this submission does not invent one. If the course requires an actual classmate exchange in addition to this supplied probe, that exchange remains to be documented.

## 5. The call — admit with an as-of rule and a condition

**Admit DGS10:** it is a daily market rate with almost no publication lag—about one business day in the checked vintages—and **zero revisions in the tested month-end comparison**. It is relevant to the Treasury and broad-bond exposure in the SGOV, IEF, BND and VT universe, but economic relevance does not override availability.

**As-of rule:** For every trade, use the ALFRED vintage dated the previous calendar day, and only its nonmissing observations. Execute on the next actual trading session after the vintage date. Keep the measurement date, vintage date, download timestamp and trade date with the signal, and preserve the actual downloaded vintage. Computing a change requires both observations to be present in that eligible vintage. Do not substitute today's historical values with an assumed fixed lag.

**Condition that changes the call:** Quarantine if a required vintage is unavailable or availability before the trade cannot be verified. Admit again after that evidence is established. An exact intraday trading strategy would require release-time evidence beyond this date-level app. The checked dates do not certify every historical Project 2 trade, and the portfolio model has not been changed to consume DGS10.

[ALFRED's help](https://alfred.stlouisfed.org/help) explains that historical vintages preserve information sets, that database updates typically follow source releases within one business day, and that release dates are determined from available source/provider information. A measurement date and an availability date serve different purposes.

## Rubric evidence map

| Criterion | Where the submission provides evidence |
|---|---|
| Known answer reproduced | Section 1; all four matched rows and the nonzero PAYEMS revision result in `evidence/VALIDATION.json`; saved CSVs. |
| The app | `asof_app.py`; four defaults, typed ID, individual and overlay charts, linked table, late/revised counts, linked sources and graceful unknown-ID errors. |
| Data card | `DATA_CARD.md`; all requested fields, three direct page comparisons and dated provenance. |
| Fresh eyes | Section 4; the supplied PAYEMS attack answered by actual app results and source downloads. Separate classmate attribution is not claimed. |
| The call | Section 5 and `DATA_CARD.md`; Admit, precise as-of rule, and the condition requiring quarantine. |

## Verification and scope

To rerun the submitted acceptance checks from this folder:

```powershell
python verify_lab17.py
```

The validator runs the packaged app through Streamlit AppTest, checks the known answers, PAYEMS revision and independent axis, individual/overlay chart counts, unknown-ID isolation, missing-value handling and cache reuse. It records the app hash and raw download receipts. Historical vintage values should be reproducible; today's data and revision counts can change after the submission date. The saved evidence fixes what was downloaded on October 29.

The local app server was launched and its health endpoint returned **200 / ok**. The computer/browser automation hosts were unavailable, so browser appearance was not visually inspected. App execution and controls were verified with Streamlit's test runner. No screenshots or partner attestations have been fabricated.

AI assistance covered code, comparison logic, tests, source reading, explanations and packaging. This is not represented as an independently completed AI-off exercise.
