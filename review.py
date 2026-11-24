"""Shared committee screens, saved-vintage signal and isolated sensitivity runs.

These are diagnostics of the supplied teaching case, not live eligibility checks.
"""
from copy import deepcopy
import csv
from datetime import date
from pathlib import Path

from portfolio import (build_covariance_matrix, equal_weights,
                       inverse_volatility_weights, portfolio_expected_return,
                       portfolio_volatility, reserve_eligible_weight,
                       search_lowest_risk)

ROOT = Path(__file__).resolve().parent
VINTAGE = '2026-09-30'
SIGNAL_PATH = ROOT / 'labs/17_fred_asof/evidence/asof_dgs10/DGS10_asof_2026-09-30.csv'


def comparison_rows(sleeves, correlations, objective, reserve, cost_bps, candidate):
    """Evaluate all mixes with the same current estimates, costs and rules."""
    means = [s['expected_return'] for s in sleeves]
    vols = [s['volatility'] for s in sleeves]
    covariance = build_covariance_matrix(vols, correlations)
    rows = []
    mixes = {'Constrained portfolio': candidate['weights'] if candidate else None,
             'Equal weight': equal_weights(len(sleeves)),
             '60/40 reference': [0, 0, .4, .6],
             'Inverse volatility': inverse_volatility_weights(vols)}
    for name, weights in mixes.items():
        if weights is None:
            rows.append({'Portfolio': name, 'Weights': 'No feasible grid mix',
                         'Net estimate': 'N/A', 'Volatility': 'N/A', 'Reserve': 'N/A',
                         'Modeled verdict': 'FAIL: no mix meets gross target and reserve',
                         'Full mandate': 'NOT CLEARED'})
            continue
        net = portfolio_expected_return(weights, means) - cost_bps / 10000
        held_reserve = reserve_eligible_weight(weights, sleeves)
        failures = []
        if abs(sum(weights) - 1) > 1e-9 or min(weights) < 0:
            failures.append('S5 long-only/full investment')
        if held_reserve + 1e-12 < reserve:
            failures.append('S3 reserve')
        if net + 1e-12 < objective:
            failures.append('S2 net planning hurdle')
        rows.append({'Portfolio': name,
                     'Weights': ' / '.join(f'{s["name"]} {w:.1%}' for s, w in zip(sleeves, weights)),
                     'Net estimate': f'{net:.2%}',
                     'Volatility': f'{portfolio_volatility(weights, covariance):.2%}',
                     'Reserve': f'{held_reserve:.2%}',
                     'Modeled verdict': 'FAIL: ' + '; '.join(failures) if failures else 'PASS: S3, S5 and net planning screen',
                     'Full mandate': 'NOT CLEARED: S1 path, S2 realized CPI, S7 turnover, S9 loss rule; S6/S8 live eligibility conditional'})
    return rows


def point_in_time_signal(available=True, path=SIGNAL_PATH):
    """20-observation yield change entirely within one archived eligible vintage.

    Quarantine missing/malformed data; never fetch or substitute current history.
    The signal is a research context and data-admission gate, not a weight rule.
    """
    record = {'series': 'DGS10', 'vintage_date': VINTAGE,
              'proposed_review_date': '2026-10-01', 'lookback_observations': 20,
              'role': 'Research context and data-admission gate only; does not change ETF weights',
              'source': SIGNAL_PATH.relative_to(ROOT).as_posix()}
    try:
        if not available:
            raise ValueError('Required vintage marked unavailable')
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            data = list(csv.reader(stream))
        values = []
        for row in data[1:]:
            if len(row) < 2 or row[1] in ('', '.'):
                continue
            day = date.fromisoformat(row[0]).isoformat()
            value = float(row[1])
            if not (-100 < value < 100):
                raise ValueError('Nonfinite or implausible yield')
            if day > VINTAGE or (values and day <= values[-1][0]):
                raise ValueError('Future, duplicate or unordered measurement')
            values.append((day, value))
        if len(values) < 21:
            raise ValueError('Insufficient known observations')
        old, latest = values[-21], values[-1]
        if latest[0] >= record['proposed_review_date']:
            raise ValueError('Measurement unavailable before review')
        change = (latest[1] - old[1]) * 100
        record.update(status='ADMIT saved-vintage research context',
                      measurement_date=latest[0], yield_percent=latest[1],
                      lookback_date=old[0], lookback_yield_percent=old[1],
                      change_bps=change,
                      direction='RISING' if change > 0 else 'FALLING' if change < 0 else 'UNCHANGED')
    except (OSError, ValueError, TypeError, IndexError) as error:
        record.update(status='QUARANTINE / STOP', reason=str(error))
    return record


def sensitivity_rows(sleeves, correlations, objective=.065, reserve=.03, cost_bps=25):
    """Each scenario starts from the same saved base; no combined/optimized repair."""
    rows = []
    for label, mean_delta, minimum, drag in [
        ('Baseline current estimates', 0, reserve, cost_bps),
        ('Estimates: VT mean -1 percentage point', -.01, reserve, cost_bps),
        ('Costs: additional drag 0 bp', 0, reserve, 0),
        ('Constraints: reserve minimum 70% (severe diagnostic)', 0, .70, cost_bps),
    ]:
        changed = deepcopy(sleeves)
        changed[-1]['expected_return'] += mean_delta
        mix = search_lowest_risk(changed, correlations, objective, minimum)
        if mix is None:
            rows.append({'Scenario': label, 'Weights': 'INFEASIBLE', 'Net estimate': 'N/A',
                         'Verdict': 'STOP: gross target/reserve infeasible'})
        else:
            net = mix['expected_return'] - drag / 10000
            rows.append({'Scenario': label,
                         'Weights': ' / '.join(f'{s["name"]} {w:.0%}' for s, w in zip(changed, mix['weights'])),
                         'Net estimate': f'{net:.2%}',
                         'Verdict': 'PASS modeled screen' if net >= objective else 'STOP: net planning hurdle fails'})
    return rows
