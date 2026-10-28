# Economy God Mode — detailed cross-LLM continuation brief

> Latest integration: teammate commit `10afec8` has been merged locally from the identical `origin/shivangi` and `origin/shivanginarayan` branches. It adds ten typed deterministic Fetch service adapters, in addition to the live AI roles described here. They now use actual saved-world calculations and explicit errors rather than sample outcomes. They are not ten additional live LLM models or ten verified externally registered agents. See [the current ecosystem guide](./FETCH_ECOSYSTEM.md). Existing implementation and documentation checkpoints are preserved; check current Git history for the final integration commit and publication state.

Prepared October 25, 2026, approximately 05:47 UTC / October 24, 10:47 PM Pacific. This is a self-contained transfer of project context, not a new implementation request. Read the user's next instruction before starting new work.

## 1. Start here

You are continuing **Economy God Mode**, a Cal Hacks 13.0 financial simulation and bounded AI-agent prototype. Its current implementation is working, tested, and pushed to GitHub. Preserve it. Do not rebuild the project, replace the connected frontend with fixtures, reset databases, rotate identity seeds, redeploy Actors, rerun paid workflows, or claim incomplete submissions are complete merely to recover context.

Read, in order:

1. Root [AGENTS.md](../AGENTS.md): continuity, preservation and credential rules.
2. This brief: consolidated current state.
3. [SESSION_HANDOFF.md](./SESSION_HANDOFF.md): detailed chronological implementation history. Its newest milestones supersede older blocked/unverified/unpushed notes.
4. The relevant implementation or sponsor guide before changing that feature.

The latest user requests were to complete SpacetimeDB and the already-started partial integrations, push the result to GitHub, and prepare this detailed transfer summary. SpacetimeDB, a real x402 payment, and the ASI:One conversation were completed. CRS remains blocked on missing sponsor configuration. The user has not asked to implement an unrelated new track or submit forms in this summary request.

## 2. Workspace, Git and collaboration preferences

| Item | Current state |
| --- | --- |
| Local workspace | `C:/Users/naray/Downloads/Calhacks` |
| Shell/platform | Windows PowerShell |
| GitHub | https://github.com/shivanginarayan/CalHacks |
| Branch | `main`, upstream `origin/main` |
| Latest pushed implementation | `6cfdf86 Complete shared Spacetime control room and verified track demos` |
| Git check before writing this brief | Clean working tree; `HEAD...@{u}` was `0 0` |
| Git identity | `shivanginarayan <narayan.shivangi@gmail.com>` |
| Summary-document publication | This brief and the corresponding continuity corrections were written after `6cfdf86`; they are local documentation changes until separately committed/pushed. |

Recent history:

- `6cfdf86`: shared SpacetimeDB control room, generated client bindings, verified x402/ASI:One guides, tests and QA.
- `da84403`: registered Fetch mailbox gateway and real ACP conversation verification.
- `3c5923f`: connected teammate's rebuilt city to current backend financial state.
- `05cdbcf`: merge of incoming city work, preserving both histories.
- `17c00d0`: checkpoint of sourced public inputs, reports, safeguards and track demonstrations.
- `2a3eba2`: teammate's rebuilt San Francisco diorama.

The user wants:

- Continue the original product and preserve teammate/UI work.
- Complete authorized work autonomously; avoid repetitive permission questions.
- Explain financial concepts and controls plainly.
- Save continuity so another LLM can resume without repeating work.
- Use their normal Git identity; no Codex coauthor attribution or collaborator invitations.
- Pull/integrate safely when requested; never force-push or discard work.
- Public inputs loaded automatically when the app opens. A manual collection prerequisite is unacceptable.
- Clear separation of public observations, hypothetical scenario assumptions and synthetic financial state.

Do not spawn parallel agents unless the user or applicable repository instructions explicitly request delegation. Publishing an implementation to GitHub does not mean a Devpost entry, public video, hosted demo or sponsor-specific submission was made.

## 3. What the product does

Economy God Mode lets a user observe a small synthetic economy, trigger a bank investment loss, see distress propagate, compare three rescue strategies, and inspect live AI-agent recommendations before separately authorizing financial changes. Business/bank agents negotiate payroll credit; buyer/supplier agents negotiate restocking contracts; the policy agent tests interventions on isolated copies.

Target customer hypothesis: regional/community-bank risk analysts, credit officers and bank-supervision analysts. This is a hypothesis. No customer interviews, willingness-to-pay evidence, production savings or real-world policy validation have been established.

Default world: seed 42, 40 households, eight businesses, five commercial banks, plus government and central-bank entities. One simulation tick is one day. Supported starting scenarios include `standard`, `credit_crunch` and `supply_crunch`.

The San Francisco geography is decorative. It does not establish actual neighborhood-level populations, resident behavior, real bank balance sheets or institution-specific exposures. The 400 visual movers are pooled animation objects, not 400 financial or LLM agents.

## 4. Architecture and important code map

### Backend

Python, FastAPI, Pydantic, httpx and SQLite. The default persistent database is ignored `data/economy.sqlite3`.

