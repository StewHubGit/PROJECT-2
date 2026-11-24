# Lab 19 - Same facts, different investor rules
Sam Stewart | Individual submission | Prepared with AI assistance

## What the panel is and why it disagrees
The panel applies separate Buffett, Graham and Burry skill instructions to one shared set of annual SEC facts. Buffett emphasizes returns and owner earnings, Graham emphasizes liquidity and earnings stability, and Burry emphasizes cash backing and leverage. Different verdicts arise from different predicates and thresholds, not from giving each persona different financial statements. The calculation and memo pipeline is deterministic and AI-assisted; these are simulated perspectives, not three independent live model calls or the actual investors.

## COST: reproduce the known answer
The engine calculates actual SEC facts before the separate acceptance script reads the instructor answer key. No expected value enters the extraction or checks.

| FY end | Current ratio | Liabilities/equity |
|---|---:|---:|
| 2022-08-28 | 1.02 | 2.11 |
| 2023-09-03 | 1.07 | 1.75 |
| 2024-09-01 | 0.97 | 1.96 |
| 2025-08-31 | 1.03 | 1.64 |
| 2026-08-30 | 1.06 | 1.49 |

| Investor | Check | Result |
|---|---|---|
| Buffett | ROE of 15% or more every year | pass |
| Buffett | Owner earnings positive every year | pass |
| Buffett | Owner earnings grew, first year to last | pass |
| Graham | Current ratio of 2.0 or more, latest year | fail |
| Graham | Net income positive every year | pass |
| Graham | Net income grew, first year to last | pass |
| Burry | Operating cash flow at least net income every year | pass |
| Burry | Liabilities no more than 2 times equity, latest year | pass |
Buffett: 3 of 3; verdict pass.
Graham: 2 of 3; verdict fail.
Burry: 2 of 2; verdict pass.

## Threshold probe
The probe changes only Graham's current-ratio rule from 2.0 to 1.0. At the unchanged COST ratio of 1.06, Graham moves from 2 of 3 to 3 of 3: verdict pass. That is a changed policy, not new company evidence. The saved baseline skill retains the stricter rule.

## Fund and company selection
The existing Project 2 coursework selects SGOV, IEF, BND and VT; VT is the equity fund. This lab therefore uses Vanguard Total World Stock ETF (VT), rather than treating Treasury or bond holdings as operating companies. The saved Project 2 context is `project2_fund_context.md` in this evidence folder.

