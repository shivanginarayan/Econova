# Additional track implementation and setup

This milestone implements the priority additions from the local track-coverage plan without replacing the working economy. Live Nemotron remains on Nebius. Existing SpacetimeDB, ordinary credit, procurement, playback, forks and audited settlement remain available. New CRS controls, calibration and external research payments are opt-in. Capital One Nessie remains the plan's optional later item; it is not integrated or claimed.

## Hyphenate credit controls

Inspect a business and open **Credit safeguards**. Set the review threshold in dollars, optionally choose a sponsor CRS owner profile, and click **Review with safeguards**. The backend interprets the threshold in integer cents. Default ordinary credit behavior is unchanged. Optionally set `CREDIT_APPROVAL_THRESHOLD_CENTS` to enforce a server-wide threshold that a request can tighten but cannot raise.

The bank agent has a `pull_credit_report` tool when CRS underwriting is requested. It must call that tool before assessment. The tool returns normalized score/risk evidence and a report ID; it never returns raw names, SSNs, addresses or credentials. It uses the account's documented Experian credit-profile product, authenticating against the CRS sandbox. Cached results are reusable for 15 minutes; a selected profile remains bound to the business and captured in its report.

- Blocked CRS identity/fraud evidence makes the credit ineligible. Human review cannot override it.
- Unknown evidence or a score below the illustrative sandbox threshold of 620 requires human review. This is a demonstration policy, not a production credit-scoring model.
- Principal above a configured threshold also requires review, including when automatic settlement was requested.
- `needs_human_approval` is shown in the inspector with its reasons. An operator must approve/decline with a rationale. Approval itself moves no money; settlement remains a separate confirmation.
- Settlement rechecks the source snapshot, financial eligibility and CRS evidence expiry, and remains exactly-once. A changed world requires a fresh review.

The development API still has no user authentication. The recorded reviewer is a local operator, not a verified corporate identity. Production access controls remain future work.

### CRS credit setup

Use the sandbox credentials already described in [the sponsor guide](./SPONSOR_INTEGRATIONS.md). Also configure:

```dotenv
CRS_CREDIT_PRODUCT_CONFIG=YOUR_ENABLED_PRODUCT_CONFIG
CRS_CREDIT_REPORT_VARIANT=standard
CRS_CREDIT_RULES_PATH=data/crs-credit-rules.json
```

The sponsor portal demonstrates the `standard` Experian product; its public OpenAPI also documents a `basic` variant. Select the one enabled for your account. No endpoint is guessed by the model.

Each entry in the private test-profile file may contain a separate `credit_request` object using the exact sponsor-provided credit-report payload. Fraud verification continues to use its separate `request` object; these product payloads are not assumed interchangeable.

The private credit-rules file contains `score_path` and `risk_rules`. `score_path` points to the actual account-specific score field. Each risk rule contains `path`, `clear_values`, and `blocked_values` using documented vendor codes. Missing/unknown values require review. Example structure only, not vendor field names/codes:

```json
{"score_path":"YOUR.DOCUMENTED.SCORE.FIELD","risk_rules":[{"path":"YOUR.DOCUMENTED.RISK.FIELD","clear_values":[],"blocked_values":[]}]}
```

Live Cal Hacks verification completed October 25: authenticated sandbox HTTP200 and actual Experian CRS Standard Format report HTTP200 for sponsor synthetic P19 small-business owner. The live Nebius/Nemotron business and bank workflow pulled CRS before assessment, displayed score 770, and stopped at human review with no settlement or financial transactions added. Score path is `scores.0.scoreValue`, per the sponsor OpenAPI. No identity/fraud clearance is inferred: private risk rules are empty, so risk remains review.

Demo: inspect Business 1 in a world with a payroll shortfall, open **Credit safeguards**, select **CRS sandbox: sponsor_p19_owner** under Owner credit evidence, keep Agent mode **live**, and select **Review with safeguards**. Show the redacted CRS score and recorded tool trace, then the separate human-approval gate. Use only sponsor synthetic profiles. Verified run: `credit_4300cc3429b747009a2ff1a2ab955f36`, world `world_005d442774c04101`.