| Code | Responsibility |
| --- | --- |
| `backend/main.py` | Application, API routes, playback scheduler and job/mirror workers |
| `backend/models.py` | Strict request/response contracts and integer-cent parameters |
| `backend/ledger.py` | Double-entry journal, idempotent transaction IDs and audit reconstruction |
| `backend/engine.py` | World creation, economy state, metrics and shared financial operations |
| `backend/store.py` | Atomic complete-world SQLite checkpoints and snapshots |
| `backend/crisis.py`, `clearing.py`, `credit_policy.py` | Bank shocks, defaults, exposures, clearing and lending constraints |
| `backend/production.py`, `contracts.py` | Finite goods, material inventory, supplier obligations and settlement |
| `backend/forks.py`, `interventions.py` | Reproducible three-branch comparisons and public support accounting |
| `backend/agents.py`, `provider.py`, `tool_loop.py` | Policy tool loop and live/demo providers |
| `backend/credit_agents.py`, `credit_store.py` | Separate business/bank credit roles and approval/settlement |
| `backend/procurement.py`, `supply_store.py`, `supply_policy.py` | Supplier negotiation and contract workflows |
| `backend/jobs.py`, `playback.py`, `streaming.py` | Durable background jobs, timed playback, SSE replay |
| `backend/shock_stories.py` | Sourced Treasury baseline plus explicit hypothetical shock assumptions |
| `backend/apify_collection.py`, `apify_recipe.py`, `calibration.py` | Automatic public inputs, collection jobs and immutable calibration |
| `backend/research.py` | Census/FDIC observations and optional separate ASI inference |
| `backend/fetch_chat.py` | Bounded ACP commands and chat experiment/evidence workflow |
| `backend/fraud.py`, `crs_credit.py`, `sponsor_store.py` | Optional CRS evidence, normalization, redaction and guarded payment |
| `backend/spacetime.py`, `sponsor_routes.py` | Event mirror, shared control-room context and approved execution |
| `backend/paid_research.py` | Durable at-most-one external research purchase attempt per live agent run |
| `x402_service/server.py`, `buyer.py` | Actual x402 merchant, bounded buyer and chain receipt checks |

`Store.mutate` acquires a SQLite `BEGIN IMMEDIATE` lock before reading state. An operation, its audit and its saved checkpoint commit together. Exceptions roll back the operation. Keep snapshot validation inside this transaction where implemented; checking only before acquiring the lock would introduce races.

### Frontend

React 19, TypeScript, Zustand, Vite, Three.js/three-globe and generated SpacetimeDB TypeScript bindings.

- Active entry: `apps/web/src/main.tsx` → `ConnectedApp.tsx`; `App.tsx` reexports the connected app.
- `apps/web/src/state/store.ts`: current backend world, SSE/polling, actions, background jobs, separate settlement, saved-world restore and `?room=<world_id>` links.
- `apps/web/src/state/publicInputs.ts`: shared automatic public-input initialization.
- `apps/web/src/data/api.ts`: API types, currency conversion and retry-safe request IDs.
- `apps/web/src/ui/LiveDashboard.tsx`: active controls, financial inspection and views.
- `apps/web/src/data/liveCity.ts`: maps decorative city geometry to actual current world entities.
- `CityCanvas.tsx`: current entity binding, geometry/cache continuity and bank/business visual state.
- `apps/web/src/data/comparisonReport.ts`: standalone escaped HTML comparison export.
- `apps/web/src/ui/PublicDataPanel.tsx`: observed inputs, provenance and optional refresh controls.
- `apps/web/src/ui/ShockStory.tsx`: sourced debt-shock preview/apply.
- `apps/web/src/ui/IntegrationsPanel.tsx`: public sources, CRS controls and shared control room.
- `apps/web/src/ui/ControlRoom.tsx`: direct SpacetimeDB subscription UI.
- `apps/web/src/data/spacetime/`: generated SDK bindings; regenerate from module schema, do not hand-edit.
- `spacetimedb/src/index.ts`: authoritative collaborative tables and reducers.

Old fixture components and layout fixtures remain for geometry/reference/tests. They are not the active financial data source. Some older visual QA scripts assume obsolete fixture buttons; do not revert the product to satisfy those scripts.

## 5. Financial semantics and invariants

- All monetary calculations use integer USD cents. Convert to display dollars once.
- Each financial posting balances; audits reconstruct journal balances and check bank/customer, interbank, public and inventory counterparties.
- Exact transaction replay returns the original receipt. Reusing an ID with different contents fails.
- Opening balances and bank reserves are explicit synthetic genesis endowments.
- Credit creates a loan asset, deposit liability, borrower deposit and borrower debt. Repayment reverses the corresponding amounts.
- Bank lending eligibility distinguishes capital from liquidity. A liquidity loan adds debt and does not restore equity.
- A 40% risky-investment loss is not a 40% haircut to deposits.
- Household cash support records government debt and the corresponding money movements. Gross public support is not net fiscal loss.
- `finite_v1` worlds have raw materials, finished stock, cost-basis accounting, stock-constrained consumption and supplier default rules. Legacy worlds retain their original semantics.
- Current behaviors/thresholds are experiment assumptions, not calibrated regulations or forecasts.
- The ordinary tick engine is rule-based. Playing the world does not automatically invoke an LLM for every entity.
- Agent analysis, human approval and financial settlement are distinct actions.
- Pause before analysis/approval/settlement where unchanged snapshots are required. A changed world invalidates stale financial actions.

### Fork Reality

Three strategies: `no_intervention`, `bank_lending`, `household_cash`. They use the same saved source state and matched random stream. Branches are isolated and include timelines, audits, funding measures and deltas. The source world is preserved.

