"""Lab 19: one SEC fact set, three explicit investor rubrics, no inferred facts.

Default execution is offline. Expected answers are imported only by validate.py.
"""
from __future__ import annotations
import argparse
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
RAW = HERE / 'evidence' / 'raw'
NOT_FOUND, NOT_KNOWN = 'not found', 'not known'
TAGS = {
    'revenue': ['RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues'],
    'net_income': ['NetIncomeLoss'],
    'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities'],
    'capital_spending': ['PaymentsToAcquirePropertyPlantAndEquipment', 'PaymentsToAcquireProductiveAssets'],
    'equity': ['StockholdersEquity'],
    'liabilities': ['Liabilities'],
    'current_assets': ['AssetsCurrent'],
    'current_liabilities': ['LiabilitiesCurrent'],
}
FLOWS = {'revenue', 'net_income', 'operating_cash_flow', 'capital_spending'}
INVESTORS = ['Buffett', 'Graham', 'Burry']
NUMBERS = re.compile(r'(?<![A-Za-z])(?:\d{4}-\d{2}-\d{2}|[-+]?\$?\d+(?:,\d{3})*(?:\.\d+)?%?)')

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False), encoding='utf-8')

def number(x):
    return type(x) in (int, float) and math.isfinite(x)

def fmt(x, kind='money'):
    if not number(x):
        return str(x)
    v = Decimal(str(x))
    if kind == 'money':
        v /= Decimal(1000000)
        return f'{v:,.0f}' if v == v.to_integral() else f'{v:,.3f}'
    places = '0.1' if kind == 'percent' else '0.01'
    return str(v.quantize(Decimal(places), rounding=ROUND_HALF_UP)) + ('%' if kind == 'percent' else '')

def annual(item):
    if not item.get('start'):
        return False
    return (date.fromisoformat(item['end']) - date.fromisoformat(item['start'])).days + 1 in {364, 365, 366, 371}

def eligible(item, cutoff, flow):
    return (item.get('form') == '10-K' and item.get('filed', '9999') <= cutoff
            and item.get('end', '9999') <= cutoff and number(item.get('val'))
            and (annual(item) if flow else not item.get('start')))

def select_fact(data, metric, end, cutoff):
    candidates = []
    for priority, tag in enumerate(TAGS[metric]):
        items = data.get('facts', {}).get('us-gaap', {}).get(tag, {}).get('units', {}).get('USD', [])
        for item in items:
            if item.get('end') == end and eligible(item, cutoff, metric in FLOWS):
                candidates.append((item, priority, tag))
    if not candidates:
        return {'value': NOT_FOUND, 'tag': NOT_FOUND, 'reason': 'No eligible USD 10-K fact under the documented tags.'}
    newest = max((x[0]['filed'], x[0].get('accn', '')) for x in candidates)
    candidates = [x for x in candidates if (x[0]['filed'], x[0].get('accn', '')) == newest]
    best = min(x[1] for x in candidates)
    candidates = [x for x in candidates if x[1] == best]
    contexts = {(x[0].get('start'), x[0]['val']) for x in candidates}
    if len(contexts) != 1:
        return {'value': NOT_FOUND, 'tag': candidates[0][2], 'reason': 'Conflicting contexts; no selection by guess.'}
    item, _, tag = candidates[0]
    return {'value': item['val'], 'tag': tag, 'unit': 'USD', 'start': item.get('start', NOT_FOUND),
            'end': end, 'filed': item['filed'], 'accession': item.get('accn', NOT_FOUND)}

def every(values, predicate):
    if len(values) != 5 or any(not number(v) for v in values):
        return NOT_KNOWN
    return 'pass' if all(predicate(v) for v in values) else 'fail'

def grew(rows, field):
    if len(rows) != 5 or not number(rows[0][field]) or not number(rows[-1][field]):
        return NOT_KNOWN
    return 'pass' if rows[-1][field] > rows[0][field] else 'fail'

def ratio(a, b, percent=False):
    return a / b * (100 if percent else 1) if number(a) and number(b) and b > 0 else NOT_KNOWN

