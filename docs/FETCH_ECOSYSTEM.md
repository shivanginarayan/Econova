# Ten typed Fetch economic services

The incoming teammate commit adds ten uagents roles. Integration binds them to the existing saved-state engine. These services are deterministic protocol adapters, not ten new Nemotron models or ten already registered Agentverse/ASI:One agents. The previously verified `economy-god-mode` ACP gateway and live policy/credit/procurement roles remain separate.

| Service | Real task | Limits |
| --- | --- | --- |
| central_bank | Preview a bounded hypothetical risky-asset loss on a copy, calculate three actual futures and return the engine ranking | No source shock/support applied; ranking is rule-based |
| commercial_bank | Assess actual payroll credit against saved borrower/bank state | Caller-stated shortfall is not trusted; no settlement |
| corporate_borrower | Audit actual deposits/payroll gap | Acceptance messages cannot authorize a loan |
| procurement_buyer | Run the existing bounded procurement workflow, explicit demo or live mode through coordinator | Two actual suppliers, full invoice budget; no contract settled |
| supplier_quotation | Quote recorded stock/policy; validate counteroffer terms | Deterministic policy preview, not invented commercial offers |
| treasury_macro | Retrieve actual Treasury source or calculate bounded duration assumptions against recorded risky assets | No source fallback; zero assumed yield change stays zero; debt does not infer yields |
| apify_wage_oracle | Read latest validated saved Apify observations with source metadata | No crawl triggered; missing observations fail closed |
| clearinghouse_settlement | Audit real outstanding interbank obligations | Network messages cannot execute settlement; no fabricated netting efficiency |
| household_welfare | Calculate actual synthetic employment/balance distribution and Gini | No assumed 1.38 multiplier or unsupported stimulus forecast |
| auditor_inspector | Run ledger audit and count actual stored fraud reports | No fictional compliance certification; missing CRS remains unverified |

## Run locally

Use Windows PowerShell and preserve the existing private stable `FETCH_AGENT_SEED`. There is no public default seed. The launcher loads ignored root configuration.

```powershell
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_ecosystem --list
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_ecosystem --bureau --port 8100
# An existing saved world is required for workflows:
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_ecosystem --workflow credit --world-id YOUR_WORLD_ID --mode demo
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_ecosystem --workflow procurement --world-id YOUR_WORLD_ID --mode demo
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_ecosystem --workflow crisis --world-id YOUR_WORLD_ID
.\.venv-fetch\Scripts\python.exe -m scripts.verify_fetch_ecosystem
```

`--mode live` makes real Nebius calls for credit/procurement; it does not permit settlement. The coordinator is backend orchestration, not evidence of peer-message delivery. The Bureau provides typed SDK handlers; runtime deployment/registration of these ten identities must be verified separately before claiming external discoverability. Their seeds derive privately from the existing master seed, independently of the established chat gateway identity.

The verifier constructs all ten actual SDK identities against an isolated real SQLite world, runs saved-state workflows and asserts the financial source remains unchanged. It makes no model calls, payments, source requests or registrations. Evidence: ignored `artifacts/fetch-ecosystem-verification.json`. This verifies SDK construction and real calculations, not external registration or inter-agent transport.

## Application integration

Expand **Data, fraud & shared events** and click **Inspect economic services**. `GET /api/worlds/{id}/economic-services` returns the ten roles and current ledger, household and interbank reports. It moves no money and performs no external collection or inference. Existing live role controls, public-input autoload, Fetch ACP, SpacetimeDB collaboration and x402 integration remain available.

## Integration corrections

Incoming sample flows contained fixed employment/default values, assumed capital ratios, a 55% netting claim, a 1.38 demand multiplier, fictional world IDs and execution flags without ledger postings. Those are not live evidence and were removed from operational paths. New adapters use existing policy/source functions; unavailable backing data produces explicit typed errors. The copied Treasury baseline fallback and published default identity seed were removed. Credit and contract settlement remain the existing explicitly authorized, snapshot-checked endpoints.

The incoming thread-local SQLite connection reuse was also corrected: nested contexts could prematurely commit an outer operation, and manual-step permission had been moved outside the write lock. Connection scopes now own transactions and the paused-step check again runs under the mutation lock. Regression tests cover both behaviors.
