# Data sources and sponsor integrations

## Population, businesses and banks

Our worlds are generated deterministically from a seed and configured counts. Genesis journal entries create initial reserves, deposits and equity. Employment, wages, inventory and exposures follow synthetic rules. The small default world is not a calibrated San Francisco forecast.

The new reference-data tools retrieve actual public data:

| Source | Observed live result | Scope |
| --- | --- | --- |
| US Census county estimates, Vintage 2024 | 827,526 residents | San Francisco County, July 1, 2024; people, not simulation households. |
| FDIC BankFind institutions | Five institutions | Active FDIC-insured institutions headquartered in San Francisco, CA; not branch counts or all banks serving the city. |

Observations include source URLs, reference dates and retrieval timestamps. The public Census CSV is used because the ACS API redirected keyless requests to `missing_key.html`. These figures do not silently change world size, synthetic bank names/balances or fork reproducibility. Failed sources are labeled unavailable; the model cannot supply replacement numbers.

Open **Data, fraud & shared events → Load Census + FDIC data** in the dashboard. Public retrieval works without an AI key. **Research with Fetch ASI:One** separately uses actual function calls to the same tools and requires valid `ASI1_API_KEY`. Its model prose is not accepted as data. See [Fetch ACP gateway](./FETCH_AGENT.md) for Agentverse conversation access; this gateway's data command does not require a separate inference key.

## CRS identity / fraud

