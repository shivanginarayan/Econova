# Connected UI: alignment and setup

Upstream commit `a924311` supplied the globe, San Francisco miniature, responsive shell and fixture storyboards. The connected entry point keeps that visual direction and uses the Python backend for financial state and actions.

| Agreed direction | Pulled UI | Connected behavior |
| --- | --- | --- |
| Healthy economy → crisis → consequences | Fixed storyline | Seeded worlds, actual bank asset losses, defaults and committed events. |
| Create, Play/Pause, speed, reset | Local counter | Backend scheduling and a fresh reset world that preserves source history. |
| Institution inspector | Preset café/bank records | Real IDs, balances, inventory, employees, ratios, supplier bills and recent ledger. |
| Financial network | Static exposures | Current interbank, bank-credit, public-loan and supplier claims. |
| Fork Reality | Preset charts | Three calculated futures from a shared snapshot, synchronized by day. |
| Agent decisions | Timed mock response | Background jobs, public tool traces, explicit demo/live labels and guarded settlement. |
| Supplier payments | Recorded storyboard | Actual offers, negotiation, selected terms, explicit confirmation and invoices. |

Unsupported rent, tax and interest-rate controls were removed from the active entry flow. Time is now in days; integer cents convert to dollars exactly once. Bank stress is a count of stressed banks. The San Francisco geometry visualizes 40 households, 8 businesses and 5 banks; it is not calibrated city data.

## Run locally

Use Python 3.11+ and Node 22 LTS. Install Python dependencies using [the main README](../README.md), then start the API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_backend --reload
```

In another terminal:

```powershell
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` and `/health` to port 8000, including SSE. No frontend key or environment variable is required. The launcher reads allowed settings from the ignored root `.env`, while shell variables take precedence. When live credentials and a model are configured, the UI selects **Live Nemotron via Nebius** and displays the model ID. Otherwise it selects the explicit deterministic demo. Simulation and settlement execute on the backend in either mode.

To use another API origin, set `VITE_API_BASE_URL` before starting/building Vite, for example `http://127.0.0.1:8001`. An untracked `apps/web/.env.local` can hold this non-secret value. Permit the frontend origin using `ECONOMY_CORS_ORIGINS`. Production builds need that API origin or a host reverse proxy; the Vite development proxy does not configure production hosting. Provider secrets remain exclusively on the backend.

## Demo paths

Choose United States → San Francisco → starting scenario → Create and explore economy.

For the crisis demo, choose **Credit crunch**, trigger a 40% risky-asset loss at Bank 1 while paused, and compare futures immediately or advance days to observe actual effects. City and Network preserve institution selection. A standard world may absorb the same shock; outcomes are calculated rather than forced.

Test rescue policies queues central-bank analysis with a $10,000 cap and a 12-day horizon. Read its trace and explicitly apply the recommendation. Fork Reality separately labels its employment-first ranking as rule-based; it can disagree with the agent. The comparison uses Bank 1, $10,000 and 12 future days. Its scrubber reads branch history without rewinding or mutating the source.

For inventory recovery, choose **Supply crunch**, advance one day, and inspect Business 1 using the institution list, its city building or the network. Negotiate supplies requests 20 material units with a $1,000 full-invoice cap. Review original/revised offers and selected down payment, then explicitly confirm the contract. Advance another day to see production and household purchases resume. Review payroll credit uses the existing business/bank underwriting workflow.

The UI pauses before analysis, shocks, comparisons, negotiations and settlement. Later source changes still invalidate unexecuted reports; errors are visible. Queued jobs can be cancelled; running jobs remain inspectable. Reload restores the saved world ID and its latest job from the backend. Reset switches to a fresh world ID while preserving the old world. Financial action retries retain their request ID after an uncertain response.

## Code and validation

[ConnectedApp](../apps/web/src/ConnectedApp.tsx) owns the visual shell, [LiveDashboard](../apps/web/src/ui/LiveDashboard.tsx) owns connected views, [the API adapter](../apps/web/src/data/api.ts) handles typed requests and currency, and [the store](../apps/web/src/state/store.ts) manages batched SSE, polling and action acknowledgements. [City mapping](../apps/web/src/data/liveCity.ts) assigns backend IDs to buildings. Extra scenery has no invented inspector record. Traffic movers are decorative, with aggregate activity based on employment.

Original fixture components/data remain as references and for existing tests. They are not the active connected data path. Live provider failure never substitutes a fixture policy.

```powershell
npm test
npm run build
.\.venv\Scripts\python.exe -m pytest -q
node scripts/qa-integration.mjs
```

The integration QA needs both servers and installed Google Chrome. It exercises creation, playback, shocks, forks, policy application, supplier settlement, production, reload, reset and a mobile viewport. Screenshots and the report go to ignored `artifacts/`. Old storyboard QA scripts target the previous fixture flow.

Use `python -m scripts.check_nebius` to list your account's Nemotron models, and `python -m scripts.check_nebius --probe` to make one real tool-call check. `python -m scripts.smoke_live` verifies the three full live workflows without automatically settling their proposed financial actions; it incurs inference usage. These commands never print the key. The launcher is optional: plain Uvicorn still reads shell variables and does not load `.env` itself.

External payments, rent/tax/interest-rate economics, continuous autonomous agent scheduling, authentication and production deployment remain outside this integration.
# Rebuilt city integration

The current San Francisco diorama keeps its decorative geometry, path IDs, eight landmarks, camera detail levels and static cache while binding selected buildings to real backend entity IDs. Featured banks inspect banks; featured shops inspect businesses. Bindings refresh when backend world objects change, so same-day bank losses and subsequent business closures appear without remounting the canvas. Resetting into a new world may remount it.

District navigation filters recorded backend events using the building-to-entity bindings. Districts are visual groupings, not measured neighborhood economies. The 400 pooled movers are decorative activity indicators, not additional households or independent model agents. The app's financial metrics, reports and settlements still come from the backend. Automatic public-input loading and frozen world provenance remain active.

Run `node scripts/qa-live-city.mjs` against the running API and Vite to check live building inspection, same-day bank stress, closure updates, district filtering, static-cache preservation, forks/report export and mobile layout. It creates separate test worlds, makes no model or payment calls, and uses saved public observations; normal app-open refresh rules still apply. The older visual-only QA scripts assume legacy fixture entry flows and should not be used to claim current live-backend verification.
