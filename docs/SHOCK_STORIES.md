# Sourced crisis stories

The first supported story is **What if US public debt rises by 25%?** It combines dated Treasury context with a transparent conditional bond stress. It does not forecast how national debt affects interest rates, and does not claim war, oil, tax or government-budget mechanics are implemented.

## UI walkthrough

1. Create a world (Credit crunch is available for stressed starting conditions) and pause it.
2. Open **Build a sourced crisis story** in the live-events sidebar.
3. Select the bank and hypothetical debt increase (default 25%).
4. Independently choose a yield increase, assumed modified duration, and bond exposure share.
5. Click **Load Treasury data and preview**. Inspect actual debt, its observation/retrieval dates, the hypothetical debt level, model assumptions and calculated investment loss. No balances change.
6. Click **Apply this story shock**. A journaled loss reduces the selected bank's risky investments and equity, with a provenance event. Deposits are not directly reduced.
7. Before advancing, use **Fork Reality** and **Test rescue policies**. Nemotron's inspection tool receives the saved story and its hypothetical assumptions.
8. Apply a recommendation if desired, then play/step and inspect the calculated lending, payroll and spending effects. A mild stress may have little effect; a crisis is not forced.

Refresh restores saved evidence. Viewing older previews is allowed, but application requires the exact unchanged world snapshot and paused playback. Repeated application of the same report returns its original receipt, including after later ticks; it never applies another loss. Different reports are separate intentional shocks.

## Data and calculation

The keyless [Treasury Debt to the Penny API](https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?sort=-record_date&page%5Bsize%5D=1) returns total public debt outstanding. The [Treasury dataset](https://fiscaldata.treasury.gov/datasets/debt-to-the-penny/debt-to-the-penny) includes publicly held and intragovernmental debt. This national dollar figure is context, not an opening balance on the simulated government's ledger. Decimal arithmetic preserves cents. Missing/invalid API responses stop preview; no fixture or guessed number is substituted. Observations over seven days old are flagged visibly.

Hypothetical debt = observed debt × (1 + chosen increase / 100).

Estimated risky-portfolio loss fraction = assumed bond exposure fraction × modified duration × yield increase / 10,000.

Defaults: 25% debt increase, **separate illustrative** 200-basis-point yield rise, five-year duration, 50% bond exposure. This produces a 5% risky-portfolio haircut, **not a 25% haircut**. The debt increase is not used to infer the yield change. Holding the yield assumption fixed while changing debt growth leaves the bank loss unchanged. Zero yield change or zero exposure produces no bank loss and cannot be applied as a financial shock.

This uses a first-order duration approximation, excluding convexity, hedges, maturity schedules and held-to-maturity treatment; larger moves reduce approximation quality. The engine immediately recognizes the assumed loss. Exposure/duration are not sourced holdings, and the economy remains synthetic. A policy change or war could motivate a hypothetical input, but the software does not claim a causal mapping from such events. Oil cost pass-through needs a separate real price adapter and production-cost model before it can be presented as supported.

## API

- `POST /api/worlds/{id}/shock-stories/preview`: optional `bank_id`, `debt_increase_percent` (0–100), `yield_increase_bps` (0–500), `modified_duration_years` (1–10), `portfolio_exposure_percent` (0–100). All numeric inputs are integers. Each preview saves immutable evidence; it moves no money.
- `GET /api/worlds/{id}/shock-stories`: latest 50 saved reports with current applied/preview status.
- `POST /api/worlds/{id}/shock-stories/apply`: `{"report_id":"evidence_..."}`. Uses a report-specific transaction key, paused state, snapshot validation, atomic journal/event persistence and audit.

Verify with `python -m pytest tests/test_shock_stories.py -q`. With both development servers running, `node scripts/qa-shock-story.mjs` uses the live Treasury API in a fresh test world, validates preview/application/retry, agent context, forks, persisted evidence and mobile layout. It makes no live model calls or external payments.
