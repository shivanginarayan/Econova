# Production, stock shortages, and supplier recovery

Milestone 9 connects supplier materials to the goods households can actually buy. New worlds use `production_model: "finite_v1"`. The existing API, playback, forks, credit reviews, and procurement workflows share that same inventory state.

## Rules

New businesses start with zero finished goods. `standard` and `credit_crunch` give every business 1,000 generic raw-material units at zero opening book cost. `supply_crunch` uses the standard financial starting conditions but gives Business 1 zero raw materials; other businesses retain 1,000 units. This is a disclosed starting shortage, without a hidden asset loss or financial transaction.

Each day, an active business can use one raw-material unit per employee to produce ten finished goods per material unit. Output is limited by available materials and the current workforce. For example, five employees and two material units produce 20 goods. No employees or no materials means zero new output. This conversion ratio is a synthetic demo assumption. Payroll remains an immediate expense; material costs are carried in inventory until sale. One missed payroll day does not itself stop production; the existing default rules determine when the business closes.

Unsold goods carry forward. A household retains its seeded seller choice and spending budget, then buys the lesser of affordable whole units and that seller's stock. There is no fallback seller search. Closed businesses are skipped. An empty seller makes no sale, and the household retains its cash. Insufficient materials do not directly close a business; reduced sales can create later cash and payroll pressure.

Due supplier bills settle before payroll preparation. After loan maturities, wages, and payroll-default checks, active businesses produce, then households buy. Businesses that default earlier that day cannot produce or sell. Closed businesses retain their inventory at book value; liquidation, spoilage, and impairment are not modeled.

## Accounting and audit

Production transfers pooled material cost from the `materials` asset to the `goods` asset without creating deposits or profit. Consuming `u` units from `s` units with carrying value `c` transfers `floor(c × u / s)` cents. Remaining inputs retain rounding cents.

A retail sale settles the household payment, bank liabilities/reserves, sales revenue, and cost of goods sold **in one journal entry**. Selling `q` goods from `g` goods carrying value `v` expenses `floor(v × q / g)` cents. Selling the last unit releases all remaining cost. Quantity falls only after the ledger accepts the complete entry. Rejected payments preserve both stock and money; exact transaction retries do not sell twice.

The audit reconstructs finished-goods quantities from production and purchase journal metadata and compares them to physical stock. It also checks that zero stock has zero carrying cost, in addition to the existing financial and counterparty checks. `goods_inventory_matches` is true for verified finite worlds and null for older unlimited worlds.

## Inspector, metrics, and events

Business responses add `goods_units`, `last_produced_units`, and `production_capacity_units`, alongside `materials_units`. Capacity is the current active workforce times ten, before material constraints. Inventory value appears under `balance_sheet.assets.goods`. Credit facts and buyer offer inspection include inventory observations for model decisions.

Metrics and fork timelines add:

| Field | Meaning |
| --- | --- |
| `finished_goods_units` | Current total physical goods, including stock retained by closed firms. |
| `produced_units_this_tick` | Output created during the current tick. |
| `sold_units_this_tick` | Goods successfully sold during the current tick. |
| `unmet_demand_units_this_tick` | Attempted affordable units unfilled because the chosen active seller lacked stock. |

Flow counters reset each tick; they are not cumulative. Financially rejected purchases and choices of closed firms are not counted as stock-related unmet demand. Legacy unlimited worlds report zero for these untracked metrics; use `production_model` to label them correctly. Fork reports include final inventory/flow deltas while retaining their original employment-first ranking.

Use these SSE event types in the city and inspector:

- `goods_produced`: business, materials used, output quantity, and transferred carrying cost.
- `production_limited`: required/used materials, unproduced capacity, and shortage reason.
- `purchase`: household/seller, actual paid amount, quantity, unit price, and cost of goods sold.
- `purchase_stock_limited`: requested, fulfilled, and unmet quantities, including zero-stock attempts.

## Runnable shortage-to-restocking demo

Start the API using [the README](../README.md), then run in PowerShell:

```powershell
$world = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/worlds -ContentType application/json -Body '{"seed":42,"scenario":"supply_crunch"}'
$base = 'http://127.0.0.1:8000/api/worlds/' + $world.simulation_id
Invoke-RestMethod -Method Post -Uri "$base/step" -ContentType application/json -Body '{"ticks":1}'
Invoke-RestMethod -Uri "$base/entities/business_1"
$run = Invoke-RestMethod -Method Post -Uri "$base/businesses/business_1/procurement-runs" -ContentType application/json -Body '{"request_id":"restock-1","mode":"demo","quantity":20,"max_total_cents":100000,"auto_settle":true}'
$run.status
Invoke-RestMethod -Method Post -Uri "$base/step" -ContentType application/json -Body '{"ticks":1}'
Invoke-RestMethod -Uri "$base/entities/business_1"
Invoke-RestMethod -Uri "$base/audit"
```

At tick 1, Business 1 produces zero goods. The procurement workflow delivers 20 material units and creates the matching invoice. At tick 2, its five employees use five material units to produce 50 goods, and households can buy from it again. See [the calculated production demo](./production_demo.json) for the real trace, sales, balances, and audit. For frontend use, [background procurement jobs](./AGENT_JOBS.md) accept the same request body; wait for the job/report result before advancing.

Show the material shortage on Business 1, open its supplier negotiation, then animate production and actual sales after settlement. Use current backend quantities; output and sales need not be equal. The deferred invoice still follows existing due-date/default rules. This workflow does not automatically schedule future procurement.

## Compatibility and limits

Saved worlds without a production-model marker keep `legacy_unlimited` behavior, including the previous direct material-consumption expense. Loading them does not grant goods or add inventory accounts. Their existing snapshots and historical reports remain intact. Create or reset a world to use the current production model; reset preserves the source history and starts a new world under current rules.

Raw materials remain a finite genesis endowment shared among businesses. Supplier trades redistribute them; there is no external producer or automatic replenishment. Long runs can exhaust the economy's inputs. Production, stock, cost basis, and invoices persist and remain isolated in Fork Reality. The model does not include price adaptation, shipping delays, input-specific recipes, capital investment, or real-world calibration.