def load_rules(root=HERE / 'skills'):
    rules = {}
    for key in ['warren-buffett-expert', 'ben-graham-expert', 'michael-burry-expert']:
        rules.update(read_json(root / key / 'rules.json'))
    return rules

def compute(data, ticker, cutoff, rules):
    ni = data.get('facts', {}).get('us-gaap', {}).get('NetIncomeLoss', {}).get('units', {}).get('USD', [])
    ends = sorted({x['end'] for x in ni if eligible(x, cutoff, True)})[-5:]
    if not ends:
        raise ValueError(f'{ticker}: no eligible annual 10-K net income facts.')
    rows = []
    for end in ends:
        inputs = {k: select_fact(data, k, end, cutoff) for k in TAGS}
        values = {k: v['value'] for k, v in inputs.items()}
        cfo, capex = values['operating_cash_flow'], values['capital_spending']
        oe = cfo - capex if number(cfo) and number(capex) else NOT_FOUND
        ni_value = values['net_income']
        gap = cfo - ni_value if number(cfo) and number(ni_value) else NOT_FOUND
        rows.append({'fiscal_year_end': end, **values, 'owner_earnings': oe,
                     'roe_percent': ratio(ni_value, values['equity'], True),
                     'current_ratio': ratio(values['current_assets'], values['current_liabilities']),
                     'liabilities_to_equity': ratio(values['liabilities'], values['equity']),
                     'ocf_minus_net_income': gap, 'inputs': inputs})
    last = rows[-1]
    checks = {
        'Buffett': {
            f"ROE of {rules['roe_min_percent']:g}% or more every year": every([r['roe_percent'] for r in rows], lambda v: v >= rules['roe_min_percent']),
            'Owner earnings positive every year': every([r['owner_earnings'] for r in rows], lambda v: v > 0),
            'Owner earnings grew, first year to last': grew(rows, 'owner_earnings'),
        },
        'Graham': {
            f"Current ratio of {rules['current_ratio_min']:.1f} or more, latest year": NOT_KNOWN if not number(last['current_ratio']) else 'pass' if last['current_ratio'] >= rules['current_ratio_min'] else 'fail',
            'Net income positive every year': every([r['net_income'] for r in rows], lambda v: v > 0),
            'Net income grew, first year to last': grew(rows, 'net_income'),
        },
        'Burry': {
            'Operating cash flow at least net income every year': every([r['ocf_minus_net_income'] for r in rows], lambda v: v >= 0),
            f"Liabilities no more than {rules['liabilities_equity_max']:g} times equity, latest year": NOT_KNOWN if not number(last['liabilities_to_equity']) else 'pass' if last['liabilities_to_equity'] <= rules['liabilities_equity_max'] else 'fail',
        },
    }
    scores = {who: {'passed': list(v.values()).count('pass'), 'failed': list(v.values()).count('fail'),
                    'not_known': list(v.values()).count(NOT_KNOWN), 'total': len(v),
                    'verdict': NOT_KNOWN if NOT_KNOWN in v.values() else 'pass' if all(x == 'pass' for x in v.values()) else 'fail'}
              for who, v in checks.items()}
    gaps = [{'period': r['fiscal_year_end'], 'field': k, 'status': r[k],
             'reason': r['inputs'][k].get('reason', '')} for r in rows for k in TAGS if not number(r[k])]
    return {'ticker': ticker, 'company': data.get('entityName', ticker), 'cik': data.get('cik'),
            'asof': cutoff, 'rules': rules, 'rows': rows, 'checks': checks, 'scores': scores, 'gaps': gaps}

