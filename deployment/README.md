# Hosted Econova build

This prepares the existing application for a persistent, HTTPS hosting service. It does not create a hosting account or publish a URL.

The root Dockerfile builds the React UI, then runs one Python UI/API process. Mount a persistent writable volume at `/app/data` owned by UID10001. Use a service that stays running for background agent jobs and SSE; this SQLite/worker configuration is not a stateless function deployment. Multiple replicas require another storage/queue design.

Configure secrets in the host's secret store:

- `NEBIUS_API_KEY`: existing Token Factory key, server-side only.
- `NEBIUS_MODEL`: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.
- `ECONOMY_ACCESS_PASSWORD`: randomly generated, at least16characters; supply the judging credentials separately. Username is `econova`.
- `ECONOMY_SESSION_SECRET`: a different random secret, at least32characters; keep stable across restarts.

Use the host's HTTPS endpoint and port mapping. Set `PORT` if required. Set `ECONOMY_TRUSTED_PROXIES` to the trusted reverse proxy addresses; use `*` only where direct access to the container is blocked and requests come through the host's trusted proxy. Cookies are secure by default. Do not set `ECONOMY_COOKIE_SECURE=0` on an internet service.

The validated public-observation bundle seeds missing calibration files on first launch. It contains public source observations with dates, not API keys or private account profiles. Saved worlds freeze their selected inputs. The hosted build does not automatically launch paid Apify runs; source dates remain visible. Regenerate the bundle intentionally with `python -m scripts.prepare_hosted_inputs` after collecting and checking a new vintage. No economic-calibration promotion is implied.

Hosted access is separate from the local development app:

- Browser credentials protect the application; a signed HttpOnly visitor cookie scopes experiments and derived resources to that visitor.
- Forks inherit the originating visitor's access; resetting retains ownership. A shared room link alone does not grant another hosted visitor access.
- Agent jobs require supervision and explicit settlement. Default request budgets allow12agent submissions per visitor/hour and60globally/hour; configure `ECONOMY_JOBS_PER_HOUR` and `ECONOMY_GLOBAL_JOBS_PER_HOUR` for expected legitimate judging traffic and available credits. Attempts, including retries, count toward the request budget. Provider requests have at most three attempts for explicit transient HTTP failures; no automatic retry of settlement or model decisions occurs.
- Hosted experiments support up to200households,40businesses and240simulation steps. Create a new experiment after the step limit. These are resource bounds, not financial assumptions.
- Paid research, private CRS profiles, wallet actions and optional old control-room integrations are disabled. Local development behavior remains available with public mode off.

Before treating deployment as complete, verify: HTTPS login, a clean visitor creating an economy, live Nemotron investigation and recorded handoffs, supervisor status, policy comparison, no automatic source mutation, separate-visitor isolation, refresh/resume, restart persistence, and adequate model/hosting credits through the judging period. Inspect actual provider errors; do not relabel blocked reviews or failed requests as successful financial actions.
