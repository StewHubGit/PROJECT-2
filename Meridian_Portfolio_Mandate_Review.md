# Meridian Foundation: mandate and candidate portfolio review

Based on the supplied case facts. This is an AI-assisted analysis, not a record of an independently completed no-AI exercise.

## S1-S10: sort before building

| Statement | Classification | One-line reason |
|---|---|---|
| S1: Horizon seven years; annual rebalancing. | Hard constraint | Seven years sets the planning horizon; annual rebalancing is a stated implementation rule. |
| S2: CPI + 4% a year, net of costs, over rolling five-year periods. | Objective | Specifies the return sought, its inflation and cost basis, and its evaluation window; it is a target rather than a guaranteed outcome. |
| S3: $0.75 million quarterly payouts; twelve months held in cash or daily-liquid government securities. | Hard constraint | Requires a $3 million payout reserve, equal to 3% of the $100 million portfolio. |
| S4: Benchmark of 60% global equities and 40% U.S. investment-grade bonds. | Preference / evaluation reference | Establishes the performance comparator; it does not expressly require portfolio weights of 60/40 or prohibit other holdings. |
| S5: Long-only; no borrowing, short sales, or derivatives. | Hard constraint | Explicitly restricts permitted positions and financing methods. |
| S6: No single issuer above 8%. | Hard constraint | Caps combined exposure to one company at 8%, subject to the stated exemptions. |
| S7: Annual turnover at most 25% without committee approval. | Hard constraint, with an approval exception | Turnover above 25% requires committee approval; annual rebalancing does not waive this rule. |
| S8: At least 90% redeemable within five business days. | Hard constraint | Establishes a measurable portfolio liquidity minimum. |
| S9: No calendar-year loss greater than 10%, without a measure or breach rule. | Unverifiable promise as stated | A future loss ceiling cannot be assured from these holdings; the loss definition, evaluation method, and required response are unspecified. |
| S10: No sector, ESG, tax, or home-bias preference; pilot optimization unspecified. | Missing | Those preferences are explicitly absent, but the criterion the pilot should optimize has not been chosen. |

S4 should be recorded and used in evaluation, not silently converted into an exact-allocation constraint. S9 expresses a downside concern that needs an operational definition before it can be tested as policy.

## Candidate checks

Twelve months of payouts = 4 x $0.75 million = **$3 million**, or **3%** of the reserve. Reserve eligibility follows the supplied table, including the Treasury 10-year note. Its liquidity does not imply stable market value.

Five-day liquidity includes every listed holding except the private real estate fund. Cash, Treasuries, and diversified funds are exempt from the issuer cap. Acme stock and bonds must be combined.

| Check | A | B | C |
|---|---|---|---|
| Weights total 100% | Pass: 100% | Pass: 100% | Pass: 100% |
| Long-only, fully allocated, permitted instrument types (S5), based on supplied holdings | Pass | Pass | Pass |
| Reserve-eligible holdings at least 3% (S3) | Pass: 14%, or $14m | Fail: 1%, or $1m | Fail: 2%, or $2m |
| At least 90% redeemable within five days (S8) | Pass: 100% | Fail: 85% | Pass: 100% |
| Nonexempt issuer exposure at most 8% (S6) | Pass: none | Fail: Acme 5% + 4% = 9% | Pass: Acme exactly 8% |
| Annual turnover rule (S7) | Unverified | Unverified | Unverified |
| Seven-year implementation and annual rebalancing (S1) | Unverified | Unverified | Unverified |
| CPI + 4% objective and loss concern (S2, S9) | Not established by holdings | Not established by holdings | Not established by holdings |

**A is the only candidate that passes all supplied, directly testable holdings constraints.** It is eligible for further evaluation, subject to unresolved implementation and risk questions. This does not establish that it will achieve the return objective or avoid a loss greater than 10%.

**B is not permitted as submitted:** it has a $2 million payout-reserve shortfall, only 85% five-day liquidity, and 9% combined Acme exposure.

**C is not permitted as submitted:** it has a $1 million payout-reserve shortfall. Its 8% Acme position is allowed at the stated limit; its equity allocation differs from the benchmark but is not prohibited by S4.

Turnover cannot be inferred from target weights alone. It requires the starting holdings, trading path, measurement convention, and any relevant committee approval.

## What the CIO must answer before optimization

1. **Choose the optimization criterion.** Is the pilot to minimize the risk of failing CPI + 4%, minimize risk while targeting that return, minimize benchmark tracking error, or pursue another explicitly approved goal? S2 is a performance objective but does not fully specify the optimization problem.
2. **Define the loss concern.** Does the 10% refer to calendar-year total return, a decline in portfolio value after payouts, or peak-to-trough drawdown? Is it an aspiration, a modeled probability limit, a stress-test threshold, or a binding policy trigger? Specify the measurement basis, monitoring responsibility, breach response, and escalation authority.
3. **Clarify horizon and cash-flow treatment.** How do rolling five-year evaluation periods operate within the seven-year horizon? Are quarterly payouts fixed or inflation-linked, and how is the twelve-month reserve replenished?
4. **Confirm the benchmark's role.** Is 60/40 only a comparator, or are there intended allocation bands or tracking-error limits? None are supplied, so they cannot be assumed.
5. **Define implementation conventions.** Specify turnover measurement, approval timing, annual rebalancing dates, and how liquidity and issuer limits are maintained between reviews.
6. **Approve model inputs and feasibility handling.** Establish expected returns, inflation, risks, correlations, and all-in costs consistently with the mandate. If no portfolio meets the approved objectives and constraints, report infeasibility and identify who can authorize a policy change.

The case facts support a compliance screen. They do not supply enough information to rank the candidates by expected investment performance or to run a defensible optimization.