def print_report(report):
    lines = [f"# {report['ticker']} | {report['company']}", f"Filing cutoff: {report['asof']}",
             'USD millions unless a ratio or percentage is labeled. Calculations use unrounded USD facts.',
             'ROE = net income / fiscal-year-end equity; owner earnings proxy = operating cash flow - capital spending.',
             'Current ratio = current assets / current liabilities; liabilities/equity uses total liabilities, not debt.',
             '', '| FY end | Revenue | Net income | OCF | Capex | Equity | Current assets | Current liabilities | Liabilities | ROE | Owner earnings | Current ratio | Liabilities/equity | OCF minus NI |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    fields = ['revenue', 'net_income', 'operating_cash_flow', 'capital_spending', 'equity', 'current_assets',
              'current_liabilities', 'liabilities', 'roe_percent', 'owner_earnings', 'current_ratio', 'liabilities_to_equity', 'ocf_minus_net_income']
    for r in report['rows']:
        lines.append('| ' + r['fiscal_year_end'] + ' | ' + ' | '.join(fmt(r[k], 'percent' if k == 'roe_percent' else 'ratio' if k in ['current_ratio', 'liabilities_to_equity'] else 'money') for k in fields) + ' |')
    lines += ['', '| Investor | Check | Result |', '|---|---|---|']
    for who, checks in report['checks'].items():
        lines += [f'| {who} | {check} | {value} |' for check, value in checks.items()]
    for who, score in report['scores'].items():
        lines.append(f"{who}: {score['passed']} of {score['total']} passed; {score['failed']} failed; {score['not_known']} not known. Verdict: {score['verdict']}.")
    rules = report['rules']
    lines += [f"Thresholds: ROE {rules['roe_min_percent']:.1f}%; current ratio {rules['current_ratio_min']:.1f}; liabilities/equity {rules['liabilities_equity_max']:.1f}.",
              'Interpretation: 5 annual observations required. A missing required input stays not found; its dependent check stays not known.',
              'Valuation: current price not found; intrinsic value not known; margin of safety not known; price target not known.',
              'Revenue-recognition fraud: not known; these eight checks cannot establish fraud.', '', '## Source provenance']
    for r in report['rows']:
        lines.append(r['fiscal_year_end'])
        for field, item in r['inputs'].items():
            lines.append(f"- {field}: {item['tag']}; filed {item.get('filed', NOT_FOUND)}; accession {item.get('accession', NOT_FOUND)}; {item.get('reason', 'USD, exact fiscal period')}.")
    lines += ['', '## Missing-input register']
    lines += [f"- {g['period']} {g['field']}: {g['status']}; {g['reason']}" for g in report['gaps']] or ['- No required raw-input gaps found in this extraction.']
    return '\n'.join(lines) + '\n'

def memo(report, investor):
    rows, score = report['rows'], report['scores'][investor]
    first, last = rows[0], rows[-1]
    head = [f"# {report['ticker']} - {investor} memo", 'AI-assisted simulated perspective; not the actual investor or an independent analyst vote.',
            f"Screen verdict: {score['verdict']}; {score['passed']} of {score['total']} checks pass, {score['failed']} fail, {score['not_known']} not known."]
    if investor == 'Buffett':
        lowest = min((r['roe_percent'] for r in rows if number(r['roe_percent'])), default=NOT_KNOWN)
        body = (f"The lowest observed ROE is {fmt(lowest, 'percent')}, against the {report['rules']['roe_min_percent']:.1f}% rule. "
                f"Owner earnings proxy moves from {fmt(first['owner_earnings'])} to {fmt(last['owner_earnings'])} million. "
                'I favor durable cash generation, but OCF less all capex is a simplified proxy, not a maintenance-capex estimate. '
                'A strong final year cannot erase a failed earlier year. A screen pass would justify deeper moat and management work, not a purchase.')
    elif investor == 'Graham':
        body = (f"Latest current ratio is {fmt(last['current_ratio'], 'ratio')} versus the {report['rules']['current_ratio_min']:.1f} minimum. "
                f"Net income moves from {fmt(first['net_income'])} to {fmt(last['net_income'])} million. "
                'I place more weight on a liquid balance sheet and earnings stability than on a compelling growth narrative. '
                'These assignment checks are a simplified adaptation, not the complete historical defensive-investor framework. '
                'A margin of safety still requires a separately verified price and valuation.')
    else:
        bad = [r['fiscal_year_end'] for r in rows if number(r['ocf_minus_net_income']) and r['ocf_minus_net_income'] < 0]
        body = (f"Latest OCF is {fmt(last['operating_cash_flow'])} against net income of {fmt(last['net_income'])} million; "
                f"the difference is {fmt(last['ocf_minus_net_income'])} million. Latest liabilities/equity is {fmt(last['liabilities_to_equity'], 'ratio')}. "
                + ('OCF trails income in these fiscal years: ' + ', '.join(bad) + '. ' if bad else 'No known annual OCF shortfall was found. ')
                + 'I would reconcile working capital, noncash items and recurring earnings before calling the divergence aggressive accounting. '
                'A failed cash test is a research question, not proof of fraud or a short recommendation.')
    head += ['', body, '', 'Known limits: current price not found; intrinsic value not known; margin of safety not known; price target not known. '
             'Missing required inputs remain not found, with dependent checks not known.']
    if investor == 'Graham':
        head += ['', f"Threshold kept: {report['rules']['current_ratio_min']:.1f}; retain the conservative baseline for comparability, and show the looser threshold only as a sensitivity probe."]
    return '\n'.join(head) + '\n'