The engine's ranking is deterministic/rule-based. It is separate from the model's recommendation and neither establishes real-world optimality.

The HTML export includes exact outcomes, baseline differences, funding breakdown, provenance and synthetic assumptions. A model report is attached only if its completed report matches the exact fork and snapshot. Exports escape source data and execute no financial action.

## 6. What is real, hypothetical and simulated

| Category | Examples |
| --- | --- |
| Actual observed public inputs | Census county population, FDIC headquarters directory, Treasury debt record, Apify cafe menu and statutory wage source |
| Explicit hypothetical assumptions | Bank-loss percentage; debt increase; assumed bond yield change, duration and portfolio exposure |
| Synthetic financial state | Households, businesses, balances, bank portfolios, employment, spending behavior, default rules and rescue budgets |
| Actual external services | Nebius inference, Apify Actor runs, Agentverse/ASI:One conversation, local SpacetimeDB server, Base Sepolia x402 settlement |
| Fixture-only sponsor evidence | CRS HTTP responses and sponsor profile mappings in unit tests |

Never describe a synthetic result as a real customer outcome or calibrated San Francisco forecast. Provider-generated prose can be wrong even when the tool calls and numerical results are valid.

### Known example of model prose exceeding the evidence

The successful ASI:One run recommended household cash and said it reduced insolvent banks. Its returned delta for insolvent banks was actually zero. The quantitative evidence showed five more employed households, one fewer business default and two fewer stressed banks in that seeded scenario. Preserve the raw trace, but do not repeat the inaccurate insolvency claim as a fact.

## 7. Live AI provider

Actual provider: Nebius Token Factory. Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. Base URL: `https://api.tokenfactory.nebius.com/v1`.

The adapter forces function calls, caps output at 4096 tokens and disables thinking for these bounded workflows. It persists public tool arguments/results and rationale, not hidden chain-of-thought. Live-provider failures do not silently fall back to a demo model.

Live policy, credit and procurement flows have been verified. A real credit failure revealed that the bank could repeatedly try deciding after a rejected assessment. The correction exposes tools by successfully completed prerequisites: inspect, optional CRS evidence, assessment, then decision. Backend validation still rejects invalid calls and preserves the human gate. Do not remove those guards to make a demonstration pass.

Demo providers and scripted rehearsals are explicitly labeled. `scripts/hyphenate_demo.py` demonstrates deterministic rejection/recovery; it is not proof of a live LLM independently recovering.

## 8. Public inputs and automatic Apify behavior

The app initializes public inputs immediately on mount, including the globe screen. `POST /api/calibrations/ensure` returns valid cached observations immediately and starts collection when missing or older than six hours. Multiple tabs share a durable automatic request ID. Reloading does not trigger duplicate crawls for the same window. Failed/ambiguous automatic work is not blindly retried in that window.

New UI worlds default to observed public inputs and wait for the first dataset if necessary. Explicit seeded synthetic demo remains selectable. Existing worlds never silently reload or replace their frozen observations.

Private custom Actor: `economy-public-sf`, limited permissions, allowlisted sources, no arbitrary URLs, robots checks and run-scoped dataset writes. The general Cheerio Actor requested broad account permissions; those were not granted. Do not enable broad permissions as a convenience.

Observed scope:

- Cafe Seventy8 public menu: 29 posted drink-price options at one venue; not a citywide price index. Tax/surcharge details and missing sizes are not guessed.
- Official SF wage page: one general statutory minimum wage reference, observed $19.61/hour effective July 1, 2026. This is a wage floor, not average earnings. The simulation explicitly assumes eight paid hours/day, giving 15,688 cents/day at that observation.
- Public source pages and values may change. Preserve dates and parse source evidence; do not hardcode these as perpetually current.

Prices actually initialize new business prices; wage observations actually initialize household wage references. Everything else remains synthetic unless separately sourced. Calibration IDs are immutable; worlds freeze the entire sample/provenance object and checksum. Forks and reset retain the frozen source even if its file changes/disappears.

Actor runs are bounded to configured resources and durations. A per-run charge parameter is not a guarantee against every possible platform charge. Avoid unnecessary recrawls/deployments. Best Actor Store-publication requirements were not conclusively resolved; the current Actor is private, not Store-published.

Sources: `https://www.cafeseventy8.com/` and `https://www.sf.gov/information/understanding-minimum-wage-ordinance`.

### Treasury shock stories

Uses the actual Debt to the Penny source and dated observations. A default hypothetical debt increase of 25% does not causally infer interest rates or bank losses. Separate assumptions include 200 bps yield increase, five-year modified duration and 50% exposure to a synthetic risky portfolio. The first-order duration calculation implies a 5% risky-portfolio loss under these defaults, not 25%.

Preview is nonfinancial and saves evidence. Apply requires the unchanged paused snapshot and posts once with provenance. Zero calculated loss cannot apply a financial shock. Oil/war/tax/rent/interest transmission models are not implemented.

## 9. Fetch.ai — completed technical demonstration

Two different credential types exist. `FETCH_AGENTVERSE_TOKEN` registers/connects the mailbox; `ASI1_API_KEY` is a separate optional inference credential. Do not put an Agentverse JWT into the ASI inference key setting. The successful agent workflow uses ACP plus live Nebius and does not require separate ASI inference.