Vanguard's fund factsheet, dated September 30, 2026, lists NVIDIA first at 4.6% of total net assets, followed by Apple at 4.1% and Microsoft at 3.3%. This identifies NVIDIA (NVDA) as the largest company in the selected equity fund on that disclosed date, not as a live holdings claim. The factsheet's figures are rounded. Source: [Vanguard VT factsheet](https://fund-docs.vanguard.com/F3141.pdf), second page; the original PDF, retrieval receipt and extracted text are included.

NVIDIA files a Form 10-K on EDGAR. Its latest annual fiscal year in this run ends January 25, 2026; the filing was submitted February 25, 2026, accession 0001045810-26-000021. No next-largest-company fallback was required. The five-year panel uses annual statements only, available by November 5, 2026, including eligible comparative disclosures for older fiscal periods.


## NVIDIA: same facts, three verdicts
| Investor | Check | Result |
|---|---|---|
| Buffett | ROE of 15% or more every year | pass |
| Buffett | Owner earnings positive every year | pass |
| Buffett | Owner earnings grew, first year to last | pass |
| Graham | Current ratio of 2.0 or more, latest year | pass |
| Graham | Net income positive every year | pass |
| Graham | Net income grew, first year to last | pass |
| Burry | Operating cash flow at least net income every year | fail |
| Burry | Liabilities no more than 2 times equity, latest year | pass |
Buffett: 3 of 3; 0 not known; verdict pass.
Graham: 3 of 3; 0 not known; verdict pass.
Burry: 1 of 2; 0 not known; verdict fail.

## Investor memos

### NVDA - Buffett memo
AI-assisted simulated perspective; not the actual investor or an independent analyst vote.
Screen verdict: pass; 3 of 3 checks pass, 0 fail, 0 not known.

The lowest observed ROE is 19.8%, against the 15.0% rule. Owner earnings proxy moves from 8,132 to 96,676 million. I favor durable cash generation, but OCF less all capex is a simplified proxy, not a maintenance-capex estimate. A strong final year cannot erase a failed earlier year. A screen pass would justify deeper moat and management work, not a purchase.

Known limits: current price not found; intrinsic value not known; margin of safety not known; price target not known. Missing required inputs remain not found, with dependent checks not known.


### NVDA - Graham memo
AI-assisted simulated perspective; not the actual investor or an independent analyst vote.
Screen verdict: pass; 3 of 3 checks pass, 0 fail, 0 not known.

Latest current ratio is 3.91 versus the 2.0 minimum. Net income moves from 9,752 to 120,067 million. I place more weight on a liquid balance sheet and earnings stability than on a compelling growth narrative. These assignment checks are a simplified adaptation, not the complete historical defensive-investor framework. A margin of safety still requires a separately verified price and valuation.

Known limits: current price not found; intrinsic value not known; margin of safety not known; price target not known. Missing required inputs remain not found, with dependent checks not known.

Threshold kept: 2.0; retain the conservative baseline for comparability, and show the looser threshold only as a sensitivity probe.


### NVDA - Burry memo
AI-assisted simulated perspective; not the actual investor or an independent analyst vote.
Screen verdict: fail; 1 of 2 checks pass, 1 fail, 0 not known.

Latest OCF is 102,718 against net income of 120,067 million; the difference is -17,349 million. Latest liabilities/equity is 0.31. OCF trails income in these fiscal years: 2022-01-30, 2024-01-28, 2025-01-26, 2026-01-25. I would reconcile working capital, noncash items and recurring earnings before calling the divergence aggressive accounting. A failed cash test is a research question, not proof of fraud or a short recommendation.

Known limits: current price not found; intrinsic value not known; margin of safety not known; price target not known. Missing required inputs remain not found, with dependent checks not known.


## Where they agree and split
They share the same reported history. Buffett and Graham both inspect profitability, but Graham does not require a high ROE in this simplified lab. Burry can reject cash backing even when net income is positive and growing. The panel should preserve those disagreements rather than average them into a confidence score. A balance-sheet pass can coexist with a cash-conversion failure; a final-year improvement does not repair an every-year failure.

## Bull and bear
**Bull:** Positive and growing earnings, owner earnings and balance-sheet liquidity can support further research into durable AI infrastructure demand and competitive strength. The historical screen does not establish that future growth will continue or that the shares are cheap.
**Bear:** Cash conversion trails reported income in several years despite strong reported returns. Working-capital needs and an investment-cycle slowdown could weaken cash generation. These are scenarios requiring investigation, not findings of fraud or quantified forecasts.

## Honest gaps and scope
No current price was fetched: price is not found; intrinsic value, margin of safety and price target are not known. Unknowns do not become zero or pass. The included JPM robustness run also preserves absent classified current assets/current liabilities and allowed capex tags, so dependent liquidity and owner-earnings checks stay not known. Its standard bank reporting makes these industrial-company tests a poor fit. The baseline required-input gaps are listed in each facts_and_checks.json and printed_numbers.md. ROE uses ending equity to match the assignment. Owner earnings subtracts all reported capex, not a guessed maintenance portion. Each company uses its own latest annual fiscal periods, not artificially aligned calendar years.

## My Project 2 decision
**Only with a condition:** I would use the panel to prioritize research only after the SEC facts, missing-data treatment and thresholds are verified; valuation and sector-specific judgment must precede any buy or sell decision.

## Reproduction and evidence
- Run `python panel.py` to reproduce both baseline panels, the threshold probe and the JPM gap probe offline.
- Run `python validate.py` for cell-by-cell COST acceptance, sensitivity, gap preservation and deliberate unsupported-number probes across every persona.
- Run `python panel.py --audit-memos` to audit every saved memo. The audit is a numeric provenance guard, not a semantic fact checker.
- Full annual figures, source tags, accession numbers and filed dates: outputs/COST/printed_numbers.md and outputs/NVDA/printed_numbers.md.
- Original investor prompts and checksummed SEC downloads: evidence/raw/. Editable lab skills: skills/.
- Acceptance proof: evidence/validation.json. Memo audit: evidence/memo_audit.json.

## Sources
- [SEC COST company facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000909832.json)
- [SEC NVIDIA company facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json)
- [NVIDIA annual filing](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm)
- [Vanguard VT factsheet](https://fund-docs.vanguard.com/F3141.pdf)
- [Original Graham framework](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/ben_graham.md)
- The COST acceptance targets come from the assignment, plus the prior Lab 18 known-answer fixture. They are verification targets only.

Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.
