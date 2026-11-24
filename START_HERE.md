# Lab 18 submission folder

Sam Stewart — Buffett: code computes, model judges.

This folder contains the SEC-only skill, Python script, Streamlit app, known-answer fixture and verification tools. It does not include FAskills, paid-service configuration or API keys.

**Status:** the code and automated tests are prepared. Live COST/JPM acceptance, their verified model-written memos and the final trust decision remain pending. A real name and email are needed for the SEC User-Agent. The COST known-answer fixture is validation material, not downloaded evidence.

## Open the app

Open a terminal in this folder. With Python available:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On the original AIFinance2026 workspace, use the existing environment:

```powershell
..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8506 --server.showEmailPrompt false --browser.gatherUsageStats false
```

## Finish the evidence

Set `SEC_USER_AGENT` locally to your real name and email, then run:

```powershell
python warren-buffett-expert/scripts/buffett.py COST --refresh
python warren-buffett-expert/scripts/buffett.py JPM --refresh
python verify_acceptance.py
```

Use `..\.venv\Scripts\python.exe` instead of `python` to reuse the existing environment. No paid API keys are needed. New SEC requests require internet access; saved snapshots can be replayed with `--offline`.

Ask the AI assistant to read `warren-buffett-expert/SKILL.md`, use each company's actual `printed.txt`, and save `outputs/COST/memo.md` and `outputs/JPM/memo.md`. Each memo must judge the business without price data. JPM's memo must say it cannot judge owner earnings when capital spending is absent. Put the separate one-line trust decision in `outputs/COST/decision.md`; review an AI-drafted decision before submitting it.

The app displays the chart, table, three checks, memo and trust decision. Add `40.0%` to COST's memo to demonstrate the number flag, then remove the probe. The app does not generate a fresh model memo automatically.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit chart, table, three checks and memo-number audit |
| `warren-buffett-expert/SKILL.md` | Reusable workflow and exact assignment rules |
| `warren-buffett-expert/scripts/buffett.py` | SEC downloads, financial calculations and printed XBRL provenance |
| `verify_acceptance.py` | COST known-answer and JPM missing-data acceptance checks |
| `tests/` | Isolated rule/UI tests and the supplied COST expected values |
| `requirements.txt` | Dependency versions |
| `evidence/` | Test record; location for actual SEC snapshots and acceptance results |
| `outputs/` | Location for computed company outputs, memos and decisions |
| `MANIFEST.json` | File inventory and SHA-256 checksums |

Run the automated tests from this folder with `python -m unittest discover -s tests -v`. The UI test uses a temporary synthetic fixture, clearly separated from live acceptance.

The app disclosure is: data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.

Disclaimer: This tool is for educational and informational purposes only. It does not constitute financial advice, investment recommendations, or professional guidance of any kind. The analyses generated are AI-simulated perspectives and should not be used as the basis for any investment decisions. Always consult a qualified financial advisor before making investment decisions. Use at your own risk.