Earlier keys returned 401. A replacement Agentverse token authenticated successfully, was saved privately, and completed the SDK `/connect` registration. A new stable private seed was created only because none existed. Preserve that seed: it determines the public identity.

**Agent address:** `agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm`.

**Public ASI:One profile:** https://asi1.ai/ai/agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm

Actual SDK: uagents 0.25.5, isolated `.venv-fetch`. ACP digest: `proto:30a801ed3a83f9a0ff0a9f1e6fe958cb91da1fc2218b153df7b6cbf87bd33d62`.

Verified stages:

1. Authenticated Agentverse list returned HTTP 200.
2. SDK mailbox registration succeeded.
3. Public discovery returned active/searchable status and the actual ACP protocol.
4. A signed temporary peer sent through `https://agentverse.ai/v2/agents/mailbox/submit`, received acknowledgement and completed the full workflow.
5. The same workflow was demonstrated in the actual ASI:One UI, not just the backend.

Commands:

- `data <world_id>`: sourced Census/FDIC context.
- `stress <world_id>`: bounded live policy analysis, no application.
- `status <job_id>`: inspect/wait for analysis.
- `stress-test bank 1 with a 40% loss and compare rescue plans`: create fresh synthetic world, apply hypothetical shock, compare and run live analysis.
- `why did you pick that?`: retrieve the last saved job/evidence for the same sender.

Actual UI evidence:

- Chat URL: `https://asi1.ai/chat/ebb13345-9c78-4175-8345-d3d44a9b87e8?from=profile` (account-scoped history, not guaranteed public judge access).
- Job: `job_9f21d7b98d9e41c697effc754e7a04da`.
- World: `world_c4824167313f4dbe`.
- Completed live Nebius/Nemotron response, three futures, three saved tool calls, same job on follow-up, `funds_applied=false`.
- Ignored proof: `artifacts/fetch-asi-one/evidence.json` and `artifacts/fetch-mailbox-verification.json`.

Recipient autocomplete did not find the full address/name, but the direct profile worked. Existing authenticated tab worked; a newly opened tab was logged out. Onboarding used the Researcher preset and skipped optional avatar generation; existing account/assistant names were preserved.

Do not interfere with a user's in-progress draft. An early stale-ref attempt sent an existing short draft and got the bounded help response; no world or financial action occurred. Subsequent sends checked the exact textarea `inputValue` before clicking. `innerText` is empty for a textarea and is not a safe draft check. Force-click was needed on an enabled visible send button because the page never settled its stability wait.

The mailbox verification peer originally hit an SDK shutdown cancellation cycle after successful assertions. Its harness now runs the SDK in the root task and stops its Uvicorn server normally. The corrected complete run exited cleanly. This was a test-lifecycle issue, not a failed financial workflow.

Technical demonstration is complete. Sponsor submission, Devpost and any additional hackpack submission workflow are still separate. Badges are present in the root README and Fetch guide. See [FETCH_AGENT.md](./FETCH_AGENT.md).

## 10. SpacetimeDB — completed collaborative workflow

Real TypeScript SDK/runtime 2.13.0, local server on port 3000. Existing module/database `economy-god-mode` was updated with `--delete-data=never`; old events and publishing identity were preserved.

SpacetimeDB is authoritative for collaborative presence/proposals/reviews/receipts. SQLite remains authoritative for financial accounting. Main dashboard SSE remains; shared control-room data arrives directly through real SpacetimeDB WebSocket subscriptions.

Tables:

- Private `publisher`: authorized backend publishing identity.
- Public `economy_event`: immutable bounded financial projection keyed by world/sequence.
- Public `control_room`: backend-published world ID, source SHA, tick and allowed banks.
- Public `participant`: browser identity, selected name and world.
- Public `proposal`: proposed loss, author, reviewing identity, source snapshot/tick, status and financial receipt ID.

Reducers:

- `ingest_events`: publisher-only atomic bounded event batches; exact replay succeeds, conflicting replay fails.
- `publish_context`: publisher-only snapshot/bank context.
- `join_room`: adds/updates named participation; disconnect removes presence for that identity.
- `propose_shock`: validates room membership, bank, loss and idempotent proposal ID; snapshots the room context.
- `review_proposal`: requires a different participating identity and a pending proposal; approve/reject transitions occur transactionally.
- `complete_proposal`: publisher-only execution receipt transition.

Backend endpoints:

```text
POST /api/worlds/{world_id}/control-room
POST /api/worlds/{world_id}/control-room/{proposal_id}/execute
POST /api/worlds/{world_id}/spacetime/enable
GET  /api/worlds/{world_id}/spacetime
GET  /api/worlds/{world_id}/spacetime/events
```

Execution loads actual approved proposal state from SpacetimeDB, verifies world ownership, and checks source SHA inside the locked SQLite mutation. Financial transaction ID is `room_<proposal_id>`. If the financial commit succeeds but the SpacetimeDB acknowledgement fails, retry returns the existing ledger receipt and finishes the shared status without applying another loss. Stale/unapproved/wrong-world proposals fail closed.

UI demonstration:

1. Open a paused economy; expand **Data, fraud & shared events**.
2. **Open shared control room**, enter a name and join.
3. Share `?room=<existing_world_id>` with another browser profile/private window; join there.
4. Propose a hypothetical 40% Bank 1 loss.
5. A different participant approves. Approval moves no money.
6. Execute separately and observe the synchronized receipt/event.
7. Demonstrate safe replay and rejection after the world changes.

