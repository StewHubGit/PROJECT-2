# My robo-advisor

From this repository folder, open the main app and select **Personal
robo-advisor — Rule B** in the sidebar:

```powershell
python -m pip install -r requirements-app.txt
python -m streamlit run app.py
```

You can also run `python -m streamlit run robo_app.py` directly. This app
does not install or import the matvix90 repository, call an LLM, or require keys.
The design follows its questionnaire → allocation → checks flow.

Sam selected **option B, the age-based rule**, from AI-proposed options on
November 23, 2026. Codex implemented the selected rule; this records a choice
of an AI-proposed rule and does not claim Sam originated its formula.

1. If the horizon is one year or less, or money may be needed within one year,
   use **100% cash**, overriding the other steps.
2. Otherwise stocks start at **100 − age percent**, bounded between 0% and 80%.
3. Cash is **20%** without an emergency fund or if money may be needed within
   three years; otherwise **10%**. These conditions are not additive.
4. A reaction of **sell all** caps stocks at **20%**; **sell some** caps them at
   **40%**. Hold/buy more leaves the starting stock share unchanged. A cap never
   increases stocks.
5. Bonds take the remainder so stocks, bonds and cash total **100%**.

The maximum acceptable loss is tested independently against history; a failure
does not automatically retune the rule. Initial investment only scales dollars.
At the default age of 35, ten-year horizon, money needed in 5–10 years,
emergency fund and hold reaction, the app calculates **65/25/10** on **$100,000**.
Enable **Override allocation by hand** for the supplied **60/40/0** acceptance
case or another allocation; all three weights are editable and must total 100%.

Both public data sources are downloaded on **every Streamlit rerun** without
caching or a local fallback. Download or data-validation failures withhold
results. The historical window must have exactly 432 months, January 1990 to
December 2025. December 1989 GS10 seeds January's bond return. Only six-digit
YYYYMM French rows are parsed. The portfolio rebalances monthly.

The loss check and exhaustive 10% stock grid are code. The grid fixes the active
allocation's cash share and assigns the remainder to bonds. It checks every
feasible candidate rather than assuming that more stocks always means more
historical loss. A passing historical screen cannot ensure a future loss limit.

GS10 is a nominal Treasury yield; "real yields" in the brief is interpreted as
real observed data, not inflation-adjusted TIPS yields. The bond return follows
the supplied constant-ten-year par-bond approximation, **not a published bond
index**. No transaction costs, tax, or advisory fees are included.

Run the deterministic unit tests and the separately requested live acceptance
checks:

```powershell
python -m unittest test_robo_app -v
python test_robo_app.py --live
python -m unittest test_robo_ui -v
```

The live acceptance run writes source snapshots, SHA-256 hashes, and the result
to `tmp/robo_validation/acceptance.json`. Those files support verification only;
the app always downloads live sources. The supplied 60/40 statistics allow
0.1 percentage point for revisions; all four allocation probes and their dates
must match. The supplied benchmark is a disclosed acceptance test, not a new
AI-off prediction exercise.

The packaged November 23 verification snapshots in `validation/robo/` support
offline app interaction tests. The live app never reads those snapshots.

Verified against fresh downloads on November 23, 2026:

| 60/40/0 result | Observed |
| --- | --- |
| Months | 432 |
| CAGR | 8.8806% |
| Volatility | 9.3793% |
| Max drawdown | −28.3970% |
| Worst 12 months | −24.4145%, ended February 2009 |
| Worst 12-month dollars on $100,000 | −$24,415 |

All four allocation probes pass: 50% stocks at a 20% loss limit with no cash;
no mix at 15% with no cash; 30% stocks at 15% with 20% cash; no mix at 15%
with 10% cash. Bonds alone return −16.8726% in their worst 12 months, ended
October 2022. Fourteen calculation tests and five app interaction tests also
pass, including the selected rule, its boundaries, the cash override and manual
override switching.

Design after matvix90/ai-robo-advisor (MIT). Data: Ken French Data Library; FRED, Federal Reserve Bank of St. Louis. Education, not investment advice.