The adapter implements the documented sandbox login (`POST /api/users/login`, response `token`) and TransUnion TruValidate identity verification (`POST /api/transunion/identity-manager-verification/basic/{config}`). The service base is fixed to the sandbox. Confirm this product is enabled for your account and obtain its config, credentials, test identities and response-code mapping from the [CRS sponsor portal](https://calhacks.crscreditapi.com/). Other products need their own documented adapter.

Set `CRS_ACCESS_TOKEN`, or `CRS_USERNAME` plus `CRS_PASSWORD`; also set `CRS_PRODUCT_CONFIG`, `CRS_TEST_PROFILES_PATH` and `CRS_DECISION_RULES_PATH`. Store private files under ignored `data/`. The browser passes only an opaque profile ID, never raw identity fields.

Private profile file structure (replace the empty request with the exact sponsor-supplied TruValidate test request):

```json
{"sponsor_profile_a":{"sponsor_test_identity":true,"request":{}}}
```

The decision-rules file is an array of objects with `path`, `clear_values` and `blocked_values`. Paths use dot-separated vendor fields and optional array indices. Use the documented fields/codes for your account. Do not invent PASS/FRAUD values; those appear only in unit-test fixtures. Empty rules, unknown values and missing fields yield `review`. Any blocking rule blocks; every configured rule must explicitly clear before clearance.

Only normalized decisions, rule paths, opaque profile/entity IDs, source tick and timestamps are persisted. Raw identity responses, names, addresses, SSNs and tokens are not stored in reports or sent to models, the frontend or the shared feed.

The UI screens a receiver and permits an explicitly confirmed $1 simulated payment only after live CRS clearance. The guarded API requires that screen to match the receiver/world, current tick and a 15-minute expiry. Settlement is atomic and idempotent. Blocked, review, expired and local demo results cannot authorize it. This is a dedicated guarded payment workflow; ordinary simulation payments and existing agent settlements retain their behavior. Clearance means the configured sandbox checks passed, not a guarantee against fraud.

No live CRS request is verified yet: sponsor credentials/config/test profiles are still needed. Authentication, redaction, holds, expiry, receiver binding and settlement are tested with mocked vendor responses. The UI's two demo profiles are explicitly local and cannot authorize guarded payments.

## SpacetimeDB shared event feed

A real TypeScript module stores public `economy_event` rows and a private publishing-identity record. Only that identity can ingest. Batches are atomic and immutable, keyed by world ID/event sequence: identical replay succeeds; conflicting replay fails. The projection contains ticks, event types, synthetic actor IDs and integer-cent amounts, excluding identity reports/model prompts.

SQLite remains the authoritative ledger. Enabling a feed mirrors committed events in batches of at most 100 using a durable cursor. A background worker retries every two seconds. Delivery failure cannot roll back or duplicate financial settlement. The UI shows delivered/source counts and errors. The shared control room now uses direct SpacetimeDB SDK subscriptions for presence, proposals, independent-identity reviews, execution receipts and financial events. SpacetimeDB owns this collaborative workflow; SQLite remains the accounting source of truth and the main dashboard retains its SSE transport. See [the complete demonstration](./SPACETIME_SUBMISSION.md).

### Local Windows setup

Tested runtime/SDK: 2.13.0. Download the [official Windows archive](https://github.com/clockworklabs/SpacetimeDB/releases/download/v2.13.0/spacetime-x86_64-pc-windows-msvc.zip) and extract its CLI/standalone executables into ignored `data/spacetime-bin/`. They are already present on this development machine. Binaries, keys and databases are not committed.

```powershell
npm ci --prefix spacetimedb
npm run check --prefix spacetimedb
node scripts/spacetime_keys.mjs
.\data\spacetime-bin\spacetimedb-standalone.exe start --listen-addr 127.0.0.1:3000 --data-dir data/spacetime-server --jwt-pub-key-path data/spacetime-keys/public.pem --jwt-priv-key-path data/spacetime-keys/private.pem --non-interactive
```

Keep that terminal running. In another terminal:

```powershell
.\.venv\Scripts\python.exe -m scripts.configure_spacetime
.\data\spacetime-bin\spacetimedb-cli.exe --root-dir data/spacetime-cli publish economy-god-mode --module-path spacetimedb --server http://127.0.0.1:3000 --delete-data=never --yes=skip-login
.\.venv\Scripts\python.exe -m scripts.run_backend --reload
```

The helper saves the local publishing token only in ignored `.env`. Restart the backend after configuring it. `SPACETIMEDB_TOKEN` must be the publishing identity. Other platforms should use the official CLI and configure a corresponding local token; the helper is Windows-specific.

In a world click **Enable shared event feed**, then advance a day. Inspect the table independently:

```powershell
.\data\spacetime-bin\spacetimedb-cli.exe --root-dir data/spacetime-cli sql economy-god-mode "SELECT * FROM economy_event LIMIT 20" --server http://127.0.0.1:3000
```

## Verification and track evidence

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sponsors.py -q
.\.venv\Scripts\python.exe -m scripts.check_integrations --spacetime
# Optional real inference; consumes usage
.\.venv\Scripts\python.exe -m scripts.check_integrations --research
# Optional real CRS sandbox call using a private sponsor profile
.\.venv\Scripts\python.exe -m scripts.check_integrations --crs-profile sponsor_profile_a
# Backend, UI and local database must be running
node scripts/qa-sponsors.mjs
```

Verified locally: module built/published, public data retrieved, 20 events written/read from SpacetimeDB, duplicate replay unchanged, ledger balanced. Browser checks verified sourced data, blocked demo payment, automatic event catch-up, reload persistence and mobile layout. ACP validates against the actual SDK. Agentverse registration, active public discovery and a full ACP mailbox stress/evidence conversation are verified. The ASI:One UI stress-test/evidence conversation is also verified. No successful separate ASI inference or live CRS call is claimed.

Meaningful live CRS sandbox use is required by its [challenge](https://calhacks.crscreditapi.com/); mocked tests do not establish it. SpacetimeDB now has an actual database-backed feature to demonstrate. Sponsor eligibility/winning remains subject to their rubric.

Official references: [CRS OpenAPI](https://www.crscreditapidocumentation.com/openapi.json), [ASI tool calling](https://docs.asi1.ai/documentation/build-with-asi-one/tool-calling), [Fetch hackpack](https://www.fetch.ai/events/hackathons/calhacks-13-0/hackpack), [Spacetime HTTP API](https://spacetimedb.com/docs/http/database/), [module owner identity](https://spacetimedb.com/docs/functions/reducers/lifecycle/).