Browser identities are not verified separate people or authenticated production roles. The local API remains unauthenticated. Do not claim a regulated two-person control. Localhost share links only work on the same host; remote judging needs separately configured accessible services.

Verified: two independent Chrome contexts, presence and actual subscriptions, proposer approval blocked, server-side self-approval rejected, pending execution rejected, approval without mutation, execution/replay, actual shared loss event, balanced audit, stale rejection, persistence on reload, forged context/receipt and invalid bank rejected, mobile capture, no browser page exceptions.

Harness: `scripts/qa-control-room.mjs`. Evidence: ignored `artifacts/control-room/evidence.json`, `alice.png`, `mobile.png`. Unit tests additionally cover the lost-acknowledgement recovery path. See [SPACETIME_SUBMISSION.md](./SPACETIME_SUBMISSION.md).

## 11. x402 — real on-chain test payment completed

Actual Python x402 SDK 2.25 in isolated `.venv-x402`. Merchant: local FastAPI on port 8402. Facilitator: `https://x402.org/facilitator`.

- Network is **Base Sepolia only**, CAIP-2 `eip155:84532`.
- USDC contract: `0x036CbD53842c5426634e7929541eC2318f3dCF7e`.
- Price cap: 10,000 atomic USDC units = 0.01 test USDC.
- Buyer: `0xfdd50b3fCF1457DaeC03D2A1Fa3A087e98C81683` (public address, not a secret).
- Circle public faucet sent 20 test USDC; independent RPC confirmed 20,000,000 atomic units before purchase.
- Successful payment: `0xf003b24fbbd32c3171161e8026615a8efa851591174db961ee1025c431906e86`.
- Explorer: https://sepolia.basescan.org/tx/0xf003b24fbbd32c3171161e8026615a8efa851591174db961ee1025c431906e86

The actual SDK performed the real HTTP 402 challenge, bounded signature, facilitator settlement and response. Independent RPC verified successful transaction status and exact token transfer parties/amount. The forecast response matched the requested synthetic world and snapshot. No simulated ledger debit occurred.

Buyer and merchant are separate project-controlled test identities. This is not mainnet spending, customer revenue or evidence of a validated financial forecasting product. Do not assume today's wallet balance; query it before any new authorized payment.

Merchant route: `GET /market-forecast/{world_id}?snapshot={sha256}`. It returns a three-day trailing-employment trend extrapolation from that exact synthetic world, with explicit limitations. It is not a causal or real-market forecast.

Safety and replay:

- Fixed supported network/asset/recipient, one-cent cap and short authorization validity.
- Explicit live-run `allow_paid_research=true` is required for the policy tool.
- Durable reservation permits at most one purchase attempt per agent run.
- Ambiguous payment failures do not automatically retry.
- Both receipt and returned world/SHA must verify before success.
- Standalone verification `scripts/verify_x402_live.py` exclusively creates ignored `data/x402-live-verification.json`; rerunning refuses another attempt. Do not delete that marker to retry blindly.

Proof: ignored `artifacts/x402-live-verification.json`. This was an explicitly invoked SDK verification, not an autonomous LLM purchase. A separate actual live Nemotron run with paid research enabled completed with inspect/inspect/compare/recommend and did not choose the optional purchase tool. Its report is `artifacts/x402-live-agent.json`. Do not conflate tool permission with actual tool use.

See [X402_SUBMISSION.md](./X402_SUBMISSION.md). Sponsor submission remains separate.

## 12. CRS — implemented, but not live-complete

Existing implementation includes sandbox auth, identity/fraud screens, strict vendor decision normalization, redacted report caching, optional credit-report underwriting, receiver-bound approval evidence and guarded simulated payment.

Current development configuration has no CRS username/password/access token/product config/test profile path/decision-rule path. The user was asked to provide private sponsor sandbox configuration; none was available at the last check. Do not invent profiles, response mappings or successful calls.

Required private settings may include:

```text
CRS_USERNAME / CRS_PASSWORD, or CRS_ACCESS_TOKEN
CRS_PRODUCT_CONFIG
CRS_TEST_PROFILES_PATH
CRS_DECISION_RULES_PATH
CRS_CREDIT_PRODUCT_CONFIG
CRS_CREDIT_REPORT_VARIANT
CRS_CREDIT_RULES_PATH
```

Use actual enabled products and documented sponsor test identities only. Unknown or missing fields are `review`, not clear. Blocking evidence cannot be overridden to settle. Browser/API reports expose opaque profile IDs and normalized evidence; raw SSNs, addresses, tokens and identity reports must not reach models, shared feeds, source control or logs.

The dedicated guarded $1 simulated payment requires fresh live clearance for the exact receiver/world/tick; demo-clear results cannot authorize it. Ordinary simulation payments are separate. Approval is not proof against fraud or production identity verification.

Next work after credentials arrive: verify authentication/product config, map real documented fields, pull sponsor test evidence, demonstrate clear/block/review and human escalation, verify no mutation on block/approval, settle separately once, and update live evidence. See [SPONSOR_INTEGRATIONS.md](./SPONSOR_INTEGRATIONS.md) and [TRACK_IMPLEMENTATION.md](./TRACK_IMPLEMENTATION.md).

