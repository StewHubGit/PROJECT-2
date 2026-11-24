"""Acceptance checks independent of the calculation engine's input data."""
import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile
import panel

HERE = Path(__file__).resolve().parent

def main():
    checks = []
    def check(name, passed, **details):
        checks.append({'check': name, 'pass': bool(passed), **details})
    raw = panel.read_json(panel.RAW / 'COST_companyfacts.json')
    rules = panel.load_rules()
    report = panel.compute(raw, 'COST', '2026-11-05', rules)
    # Instructor-provided targets are read only here, after compute().
    expected = panel.read_json(HERE / 'tests' / 'cost_known_answer.json')
    fields = ['revenue', 'net_income', 'operating_cash_flow', 'capital_spending', 'equity', 'roe_percent', 'owner_earnings']
    ratios = [[1.02, 2.11], [1.07, 1.75], [.97, 1.96], [1.03, 1.64], [1.06, 1.49]]
    check('COST exactly five annual periods', len(report['rows']) == len(expected) == 5)
    for row, target, ratios_target in zip(report['rows'], expected, ratios):
        check('COST fiscal year end', row['fiscal_year_end'] == target[0], actual=row['fiscal_year_end'], expected=target[0])
        for field, val in zip(fields, target[1:]):
            actual = panel.fmt(row[field], 'percent' if field == 'roe_percent' else 'money')
            wanted = f'{val:.1f}%' if field == 'roe_percent' else f'{val:,}'
            check('COST '+field+' '+target[0], actual == wanted, actual=actual, expected=wanted)
        for field, val in zip(['current_ratio', 'liabilities_to_equity'], ratios_target):
            actual, wanted = panel.fmt(row[field], 'ratio'), f'{val:.2f}'
            check('COST '+field+' '+target[0], actual == wanted, actual=actual, expected=wanted)
    for who, expected_checks in [('Buffett', ['pass']*3), ('Graham', ['fail', 'pass', 'pass']), ('Burry', ['pass']*2)]:
        check('COST baseline '+who, list(report['checks'][who].values()) == expected_checks, actual=report['scores'][who])

    # Exercise the actual skill file in an isolated copy, not just a local constant.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for folder in (HERE / 'skills').iterdir():
            target = root / folder.name
            target.mkdir()
            (target / 'rules.json').write_bytes((folder / 'rules.json').read_bytes())
        graham = root / 'ben-graham-expert' / 'rules.json'
        graham.write_text(json.dumps({'current_ratio_min': 1.0}), encoding='utf-8')
        probe = panel.compute(raw, 'COST', '2026-11-05', panel.load_rules(root))
        check('Changing Graham skill rule to 1.0 produces 3 of 3', probe['scores']['Graham']['passed'] == 3 and probe['scores']['Graham']['verdict'] == 'pass')
        check('Threshold probe leaves financial facts unchanged', report['rows'] == probe['rows'])
        check('Threshold probe leaves other personas unchanged', report['checks']['Buffett'] == probe['checks']['Buffett'] and report['checks']['Burry'] == probe['checks']['Burry'])
    check('Retained skill threshold is 2.0', panel.load_rules()['current_ratio_min'] == 2.0)

    # Real sector-specific gaps; do not fill bank facts using a different concept.
    jpm = panel.compute(panel.read_json(panel.RAW / 'JPM_companyfacts.json'), 'JPM', '2026-11-05', rules)
    check('JPM real capex gaps preserved', all(r['capital_spending'] == panel.NOT_FOUND and r['owner_earnings'] == panel.NOT_FOUND for r in jpm['rows']))
    check('JPM owner earnings checks stay not known', list(jpm['checks']['Buffett'].values())[1:] == [panel.NOT_KNOWN]*2)
    check('JPM classified liquidity facts stay missing', all(r['current_assets'] == panel.NOT_FOUND and r['current_liabilities'] == panel.NOT_FOUND and r['current_ratio'] == panel.NOT_KNOWN for r in jpm['rows']))
    check('JPM current ratio check stays not known', list(jpm['checks']['Graham'].values())[0] == panel.NOT_KNOWN)

    # A missing year cannot be silently dropped, even if other years pass.
    missing = copy.deepcopy(raw)
    missing['facts']['us-gaap']['NetCashProvidedByUsedInOperatingActivities']['units']['USD'] = [x for x in missing['facts']['us-gaap']['NetCashProvidedByUsedInOperatingActivities']['units']['USD'] if x['end'] != report['rows'][0]['fiscal_year_end']]
    missing_report = panel.compute(missing, 'COST', '2026-11-05', rules)
    check('Injected missing annual OCF does not become pass', list(missing_report['checks']['Burry'].values())[0] == panel.NOT_KNOWN)
    # Future-filed comparative revisions cannot enter a historical run.
    point = copy.deepcopy(raw)
    sample = copy.deepcopy(next(x for x in point['facts']['us-gaap']['AssetsCurrent']['units']['USD'] if x.get('form') == '10-K' and x['end'] == report['rows'][-1]['fiscal_year_end']))
    sample.update({'filed': '2099-01-01', 'val': 999999999999, 'accn': 'future-probe'})
    point['facts']['us-gaap']['AssetsCurrent']['units']['USD'].append(sample)
    check('Future-filed fact excluded', panel.compute(point, 'COST', '2026-11-05', rules)['rows'] == report['rows'])

    # Audit the actual all-memo traversal, with unsupported values in each persona.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        panel.export(report, root / 'COST')
        clean = panel.audit_all(root)
        check('All generated COST memos pass numeric audit', clean['all_pass'] and clean['memos_checked'] == 3, actual=clean)
        for who in panel.INVESTORS:
            path = root / 'COST' / (who.lower() + '_memo.md')
            original = path.read_text(encoding='utf-8')
            path.write_text(original + '\nUnsupported claim: 987654321.123%.\n', encoding='utf-8')
            audit = panel.audit_all(root)
            flagged = [a for a in audit['audits'] if not a['pass']]
            check('All-memo flag catches injected number in '+who, len(flagged) == 1 and '987654321.123%' in flagged[0]['unsupported_numbers'], actual=flagged)
            path.write_text(original, encoding='utf-8')
    final_audit = panel.audit_all(HERE / 'outputs')
    check('Every saved memo audited', final_audit['all_pass'] and final_audit['memos_checked'] == 12, actual=final_audit)
    for ticker in ['COST', 'NVDA', 'JPM']:
        path = panel.RAW / (ticker + '_companyfacts.json')
        receipt = panel.read_json(str(path) + '.receipt.json')
        check(ticker+' source checksum', hashlib.sha256(path.read_bytes()).hexdigest() == receipt['sha256'])
    result = {'all_pass': all(x['pass'] for x in checks), 'checks_passed': sum(x['pass'] for x in checks), 'checks_total': len(checks),
              'cost_comparison_cells': 50, 'all_memos': final_audit, 'checks': checks}
    panel.write_json(HERE / 'evidence' / 'validation.json', result)
    print(json.dumps(result, indent=2))
    if not result['all_pass']:
        raise SystemExit('Validation failed. Inspect evidence/validation.json; do not replace the facts with the answer key.')

if __name__ == '__main__':
    main()