def audit_text(memo_text, printed):
    def normalize(t):
        return t.replace('$', '').replace(',', '').lstrip('+')
    allowed = {normalize(m.group()) for m in NUMBERS.finditer(printed)}
    return sorted({m.group() for m in NUMBERS.finditer(memo_text) if normalize(m.group()) not in allowed})

def audit_all(root):
    audits = []
    for path in sorted(Path(root).rglob('*_memo.md')):
        printed = path.parent / 'printed_numbers.md'
        unsupported = audit_text(path.read_text(encoding='utf-8'), printed.read_text(encoding='utf-8')) if printed.exists() else ['printed evidence not found']
        audits.append({'memo': str(path.relative_to(root)), 'unsupported_numbers': unsupported, 'pass': not unsupported})
    return {'memos_checked': len(audits), 'all_pass': bool(audits) and all(a['pass'] for a in audits), 'audits': audits}

def export(report, directory):
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / 'facts_and_checks.json', report)
    printed = print_report(report)
    (directory / 'printed_numbers.md').write_text(printed, encoding='utf-8')
    for who in INVESTORS:
        (directory / (who.lower() + '_memo.md')).write_text(memo(report, who), encoding='utf-8')
    return printed

def table(report):
    out = ['| Investor | Check | Result |', '|---|---|---|']
    for who, checks in report['checks'].items():
        out += [f'| {who} | {check} | {value} |' for check, value in checks.items()]
    return '\n'.join(out)