## 13. Track readiness — distinguish implementation from submission

| Category | Current technical/evidence status | Remaining |
| --- | --- | --- |
| Hyphenate autonomous finance | Live credit/policy, recovery guards, human approval, separate audited settlement and recorded demo | Final submission and judging rehearsal |
| Apify Best Use | Real private Actor, actual inputs used, automatic load, provenance/frozen snapshots | Final submission/judge access |
| Apify Best Actor | Custom Actor built and verified | Confirm whether Store publication is required; private Actor is not Store-published |
| Microsoft Built for the Real World | End-to-end workflow, comparison report, multi-seed evaluation and production plan | Submission; real customer discovery remains unperformed |
| Most Technically Complex Hack | Accounting, reproducible forks, tools, safeguards, realtime collaboration and test evidence | Submission and concise technical presentation |
| Fetch.ai | Registered/searchable ACP agent, mailbox test and full ASI:One UI conversation completed | Event-specific submission paths and judge-access arrangement |
| SpacetimeDB | Real shared workflow, reducers and direct subscriptions, two-browser verified demo | Submission and any remote judging access |
| Coinbase x402 | Real testnet purchase and independent receipt proof; optional agent tool implemented | Submission; do not claim autonomous payment choice |
| CRS | Adapter, policies and fixtures implemented | Sponsor configuration and live verification |
| Capital One Nessie | Not implemented, never started | Out of the requested partial-completion scope unless user asks |
| Nebius × NVIDIA | Actual Nebius/NVIDIA model usage and working local application | Separate event: team-approved license, remote access, public video and submission |

Microsoft Customer Impact is a possible related category, but customer impact has not been established. Eligibility and selection remain organizer decisions; working integrations do not guarantee a prize or accepted entry.

Official reference locations already used:

- https://hive.hackberkeley.org/prizes — client-rendered prize cards; a plain fetch may show only loading/unavailable.
- https://cal-hacks-13-0.devpost.com/
- https://www.fetch.ai/events/hackathons/calhacks-13-0/hackpack
- https://calhacks.crscreditapi.com/
- https://nebiusglobalaihackathon.devpost.com/

Previously observed Cal Hacks deadline: October 25, 2026 at 9 AM Pacific; Nebius separate-event deadline: October 30 at 10 AM Pacific. These are historical observations, not a replacement for checking current rules before submission. Nebius judging/access was listed through December 15, 2026. Do not select an open-source license on behalf of all contributors without resolving their ownership/choice.

## 14. Existing judging assets and evaluation results

### Hyphenate/Apify

Guide: [HYPHENATE_APIFY_SUBMISSION.md](./HYPHENATE_APIFY_SUBMISSION.md). Final readable live recording:

```text
artifacts/hyphenate-apify-2026-10-25T03-52-13-456Z/
  evidence.json
  page@2cc9d7dd6010ba1c0fe36444b632a5e5.webm
  [six screenshots]
```

Actual live credit principal: 78,440 cents. Human approval moved no money; separate settlement posted once. Final recommendation in that recording was household cash for 1,000,000 cents; it was not applied. An earlier successful run recommended no intervention. Never promise a fixed model decision.

Public-input worlds in the recorded experiments ended with zero employment/eight defaults across all branches at day 12. Do not reuse the favorable seeded-demo results to describe those public-input worlds.

### Microsoft/technical complexity

Guide: [MICROSOFT_TECHNICAL_SUBMISSION.md](./MICROSOFT_TECHNICAL_SUBMISSION.md).

`scripts/evaluate_track_scenarios.py` evaluated seeds 41–45 × synthetic/public-input modes × three strategies = 30 branches, 12 days, 40% Bank 1 risky-asset loss and $10,000 support. All branch audits balanced; ten source worlds stayed unchanged.

- Seeded seed 42: household support saved five simulated jobs and avoided one default relative to baseline.
- All five public-input seeds: all three strategies ended at zero jobs/eight defaults. This is an unfavorable/zero-benefit result that must remain visible.
- Public observations do not calibrate the remaining behavioral assumptions.

Ignored output: `artifacts/microsoft-technical-evaluation/evaluation.md` and JSON. Standalone comparison examples: `artifacts/microsoft-technical-evidence/public-comparison.html` and `seeded-comparison.html`.

### Other saved evidence

| Location | Meaning |
| --- | --- |
| `artifacts/live-city-integration/verification.json` | Live rebuilt-city financial binding/browser checks |
| `artifacts/control-room/evidence.json` | Actual shared-control-room verification |
| `artifacts/fetch-mailbox-verification.json` | Real signed ACP mailbox experiment and follow-up |
| `artifacts/fetch-asi-one/evidence.json` | Browser UI witness plus actual backend report |
| `artifacts/x402-live-verification.json` | Real SDK payment and verified transfer receipt |
| `artifacts/x402-live-agent.json` | Live policy run with permission, no purchase chosen |
| `artifacts/apify-remote-verification.json` | Read-only remote Actor/run verification |

Artifacts, databases, recordings and private configuration are ignored and do not arrive in a fresh Git clone. Transfer selected non-secret recordings/reports separately if another machine needs them. Never copy all ignored `data/` or credential documents into a public repository.

## 15. Verified tests and practical test selection

Latest results for pushed implementation `6cfdf86`:

