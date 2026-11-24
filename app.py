"""Streamlit front end for the assignment's exact SEC-only Buffett rules."""
from datetime import date
import json
import os
from pathlib import Path
import sys
import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "warren-buffett-expert/scripts"))
from buffett import DISCLOSURE, DISCLAIMER, SEC, DataError, audit_memo, build, export, formatted, numeric, print_report

st.set_page_config(page_title="Buffett: code computes, model judges", layout="wide")
st.title("Buffett: code computes, model judges")
st.caption(DISCLOSURE)
with st.sidebar:
    with st.form("run"):
        ticker = st.text_input("Ticker", "COST").strip().upper()
        cutoff = st.date_input("Filings available by", date.today(), max_value=date.today())
        mode = st.selectbox("Data source mode", ["Saved SEC snapshot", "Live SEC download"])
        identity = st.text_input("SEC User-Agent: your name and email", os.getenv("SEC_USER_AGENT", ""))
        cik = st.text_input("Optional verified CIK", "", help="Only use if you independently know the CIK and SEC ticker lookup is blocked. This choice is recorded.")
        run = st.form_submit_button("Compute from 10-Ks", type="primary")
    st.caption("No price data. Latest eligible 10-K wins for each fiscal period. Saved mode does not access the network.")

if run:
    st.session_state.pop("report", None)
    try:
        with st.spinner("Reading SEC facts and computing…"):
            sec = SEC(HERE / "evidence/downloads", identity, offline=mode == "Saved SEC snapshot", refresh=mode == "Live SEC download")
            report = build(sec, ticker, cutoff.isoformat(), cik or None)
            export(report, HERE / "outputs" / ticker)
            st.session_state.report = report
            st.session_state.mode = mode
    except (DataError, ValueError, KeyError, OSError) as exc:
        st.error(str(exc))

if "report" not in st.session_state and not run:
    saved = HERE / "outputs/COST/evidence.json"
    if saved.exists():
        st.session_state.report = json.loads(saved.read_text(encoding="utf-8"))
        st.session_state.mode = "Included COST SEC snapshot"
if "report" not in st.session_state:
    st.info("Enter a ticker and compute its evidence. A real requester name and email are needed for new SEC downloads.")
    st.stop()

report = st.session_state.report
selected_ticker = report["ticker"]
folder = HERE / "outputs" / selected_ticker
st.subheader(f"{selected_ticker} — {report['company']}")
st.caption(f"{st.session_state.mode} · filing cutoff {report['filing_cutoff']} · amounts in $ millions")
chart = pd.DataFrame([{"FY end": r["fiscal_year_end"], "Owner earnings": r["owner_earnings"] / 1e6 if numeric(r["owner_earnings"]) else None, "Net income": r["net_income"] / 1e6 if numeric(r["net_income"]) else None} for r in report["rows"]]).set_index("FY end")
st.line_chart(chart, y_label="$ millions")
columns = {"revenue": "Revenue", "net_income": "Net income", "operating_cash_flow": "Operating cash flow", "capital_spending": "Capital spending", "equity": "Equity", "roe_percent": "ROE", "owner_earnings": "Owner earnings"}
st.dataframe([{"FY end": r["fiscal_year_end"], **{label: formatted(r[key], "roe" if key == "roe_percent" else "money") for key, label in columns.items()}} for r in report["rows"]], hide_index=True, width="stretch")
st.caption("ROE = net income ÷ year-end equity. Owner earnings = operating cash flow − capital spending. Missing facts: not found. Undefined ratios/checks: not known. Checks use full precision.")
st.subheader("Buffett's three checks")
st.dataframe([{"Check": check, "Result": outcome} for check, outcome in report["checks"].items()], hide_index=True, width="stretch")

st.subheader("Model-written memo: judge the business")
memo_path = folder / "memo.md"
saved_memo = memo_path.read_text(encoding="utf-8") if memo_path.exists() else ""
memo = st.text_area("Memo — edit or paste the model's text", saved_memo, height=210, key="memo_" + selected_ticker)
if not memo.strip():
    st.info("A model-written memo is pending. Run the skill on this ticker, then save memo.md beside evidence.json or paste it here. The app does not pretend a model has reviewed a new company.")
else:
    st.markdown(memo)
    flagged = audit_memo(memo, print_report(report))
    if flagged:
        st.error("Numbers not printed by the script: " + ", ".join(flagged))
    else:
        st.success("Every number in this memo was printed by the script.")
    st.caption("This checks exact numeric tokens, including dates and percentages. It cannot prove a number is used in the right context or validate the model's judgment.")
    if selected_ticker == "JPM" and all(not numeric(r["owner_earnings"]) for r in report["rows"]) and "cannot judge owner earnings" not in memo.lower():
        st.warning("JPM memo must say it cannot judge owner earnings because capital spending was not found.")
    st.download_button("Download memo as Markdown", memo, file_name=f"{selected_ticker}_memo.md", mime="text/markdown")

decision_file = folder / "decision.md"
decision = decision_file.read_text(encoding="utf-8").strip() if decision_file.exists() else "Decision pending — review the evidence and state whether you trust the verdict."
st.write(decision)
st.caption("The included decision is an AI-assisted draft for your review.")

with st.expander("Script printout, XBRL tags and source receipts"):
    printed = print_report(report)
    st.code(printed, language="text")
    st.json(report.get("receipts", []), expanded=False)
    st.download_button("Download the script printout", printed, file_name=f"{selected_ticker}_printed.txt")
    st.download_button("Download evidence JSON", json.dumps(report, indent=2), file_name=f"{selected_ticker}_evidence.json", mime="application/json")
st.caption(DISCLAIMER)