The adapter uses `POST /experian/credit-report/standard/{config}` with `exp-prequal-vantage4`. HTTP200 can contain `errorMessages`; these are rejected rather than treated as evidence. No separate TruValidate fraud integration is claimed as live verified.

## Full Fetch conversation

The ACP gateway now accepts:

```text
stress-test bank 1 with a 40% loss and compare rescue plans
why did you pick that?
```

The first command creates a fresh credit-crunch world, applies the specified shock, computes three matched futures, and queues live Nemotron analysis constrained to that bank. It returns all three outcomes and the tested recommendation. It does not apply interventions or buy research. The follow-up retrieves saved public traces and comparison metrics; it does not invent a new rationale. Supported natural-language syntax is intentionally bounded; arbitrary instructions return help. Banks 1–10 and losses above 0% through 100% are supported.

The running agent remembers the last job per sender using its local storage, so the follow-up works after a message boundary. Existing `data <world_id>`, `stress <world_id>` and `status <job_id>` commands remain supported. A still-running analysis returns a job ID and can be completed with `status` inside the conversation.

The complete backend conversation was verified with live Nemotron: three futures, three public tool calls, and a saved-evidence follow-up, with no intervention applied. ACP validates against the installed SDK. Actual Agentverse mailbox registration, active public discovery, and the complete signed ACP mailbox workflow are now verified with the replacement credential. The complete ASI:One UI experiment and saved-evidence follow-up are now verified as well. See [the gateway setup](./FETCH_AGENT.md).

```powershell
# Makes real model calls against the running backend
.\.venv\Scripts\python.exe -m scripts.check_fetch_workflow --live
```

## x402 paid research

The optional service uses Coinbase's actual Python x402 SDK and FastAPI middleware. `GET /market-forecast/{world_id}?snapshot={sha256}` issues an HTTP 402 challenge for at most 0.01 Base Sepolia test USDC, then provides a three-day employment trend projection from that exact synthetic snapshot after payment. This is a separate analysis service, not a claim of real-market forecasting accuracy.

The central-bank agent receives `buy_market_forecast` only when the caller explicitly sets `allow_paid_research=true` on a live run. The dashboard has a separate unchecked authorization box. The agent can decide whether to use the tool; permission does not force a purchase. A rejected/failed optional purchase leaves intervention testing available.

The buyer signs only x402 v2 exact USDC payments on `eip155:84532`, for the configured merchant, capped at 10,000 USDC atomic units. It rejects mainnet, other assets/recipients and long-lived authorizations. A durable reservation permits at most one purchase attempt per run. An ambiguous timeout is not automatically retried. Before recording success it verifies the Base Sepolia transaction receipt and matching USDC Transfer log, then exposes the transaction hash/explorer link in the public tool trace. No simulated balances are debited.

### Run and fund the test service

```powershell
python -m venv .venv-x402
.\.venv-x402\Scripts\python.exe -m pip install -r requirements-x402.lock.txt
.\.venv-x402\Scripts\python.exe -m scripts.create_test_wallets
# Keep the normal backend running on localhost:8000
.\.venv-x402\Scripts\python.exe -m x402_service.server
```

The wallet helper does not overwrite existing configured identities. It saves the buyer key only in ignored `.env` and a newly generated merchant key only under ignored `data/`. It prints public addresses, never private keys. `X402_PYTHON` can select another isolated Python executable; otherwise the backend locates `.venv-x402` automatically. `X402_FORECAST_URL` defaults to localhost:8402.