- Full backend: **176 passed, one optional skipped**.
- Frontend: **74 tests passed**, 12 files.
- Isolated actual x402 SDK suite: **nine passed** with mocked facilitator/RPC for deterministic regression checks; supplemented by the real payment above.
- SpacetimeDB module TypeScript check: passed.
- Production TypeScript/Vite build: passed.
- Shared-control-room real browser QA: seven final check groups passed, no page exceptions.
- Earlier rebuilt-city and broader integration browser checks passed.
- Full publishable-file private-credential scan passed before push, including DOCX XML scanning.

Commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm test
npm run build
npm run check --prefix spacetimedb
.\.venv-x402\Scripts\python.exe -m pytest tests/test_x402_sdk.py -q
node scripts/qa-control-room.mjs
node scripts/qa-live-city.mjs
node scripts/qa-integration.mjs
git diff --check
```

Other useful browser checks: `qa-apify-auto.mjs`, `qa-apify.mjs`, `qa-shock-story.mjs`, `qa-comparison-report.mjs`, `qa-credit-safeguards.mjs`, `qa-sponsors.mjs`, `qa-hyphenate-apify.mjs --live`.

Do not rerun every test or paid workflow merely because a new LLM joined. Rerun checks appropriate to actual changes or unresolved concerns. Some browser scripts create separate synthetic worlds; some consume inference or collection usage. `verify_x402_live.py` deliberately refuses reruns after its saved attempt.

Existing warnings: Starlette/httpx deprecation; large Vite JS bundle, approximately 5.25 MB uncompressed. Three geometry correctness tests have bounded 20-second timeouts because they exceed Vitest's default five seconds even standalone. Assertions were preserved; geometry was not altered to hide failures.

## 16. Private configuration and fresh-machine limitations

Never paste credentials into chat, docs, logs, URLs, process arguments, frontend code or Git. The user previously shared Fetch credentials in chat; those values are intentionally omitted here. Read local private settings only as required to use them safely.

Ignored locations include:

- Root `.env`, `.env.*` except the example template.
- `data/`, including `economy.sqlite3`, calibrations, publisher JWT/keys, test wallets, candidate credential probes and attempt markers.
- `.venv`, `.venv-fetch`, `.venv-x402` and installed dependencies.
- `private_keys.json`, agent SDK state files and wallet material.
- `artifacts/`, logs, build outputs and browser QA recordings.
- `Free api resources cal hacks.docx`, a credential-bearing source document. Do not dump or publish it.

Relevant environment variable names, without values:

| Area | Variables/status |
| --- | --- |
| Live model | `NEBIUS_API_KEY`, `NEBIUS_MODEL`, `NEBIUS_BASE_URL` — configured and verified |
| Public collection | `APIFY_TOKEN`, `APIFY_ACTOR_ID`, optional `APIFY_CALIBRATION_DIR` — configured and verified |
| Fetch mailbox | `FETCH_AGENT_SEED`, `FETCH_AGENTVERSE_TOKEN`, optional `FETCH_AGENT_ENDPOINT` — configured/verified; preserve seed |
| Separate ASI inference | `ASI1_API_KEY`, `ASI1_MODEL` — adapter configured but successful inference not established |
| SpacetimeDB | `SPACETIMEDB_URL`, `SPACETIMEDB_DATABASE`, `SPACETIMEDB_TOKEN` — local publisher configured/verified |
| x402 | `X402_WALLET_PRIVATE_KEY`, `X402_MERCHANT_ADDRESS`, optional `X402_FORECAST_URL`, `X402_PYTHON` — configured/verified |
| CRS | Auth/product/profile/rule variables listed above — missing at last check |
| Local service | `ECONOMY_DB_PATH`, `ECONOMY_CORS_ORIGINS`, approval threshold options |

`scripts.run_backend.load_environment` loads only supported keys from root `.env`; shell variables take precedence. Plain Uvicorn does not automatically load that file. Restart the appropriate known project process after changing environment settings.

SpacetimeDB publisher credentials must never be sent to browsers. Browser room tokens identify only the participant and are retained in session storage scoped to host/database. Sharing a world URL is not authorization for real financial operations.

## 17. Runtime snapshot and restart instructions

At approximately 05:47 UTC, all of these listeners were present. Treat PIDs as historical; recheck before acting.

| Port | Service | Observed PID |
| --- | --- | --- |
| 5173 | Vite app | 29732 |
| 8000 | FastAPI | 24160 |
| 3000 | Local SpacetimeDB | 30460 |
| 8002 | Fetch ACP gateway/inspector | 21712 |
| 8402 | x402 merchant | 29548 |

First inspect listeners/process command lines. Never stop arbitrary Python or database processes just because a port is occupied.

Core API/UI:

```powershell
Set-Location C:\Users\naray\Downloads\Calhacks
.\.venv\Scripts\python.exe -m scripts.run_backend --port 8000
# Separate terminal:
npm run dev
```

Use `npm ci` and environment installation only for first setup/dependency changes, not on every turn. Normal API launcher without reload was used for the latest stable checks. App: `http://127.0.0.1:5173`; API docs: `http://127.0.0.1:8000/docs`; health: `/health`. Vite proxies `/api` and `/health` to port 8000.

SpacetimeDB, if stopped:

