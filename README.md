**AI use:** I used OpenAI Codex to help implement the apps, check calculations, assemble evidence, and draft the memo and video scripts.

**Ownership statement — pending Sam's review and confirmation:** “The analysis and the decision are mine; education, not investment advice.”

# Project 2 — Meridian decision and robo-advisor

**Prepared locally; submission incomplete.** GitHub publication, a genuine AI-off prediction committed before its run, YouTube recordings with enabled transcripts, and personal ownership confirmation remain pending. See the [manifest](SUBMISSION_MANIFEST.md) and [validation and AI use](docs/validation-and-ai-use.md).

**Recommendation: REDESIGN; $0 live capital.** The frozen Meridian candidate is 65% SGOV / 35% VT. Its 6.58% annualized arithmetic estimate falls to 6.33% after an assumed 25 bp annual cost, below the 6.50% planning hurdle. These historical estimates do not establish the actual five-year CPI+4 objective.

## Start and operate the web app

You need **Python 3.12 or newer**, a terminal, and a browser. Download this repository's ZIP from GitHub and extract it, or clone it. Open a terminal in the folder containing this README and `app.py`.

```console
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```console
source .venv/bin/activate
```

Install the dependencies and start the app:

```console
python -m pip install -r requirements-app.txt
python -m streamlit run app.py
```

Open the **Local URL** printed in the terminal, usually `http://localhost:8501`. Keep the terminal running. Press Ctrl+C there to stop the app. If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` in place of `python` for the install/start commands. Use `python3` for the initial command on systems that name Python that way. No sibling coursework folders or API keys are needed.

The sidebar **App mode** has two choices:

| Mode | Operate it | What it establishes |
| --- | --- | --- |
| **Meridian mandate — Project 2** (default) | Compare the constrained portfolio with equal weight and 60/40; read each rule-specific verdict. Change estimates, cost, window or reserve. Uncheck required vintage availability to halt allocation calculations. | Lab 13 decision, baselines, four stress dimensions, saved-vintage signal and process controls. Included source snapshots; no network after installation. |
| **Personal robo-advisor — Rule B** | Answer the questionnaire. Rule B calculates weights; enable manual override for 60/40/0 on $100,000. Inspect the loss flag, grid and chart. | A separate US stocks/Treasury approximation/cash extension; fresh French/FRED downloads on every rerun. Requires internet; errors withhold results. |

The personal mode does not replace Meridian's global ETF universe, annual rebalancing policy or payout mandate. Its monthly-rebalanced 1990–2025 returns are a different experiment. [Selected rule and calculations](ROBO_README.md).

## Mandate, baselines, signal and stresses

- **Objective:** $100m Meridian case; seven-year horizon; $0.75m quarterly payouts; rolling five-year CPI+4% net objective. 6.50% is a planning proxy using 2.50% CPI.
- **Universe/benchmark:** SGOV, IEF, BND, VT; 60% VT / 40% BND reference.
- **Risk/limits:** annualized sample volatility; long-only, fully invested; 3% reserve, 90% five-day liquidity, nonexempt issuer cap 8%, annual turnover at most 25% without approval. S9's calendar-year 10% loss definition/response remain unresolved. [Original mandate](labs/13_15_portfolio/Lab_13_Meridian_Mandate.md).
- **Baselines:** equal weight and 60/40, plus inverse volatility, share the portfolio's current estimates, cost and mandate screen. Every row identifies PASS/FAIL and the modeled rule. Full mandate conditions remain unresolved.
- **Signal:** saved 2026-09-30 DGS10 vintage; 20-observation change through 2026-09-29 is +51 bp for a proposed 2026-10-01 review. Historical context/data-admission gate; does not set weights. [Data card](docs/DATA_CARD.md).
- **Disclosed stresses:** VT mean −1 point; 60 versus 36 months; cost 25 versus 0 bp; reserve 3% versus 70%. Missing vintage halts calculations; infeasibility or failed net hurdle blocks use. These known demonstrations do not qualify as a new AI-off test.

## Decision and evidence

[Decision memo](docs/decision-memo.md) · [Validation, AI use and Locked Changed-Input Record](docs/validation-and-ai-use.md) · [Frozen results](results/RESULTS.md) · [Requirement audit](REQUIREMENTS_AUDIT.md).

Live range: **0%–0% ($0–$0)**. Conditional shadow range: **$0–$1m notional**, no actual funding, for a separately approved 12-month operational protocol. Written objective/loss rules, documented costs and a preregistered point-in-time process are required first. Monitor sources, vintages, reserve, costs, turnover and exceptions. Stop on a missing vintage, unexplained mismatch, reserve breach, unapproved turnover or approved loss breach. Twelve months cannot validate a rolling five-year return objective.

Reproduce frozen evidence separately from the app:

```console
python run.py
```

This offline runner is supporting evidence, not the submitted app. Tests:

```console
python tools/check_app.py
python -m unittest test_robo_app test_robo_ui -v
```

Repeat the disclosed personal acceptance benchmarks with fresh downloads:

```console
python test_robo_app.py --live
```

The supplied benchmark reproduces 432 months, 8.88% CAGR, 9.38% volatility, −28.40% drawdown and −24.41% worst 12 months ending February 2009. All four stock/cash probes passed. [Verification](validation/robo/acceptance.json).

## Finish the actual submission

[Step-by-step AI-off handoff and recording guide](FINISH_AND_RECORD.md), with
blank prediction/result worksheets and screen directions for all three videos.

1. Publish this folder's contents to your own GitHub repository.
2. Follow the [AI-off protocol](validation/AI_OFF_PRECOMMIT_PROTOCOL.md): close AI, choose an unrun single change, write and commit your own prediction on GitHub, then run it once and commit the result later. No disclosed benchmark or replay qualifies. Currently **PENDING**.
3. Review the recommendation and confirm the ownership statement before using it in final documents/recordings.
4. Record the three [video scripts](videos/README.md), with Video 3 opening on the app running live. Upload to YouTube, enable/publish transcripts, verify links and attach/link matched transcripts in the repo.
5. Set real delivery locations in `delivery.json`; run `python tools/prepare_delivery.py`. Verify published links. Manifest locations must be GitHub links except for the three YouTube links.
6. Attach the same `docs/decision-memo.md` and `docs/validation-and-ai-use.md` files to Brightspace with the manifest. Matching copies are generated beside this repository in `Project2_Brightspace_Attachments`.

Personal-extension design after [matvix90/ai-robo-advisor](https://github.com/matvix90/ai-robo-advisor) (MIT); the repository was not installed. Allocation and checks are code. Revised French/GS10 history is not a point-in-time backtest or a published bond total-return index.

## Video links and actual transcripts

[Video links and matched transcripts](videos/VIDEO_LINKS_AND_TRANSCRIPTS.md). Add the three real YouTube links and actual transcripts before submission.
