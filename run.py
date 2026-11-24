"""Reproduce the frozen Project 2 result offline using Python's standard library."""
from __future__ import annotations

import csv
from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import html
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write_json(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def compute_result():
    config = load_json('project.json')
    engine = load_module('portfolio', 'portfolio.py')
    review = load_module('project2_review', 'review.py')
    estimates = []
    for last_36 in (False, True):
        inputs = engine.estimate_from_csv(ROOT / 'data/prices.csv', last_36)
        for sleeve in inputs['sleeves']:
            sleeve['reserve_eligible'] = sleeve['name'] == 'SGOV'
        mix = engine.search_lowest_risk(inputs['sleeves'], inputs['correlations'],
                                       config['target_annual'], config['reserve_minimum'])
        if mix is None:
            raise ValueError('Frozen search unexpectedly infeasible; inspect the inputs.')
        estimates.append({'months': inputs['months'], 'price_start': inputs['price_start'],
                          'price_end': inputs['price_end'], **mix})
    inputs = engine.estimate_from_csv(ROOT / 'data/prices.csv')
    for sleeve in inputs['sleeves']:
        sleeve['reserve_eligible'] = sleeve['name'] == 'SGOV'
    tickers = [s['name'] for s in inputs['sleeves']]
    means = [s['expected_return'] for s in inputs['sleeves']]
    vols = [s['volatility'] for s in inputs['sleeves']]
    covariance = engine.build_covariance_matrix(vols, inputs['correlations'])
    baseline_weights = {
        '60/40 reference': [config['benchmark_weights'][t] for t in tickers],
        'Equal weight': engine.equal_weights(len(tickers)),
        'Inverse volatility': engine.inverse_volatility_weights(vols),
    }
    cost = config['additional_annual_cost_bps'] / 10000
    baselines = {name: {
        'weights': weights, 'gross_arithmetic_estimate': engine.portfolio_expected_return(weights, means),
        'volatility': engine.portfolio_volatility(weights, covariance),
        'reserve_weight': sum(w for t, w in zip(tickers, weights) if t == 'SGOV'),
    } for name, weights in baseline_weights.items()}
    for values in baselines.values():
        values['after_assumed_cost_estimate'] = values['gross_arithmetic_estimate'] - cost
        values['reserve_check'] = values['reserve_weight'] >= config['reserve_minimum']
    gross = estimates[0]['expected_return']
    net = gross - cost
    result = {
        'freeze_date': config['freeze_date'], 'ai_announcement': config['ai_announcement'],
        'data_sha256': sha('data/prices.csv'), 'tickers': tickers,
        'target_annual': config['target_annual'], 'reserve_minimum': config['reserve_minimum'],
        'all_months': estimates[0], 'last_36_months': estimates[1], 'baselines': baselines,
        'largest_window_weight_change_points': 100 * max(abs(a-b) for a, b in zip(
            estimates[0]['weights'], estimates[1]['weights'])),
        'cost_test': {
            'id': 'COST-01', 'single_changed_input': 'additional annual cost drag, 0 -> 25 basis points',
            'cost_bps': config['additional_annual_cost_bps'], 'cost_status': config['cost_status'],
            'gross_arithmetic_estimate': gross, 'after_assumed_cost_estimate': net,
            'headroom_bps': (gross - config['target_annual']) * 10000,
            'baseline_after_assumed_cost_estimate': baselines['60/40 reference']['after_assumed_cost_estimate'],
            'candidate_minus_baseline_bps': (gross - baselines['60/40 reference']['gross_arithmetic_estimate']) * 10000,
            'net_target_claim': 'FAIL' if net < config['target_annual'] else 'PASS',
            'beats_reference_claim': 'FAIL' if net <= baselines['60/40 reference']['after_assumed_cost_estimate'] else 'PASS',
            'interpretation': 'A frozen in-sample arithmetic estimate under assumed common costs; not a realized, annual-rebalanced or out-of-sample performance test. No retuning.',
        },
        'mandate': {
            'long_only_full_investment': 'PASS on the grid',
            'reserve': 'PASS: SGOV 65% versus selected minimum 3%',
            'net_return_hurdle': 'FAIL under COST-01 assumption; rolling five-year CPI+4 objective not established',
            'liquidity_and_issuer': 'Conditional on ETF eligibility assumptions; no live dealing or look-through audit',
            'turnover': 'NOT ESTABLISHED: starting holdings and trading path absent',
            'calendar_year_loss_S9': 'UNRESOLVED: CIO definition and breach response absent',
        },
        'decision': config['decision'],
        'portfolio_comparison': review.comparison_rows(inputs['sleeves'], inputs['correlations'],
            config['target_annual'], config['reserve_minimum'], config['additional_annual_cost_bps'], estimates[0]),
        'sensitivity_runs': review.sensitivity_rows(inputs['sleeves'], inputs['correlations'],
            config['target_annual'], config['reserve_minimum'], config['additional_annual_cost_bps']),
        'point_in_time_signal': review.point_in_time_signal(),
    }
    return result


def validate(result):
    checks = []

    def check(name, passed, detail=''):
        checks.append({'name': name, 'pass': bool(passed), 'detail': detail})
        if not passed:
            write_json('validation/checks.json', {'all_pass': False, 'checks': checks})
            raise ValueError(f'Validation failed: {name}: {detail}')

    config = load_json('project.json')
    check('Frozen CSV fingerprint', result['data_sha256'] == config['expected_prices_sha256'])
    provenance = load_json('evidence/assembly_provenance.json')
    damaged = [r['repository_path'] for r in provenance['files'] if sha(r['repository_path']) != r['sha256']]
    check('All assembled original lab files unchanged', not damaged, str(damaged))
    with (ROOT / 'data/prices.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    check('61 prices supply 60 returns', len(rows) == 61 and result['all_months']['months'] == 60)
    for source in load_json('evidence/fund_prices_sources/sources.json'):
        ticker = source['ticker']
        path = f'evidence/fund_prices_sources/{ticker}_daily.json'
        check(f'{ticker}: original source receipt', sha(path) == source['sha256'])
        raw = load_json(path)['chart']['result'][0]
        monthly = {}
        for stamp, value in zip(raw['timestamp'], raw['indicators']['adjclose'][0]['adjclose']):
            # These saved US market observations are daytime UTC; no UTC/local date rollover.
            day = datetime.fromtimestamp(stamp, timezone.utc).date().isoformat()
            if '2021-09-01' <= day <= '2026-09-30' and value is not None:
                month = day[:7]
                if month not in monthly or day > monthly[month][0]:
                    monthly[month] = (day, value)
        check(f'{ticker}: each CSV cell equals raw month-end adjusted close', all(
            monthly[row['Date'][:7]][0] == row['Date'] and
            math.isclose(monthly[row['Date'][:7]][1], float(row[ticker]), rel_tol=0, abs_tol=1e-10)
            for row in rows))
    saved = load_json('evidence/window_comparison_original.json')
    for key in ['all_months', 'last_36_months']:
        now, old = result[key], saved[key]['engine']
        check(f'{key}: weights reproduce prior record', now['weights'] == old['weights'])
        check(f'{key}: return and volatility reproduce prior record', all(
            math.isclose(now[k], old[k], abs_tol=1e-12) for k in ['expected_return', 'volatility']))
    check('Window stress reproduces 20-point allocation change', math.isclose(
        result['largest_window_weight_change_points'], 20, abs_tol=1e-10))

    # Independent known-answer arithmetic: fixed prior weights and saved unrounded means.
    # This deliberately does not call the optimizer or its return function.
    stats = load_json('evidence/fund_estimates_original.json')['fund_statistics']
    D = Decimal
    mu = {t: D(str(stats[t]['historical_annualized_arithmetic_mean_return'])) for t in result['tickers']}
    fixed_gross = D('0.65') * mu['SGOV'] + D('0.35') * mu['VT']
    fixed_baseline = D('0.6') * mu['VT'] + D('0.4') * mu['BND']
    net = fixed_gross - D('0.0025')
    baseline_net = fixed_baseline - D('0.0025')
    check('COST-01: independent Decimal calculation matches', abs(float(net) -
        result['cost_test']['after_assumed_cost_estimate']) < 1e-12)
    check('COST-01: known claim failure preserved', net < D('0.065') and net < baseline_net)
    check('COST-01: fixed allocation was not retuned', result['all_months']['weights'] == [.65, 0, 0, .35])
    check('60/40 reference reserve failure visible', not result['baselines']['60/40 reference']['reserve_check'])
    comparison = {row['Portfolio']: row for row in result['portfolio_comparison']}
    check('Same-rule baselines identify their failing mandate rule',
          'S2' in comparison['Equal weight']['Modeled verdict'] and
          'S3' in comparison['60/40 reference']['Modeled verdict'] and
          comparison['Constrained portfolio']['Reserve'] == '65.00%')
    signal = result['point_in_time_signal']
    check('Saved-vintage signal known answer and date ordering',
          signal['measurement_date'] == '2026-09-29' and
          signal['lookback_date'] == '2026-08-31' and
          math.isclose(signal['change_bps'], 51, abs_tol=1e-9) and
          signal['measurement_date'] <= signal['vintage_date'] < signal['proposed_review_date'])
    review = load_module('project2_review_validation', 'review.py')
    check('Missing required vintage quarantines; no fallback',
          review.point_in_time_signal(False)['status'] == 'QUARANTINE / STOP')
    diagnostic = result['sensitivity_runs']
    check('Severe reserve constraint fails closed without retuning committee mix',
          diagnostic[-1]['Weights'] == 'INFEASIBLE' and result['all_months']['weights'] == [.65, 0, 0, .35])
    check('Zero additional cost recovers modeled screen only',
          diagnostic[2]['Verdict'] == 'PASS modeled screen' and
          diagnostic[0]['Verdict'].startswith('STOP'))

    # Reproduce the existing training stress, without editing original source files.
    engine = load_module('project2_validation_engine', 'portfolio.py')
    training = engine.search_lowest_risk(engine.SLEEVES, engine.CORRELATIONS)
    stress_inputs = deepcopy(engine.SLEEVES)
    stress_inputs[-1]['expected_return'] = .07
    stress = engine.search_lowest_risk(stress_inputs, engine.CORRELATIONS)
    check('Lab 15: training case known answer', training['weights'] == [0, .2, .25, .55])
    check('Lab 15: one-point equity stress known answer', stress['weights'] == [0, .1, .1, .8])

    # Invalid prices must fail closed instead of silently changing the sample.
    bad = (ROOT / 'data/prices.csv').read_text(encoding='utf-8').replace(rows[0]['SGOV'], '0', 1)
    rejected = False
    try:
        engine.estimate_from_csv(io.StringIO(bad))
    except ValueError:
        rejected = True
    check('Invalid zero price rejected', rejected)

    code = ROOT / 'labs/16_point_in_time/asof.py'
    completed = subprocess.run([sys.executable, '-I', '-S', str(code)], capture_output=True, text=True, check=False)
    expected = (ROOT / 'labs/16_point_in_time/OUTPUT.txt').read_text(encoding='utf-8')
    check('Lab 16: standalone known-answer output', completed.returncode == 0 and
          completed.stdout.strip() == expected.strip())
    (ROOT / 'validation/lab16_replay.txt').write_text(completed.stdout, encoding='utf-8')

    def csv_values(path):
        with (ROOT / path).open(encoding='utf-8-sig', newline='') as f:
            data = list(csv.reader(f))
        return {r[0]: float(r[1]) for r in data[1:] if len(r) >= 2 and r[1] not in ('', '.')}

    old = csv_values('labs/17_fred_asof/evidence/asof_dgs10/DGS10_asof_2026-09-30.csv')
    current = csv_values('labs/17_fred_asof/evidence/asof_dgs10/DGS10_today.csv')
    check('Lab 17: saved vintage excludes same-day measurement', max(old) == '2026-09-29' and
          old['2026-09-29'] == 5.26 and '2026-09-30' not in old)
    check('Lab 17: 19 later arrivals, zero shared-date revisions',
          len(set(current) - set(old)) == 19 and all(current[k] == v for k, v in old.items()))

    lab18_readme = (ROOT / 'labs/18_assignment/START_HERE.md').read_text(encoding='utf-8')
    check('Lab 18: original incomplete live acceptance disclosed',
          'remain pending' in lab18_readme,
          'Archived Lab 18 rule/UI tests require optional dependencies and are not part of the standard-library replay. Lab 19 supplies the saved live snapshots.')

    panel = load_module('project2_lab19_panel', 'labs/19_investor_panel/panel.py')
    for ticker in ['COST', 'NVDA', 'JPM']:
        path = f'labs/19_investor_panel/evidence/raw/{ticker}_companyfacts.json'
        receipt = load_json(path + '.receipt.json')
        check(f'Lab 19 {ticker}: SEC snapshot fingerprint', sha(path) == receipt['sha256'])
        report = panel.compute(load_json(path), ticker, '2026-11-05', panel.load_rules())
        prior = load_json(f'labs/19_investor_panel/outputs/{ticker}/facts_and_checks.json')
        check(f'Lab 19 {ticker}: existing financial rows and checks reproduce',
              report['rows'] == prior['rows'] and report['checks'] == prior['checks'])
    audit = panel.audit_all(ROOT / 'labs/19_investor_panel/outputs')
    check('Lab 19: twelve saved memos pass number provenance audit', audit['all_pass'] and audit['memos_checked'] == 12,
          'Number matching does not certify narrative truth or independent investor votes.')
    write_json('validation/checks.json', {'all_pass': True, 'checks_passed': len(checks),
        'checks_total': len(checks), 'checks': checks,
        'financial_claim_status': 'FAIL under COST-01; validation success means the failure was reproduced.'})
    return checks


def result_markdown(result):
    r = result
    c = r['cost_test']
    a, s = r['all_months'], r['last_36_months']
    lines = [r['ai_announcement'], '', '# Frozen Project 2 result', '',
        f"Freeze: {r['freeze_date']}. Prices {a['price_start']} through {a['price_end']}; {a['months']} monthly returns.", '',
        '**Decision: REDESIGN. Live capital: $0.** The frozen candidate fails the net hurdle under the assumed cost test. No allocation was retuned.', '',
        '| Run | SGOV | IEF | BND | VT | Gross arithmetic estimate | Sample volatility |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for label, x in [('All months', a), ('Last 36 months', s)]:
        lines.append('| ' + ' | '.join([label, *[f'{w:.2%}' for w in x['weights']],
            f"{x['expected_return']:.2%}", f"{x['volatility']:.2%}"]) + ' |')
    lines += ['', f"Existing window stress: largest allocation change **{r['largest_window_weight_change_points']:.2f} percentage points**.", '',
        '## COST-01 single claim test', '',
        f"Assume a common **{c['cost_bps']:.0f} bp/year** additional drag; keep prices, estimates, weights, target and window fixed. Taxes are not modeled. The cost is an assumption, not a measured bill.", '',
        '| Measure | Frozen result |', '| --- | ---: |',
        f"| Candidate after assumed cost | {c['after_assumed_cost_estimate']:.2%} |",
        f"| Net planning hurdle | {r['target_annual']:.2%} |",
        f"| 60/40 reference after same assumed cost | {c['baseline_after_assumed_cost_estimate']:.2%} |",
        f"| Candidate minus reference | {c['candidate_minus_baseline_bps']:.2f} bp |",
        f"| Maximum additional drag before candidate misses hurdle | {c['headroom_bps']:.2f} bp |", '',
        '**Claim outcome: FAIL.** These are in-sample annualized arithmetic estimates, not realized after-cost returns or a rolling five-year CPI outcome. The 60/40 reference has 0% SGOV and fails the selected 3% reserve screen; it is an evaluation reference, not an approved substitute.', '',
        '## Baselines and mandate checks', '',
        '| Baseline | Gross arithmetic | After assumed cost | Volatility | SGOV reserve | Reserve check |',
        '| --- | ---: | ---: | ---: | ---: | --- |']
    for name, b in r['baselines'].items():
        lines.append(f"| {name} | {b['gross_arithmetic_estimate']:.2%} | {b['after_assumed_cost_estimate']:.2%} | {b['volatility']:.2%} | {b['reserve_weight']:.2%} | {'PASS' if b['reserve_check'] else 'FAIL'} |")
    lines += ['', *[f'- **{k.replace("_", " ")}:** {v}.' for k, v in r['mandate'].items()], '',
        '### Same-rule portfolio comparison', '',
        '| Portfolio | Net estimate | Volatility | Reserve | Modeled verdict |',
        '| --- | ---: | ---: | ---: | --- |']
    for row in r['portfolio_comparison']:
        lines.append('| ' + ' | '.join(row[k] for k in ['Portfolio', 'Net estimate', 'Volatility', 'Reserve', 'Modeled verdict']) + ' |')
    lines += ['', 'Full mandate use is NOT CLEARED for every mix: realized rolling CPI, annual rebalancing/turnover, live eligibility and S9 loss governance are unresolved.', '',
        '## Isolated stress runs', '',
        '| Scenario | Diagnostic weights | Net estimate | Verdict |',
        '| --- | --- | ---: | --- |']
    for row in r['sensitivity_runs']:
        lines.append('| ' + ' | '.join(row[k] for k in ['Scenario', 'Weights', 'Net estimate', 'Verdict']) + ' |')
    signal = r['point_in_time_signal']
    lines += ['', 'The separate 60-to-36-month window stress above completes the four stress dimensions. The severe 70% reserve scenario is a diagnostic, not a proposed policy. The committee candidate remains frozen.', '',
        '## Point-in-time signal', '',
        f"DGS10 {signal['direction']}: {signal['change_bps']:.2f} bp over 20 known observations, {signal['lookback_date']} to {signal['measurement_date']}. Last yield {signal['yield_percent']:.2f}%; eligible vintage {signal['vintage_date']}; proposed review {signal['proposed_review_date']}. Status: {signal['status']}.", '',
        'The signal supplies research context and a data-admission gate; it does not set ETF weights. Missing required vintage means QUARANTINE / STOP, with no current-history fallback. This is a saved historical demonstration, not a live signal. See [data card](../docs/DATA_CARD.md).', '',
        '## Committee controls', '', *[f'- **{k.replace("_", " ")}:** {v}' for k, v in r['decision'].items()], '',
        '## Scope and trace', '',
        'Adjusted history was retrieved on 2026-10-22. It supports reproduction at that research date; it is not proof of what investors knew on every historical trade date. No dynamic strategy backtest or DGS10-driven allocation exists here. Lab 18/19 stock screens are supporting research controls and do not feed ETF weights.', '',
        'Trace: [raw receipts](../evidence/fund_prices_sources/sources.json) -> [prices](../data/prices.csv) -> [engine](../portfolio.py) -> [COST-01](../validation/RISKIEST_CLAIM.md) -> [memo](../docs/decision-memo.md).', '',
        '[Machine-readable result](result.json) | [Reproduction checks](../validation/checks.json)', '']
    return '\n'.join(lines)


def main():
    try:
        result = compute_result()
        checks = validate(result)
        write_json('results/result.json', result)
        report = result_markdown(result)
        (ROOT / 'results/RESULTS.md').write_text(report, encoding='utf-8')
        # Deliberately dependency-free local report; Markdown is available for linked navigation.
        (ROOT / 'results/RESULTS.html').write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Project 2 frozen result</title><style>body{max-width:1050px;margin:36px auto;padding:0 24px;color:#152b3a;'
            'font:16px/1.6 system-ui}pre{white-space:pre-wrap;font:14px/1.7 ui-monospace,monospace}</style>'
            '<h1>Project 2 frozen result</h1><p><a href="RESULTS.md">Linked Markdown report</a></p><pre>' +
            html.escape(report) + '</pre></html>', encoding='utf-8')
        print(result['ai_announcement'])
        print(f"Reproduction checks: {len(checks)}/{len(checks)} PASS")
        print('COST-01 financial claim: FAIL (preserved); committee action: REDESIGN; live capital: $0')
        print('Candidate: 65% SGOV / 35% VT; gross estimate 6.58%; after assumed 25 bp: 6.33%')
        print('60/40 reference after same assumed cost: 6.72%; target: 6.50%')
        print('Existing 60-to-36-month window stress: 20.00 percentage-point largest weight change')
        print('Open results/RESULTS.md or results/RESULTS.html. See docs/COMMITTEE_MEMO.md and videos/.')
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f'Cannot reproduce the frozen result: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