```powershell
.\data\spacetime-bin\spacetimedb-standalone.exe start --listen-addr 127.0.0.1:3000 --data-dir data/spacetime-server --jwt-pub-key-path data/spacetime-keys/public.pem --jwt-priv-key-path data/spacetime-keys/private.pem --non-interactive
```

Only after actual module changes, preserving data:

```powershell
npm run check --prefix spacetimedb
.\data\spacetime-bin\spacetimedb-cli.exe --root-dir data/spacetime-cli publish economy-god-mode --module-path spacetimedb --server http://127.0.0.1:3000 --delete-data=never --yes=skip-login
.\data\spacetime-bin\spacetimedb-cli.exe generate --lang typescript --module-path spacetimedb --out-dir apps/web/src/data/spacetime --yes
```

The portable binaries, keys, publisher authentication and database already exist locally. Do not regenerate them just because they are absent from Git. A genuinely new machine needs its own explicit setup; read the integration guide rather than silently replacing local identity.

Fetch, if stopped:

```powershell
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_agent --check
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_agent
# Separate terminal only if registration/profile refresh is needed:
.\.venv-fetch\Scripts\python.exe -m scripts.connect_fetch_agent
```

Keep backend and gateway alive for external chat. The inspector is a development service; do not publicly expose it as the hosted application. API-based Almanac/mailbox operation works without funding the optional Almanac-contract wallet.

x402 merchant, if stopped:

```powershell
.\.venv-x402\Scripts\python.exe -m x402_service.server
```

Do not run the standalone live-payment verification again by deleting its marker. The successful existing receipt is sufficient evidence.

For background helpers on Windows use hidden windows and ignored redirected logs. Avoid cross-shell destructive commands. Before any recursive deletion/move verify resolved targets remain within the intended workspace; there should be no reason to delete this project's databases to continue.

## 18. Known pitfalls and boundaries

- Existing history has obsolete statements such as Fetch 401, x402 wallet unfunded and local commits unpushed. The latest verified/pushed milestone supersedes them.
- Snapshot hashes bind results to precise worlds. Do not attach an old model recommendation to a new fork/world just because strategies match.
- For browser harnesses, unconditional init scripts that reset localStorage can undo newly created world selection on reload. Stop the old page or initialize conditionally; late SSE/poll callbacks can also overwrite selection.
- The connected city must bind replacement backend entity objects after state changes. Featured geometry IDs remain decorative; agent bindings carry real IDs. Stress includes active-but-lending-constrained banks; closures derive from actual business status.
- Demand/movement indices are visualization proxies, not measured neighborhood economics.
- Local API authentication, customer verification, calibrated balance sheets, comprehensive role permissions and hosted multiuser security are not implemented production guarantees.
- SQLite stores complete history/checkpoints. Long-running/high-volume workloads need storage/scaling work; configured population limits are not throughput benchmarks.
- SpacetimeDB presence uses browser identities. Multiple sessions do not prove multiple humans.
- Core ledger/settlement handles real calculations on synthetic state; the only verified external token payment here is the explicit Base Sepolia x402 test purchase.
- Historical model failures are retained. A fresh successful run does not prove an old unconfirmed root cause was fixed.
- Tool execution sometimes failed sandbox helper initialization. Scoped normal escalation review worked. A later account-credit review error was not a security finding; the user added credits and authorized continuation. Do not bypass denied reviews.
- Browser page IDs and authentication are session-scoped. Re-discover current tabs; never assume an old ID or login persists.

## 19. Recommended continuation, dependent on the user's next request

1. Check Git status and read this brief plus the latest continuity section. Do not redo completed sponsor integrations.
2. If the user wants CRS finished, obtain/configure actual private sponsor sandbox credentials, product settings, test profiles and mappings, then verify the guarded workflow live.
3. If the user wants submissions, review current official rules, ensure judge access, use the prepared guides and obtain the actual submission authorization/details. No Devpost or sponsor-specific entry has been made.
4. If the user wants the separate Nebius event, resolve team licensing choice, accessible hosted/test build, funding/access through judging and public narrated video. Working runtime inference alone is not that entry.
5. If the user wants a production deployment, first implement authentication and operator roles, decide hosting for API/database/gateway, protect private keys, and validate actual remote access. A localhost tunnel alone does not make the current unauthenticated app production-ready.
6. If the user wants more financial realism, propose scoped validated datasets/behavior and honest evaluation; do not hide unfavorable public-input scenario outcomes or invent causal economics.
7. If the user asks to push this new brief, commit the documentation separately as their normal Git identity and push without force after checking upstream. The implementation through `6cfdf86` is already published.

## 20. Copy/paste starter instruction for the next LLM

> Continue the Economy God Mode repository at `C:/Users/naray/Downloads/Calhacks`. Read `AGENTS.md`, `docs/LLM_CONTINUATION_BRIEF.md`, and the newest sections of `docs/SESSION_HANDOFF.md` first. Implementation through `6cfdf86` is pushed on `main`; SpacetimeDB collaboration, real x402 testnet settlement, and the full Fetch ASI:One UI conversation are verified. Do not redo them or rerun payments. CRS still needs actual private sponsor configuration. Preserve all source, worlds, frozen public observations, stable identity seeds, private configuration and teammate city work. Keep real observations, hypothetical assumptions and synthetic state separate. Never print or commit credentials. Check current Git/runtime state instead of trusting historical PIDs. Follow my next request, and update continuity after significant changes.
