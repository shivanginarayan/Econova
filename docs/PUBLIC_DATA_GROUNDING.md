# Public-data grounding for Econova

Econova can use real aggregate observations to inform a synthetic economy. A real observation is not the same thing as a real bank, a real business, or a validated economic rule. This revision adds an explicit **experimental** opening mode and a separate reference layer. It preserves the core bank-crisis investigation project and existing saved experiments.

## What is implemented

1. **FDIC bank financial ratios.** The collector discovers the latest published financial quarter, then retrieves the complete US reporting cohort with assets from $100 million to $10 billion. It rejects truncated or mixed-quarter responses. It excludes invalid/nonpositive-equity records and reports the exclusion count. It derives the median institution equity/assets, cash-and-balances-due/assets, and deposits/assets ratios. The first two can inform synthetic opening banks; the third is reference context. This is a size cohort chosen by the model designer, not an empirically selected peer group or a picture of every bank.

2. **Census business payroll and structure.** The collector reads the official 2023 national County Business Patterns ZIP. This avoids needing a Census API key for these published bulk observations. It uses all-legal-form totals for manufacturing (31–33), retail trade (44–45), and accommodation/food services (72). Published employment, annual payroll and establishment counts are retained with noise flags. These three sectors are a deliberately limited slice, not the whole US economy. Employment refers to the March reference week; payroll covers the year. Dividing annual payroll by that employment count gives a useful benchmark, not a longitudinal mean salary. Missing or suppressed totals are rejected rather than made zero.

3. **Federal Reserve interest and credit context through FRED.** FEDFUNDS supplies the monthly effective federal funds rate. DRTSCIS supplies the quarterly net share of banks tightening small-firm commercial/industrial loan standards. A net survey balance is not a business loan rejection rate. These are displayed and frozen as context. Econova's loans still track principal; interest accrual and refinancing-rate transmission have not been implemented.

4. **BLS earnings and ACS income.** FRED provides the BLS full-time worker median nominal weekly earnings and 25th/75th percentile benchmarks. The median series is seasonally adjusted; the quartiles are not. The collector does not fit a distribution across those inconsistent adjustments, or mistake worker earnings for household income. The ACS B19001 adapter retains all income-bin estimates and 90% margins of error from the 2019–2023 five-year release, in 2023 inflation-adjusted income categories. Live ACS retrieval currently requires a locally configured CENSUS_API_KEY. No such key was configured when verified. No household-income distribution is applied to behavior yet.

5. **BEA consumption benchmarks through FRED.** PCE, DSPI and PSAVERT supply consumption, disposable income and the saving rate. PCE/DSPI is derived only when the two monthly observation periods match; their common annual-rate dollar units cancel. This is an aggregate average spending share, not a marginal propensity to consume. These observations are reference context. BEA industry input-output coefficients, crosswalks into the three-sector slice, and empirical supplier relationships remain unfinished. Current finite materials, production capacity and supplier contracts remain model assumptions.

6. **Matched simulation evaluation.** The evaluation runs both the existing opening assumptions and the experimental sourced mapping across seeds41–45, standard/credit-crunch scenarios, losses0/10/40%, and checkpoints1/6/12/30/60: 60 branches and300 checkpoints. It retains every case, checks accounting and unchanged source snapshots, and applies no rescue automatically. This measures sensitivity and internal behavior; it cannot establish real-world predictive accuracy.

## Provenance for every imported value

Each observation records parameter name, value, unit, official source, safe source URL, observation date/period, retrieval time, conversion, classification and usage. Classification is **observed**, **derived**, or **assumed**. Observed means published statistical estimate, not perfect knowledge. Derived means an explicit calculation from published values. Assumed marks the model designer's mapping and conversion choices.

Usage distinguishes opening bank ratios, opening worker wages, relative business size, and validation-only context. Census payroll's daily conversion explicitly assumes260 paid workdays per year: `annual payroll in thousands ×100000 / March employees /260`, rounded to integer cents. These are paid-workday equivalents; the rest of the engine still uses abstract simulated daily steps, not a complete calendar with weekends, taxes and benefits.

Snapshots have content-derived IDs and SHA-256 integrity checks. Refreshing creates another snapshot; each world freezes its entire selected record. Forks inherit it. Reset reuses the frozen snapshot even if the original cache file is gone. Missing/invalid selected observations cause a visible error, never an unannounced synthetic replacement. FRED values are the latest revised data at retrieval, not historical real-time vintages. Different datasets have different periods; their combination is not a single-date measured economy.

## How sourced opening conditions work

Select **Starting economy & data settings**, then the experimental FDIC/Census checkbox before starting an investigation. Cached economic observations load on opening the page. Existing public price/wage collection continues separately. Census-derived pay overrides the Apify minimum-wage reference in this mode; the menu-price sample can still supply prices. The legal minimum wage remains a reference, not a claim about actual worker earnings.

Each synthetic business is assigned one of the three industries using establishment weights. Workers are allocated using relative employees per establishment. Each household remains one worker proxy. These sampled assignments are assumptions; Census does not disclose the actual firms, workers or employer links. Small samples can be unrepresentative. Census does not supply starting business cash, creditworthiness, turnover, net worth, customer-bank links, or household wealth.

