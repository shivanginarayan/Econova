# Financial assumptions reconciled with public payroll and bank ratios

This revision keeps Econova's task: financial agents investigate bank shocks, negotiate credit and compare rescue policies. It changes financing conventions for new sourced worlds. It does not turn aggregate statistics into actual customer records or a real-world forecast.

## Findings and changes

1. **The fixed dollar loan cap was inconsistent with payroll scale.** The old $5,000 cap applied to every business. Census-derived daily worker pay and sampled employer sizes can produce much larger payrolls. New `working_capital_v2` worlds freeze a business credit line equal to20days of its opening payroll. The bank still cannot lend above five times its equity, cannot lend while insolvent, and still applies the model capital/liquidity checks. A large credit line is not an automatic loan: only an actual funding gap requests credit. Agent facts, underwriting maturity, UI request caps and engine checks now share the same effective limit. Human approval and explicit settlement remain in force. Historical worlds retain their original nominal cap.

2. **Cash buffers were independent of the size of the business.** Previously, a seeded cash amount between$5,000and$9,000 could represent very different numbers of payroll days. New sourced worlds start with five payroll-day equivalents. These are explicit opening endowments with matching bank/customer deposit entries, not sales, bailout money or an ongoing balancing transfer. They are not observed cash holdings. The credit-crunch scenario still includes its disclosed startup financing and setup-cost transfer; it is not an estimate of actual founding costs.

3. **Settlement confused temporary cash composition with insolvency.** A bank could hold positive equity and assets the model already treats as convertible at book value, yet reject payroll after earlier transfers exhausted its reserves. New financing rules include the required asset conversion in the same atomic ledger transaction as an outgoing customer/supplier payment. Failed customer payments cannot partially liquidate bank assets. No equity is injected, no interbank money is invented, and an insolvent bank remains frozen. The liquidity-health check uses cash plus the same assumed convertible assets; the separate cash/deposit ratio remains available. This is an optimistic saleability assumption, not a measured market depth or regulatory liquidity coverage ratio. A frozen market, haircut or counterparty model is still absent.

4. **Payroll and review dates mixed incompatible time scales.** Census annual payroll is divided by March reference-week employees and an assumed260paid workdays. This is a daily payroll equivalent, not a claim that the actual employees are all full-time or paid every day. For new sourced worlds, loan review/maturity intervals are20workday-equivalent simulation steps instead of five. Existing loans keep their scheduled review date when a draw is added. The engine continues to use compressed daily-equivalent payroll and a two-missed-step default rule, which remains much faster than many actual failures. A calendar, taxes, benefits and real paycheck scheduling are not implemented.

5. **Operating costs are incomplete.** The engine records actual wages, actual supplier payments, material inventory carrying value and cost-of-goods-sold entries. Opening material endowments currently have zero carrying value; recorded procurement adds a cost basis. Rent, taxes, interest, utilities, depreciation and other nonpayroll overhead are not estimated from CBP, because payroll totals do not supply those costs. BEA consumption/saving observations are national context, not estimates of individual business margins or household marginal spending propensities. We have not invented overhead to make a desirable trajectory. Results concern this wage/credit/material model, not fully measured business profitability.

## What is observed and what remains assumed

The FDIC capital/assets and cash/assets cohort ratios and Census payroll/employment/establishment totals retain their frozen observation records. Bank scale, customer assignments, employer sampling, opening cash, credit-line multiples and loan review periods remain derived mappings or explicit assumptions. The new financial version and coefficients are stored in each world and survive forks and reset. Saved worlds without the version marker keep `fixed_limits_v1`, including the first experimental public mapping.

The cashflow_v2 spending rule, capacity headroom, asset conversion at carrying value, finite goods/materials, and credit-crunch network assumptions remain separately documented. In particular, 25%capacity headroom is not a measured profit margin, and 90%of wages plus5%of other deposits is not calibrated to the national saving rate. Real inputs do not validate those rules.

## Evaluation and promotion criteria

The updated matched script retains the original synthetic assumptions, the first public mapping with fixed financing, and the new payroll-scaled version. It uses the same five seeds41–45, standard/credit-crunch starting scenarios, losses0/10/40%, and checkpoints1/6/12/30/60. Every branch starts from an unchanged cloned source. There is no automatic support. All cases are retained.