On the current development machine the generated buyer address is `0xfdd50b3fCF1457DaeC03D2A1Fa3A087e98C81683`. It received 20 Base Sepolia test USDC from Circle and completed one verified 0.01 test-USDC purchase. See [the chain receipt and evidence](./X402_SUBMISSION.md). To fund another authorized test, use the [Circle faucet](https://faucet.circle.com/) with **USDC → Base Sepolia** and that buyer address. Restart the backend after configuring wallet variables, then authorize paid research on a live policy run. A facilitator may also need operational availability; do not claim success until the transfer receipt is verified.

Verified: a real local HTTP 402 challenge; the actual SDK's challenge/signing/retry/receipt path against a mocked facilitator; mainnet/asset/recipient/spend restrictions; and matching on-chain receipt validation against mocked RPC results. The earlier mocked checks are now supplemented by an actual successful testnet payment and independent receipt verification; see [the x402 guide](./X402_SUBMISSION.md). The explicit SDK demonstration is separate from the optional tool choice of a live model.

## Apify price and wage samples

The collector runs explicitly configured Apify Actors, polls their completion, reads the resulting datasets, and records Actor/run/dataset/source provenance. It does not guess scraper fields, currencies, salary ranges or locations. Choose actors/inputs that retrieve public San Francisco samples and confirm their terms and units. The `APIFY_TOKEN` is sent only as a bearer header to Apify.

Create a private JSON spec under `data/`. For `prices` and `wages`, provide `actor_id` in `owner~actor` form, Actor-specific `input`, `value_path`, an explicit `unit`, and a public HTTPS `source_url`. Optionally specify a completed `run_id` to reuse an existing run. Allowed price unit: `usd_item`; wage units: `usd_hour`, `usd_day`, `usd_year`. Optional rent uses `usd_month_rent` and is kept as reference context because rent transactions are not implemented.

```json
{
  "calibration_id":"sf_sample_20261024",
  "prices":{"actor_id":"YOUR_OWNER~YOUR_PRICE_ACTOR","input":{},"value_path":"YOUR_NUMERIC_PRICE_FIELD","unit":"usd_item","source_url":"https://YOUR_PUBLIC_SOURCE"},
  "wages":{"actor_id":"YOUR_OWNER~YOUR_JOB_ACTOR","input":{},"value_path":"YOUR_NUMERIC_PAY_FIELD","unit":"usd_hour","source_url":"https://YOUR_PUBLIC_SOURCE"}
}
```

```powershell
.\.venv\Scripts\python.exe -m scripts.apify_calibrate --spec data/apify-spec.json
```

The collector converts numeric USD with decimal rounding. Hourly pay assumes eight hours/day; annual pay assumes 260 paid days/year. Non-numeric ranges are skipped and counted. Implausible/out-of-range or missing samples fail validation; nothing is published as a substitute. Output goes to `data/calibrations/{id}.json` without overwriting an existing ID.

Select a saved calibration in the world-creation UI, or provide `calibration_id` to `POST /api/worlds`. Prices and daily wages are sampled with the seed, and the complete sample/provenance object is frozen in world state. Forks copy it, and reset uses that frozen object even if the source file changes/disappears. Existing worlds never reload it. The UI shows the calibration ID, date and checksum. Households, businesses, bank balance sheets and behavioral rules remain synthetic; a sample of prices/wages does not calibrate the whole city economy.

The collector is now verified live through the project's private limited-permission Actor: 29 posted cafe drink-price options plus one official statutory wage reference. The UI can collect fresh data and create a world with frozen public inputs. See [the live Apify setup and scope](./APIFY.md). Generic private Actor specs remain supported by the CLI above; parsing/replay failures are also covered by fixtures.

## Rehearse and verify

```powershell
.\.venv\Scripts\python.exe -m scripts.hyphenate_demo
node scripts/qa-credit-safeguards.mjs
node scripts/qa-integration.mjs
.\.venv\Scripts\python.exe -m pytest -q
.\.venv-x402\Scripts\python.exe -m pytest tests/test_x402_sdk.py -q
npm test
npm run build
```

The rehearsal is explicitly labeled `scripted_rehearsal`. It deliberately proposes an over-budget rescue, records the real engine rejection, recovers with a valid proposal, and separately demonstrates human escalation without settlement. It uses its own ignored database and never substitutes for live inference evidence. See [submission evidence](./SUBMISSION_EVIDENCE.md) for the pitch and real-versus-simulated table.
