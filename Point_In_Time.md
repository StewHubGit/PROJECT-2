# Point-in-time filter and known-answer proof

`asof.py` applies the four removal rules, prints the row funnel and surviving panel, and compares as-of and naive signals. It preserves every original row in the disposition log and optional JSON receipt. The supplied four-row AAA excerpt is the training input; the complete course table was not supplied.

From the main `AIFinance2026` folder:

```powershell
.\.venv\Scripts\python.exe asof.py
.\.venv\Scripts\python.exe asof.py --output outputs/asof/training_receipt.json
.\.venv\Scripts\python.exe asof.py --own-series --output outputs/asof/own_gdp_receipt.json
.\.venv\Scripts\python.exe -m unittest Project2_Portfolio.test_asof -v
```

The first command runs three demonstration dates (February 28, March 31 and April 30). The known answer is checked every time. The implementation also runs directly as `python Project2_Portfolio/asof.py` with any suitable Python interpreter; no third-party packages or network connection are needed.

## Known answer: AAA, 31 March 2026

| Stage | Row count / decision |
| --- | --- |
| Input | 4 rows, original numbers 1–4 |
| Quarantine | 0 removed; 4 remain |
| Duplicates | 0 removed; 4 remain |
| Late publications | Row 4 removed: March 109.0 was published April 10; 3 remain |
| Revisions | Row 2 removed: February 104.0 was replaced by row 3 on March 25; 2 remain |
| As-of panel | Row 1: January 101.0, published February 10; row 3: February 103.0, published March 25 |
| As-of signal | `(103 / 101 - 1) × 100 = +1.980198…%` |
| Naive signal | `(109 / 103 - 1) × 100 = +5.825243…%` |
| Leak | Naive minus as-of: `+3.845044…` percentage points, displayed as **+3.85** |

The naive calculation uses the latest vintage in the supplied file and ignores its publication cutoff. It still excludes measured periods ending after the decision date. This isolates late releases and revised values for historical observation periods. It is explicitly labeled as an intentionally invalid historical information set.

| Decision date | Latest knowable period | As-of signal | Naive signal | Leak, points |
| --- | --- | --- | --- | --- |
| 2026-02-28 | January | N/A: only one eligible period | +1.98% | N/A |
| 2026-03-31 | February | +1.98% | +5.83% | +3.85 |
| 2026-04-30 | March | +5.83% | +5.83% | +0.00 |

February's missing signal stays missing; the script does not manufacture a previous month or a zero return. Signals are calculations, not portfolio recommendations or evidence of predictive performance.

## The four removal rules

1. **Quarantine.** Reject missing series, invalid measured periods, nonnumeric/nonfinite/nonpositive levels, and publications before the measured period ends. A missing or invalid publication date quarantines the entire series. Conflicting values with the same series, period and publication day are quarantined because date-only data cannot order them.
2. **Duplicates.** For identical series, period, numeric value and publication day, retain the first source record. Keep each removed row in the audit and identify the original row it duplicates. Numerically equivalent `109` and `109.0` are duplicates; the same value on a different publication day is not.
3. **Late publications.** Remove any remaining row published after the decision date. Publication on the decision date is eligible under this end-of-day convention.
4. **Revisions.** Within each series and measured period, retain the latest remaining publication. Every older eligible version records the original row that replaces it.

The order matters: choosing a later revision before excluding late publications can erase the value that was actually available. Tests exercise all four stages, including invalid duplicates, duplicate late rows and late revisions of already-known months. Signal calculation requires consecutive periods, so a gap does not silently become a one-month change.

Original row numbers remain fixed. If a CSV has no `row_number`, numbers are assigned once in source-record order, starting at 1 for the first data record. The full raw cells and source-record positions survive in JSON. Duplicate or blank explicit row numbers are input errors, since they would make the audit ambiguous.

## Your own table

Required columns: `series,month_measured,value,published_on`; optional stable `row_number`. Dates use `YYYY-MM-DD`, periods use `YYYY-MM`. Monthly level data are the default. Quarterly data use the quarter-start month and `--frequency quarterly`. This implementation accepts positive level series for the specified ratio signal; rates or signed measures need an explicitly chosen alternative signal rule.

```powershell
.\.venv\Scripts\python.exe asof.py --csv path/to/your_publication_history.csv --dates 2026-02-28 2026-03-31 2026-04-30 --output outputs/asof/your_receipt.json
```

Supply actual publication history and its data card; do not substitute observation dates, download dates, or a guessed lag. Only the built-in AAA excerpt has the supplied known-answer proof. A new table needs its own external expected values. The optional receipt stores both panels, both row audits, signals at full Decimal precision, input SHA-256 and execution time.

## Own-series extension and DRIVER

The GDP example uses quarterly nominal dollar levels verified against [BEA's historical releases](asof_data/DATA_CARDS.md), with decisions after the April, May and June 2011 releases. As-of quarter changes are +0.91%, +0.93% and +0.99%; the deliberately naive June-vintage figure is +0.99% at all three dates. This example is restricted to March 25–July 28, 2011 because later annual revisions are outside the sample. It demonstrates the filter; it does not establish that last week's downloaded ETF adjusted-price history was point-in-time. That history requires separate vendor evidence about publication timing and adjustment vintages.

**Define** — What consecutive-period signal could have been calculated from publications available by the end of each decision date?

**Represent** — Keep measured period, value, publication date and stable row number; apply quarantine, duplicates, late publications and revisions in that order.

**Implement** — One `asof.py` command prints the funnel, panel, paired signals and row dispositions.

**Validate** — AAA on March 31 retains rows 1 and 3 and reproduces +1.98%, +5.83% and the +3.85-point leak; behavioral tests probe removal order and date boundaries.

**Evolve** — Run the same filter on nominal GDP, retaining its actual 28-, 56- and 85-day Q1 publication lags and documenting revisions in the data card.

**Reflect** — A number describing a past month or quarter may still be unavailable; a known-answer match proves this case, while each new series needs defensible publication history.

See [data cards and source map](asof_data/DATA_CARDS.md), [training receipt](../outputs/asof/training_receipt.json) and [own-series receipt](../outputs/asof/own_gdp_receipt.json).