The demonstration regression gates require balanced accounting/unchanged sources, no no-shock business defaults, at least90%employment in all no-shock checkpoints, and lower step60employment in each standard40%shock case than in its matched no-shock control. These are engineering acceptance criteria, not an estimate of a real crisis or a claim of equilibrium. The exact public menu-price sample is checked separately, alongside shorter3/10/10and longer10/40/40opening-buffer/credit-line/review conventions.

Evidence and results are recorded below. Failure of an acceptance gate must remain visible and must block promotion; do not silently select a favorable seed or change the shock to hide it.

## Reproduce

```powershell
.venv/Scripts/python.exe -m scripts.evaluate_public_benchmarks --output artifacts/reconciled-public-evaluation-final.json
.venv/Scripts/python.exe -m scripts.evaluate_financing_sensitivity
.venv/Scripts/python.exe -m pytest tests/test_financing.py tests/test_public_benchmarks.py tests/test_credit.py -q
```

The sensitivity script requires the actual saved Apify calibration; it does not silently substitute one. Statistical definitions: [Census payroll units](https://api.census.gov/data/2023/cbp/variables.html), [FDIC financial data](https://api.fdic.gov/banks/docs), [BEA saving-rate definition](https://fred.stlouisfed.org/series/PSAVERT).


## Results: improved controls, promotion held

[The final matched evaluation](evidence/reconciled-public-evaluation.json) retains all450checkpoints across90branches. All accounting and source-integrity checks passed; no public support was applied. Under the new conventions, all ten sourced no-additional-shock cases avoided business default. Standard controls ended at92.5–95%employment and credit-crunch controls at95%. The10%loss cases were absorbed in this tested grid. With40%losses, standard cases ended at35–95%employment and credit-crunch cases at0–35%. Differences are outcomes of the disclosed model, not forecasts.

The strict gate requiring every standard40%shock case to lose jobs **failed**. We retained it as failed; we did not select a different seed or modify the shock to force unemployment. That criterion is also narrower than the financial question: a bank can lose capital and stop offering new credit while its existing business customers keep operating from their cash. Direct measurements in the actual-menu cases show capital/assets falling from10.38%to between-6.19%and2.32%after the40%portfolio loss. All five banks were financially damaged (three stressed, two insolvent), even where employment remained95%. The UI and narrative must distinguish absorbed investment damage from business/job losses.

[The actual-menu and sensitivity evaluation](evidence/reconciled-financing-sensitivity.json) retains60checkpoints across20branches. With the default5/20/20conventions, all five no-shock controls stayed at95%employment and had no business defaults through step60. For the existing demonstration seed42, the matched40%loss case ended at35%employment with three defaults, compared with95%and zero defaults in its control. The three other absorbed cases remained employed; seed44ended at55%with three defaults.

Shorter3/10/10buffer/credit/review assumptions exposed failures in seeds43and45: no-shock employment fell to57.5%and62.5%, respectively, with one default each. Longer10/40/40cases remained at95%. [Diagnostics](evidence/reconciled-financing-diagnostics.json) show the shorter cases first failing salary settlement because the business bank lacked reserves at steps58and57. On-demand sale of the bank's remaining investments did not supply enough liquidity. Dynamic private wholesale funding, asset haircuts/markets and funding counterparty limits are not modeled; we did not silently add central-bank support or unlimited credit to remove these failures.

**Promotion decision: hold.** The default demonstration now clearly separates a healthy control from a damaged shock case for the existing seed, but the funding sensitivity remains unresolved. Public starting conditions stay opt-in and visibly experimental. This preserves the user's requested order: reconcile, evaluate, and promote only once the remaining result is defensible. The smaller-buffer failures and the failed strict employment gate remain published alongside successful controls.

## Verification

The complete backend suite passed284tests with one optional skip. Two additional financing-evidence checks were then added and verified in the targeted suite. Frontend96tests passed; the production build passed with its existing large-bundle warning. New tests verify proportional cash/credit, bounded lending, maturity, atomic asset conversion, failure rollback, insolvency freeze, historical limits, reset and agent facts. Chrome runtime verification passed with the actual public menu-price sample: all starting banks healthy, source-specific limits visible, expanded assumptions readable, no page exceptions or mobile overflow. The standard seed42world moved from95%employment to57.5%after six consequence steps following the40%shock. These tests establish accounting/functionality, not empirical accuracy or a human usability result.
