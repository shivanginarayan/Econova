# Real public inputs through Apify

The connected UI now defaults new worlds to the latest collected public inputs. It does not silently fall back to random prices/wages if that selection is missing. The world-setup dropdown offers an explicit seeded demo option.

## What has been collected live

The private `economy-public-sf` Actor was deployed under the development account with **LIMITED_PERMISSIONS**, built successfully, and run against two fixed sources:

- [Cafe Seventy8](https://www.cafeseventy8.com/): 29 posted drink-price options, with item names, option order, source URL and collection timestamp. Drink sizes are not guessed; unspecified taxes/surcharges are not added. This is one venue's posted menu, not a citywide price index.
- [SF Office of Labor Standards Enforcement](https://www.sf.gov/information/understanding-minimum-wage-ordinance): the general statutory hourly minimum wage and its effective date. It is a legal floor, not average pay or an observed household's salary. Daily wages use the explicit eight-hour workday assumption.

The original successful price run was `3Ige9F2xAe11Vxct9`; the wage run was `l3dOGoqezfzFbsYy9`. Subsequent explicit collections create new run IDs, visible in the dashboard. Actor run IDs and dataset IDs are saved in each immutable calibration alongside parsed observations. Local data lives under ignored `data/calibrations/`; Git contains the collector and Actor source, not credentials or an undocumented fixed snapshot.

## Use the UI

1. Open **Real public inputs · Apify** in the right sidebar or world setup.
2. Public inputs load automatically on app open. Saved inputs are usable immediately; missing inputs are collected automatically, and inputs more than six hours old refresh in the background. Collection may consume Apify usage credits. No collection click is required. An optional manual action is under **Refresh options → Refresh public inputs now**.
3. Inspect counts, collection/effective dates, raw numeric observations, source links and Apify run links.
4. Click **Create new world with public inputs**. Existing worlds are preserved. Alternatively, the normal **Create World** button uses the selected collection; its initial selection is latest collected Apify inputs.
5. New business prices are sampled from the actual collected menu prices. Household wages use the collected statutory reference converted to daily pay. Run the simulation and inspect the calculated effects.

The source panel distinguishes current-world frozen data from the latest collection. Refresh, reset and forks preserve the world's exact original sample object and checksum. Fetching a new dataset does not rewrite existing balances, history or inputs.

## Set up on another machine/account

Set `APIFY_TOKEN` in private root `.env`, then deploy the fixed-source private Actor:

```powershell
.\.venv\Scripts\python.exe -m scripts.deploy_apify
```

The helper creates a private Actor, records `APIFY_ACTOR_ID` in ignored `.env`, and starts a build. Existing configured Actors have version `0.1` updated and rebuilt. Wait for the build to succeed in Apify Console before collecting. Restart the backend to load new environment settings:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_backend --reload
```

The Actor accepts only `prices` or `wages`. It cannot be given arbitrary URLs, page functions, account settings or external storage IDs through the dashboard. It checks robots.txt, skips script content, requires exact known price patterns, and fails if the official current wage/effective date cannot be parsed. It writes only to the platform-provided default dataset with its scoped token. The general-purpose official scraper required full-account permission approval, so this integration instead uses this private limited-permission Actor. It does not change billing limits or publish an Actor to the Store.

Each category run has 128 MB memory and a 120-second timeout, no proxy and no automatic restart. The request also includes `maxTotalChargeUsd=0.25`; this is not presented as an all-inclusive platform/storage/build billing cap. The UI shows the platform's reported run usage. Duplicate request IDs are durable, active work is shared, completed collections are reused for five minutes, and new collections are limited to six/hour. Interrupted or ambiguous work is not replayed by repeated page opens in the same automatic-refresh window; recorded run links remain available for inspection. A later six-hour window can start a new collection. Existing world inputs remain frozen regardless of refresh results.

## API and verification

- `POST /api/calibrations/ensure`: app-start endpoint; returns cached data immediately and starts one background collection if missing/stale. Automatic request IDs are shared per six-hour window; failed/ambiguous work is not replayed by reloads during that window.
- `GET /api/calibrations/collection/status`: configured flag and latest persistent job.
- `POST /api/calibrations/collect` with `{"request_id":"unique-id"}`: HTTP 202; queued/running work is polled separately.
- `GET /api/calibrations/collection/{job_id}`: progress, recorded runs, error or published calibration ID.
- `GET /api/calibrations/{calibration_id}`: saved numeric samples, observations, provenance and checksum.

`python -m pytest tests/test_apify_collection.py tests/test_track_additions.py -q` checks request deduplication, parsing, data conversion, no substitution on failure, and frozen world inputs. `node scripts/qa-apify.mjs` makes a real bounded collection through the UI, creates test worlds, checks actual input values, reload, default selection, a balanced tick and mobile layout. The browser test consumes Apify usage; it makes no model calls or financial payments.

## Remaining modeled assumptions

The simulation still creates synthetic households, institutions, bank portfolios, opening cash/debt, employment relationships, daily spending budgets and production rules. Apify does not grant access to private household finances or bank portfolios. One cafe's prices and a wage floor do not validate all citywide behavior or crisis forecasts. Broader business/occupation samples and validated financial datasets would be separate calibration work.

`node scripts/qa-apify-auto.mjs` verifies automatic loading, world creation without a collection click, and reload without a duplicate crawl. Frontend loader tests also cover waiting for the first dataset and keeping cached data usable during a failed refresh.

## Track demonstration

See the [Hyphenate and Apify submission guide](./HYPHENATE_APIFY_SUBMISSION.md) for the pitch, proof checklist and recorded live demonstration command. The combined script checks that actual collected values set prices/wages, then demonstrates live credit approval safeguards and policy comparisons in separate synthetic worlds. It saves video, screenshots and inspectable evidence under ignored `artifacts/`.

The official event listing includes both Best Use of Apify and Best Actor. This project has a custom deployed Actor, but the listing does not specify whether Best Actor requires Store publication. The Actor remains private; do not claim it is publicly discoverable. Its [source and usage instructions](../apify_actor/README.md) are available in the repository.
