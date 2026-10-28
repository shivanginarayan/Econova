# Econova operating model: cashflow_v2

Implemented October 28, 2026. This corrects incompatible toy operating assumptions; it is not an empirically calibrated forecast.

## What was wrong

The earlier model combined a full daily wage reference with ten sale units per worker per day and an unrelated fixed household spending cap. For the recorded public sample, a business selling its entire output could cover only about28–35%ofpayroll. Longer no-shock failures were therefore structurally built in. The prior settlement correction did not solve this separate mismatch.

## Revised assumptions

A new economy stores operating_model=cashflow_v2 and a frozen operating_assumptions object. Existing snapshots without the marker retain legacy_v1 behavior. Production/inventory accounting remains finite_v1; the separate settlement version remains unchanged.

1. **Consistent units and capacity.** Each business receives an opening integer output-per-worker coefficient calculated as `ceil(initial daily payroll ×1.25 / (initial workers × selected unit price))`. One material unit continues to represent a worker-day of inputs. The25%capacity headroom is a declared benchmark parameter, not an observed profit margin, guaranteed revenue or measured barista productivity. Units represent a composite model good using the observed price scale, not a claim that every household spends its income on cafe drinks. Capacity stays frozen per worker; layoffs reduce total output. Firms still need workers/materials and actual buyers.

2. **Income and wealth spending.** The household budget is `min(available deposits, 90%of wages actually received this step +5%of deposits excluding those new wages)`, rounded down to integer cents. Unpaid wages do not count as income. Unemployed households can use savings. A household transfer raises wealth; it is not invented employment income. The coefficients are explicit assumptions, frozen with the world. The income/wealth rule replaces the arbitrary fixed-dollar cap.

3. **Actual shopping.** Households draw a repeatable weighted basket from opening market-size weights, split initial demand across two preferred businesses and can redirect unspent money to other operating, stocked businesses. The two preferred shops can be revisited for remaining inventory. Each purchase requires real deposits, goods, a permitted payment and a journal entry. No business receives a balancing transfer or guaranteed sale. Integer-price rounding can leave money unspent. Preference draws include unavailable sellers before eligibility checks so branch differences do not redraw the initial preferences.

4. **Routine liquidity management.** At the start of a day, a solvent bank may convert recorded marketable investments into reserves toward20%ofdeposit liabilities. This uses the existing model’s carrying-value conversion assumption. It exchanges two asset categories; total assets and equity do not increase. Insolvent banks are skipped. It is neither central-bank support nor recapitalization. The assumption of liquidity at carrying value is optimistic; market discounts, trading counterparties and comprehensive resolution are not modeled. Public support remains an explicit separate action.

5. **Unchanged failure constraints.** Bank capital/liquidity checks, borrower limits, refinancing, missed-payroll defaults, finite inventory and layoff caps still apply. Strong shocks and input shortages can still cause failures. The fix does not remove defaults or freeze employment.

## Why this is a coherent benchmark

Income is paid through existing accounts. Household spending depends on received income and accumulated deposits; it need not remain permanently disconnected from the wage scale. Opening capacity can cover the selected payroll scale without guaranteeing that demand arrives. Cash moves between households and firms through actual purchases. Savings, debt, inventory and bank constraints can still change the outcome. Balanced accounting remains necessary but does not validate the behavior empirically.

## Backward compatibility

The engine branches on the saved operating marker; old states are not migrated. Forks inherit the source state and parameters. Reset repeats the original operating version and frozen coefficients, even if defaults for future worlds change. Legacy unlimited-production states keep their old purchasing behavior. The API exposes operating version/assumptions, actual last-step household budget and received wages, and correct capacity. The fixed-cap field is null for new-mode households. The UI warns about older experiments and lists the revised assumptions. Use New experiment to adopt cashflow_v2; resetting an old economy deliberately repeats its old assumptions.

## Evidence

[Operating-model comparison](./evidence/operating-model-comparison.json) retains120matchedbranches and480checkpoints: two operating versions, synthetic/frozen public input modes, strong/fragile bank scenarios, seeds41–45, losses0/10/40%, and days6/12/30/60. The settlement version is held constant to isolate the operating change. Every checkpoint audit balanced and all source snapshots remained unchanged. Three additional parameter-sensitivity cases are recorded separately, not counted as extra matched checkpoints.

At day60, all20new-mode no-shock cases have zero business defaults and no public support. Employment ranges92.5–95%; the small difference permits actual stress layoffs rather than artificially fixing employment. New synthetic fragile40%-loss cases range50–70%employment; public fragile40%-loss cases range0–70%. Strong-bank cases absorb the tested losses. Equal endpoints and full failures are retained. The no-shock mechanical collapse was corrected without removing the shock pathway.

The seed42public no-shock sensitivity cases using income/wealth coefficients80%/2%,90%/5%and100%/10%all retain95%employment atday60. This small joint-parameter check is not a statistical sensitivity analysis or proof of robustness to all assumptions.

Reproduce with `python -m scripts.evaluate_operating_model --calibration-id <saved-public-id>`. No new collection, AI inference, existing-world mutation or automatic public transfer occurs in this evaluator. The frozen sample ID/hash is in the evidence. Missing selected input files fail explicitly.

## Regression and functional verification

The backend full run passed267tests with one optional skip. Final actual-budget API metadata changes then passed30targetedoperating/API/playback tests. Frontend96tests and production build passed. Tests cover received-versus-unpaid wages, budget bounds, finite production/cost accounting, liquidity conversion without equity creation, no automatic rescue of insolvent banks, deterministic legacy replay, preserved reset parameters, and five public-fixture60daycontrols. Older tests tied to ten-unit output now use actual unit/cost calculations; legacy-specific deterioration tests explicitly request legacy_v1.

The complete clean-browser investigation flow passed with the updated backend: create, shock, observation ending, business evidence, three alternate worlds, supervised deterministic agent evidence, rescue comparison, refresh/resume and mobile, with no source mutation. This is functional verification, not validation by an unfamiliar human.

## Limits that remain

These are benchmark assumptions. There is no estimated probability of a40%loss, empirically measured consumption behavior, complete interest-rate policy, job-recovery labor market, realistic market-depth/liquidation model or validated customer decision rule. Finite materials eventually require procurement;60days does not mean perpetual equilibrium. Larger or different shock targets, parameters and horizons can produce different outcomes. Live agents and supervisors may err; their reviews do not replace deterministic checks or human judgment.
