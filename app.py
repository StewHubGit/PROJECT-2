"""Project 2 web app: Meridian mandate and the personal robo-advisor extension."""
from copy import deepcopy
from pathlib import Path

import streamlit as st

from portfolio import (CORRELATIONS, SLEEVES, estimate_from_csv, search_lowest_risk)
from run import compute_result
from review import comparison_rows, point_in_time_signal, sensitivity_rows

ROOT = Path(__file__).resolve().parent


def show_mix(mix, sleeves, cost_bps):
    if mix is None:
        st.warning('No mix meets the modeled gross objective and reserve screen.')
        return
    st.table([{'Asset': s['name'], 'Weight': f'{w:.2%}'} for s, w in zip(sleeves, mix['weights'])])
    st.metric('Gross annualized arithmetic estimate', f"{mix['expected_return']:.2%}")
    st.metric('After assumed additional cost', f"{mix['expected_return'] - cost_bps / 10000:.2%}")
    st.metric('Sample annual volatility', f"{mix['volatility']:.2%}")
    st.metric('Reserve-eligible weight', f"{mix['reserve_eligible_weight']:.2%}")


def main():
    st.set_page_config(page_title='Project 2 Meridian decision', layout='wide')
    mode_choice = st.sidebar.radio('App mode', ['Meridian mandate — Project 2', 'Personal robo-advisor — Rule B'])
    if mode_choice == 'Personal robo-advisor — Rule B':
        from robo_app import main as personal_advisor
        personal_advisor()
        return
    st.caption('I used OpenAI Codex to assemble code, check calculations and draft documents. '
               'Draft ownership statement for Sam to confirm: The analysis and the decision are mine; education, not investment advice.')
    st.title('Meridian portfolio decision')
    frozen = compute_result()
    st.error('Frozen committee recommendation: REDESIGN. Live capital: $0. Human sign-off pending.')
    st.write('The frozen 65% SGOV / 35% VT candidate gives 6.58% gross and 6.33% after an assumed '
             '25 bp/year drag, versus a 6.50% hurdle and 6.72% reference. No retuning was performed.')
    st.caption('In-sample arithmetic estimates, not realized returns or forecasts. Taxes are not modeled. '
               'The 60/40 reference has no SGOV reserve. App edits below do not change the frozen committee record.')

    with st.sidebar:
        st.header('Lab inputs')
        mode = st.selectbox('Input source', ['Saved Project 2 funds', 'Meridian training case'])
        objective = st.number_input('Annual return objective (%)', value=6.5, step=1.0) / 100
        reserve = st.number_input('Reserve minimum (%)', min_value=0.0, max_value=100.0, value=3.0, step=1.0) / 100
        cost_bps = st.number_input('Assumed annual additional cost (bp)', min_value=0.0, value=25.0, step=5.0)
        upload = st.file_uploader('Optional replacement prices.csv', type=['csv'])
        last_36 = st.toggle('Last 36 months only', value=False, disabled=mode == 'Meridian training case')
        training_stress = st.checkbox('Training stress: equity estimate 8% to 7%', value=False,
                                      disabled=mode != 'Meridian training case')
        vintage_available = st.checkbox('Required saved vintage available', value=True)
        st.caption('The cost input changes the displayed hurdle check; it does not retune the optimizer. '
                   '25 bp is an assumption, not a measured fee.')

    st.subheader('Mandate and point-in-time signal')
    st.write('$100m Meridian case; seven-year horizon; annual rebalancing; $0.75m quarterly payouts. '
             'Objective: rolling five-year CPI+4% net (6.50% planning proxy). Universe: SGOV, IEF, BND, VT. '
             'Benchmark: 60% VT / 40% BND. Modeled risk: annualized sample volatility; '
             'long-only, fully invested; 3% reserve; 90% redeemable within five business days; '
             '8% nonexempt issuer cap; annual turnover <=25% without approval. '
             'The 10% calendar-year loss measure/response needs CIO definition.')
    signal = point_in_time_signal(vintage_available)
    if signal['status'].startswith('QUARANTINE'):
        st.error('PROCESS STOP: required point-in-time signal unavailable. No trade proposal. ' + signal['reason'])
        st.caption('Restore the required saved vintage before producing any allocation or mandate screen. No current-history fallback is allowed.')
        st.stop()
    else:
        st.info(f"Saved DGS10 context: {signal['direction']}, {signal['change_bps']:.2f} bp over 20 known observations. "
                f"Last measurement {signal['measurement_date']}: {signal['yield_percent']:.2f}%; "
                f"vintage {signal['vintage_date']}; proposed review {signal['proposed_review_date']}.")
    st.caption('Historical saved-vintage demonstration, downloaded 2026-10-29; not a live signal. '
               'The previous-day vintage rule gates data admission. This context does not set ETF weights. '
               'No current-history fallback or imputation. See docs/DATA_CARD.md.')

    if mode == 'Meridian training case':
        baseline_sleeves, correlations = deepcopy(SLEEVES), deepcopy(CORRELATIONS)
        sleeves = deepcopy(SLEEVES)
        if training_stress:
            sleeves[-1]['expected_return'] = .07
        st.subheader('Meridian training assumptions')
        st.caption('Training assumptions are separate from the saved ETF historical estimates.')
    else:
        content = upload.getvalue() if upload else (ROOT / 'data/prices.csv').read_bytes()
        try:
            baseline = estimate_from_csv(content)
            chosen = estimate_from_csv(content, last_36)
            if [s['name'] for s in chosen['sleeves']] != ['SGOV', 'IEF', 'BND', 'VT']:
                raise ValueError('This mandate requires CSV columns Date,SGOV,IEF,BND,VT in that order.')
        except (ValueError, UnicodeError, TypeError) as error:
            st.error(f'Cannot estimate inputs: {error}')
            st.stop()
        baseline_sleeves, sleeves = baseline['sleeves'], chosen['sleeves']
        correlations = chosen['correlations']
        for collection in (baseline_sleeves, sleeves):
            for sleeve in collection:
                sleeve['reserve_eligible'] = sleeve['name'] == 'SGOV'
        st.subheader('Historical fund inputs')
        st.caption(f"{chosen['months']} monthly returns from {chosen['price_start']} through {chosen['price_end']}. "
                   'Adjusted prices embed fund expenses. Additional advisory/trading costs are excluded until the assumed drag is applied.')

    st.caption('Lowest modeled volatility on a fully invested, long-only 5-percentage-point grid. '
               'A positive 3% reserve rule requires at least 5% on this grid.')
    for index, sleeve in enumerate(sleeves):
        a, b = st.columns(2)
        sleeve['expected_return'] = a.number_input(f"Historical/assumed annual mean (%) - {sleeve['name']}",
            value=float(sleeve['expected_return'] * 100), step=1.0,
            key=f"mean_{mode}_{last_36}_{training_stress}_{index}_{sleeve['name']}") / 100
        sleeve['reserve_eligible'] = b.checkbox(f"Reserve eligible - {sleeve['name']}",
            value=sleeve['reserve_eligible'], key=f"eligible_{mode}_{index}_{sleeve['name']}")
    baseline_corr = CORRELATIONS if mode == 'Meridian training case' else baseline['correlations']
    try:
        edited = search_lowest_risk(sleeves, correlations, objective, reserve)
        original = search_lowest_risk(baseline_sleeves, baseline_corr, .065, .03)
    except ValueError as error:
        st.error(str(error))
        st.stop()
    left, right = st.columns(2)
    with left:
        st.subheader('Current controls')
        show_mix(edited, sleeves, cost_bps)
    with right:
        st.subheader('Original inputs, all months')
        show_mix(original, baseline_sleeves, cost_bps)
    if edited is not None and original is not None:
        delta = 100 * max(abs(a-b) for a, b in zip(edited['weights'], original['weights']))
        st.metric('Largest weight change from original', f'{delta:.2f} percentage points')
    st.subheader('Current-control mandate verdicts')
    st.table(comparison_rows(sleeves, correlations, objective, reserve, cost_bps, edited))
    st.caption('Every mix uses the same controls. PASS applies only to the modeled screen. '
               'Full use remains blocked by unresolved mandate evidence. S6/S8 use lab ETF proxies; '
               'no live issuer look-through or dealing verification. Starting holdings and a realized path are absent.')
    if edited is not None:
        net = edited['expected_return'] - cost_bps / 10000
        st.table([
            {'Check': 'Long-only, fully invested grid', 'Verdict': 'PASS'},
            {'Check': 'Selected reserve minimum', 'Verdict': 'PASS'},
            {'Check': 'Return hurdle after assumed cost', 'Verdict': 'PASS under assumption' if net >= objective else 'FAIL under assumption'},
            {'Check': 'Actual rolling five-year CPI+4 net', 'Verdict': 'NOT ESTABLISHED'},
            {'Check': 'Annual turnover <=25%', 'Verdict': 'NOT ESTABLISHED: starting holdings/path missing'},
            {'Check': 'S9 calendar-year loss rule', 'Verdict': 'UNRESOLVED: CIO definition needed'},
            {'Check': 'Liquidity / issuer eligibility', 'Verdict': 'CONDITIONAL: lab proxies; live verification absent'},
        ])
    st.subheader('Preserved window stress and decision controls')
    st.table(sensitivity_rows(sleeves, correlations, objective, reserve, cost_bps))
    st.caption('Isolated diagnostics; the estimate and constraint cases may search a different diagnostic mix, '
               'while the frozen committee mix remains 65/0/0/35. Cost does not retune weights. '
               'The severe 70% reserve case is a stress, not a proposed mandate. Full mandate approval is still blocked.')
    st.write('Saved four-fund stress: 60 months selects 65% SGOV / 35% VT; 36 months selects '
             '85% SGOV / 15% VT. Largest change: 20.00 percentage points. This is input sensitivity, not improved performance.')
    st.write('Conditional redesign proposal: $1,000,000 shadow notional, $0 live, 12 months; '
             'owner Sam Stewart subject to acceptance. Written objective, loss rule, costs and point-in-time protocol are required first.')
    st.write('Recommended live allocation range to this process: 0%-0% of the $100m mandate ($0-$0). '
             'Conditional shadow funding range: $0-$1,000,000 notional; no actual investment. '
             'Reject current live use; redesign before requesting a separate shadow approval.')
    st.write('Monitor sources/vintages, costs, allocation changes and exceptions monthly. Kill on required-vintage failure, '
             'unexplained mismatch, reserve below 3%, unapproved turnover above 25%, or approved loss breach. '
             'A separate committee decision is required to approve a shadow protocol or any later live use.')
    st.caption('Canonical figures and conditions: project.json and results/result.json. '
               'Code: portfolio.py. Sources and test: evidence/ and validation/RISKIEST_CLAIM.md.')


if __name__ == '__main__':
    main()
