# Lab 19 - Sam Stewart

**Open [SUBMISSION.html](SUBMISSION.html) for the finished individual submission.** [SUBMISSION.md](SUBMISSION.md) is the same report in plain text. The ZIP contains the entire reproducible folder.

The report includes the COST known-answer reproduction, editable threshold probe, NVIDIA panel for VT's largest company, all investor memos, bull and bear, preserved gaps, and the Project 2 trust decision.

From this folder, using Python 3.10 or newer:

```powershell
python panel.py
python validate.py
python panel.py --audit-memos
```

These commands run offline using saved SEC snapshots and require only Python's standard library. `panel.py` prints the full financial tables, thresholds and checks; the same output is saved beside each memo. `validate.py` independently checks the expected answers, real JPM gaps and deliberate unsupported-number injections in all three personas.

In the existing course workspace, Python is available through the virtual environment. From the AIFinance2026 root use:

```powershell
.\.venv\Scripts\python.exe .\Lab19_Submission\panel.py
.\.venv\Scripts\python.exe .\Lab19_Submission\validate.py
```

For a separate sensitivity run:

```powershell
python panel.py --graham-current-ratio 1.0 --output probe_outputs
```

Alternatively edit `skills/ben-graham-expert/rules.json` from 2.0 to 1.0. The baseline submission retains 2.0 and explains why under Graham's memo. The saved `outputs/COST_threshold_probe` already demonstrates the looser rule. Restore 2.0 before running baseline acceptance.

Files worth inspecting:

- `evidence/validation.json`: cell-by-cell COST comparisons and behavior checks.
- `evidence/memo_audit.json`: the number flag applied to every saved baseline and probe memo.
- `outputs/COST/printed_numbers.md`: calculated COST figures and SEC tags/accessions.
- `outputs/NVDA/`: company facts, panel, and all three memos.
- `outputs/JPM/`: a real bank gap probe, explicitly separate from the selected company.
- `skills/`: compact lab-specific investor skills and machine-readable thresholds.
- `evidence/raw/`: original SEC snapshots, investor source prompts and Vanguard factsheet, with checksum receipts.

The broader original investor prompts are reference material. The executed rules are the assignment's eight simplified checks, documented in the included lab skills. These are AI-assisted simulated perspectives sharing one fact engine, not three independent live model calls. No fabricated prices, targets, partner comments or user actions are included.

Source refresh is optional and requires `requests`: `python download_sources.py`. The one-time factsheet text extraction used `pypdf`; rerunning the panel does not require it. The original fund-holdings N-PORT index request returned HTTP 403; the successful primary Vanguard factsheet supplies the holdings evidence instead. Failed downloads are recorded honestly in `evidence/source_manifest.json`.