Opening bank assets are solved from synthetic total liabilities and the median capital ratio: `assets = liabilities / (1 - equity/assets)`. Cash/assets sets opening reserves; equity is the balancing opening endowment. Existing synthetic loans/interbank assets are retained and the residual becomes the engine's pooled shockable asset account. This residual is **not observed risky securities**. Cash/balances due from banks is broader than central-bank reserves. These proxy mappings are disclosed in the snapshot. A mapping incompatible with the existing synthetic exposures fails instead of clamping negative values. FDIC accounting equity/assets is not a risk-weighted regulatory capital ratio, and the model's8%health threshold is not a reproduction of banking regulation.

The median ratios do not make banks actual institutions, determine a war effect, or estimate shock probabilities. The existing interbank ring, liability mix, lending caps, daily liquidity conversion and default/layoff rules remain assumptions. The selected starting scenario still supplies synthetic business financing and network structure; FDIC ratios override its initial bank capital/cash proportions.

## What the first evaluation found

The initial dated evidence is [public benchmark evaluation](evidence/public-benchmark-evaluation.json). It contains the exact snapshot used; a subsequent collection added more reference series without changing its FDIC/Census opening profiles.

All300 checkpoints balanced, and every source snapshot remained unchanged. Existing no-shock controls remained at95%employment at step60. The sourced standard controls ranged from57.5%to95%employment, with zero or one business default. The sourced credit-crunch controls remained at95%employment without additional shocks. Severe40%losses produced17.5–47.5%employment in sourced standard cases and0–57.5%in sourced credit-crunch cases. These outcomes are model results, not real-world estimates.

The [control diagnostics](evidence/public-benchmark-diagnostics.json) identify concrete mechanisms. Seed42 first hit the fixed$5,000 borrower limit at step31. Seed43 recorded a bank-reserve payroll rejection at step15. Seed45 recorded reserve-related purchase rejections at steps9–10 and a payroll rejection at step12. These are recorded proximate failures, not a complete causal decomposition. Sourced nominal wages coexist with synthetic opening wealth, fixed dollar caps and stylized intraday settlement. Simply raising cash or caps until employment stays high would not validate those assumptions.

This is a **failed economic acceptance gate for making the sourced mode the default**. Real wage and firm-size benchmarks expose weaknesses rather than prove improved realism. Keep this mode opt-in and visibly experimental. Investigate operating cash runways, concentration of demand, fixed dollar credit caps, finite material replenishment and compressed payroll/default timing before promoting it. Do not tune the parameters solely until control curves look healthy. Some job losses may be consistent with deliberately fragile starting conditions; unexplained deterioration in standard controls still needs a defensible explanation.

## Reproduce locally

Use the configured Python environment from the repository root:

```powershell
.venv/Scripts/python.exe -m scripts.collect_public_benchmarks
.venv/Scripts/python.exe -m scripts.evaluate_public_benchmarks
.venv/Scripts/python.exe -m scripts.diagnose_public_benchmarks
.venv/Scripts/python.exe -m pytest tests/test_public_benchmarks.py -q
```

The collector has bounded official endpoints and reports source failures individually. It does not call an LLM. It saves observations under ignored `data/benchmarks`; the browser/API reads the saved snapshot instead of repeatedly contacting statistical services. Rerun the collector intentionally to get another dated vintage. Add CENSUS_API_KEY locally for ACS; never commit it. The local backend launcher supports that setting and ECONOMY_BENCHMARK_DIR. There is no new hosted service or automatic submission.

## Official definitions and data

- [FDIC API and financial report definitions](https://api.fdic.gov/banks/docs)
- [FDIC field examples](https://s3-us-gov-west-1.amazonaws.com/cg-2e5c99a6-e282-42bf-9844-35f5430338a5/downloads/Use_the_API_with_Examples.pdf)
- [Census CBP variables and payroll units](https://api.census.gov/data/2023/cbp/variables.html)
- [Census CBP2023 downloads](https://www2.census.gov/programs-surveys/cbp/datasets/2023/)
- [ACS B19001 estimates and margins](https://api.census.gov/data/2023/acs/acs5/groups/B19001.html)
- [FEDFUNDS definition](https://fred.stlouisfed.org/series/FEDFUNDS)
- [Small-firm credit standards definition](https://fred.stlouisfed.org/series/DRTSCIS)
- [BLS first-quartile earnings](https://fred.stlouisfed.org/series/LEU0252911300Q)
- [BEA consumption](https://fred.stlouisfed.org/series/PCE), [disposable income](https://fred.stlouisfed.org/series/DSPI), and [saving rate](https://fred.stlouisfed.org/series/PSAVERT)
- [BEA input-output accounts](https://www.bea.gov/industry/input-output-accounts-data)

## Verification of this implementation

Backend:276passed,1optional skip. Frontend:96passed. Production build passed with the existing large-bundle warning. Chrome verified selecting the real saved snapshot, creating a frozen world, viewing observation conversions, refreshing/resuming and mobile width without page errors. These checks establish functional behavior, not economic accuracy or human usability. No live model reliability evaluation was repeated because the inference workflow was unchanged.