def build_submission(reports, probe, selection):
    cost, company = reports['COST'], reports['NVDA']
    lines = ['# Lab 19 - Same facts, different investor rules', 'Sam Stewart | Individual submission | Prepared with AI assistance',
             '', '## What the panel is and why it disagrees',
             'The panel applies separate Buffett, Graham and Burry skill instructions to one shared set of annual SEC facts. '
             'Buffett emphasizes returns and owner earnings, Graham emphasizes liquidity and earnings stability, and Burry emphasizes cash backing and leverage. '
             'Different verdicts arise from different predicates and thresholds, not from giving each persona different financial statements. '
             'The calculation and memo pipeline is deterministic and AI-assisted; these are simulated perspectives, not three independent live model calls or the actual investors.',
             '', '## COST: reproduce the known answer',
             'The engine calculates actual SEC facts before the separate acceptance script reads the instructor answer key. No expected value enters the extraction or checks.',
             '', '| FY end | Current ratio | Liabilities/equity |', '|---|---:|---:|']
    lines += [f"| {r['fiscal_year_end']} | {fmt(r['current_ratio'], 'ratio')} | {fmt(r['liabilities_to_equity'], 'ratio')} |" for r in cost['rows']]
    lines += ['', table(cost)]
    for who, s in cost['scores'].items():
        lines += [f"{who}: {s['passed']} of {s['total']}; verdict {s['verdict']}."]
    lines += ['', '## Threshold probe',
              f"The probe changes only Graham's current-ratio rule from {cost['rules']['current_ratio_min']:.1f} to {probe['rules']['current_ratio_min']:.1f}. "
              f"At the unchanged COST ratio of {fmt(cost['rows'][-1]['current_ratio'], 'ratio')}, Graham moves from "
              f"{cost['scores']['Graham']['passed']} of {cost['scores']['Graham']['total']} to {probe['scores']['Graham']['passed']} of {probe['scores']['Graham']['total']}: verdict {probe['scores']['Graham']['verdict']}. "
              'That is a changed policy, not new company evidence. The saved baseline skill retains the stricter rule.',
              '', '## Fund and company selection', selection,
              '', '## NVIDIA: same facts, three verdicts', table(company)]
    for who, s in company['scores'].items():
        lines += [f"{who}: {s['passed']} of {s['total']}; {s['not_known']} not known; verdict {s['verdict']}."]
    lines += ['', '## Investor memos']
    for who in INVESTORS:
        lines += ['', memo(company, who).replace('# ', '### ', 1)]
    lines += ['', '## Where they agree and split',
              'They share the same reported history. Buffett and Graham both inspect profitability, but Graham does not require a high ROE in this simplified lab. '
              'Burry can reject cash backing even when net income is positive and growing. The panel should preserve those disagreements rather than average them into a confidence score. '
              'A balance-sheet pass can coexist with a cash-conversion failure; a final-year improvement does not repair an every-year failure.',
              '', '## Bull and bear',
              '**Bull:** Positive and growing earnings, owner earnings and balance-sheet liquidity can support further research into durable AI infrastructure demand and competitive strength. '
              'The historical screen does not establish that future growth will continue or that the shares are cheap.',
              '**Bear:** Cash conversion trails reported income in several years despite strong reported returns. '
              'Working-capital needs and an investment-cycle slowdown could weaken cash generation. These are scenarios requiring investigation, not findings of fraud or quantified forecasts.',
              '', '## Honest gaps and scope',
              'No current price was fetched: price is not found; intrinsic value, margin of safety and price target are not known. '
              'Unknowns do not become zero or pass. The included JPM robustness run also preserves absent classified current assets/current liabilities and allowed capex tags, '
              'so dependent liquidity and owner-earnings checks stay not known. Its standard bank reporting makes these industrial-company tests a poor fit. '
              'The baseline required-input gaps are listed in each facts_and_checks.json and printed_numbers.md. '
              'ROE uses ending equity to match the assignment. Owner earnings subtracts all reported capex, not a guessed maintenance portion. '
              'Each company uses its own latest annual fiscal periods, not artificially aligned calendar years.',
              '', '## My Project 2 decision',
              '**Only with a condition:** I would use the panel to prioritize research only after the SEC facts, missing-data treatment and thresholds are verified; valuation and sector-specific judgment must precede any buy or sell decision.',
              '', '## Reproduction and evidence',
              '- Run `python panel.py` to reproduce both baseline panels, the threshold probe and the JPM gap probe offline.',
              '- Run `python validate.py` for cell-by-cell COST acceptance, sensitivity, gap preservation and deliberate unsupported-number probes across every persona.',
              '- Run `python panel.py --audit-memos` to audit every saved memo. The audit is a numeric provenance guard, not a semantic fact checker.',
              '- Full annual figures, source tags, accession numbers and filed dates: outputs/COST/printed_numbers.md and outputs/NVDA/printed_numbers.md.',
              '- Original investor prompts and checksummed SEC downloads: evidence/raw/. Editable lab skills: skills/.',
              '- Acceptance proof: evidence/validation.json. Memo audit: evidence/memo_audit.json.',
              '', '## Sources',
              '- [SEC COST company facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000909832.json)',
              '- [SEC NVIDIA company facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json)',
              '- [NVIDIA annual filing](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm)',
              '- [Vanguard VT factsheet](https://fund-docs.vanguard.com/F3141.pdf)',
              '- [Original Graham framework](https://github.com/CinderZhang/FAskills/blob/main/financial-researcher/experts/ben_graham.md)',
              '- The COST acceptance targets come from the assignment, plus the prior Lab 18 known-answer fixture. They are verification targets only.',
              '', 'Data from SEC EDGAR; built with AI help, a learning demonstration, not investment advice.']
    return '\n'.join(lines) + '\n'

def simple_html(markdown):
    """Small dependency-free renderer for this report's paragraphs, tables and lists."""
    def inline(s):
        s = html.escape(s)
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    out, intable, inlist = [], False, False
    for line in markdown.splitlines():
        if not line.startswith('|') and intable:
            out.append('</tbody></table></div>'); intable = False
        if not line.startswith('- ') and inlist:
            out.append('</ul>'); inlist = False
        if line.startswith('|'):
            cells = [x.strip() for x in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-+:?', c) for c in cells):
                continue
            if not intable:
                out.append('<div class="table"><table><thead><tr>' + ''.join('<th>'+inline(c)+'</th>' for c in cells) + '</tr></thead><tbody>'); intable = True
            else:
                out.append('<tr>' + ''.join('<td>'+inline(c)+'</td>' for c in cells) + '</tr>')
        elif line.startswith('#'):
            level = min(len(line) - len(line.lstrip('#')), 4)
            out.append(f'<h{level}>'+inline(line.lstrip('# '))+f'</h{level}>')
        elif line.startswith('- '):
            if not inlist: out.append('<ul>'); inlist = True
            out.append('<li>'+inline(line[2:])+'</li>')
        elif line.strip():
            out.append('<p>'+inline(line)+'</p>')
    if intable: out.append('</tbody></table></div>')
    if inlist: out.append('</ul>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sam Stewart - Lab 19</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 25px;color:#17283a;background:#fafbfd}h1,h2,h3{color:#153c5b;line-height:1.3}h2{border-bottom:2px solid #d9e3ec;padding-bottom:8px;margin-top:40px}.table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px;background:white}td,th{padding:9px 12px;border:1px solid #d9e3ec;text-align:left}th{background:#eaf0f5}a{color:#145d91}code{background:#eaf0f5;padding:2px 4px}@media print{body{margin:0;max-width:none;background:white}h2,h3{break-after:avoid}tr{break-inside:avoid}}</style><body>' + '\n'.join(out) + '</body></html>'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--asof', default='2026-11-05')
    p.add_argument('--audit-memos', action='store_true', help='Audit all saved investor memos; exit nonzero for unsupported numbers.')
    p.add_argument('--graham-current-ratio', type=float, help='Override only Graham current-ratio threshold for an explicit sensitivity run.')
    p.add_argument('--output', type=Path, default=HERE / 'outputs')
    a = p.parse_args()
    date.fromisoformat(a.asof)
    if a.audit_memos:
        result = audit_all(a.output)
        write_json(HERE / 'evidence' / 'memo_audit.json', result)
        print(json.dumps(result, indent=2))
        return 0 if result['all_pass'] else 1
    rules = load_rules()
    if a.graham_current_ratio is not None:
        if not math.isfinite(a.graham_current_ratio) or a.graham_current_ratio <= 0:
            p.error('The threshold must be finite and positive.')
        rules['current_ratio_min'] = a.graham_current_ratio
    reports = {}
    for ticker in ['COST', 'NVDA', 'JPM']:
        path = RAW / (ticker + '_companyfacts.json')
        receipt = read_json(str(path) + '.receipt.json')
        if hashlib.sha256(path.read_bytes()).hexdigest() != receipt['sha256']:
            raise ValueError('Raw SEC snapshot checksum mismatch: ' + ticker)
        reports[ticker] = compute(read_json(path), ticker, a.asof, rules)
        print(export(reports[ticker], a.output / ticker), end='')
    probe_rules = {**rules, 'current_ratio_min': 1.0}
    probe = compute(read_json(RAW / 'COST_companyfacts.json'), 'COST', a.asof, probe_rules)
    print(export(probe, a.output / 'COST_threshold_probe'), end='')
    if a.graham_current_ratio is None:
        selection = (HERE / 'evidence' / 'company_selection.md').read_text(encoding='utf-8')
        submission = build_submission(reports, probe, selection)
        (HERE / 'SUBMISSION.md').write_text(submission, encoding='utf-8')
        (HERE / 'SUBMISSION.html').write_text(simple_html(submission), encoding='utf-8')
    audit = audit_all(a.output)
    write_json(HERE / 'evidence' / 'memo_audit.json', audit)
    print(json.dumps(audit, indent=2))
    return 0 if audit['all_pass'] else 1

if __name__ == '__main__':
    sys.exit(main())
