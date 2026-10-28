# Economy God Mode: agents, responsibilities, APIs and tracks

> Latest integration: teammate commit `10afec8` has been merged locally from the identical `origin/shivangi` and `origin/shivanginarayan` branches. It adds ten typed deterministic Fetch service adapters, in addition to the live AI roles described here. They now use actual saved-world calculations and explicit errors rather than sample outcomes. They are not ten additional live LLM models or ten verified externally registered agents. See [the current ecosystem guide](./FETCH_ECOSYSTEM.md). Existing implementation and documentation checkpoints are preserved; check current Git history for the final integration commit and publication state.

This document describes the implemented project as of October 25, 2026. The implementation through Git commit `6cfdf86` is pushed. This catalog was prepared afterward as documentation. It inventories actual code and verified evidence; it does not claim that event entries have been submitted.

## 1. Direct answer: which agents do we have?

The product has **three main financial-agent workflows**, built from **five economic AI role types**:

1. Central-bank policy analyst.
2. Business borrower/payroll-financing agent.
3. Bank underwriting/credit-officer agent.
4. Business procurement/buyer agent.
5. Supplier sales/negotiation agent, instantiated for two competing suppliers in a procurement run.

One policy run, one credit run and one procurement run therefore use **six task-specific financial role instances**: one policy analyst, two credit participants and three procurement participants. These are workflow instances, not six permanently running services or six separately registered Fetch agents. The same simulated business can occupy a borrower role in one workflow and a buyer role in another.

There is also:

- **One registered Fetch ACP chat gateway**, named `economy-god-mode`. It routes supported chat commands into backend workflows and retrieves saved evidence. Its command router does not independently use an LLM to interpret arbitrary instructions.
- **One optional ASI data-research agent implementation**, with two source-retrieval tools. This separate inference path has not been successfully verified live; it is not needed for the successful Fetch chat demonstration.

All five economic AI role types use the same configured NVIDIA Nemotron model through Nebius in live mode. Their distinct tools, instructions, observations and validation rules give them different jobs.

### Inventory at a glance

| Agent or role | Where it runs | Main task | Model or mechanism | Current verification |
| --- | --- | --- | --- | --- |
| Central-bank policy analyst | Backend policy workflow | Inspect distress, compare rescue policies, recommend a tested strategy | Live Nemotron on Nebius; explicit deterministic demo also available | Live verified |
| Business borrower | Backend credit workflow | Request useful payroll credit, then accept or reject the actual bank offer | Live Nemotron on Nebius | Live verified |
| Bank underwriter | Backend credit workflow | Assess eligibility and approve, counteroffer or decline | Live Nemotron plus deterministic financial checks | Live verified; optional CRS evidence remains fixture-tested |
| Business buyer | Backend procurement workflow | Compare full supplier obligations, negotiate and select an eligible offer | Live Nemotron on Nebius | Live verified |
| Supplier 1 | Backend procurement workflow | Quote fulfillable stock and negotiate within supplier policy | Live Nemotron on Nebius | Live verified |
| Supplier 2 | Backend procurement workflow | Independently quote competing terms and optionally handle a counteroffer | Live Nemotron on Nebius | Live verified |
| Fetch chat gateway | Separate uagents process, port 8002 | Accept supported ACP commands, launch experiments, return results/evidence | Signed ACP messages plus bounded command parsing | Registered, searchable, mailbox and ASI:One UI verified |
| Optional ASI research agent | Backend research adapter | Call Census and FDIC tools with source provenance | ASI chat-completions tool calling | Implemented; successful separate inference not verified |

## 2. What does not count as an LLM agent?

The default financial world contains **55 entities**:

| Entity type | Default number | Behavior |
| --- | --- | --- |
| Households | 40 | Rule-based wages, consumption, employment and balances |
| Businesses | 8 | Rule-based production, payroll, borrowing/default behavior, plus on-demand AI workflow roles |
| Commercial banks | 5 | Rule-based ledger, capital/liquidity, credit and clearing, plus on-demand AI underwriting roles |
| Government | 1 | Public debt and fiscal-support accounting |
| Central bank | 1 | Public lending/accounting entity, with an on-demand policy-analyst workflow |

These entities do not each make an LLM call every day. Pressing Play advances the deterministic simulation. AI reviews are separately requested through the UI, API or Fetch chat.

Additional components are services or deterministic controls:

- **Apify Actor:** a real deployed scraper/collector, not an LLM agent.
- **SpacetimeDB:** authoritative collaborative database/reducers/subscriptions, not a financial model or an AI agent.
- **x402 merchant:** paid deterministic trend-analysis service, not another live LLM.
- **CRS adapters:** evidence retrieval and normalization, not autonomous identity-verification agents.
- **Ledger/audit/settlement engine:** validates and executes financial operations deterministically.
- **Human reviewer:** a person operating an approval interface; not an AI role.
- **400 animated city movers:** visual objects; they are not 400 economic or LLM agents.
- **Fork Reality ranking:** deterministic comparison logic; it is separate from the AI recommendation.

## 3. Shared agent design and operating rules

### Model and runtime

- Provider: **Nebius Token Factory**.
- Model: **`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`**.
- API base: `https://api.tokenfactory.nebius.com/v1`.
- Inference route: `POST /chat/completions` relative to that base.
- Implementation: [provider.py](../backend/provider.py).
- Function calls are required; the model selects among explicitly supplied tools.
- Temperature is 0.2; output cap is 4096 tokens.
- Thinking is disabled for this bounded Nemotron tool configuration to keep calls within the output budget.
- Public tool calls/results and concise rationales are saved. Hidden reasoning is not stored or displayed.
- Live failures remain visible; there is no silent substitution of a deterministic demo.

### The model proposes; validated functions determine outcomes

Each role receives a limited tool list and a captured source world. It cannot gain permissions by writing instructions in prose. Tool arguments go through schemas and deterministic policy checks. Financial settlement is a separate operation with source-state and replay checks.

Every amount ending in `_cents` is an integer number of US cents. For example, `1000000` cents is **$10,000**. Model prose is not used as a ledger posting or authoritative numeric observation.

### Memory and coordination

- Financial role sessions use the workflow's saved snapshot, tools and public trace.
- A credit run records borrower, bank, proposed principal, assessments, offer and acceptance.
- A procurement run records suppliers, offers, counteroffer, selection and contract state.
- Persistent reports are stored in SQLite and can be reopened after a request finishes.
- Financial role models do not have an unrestricted persistent personal memory or an open-ended chat with every household.
- The Fetch gateway separately remembers the last analysis job per sender to support the evidence follow-up.
- SpacetimeDB owns shared room proposals/reviews/receipts; it does not replace the existing LLM provider or the SQLite ledger.

## 4. Agent 1: central-bank policy analyst

### Purpose and task

Acts as a stress-testing analyst for the synthetic economy. It observes bank distress, tests alternatives and recommends one of the outcomes actually calculated during that run.

Code: [agents.py](../backend/agents.py), [forks.py](../backend/forks.py), [interventions.py](../backend/interventions.py).

### What it sees

- Source-world metrics and tick.
- Each bank's capital ratio, liquidity ratio, equity, assets, reserves and lending availability.
- Recent applied sourced-debt shock context, when present.
- Calculated comparison outcomes and baseline deltas returned by its tools.
- Caller-selected target bank, support cap, horizon and experiment limit.

It does not receive provider credentials or raw CRS identity reports.

### Tools

| Tool | Task | Result or boundary |
| --- | --- | --- |
| `inspect_economy` | Observe the captured world before deciding | Actual synthetic metrics and bank financial state |
| `compare_interventions` | Calculate all three strategies from the same snapshot at a specified target/budget | Isolated no-intervention, bank-lending and household-cash branches |
| `recommend_intervention` | Finish with a tested strategy and short rationale | Saved recommendation bound to a comparison from this run |
| `buy_market_forecast` | Optionally purchase a snapshot-specific trend projection | Available only for explicitly authorized live runs; one-cent testnet cap |

### Typical workflow

1. Inspect the economy.
2. Choose an allowed target bank and budget.
3. Compare three futures using matched starting state/random stream.
4. Optionally test another permitted budget/target or purchase permitted research.
5. Recommend a strategy from the comparisons actually returned in this run.
6. Save the public report and quantitative evidence.
7. Wait for a separate user application action if support is to affect the source world.

Default request values are a $10,000 gross support cap, 12-day horizon and two experiments. The request schema permits bounded alternatives; inspect the current schema before changing UI assumptions. The policy loop is capped at ten model turns and validates batches of one to four tool calls.

### Restrictions

- Must inspect before comparing or buying research.
- Cannot exceed the authorized budget, experiment count or caller-selected target.
- Cannot recommend an untested comparison or invent a branch.
- Analysis does not apply the recommendation to the source.
- Applying support separately revalidates the saved source and posts once.
- Liquidity lending adds bank debt; it does not repair insolvency by itself.
- Gross disbursement, fiscal transfers and outstanding loans must remain distinct.

### APIs, tracks and proof

- Model API: Nebius/NVIDIA Nemotron.
- Local job API: `POST /api/worlds/{id}/agent-jobs`.
- Synchronous alternative: `POST /api/worlds/{id}/agent-runs`.
- Separate application: `POST /api/agent-runs/{run_id}/apply`.
- Optional paid tool: actual x402 SDK/facilitator/Base Sepolia.
- Strong relevance: **Hyphenate**, **Microsoft Built for the Real World**, **Most Technically Complex Hack**.
- Also powers the analysis behind the **Fetch.ai** conversation.
- Nebius/NVIDIA runtime usage supports a **separate Nebius event**, whose submission is not completed.

Live policy calls are verified. A successful ASI:One run returned three futures and three public tool calls without applying support. Its model rationale claimed reduced insolvencies even though that delta was zero: use quantitative returned evidence when presenting results.

## 5. Agent 2: business borrower/payroll-financing agent

### Purpose and task

Represents a selected business seeking useful short-term payroll financing. It decides whether to request credit, proposes a bounded amount, and later decides whether the bank's actual offer is useful.

Code: [credit_agents.py](../backend/credit_agents.py), [credit_store.py](../backend/credit_store.py).

### Inputs

Business deposits, payroll requirement, observed funding shortfall, existing debt, business status, bank health and caller's maximum amount. The second phase receives the approved bank offer and observed payroll coverage.

### Request-phase tools

| Tool | Task |
| --- | --- |
| `inspect_business` | Read payroll, deposits, debt and bank facts |
| `request_credit` | Propose principal within the observed payroll shortfall and caller cap |
| `continue_without_credit` | End without borrowing and record a rationale |

### Acceptance-phase tools

| Tool | Task |
| --- | --- |
| `review_offer` | Inspect the actual approved principal/maturity and coverage |
| `accept_offer` | Accept the exact offered terms |
| `decline_offer` | Reject the bank's offer without borrowing |

Acceptance is another phase of the same business role, not an additional borrower or a newly registered external agent.

### Restrictions and outputs

- Closed businesses cannot request a new payroll loan through this workflow.
- The request cannot exceed the caller cap or observed funding gap.
- Default maximum is 500,000 cents ($5,000), with the same current schema ceiling.
- It cannot change the bank's offer or create an arbitrary loan through prose.
- Acceptance records intent; it is not financial settlement.
- Result statuses can include not requested, declined, approved, human approval required, settled or failed.
- Default `auto_settle` is false. An explicitly authorized automatic settlement remains subject to the same deterministic and human-approval controls.

### APIs and tracks

- Nebius/NVIDIA Nemotron for the business decisions.
- `POST /api/worlds/{id}/businesses/{business_id}/credit-jobs`.
- Synchronous alternative: `/credit-runs` at the same business path.
- **Hyphenate:** bounded financial autonomy and knowing when to escalate.
- **Microsoft/technical complexity:** usable underwriting workflow, evidence and settlement safeguards.
- **Apify:** observed wage inputs can influence the payroll need that the agent inspects; the borrower does not directly scrape data.

Live borrower behavior was verified in the recorded human-gated credit demo. Its actual principal was 78,440 cents in that run; that is a particular observed run, not a fixed principal promised by the model.

## 6. Agent 3: bank underwriting/credit-officer agent

### Purpose and task

Represents the business's commercial bank. It reviews a request, tests financial eligibility and approves eligible principal, makes a smaller counteroffer or declines.

Code: [credit_agents.py](../backend/credit_agents.py), [credit_policy.py](../backend/credit_policy.py), [crs_credit.py](../backend/crs_credit.py).

### Tools

| Tool | Task | Availability |
| --- | --- | --- |
| `inspect_credit` | Read the proposal and captured financial facts | First prerequisite |
| `pull_credit_report` | Retrieve bound sponsor-test CRS evidence, redacted for the agent | Only when CRS-backed underwriting is explicitly requested |
| `assess_credit` | Validate principal against deterministic credit and post-issuance constraints | After inspection and any required CRS evidence |
| `decide_credit` | Approve an assessed eligible amount or decline with zero principal | After a successful assessment |

### Assessment and escalation

The deterministic assessment considers borrower debt headroom, bank capital/liquidity and post-loan constraints. Optional CRS controls add score/risk decisions and human-review reasons. Model claims cannot override eligibility.

The bank's counteroffer cannot exceed the business request. Approval requires positive principal; a decline requires zero. Interest and collateral are not modeled in this credit negotiation.

Tool exposure is staged by successfully completed prerequisites. A previous live failure repeatedly tried to decide after a rejected assessment. The implementation now withholds the decision tool until an assessment succeeds, while handlers still validate every attempted call. This is a concrete reliability improvement with a regression test.

Each credit role phase has a bounded eight-turn loop. Public traces identify role, actor, tool, arguments, acceptance/rejection and result.

### Human approval and settlement

Large or flagged credit can require a human decision with a rationale. Human approval does not create the loan. Separate settlement rechecks snapshot, evidence, acceptance and eligibility, then posts the exact amount once. Blocked identity/fraud evidence cannot be overridden to permit settlement.

Endpoints:

```text
GET  /api/credit-runs/{run_id}
POST /api/credit-runs/{run_id}/approval
POST /api/credit-runs/{run_id}/settle
```

Local operator approval is not production-authenticated access control.

### APIs, tracks and status

- Nebius/NVIDIA for the underwriting role's tool choices.
- Deterministic engine/ledger for actual eligibility and posting.
- Optional **CRS sandbox** for owner credit/fraud evidence.
- **Hyphenate** is the primary demonstration: inspect, assess, escalate, approve separately and settle once.
- **Microsoft/technical complexity** use the traceability, controls and error recovery.
- **CRS track** is partial: adapter and controls are implemented and fixture-tested, but real sponsor auth/product config/profiles/mappings are missing. No successful live CRS credit pull is claimed.

## 7. Agent 4: business procurement/buyer agent

### Purpose and task

Represents a selected active business buying materials to sustain production. It compares two actual supplier quotes, considers immediate cash and the full future obligation, optionally negotiates once and selects an eligible offer or declines.

Code: [procurement.py](../backend/procurement.py), [supply_policy.py](../backend/supply_policy.py), [supply_store.py](../backend/supply_store.py).

### Tools

| Tool | Task |
| --- | --- |
| `inspect_offers` | Read offered prices, down payments, due terms, affordability and current inventory |
| `negotiate_offer` | Request one revised price/payment/term from a supplier that actually quoted |
| `select_offer` | Accept an eligible offer produced in this run |
| `decline_offer` | End without a purchase |

After the counteroffer round, the final buyer phase no longer exposes negotiation, which bounds the conversation.

### Inputs and limits

- Materials quantity and maximum total invoice value.
- Current material/finished inventory and production context.
- Two real quotes from selected active businesses.
- Per-offer eligibility and down-payment requirements.
- Current schema defaults: quantity 20 and 100,000 cents ($1,000) maximum full cost.
- Default `auto_settle` is false.

The budget covers the entire invoice, not only today's down payment. Selecting an accepted contract includes the later automatic collection obligation. The buyer cannot negotiate with an invented supplier or select an invented offer ID.

### Settlement and economic effect

The report becomes ready after validated selection. Separate confirmation, or explicitly enabled automatic settlement, creates the contract and posts delivery/down payment atomically. Future scheduled supplier payments are deterministic contract behavior. Restocking can restore material-limited production on subsequent ticks; the model does not invent production gains.

### APIs and tracks

- Nebius/NVIDIA for buyer decisions.
- `POST /api/worlds/{id}/businesses/{buyer_id}/procurement-jobs`.
- Synchronous alternative: `/procurement-runs` at that buyer path.
- `GET /api/procurement-runs/{run_id}`.
- Separate settlement: `POST /api/procurement-runs/{run_id}/settle`.
- **Hyphenate:** another autonomous financial seat, with negotiated obligations and controlled execution.
- **Microsoft/technical complexity:** end-to-end supply/production workflow and accounting.

The live supplier workflow was previously verified. Broader integration QA separately verified contract settlement and production recovery.

## 8. Agents 5 and 6: competing supplier agents

### Why there are two instances

One procurement run asks exactly two supplier businesses for offers. They use the same supplier role implementation with different business identity, stock and policy facts. If supplier IDs are omitted, the backend selects two active businesses other than the buyer. A usable procurement world needs at least three active businesses.

### Initial quote tools

| Tool | Task |
| --- | --- |
| `inspect_supplier` | Observe fulfillable stock and supplier policy |
| `quote_offer` | Propose valid unit price, down-payment fraction and due term |
| `decline_offer` | Decline an unfulfillable or unwanted request |

### Counteroffer tools

| Tool | Task |
| --- | --- |
| `inspect_counteroffer` | Compare requested revised terms with supplier policy |
| `accept_counteroffer` | Accept the buyer's exact revised terms if valid |
| `decline_offer` | Reject revision while preserving the original offer |

The selected supplier may participate again in the single counteroffer round; this does not introduce a third supplier.

### Restrictions

- Inspect actual stock before quoting.
- Terms must satisfy deterministic minimum price, down-payment and due-date policy.
- Current quote schema bounds unit prices, requires 10–100% down payment and permits terms of 1–30 ticks; supplier-specific policy can be stricter.
- A provisional quote does not deliver materials or move balances.
- Supplier role sessions use a bounded six-turn tool loop.
- Only an accepted eligible offer can reach separate contract settlement.

They call Nebius/NVIDIA, not Apify, CRS or a real commercial supplier API. The suppliers and goods are simulated. Their primary track relevance is **Hyphenate**, with supporting evidence for **Microsoft** and **technical complexity**.

## 9. Fetch gateway: registered conversational access agent

### Identity and implementation

- Name: **`economy-god-mode`**.
- Registered address: `agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm`.
- [ASI:One profile](https://asi1.ai/ai/agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm).
- Actual uagents SDK 0.25.5 in `.venv-fetch`.
- Code: [run_fetch_agent.py](../scripts/run_fetch_agent.py), [connect_fetch_agent.py](../scripts/connect_fetch_agent.py), [fetch_chat.py](../backend/fetch_chat.py).

This is the one externally registered chat agent. The other economic roles are backend model/tool sessions invoked through it or the app.

### Tasks

1. Receive an ACP `ChatMessage` through Agentverse.
2. Send `ChatAcknowledgement`.
3. Extract text and match supported bounded commands.
4. Call the local backend for actual data/experiments/analysis.
5. Store the last job ID under a sender-specific hashed key.
6. Return a `ChatMessage` with result and end-session content.
7. On a why-follow-up, retrieve that sender's saved job evidence.

### Commands

| Command | Task |
| --- | --- |
| `data <world_id>` | Retrieve sourced Census/FDIC reference observations |
| `stress <world_id>` | Run live policy analysis for an existing world |
| `status <job_id>` | Inspect/wait for queued analysis |
| `stress-test bank 1 with a 40% loss and compare rescue plans` | Create a fresh synthetic world, apply the specified hypothetical shock, compare futures and run live analysis |
| `why did you pick that?` | Return the previous analysis's saved public evidence |

Unsupported text returns help. This router does not infer arbitrary permission to spend, settle loans or apply support.

### APIs and credentials

- Agentverse registration, active public discovery and mailbox delivery.
- Real Agent Chat Protocol (ACP), including signed delivery/acknowledgement.
- ASI:One UI for conversational interaction.
- Local FastAPI for the underlying simulation and workflow.
- Live Nebius/Nemotron behind the policy analysis.

`FETCH_AGENTVERSE_TOKEN` is for mailbox registration. `FETCH_AGENT_SEED` is the private stable identity. A separate `ASI1_API_KEY` is for optional ASI inference. Do not interchange them or rotate the stable seed during a restart.

### Verified demonstration

Actual ASI:One UI conversation returned completed job `job_9f21d7b98d9e41c697effc754e7a04da`, three futures and a same-job why-follow-up with three saved tool calls. `funds_applied=false`. Mailbox transport was separately verified using a signed temporary peer.

Track: **Fetch.ai**. The technical demonstration is complete; sponsor-specific submissions and judge access remain separate. See [FETCH_AGENT.md](./FETCH_AGENT.md).

## 10. Optional ASI data-research agent

Code: [research.py](../backend/research.py).

### Task and tools

It is instructed to retrieve both public datasets once and preserve provenance:

- `get_population`: US Census county population estimate for San Francisco.
- `get_bank_directory`: active FDIC-insured institutions headquartered in San Francisco.

Tools have empty argument schemas and no arbitrary URL input. Duplicate/unknown tools and invented arguments are rejected. The loop is bounded to three inference iterations. Returned numerical facts come from actual source responses, not model prose.

### API and status

- Optional model endpoint: `https://api.asi1.ai/v1/chat/completions`.
- Default configured model name in code: `asi1-mini`.
- Needs a valid separate `ASI1_API_KEY`.
- Successful separate ASI inference has **not** been verified. Earlier candidates were rejected.
- Direct public-source retrieval works independently and was verified.
- The Fetch ACP gateway's successful data/analysis paths do not depend on this optional model API.

Potential relevance is **Fetch.ai** and sourced research, but do not claim successful ASI inference from the verified ASI:One UI conversation; they are different paths.

## 11. Complete API/service inventory and how agents use it

| API/service | Actual use | Which roles depend on it | Verified state |
| --- | --- | --- | --- |
| Nebius Token Factory | NVIDIA Nemotron function-calling inference | Policy, borrower, bank, buyer and both suppliers | Live verified |
| NVIDIA Nemotron model | Shared language/tool-selection model hosted by Nebius | All core economic AI roles | Live verified through Nebius; no separate direct NVIDIA inference endpoint claimed |
| Fetch Agentverse | Register/discover agent, deliver ACP messages via mailbox | Fetch gateway | Registered, active, searchable and signed transport verified |
| ASI:One application | Chat with registered agent and inspect full workflow | User-facing Fetch conversation | Real UI experiment/follow-up verified |
| ASI inference API | Optional bounded data-research model | Optional research agent only | Implemented, not live-verified successfully |
| Apify Actor/run/dataset APIs | Execute fixed-source collector and retrieve observed values/provenance | Agent observations indirectly through frozen economy inputs | Real private Actor and runs verified |
| Cafe Seventy8 public menu | Posted drink-price observations | Indirect input to business prices and resulting agent facts | 29 options observed at one cafe |
| SF official wage page | Statutory minimum-wage observation | Indirect input to payroll/wages and credit facts | One dated wage-floor observation; eight-hour day is an assumption |
| Census public CSV | SF County population reference | Source-data functions, optional research, Fetch data command | Real source previously verified |
| FDIC BankFind API | SF-headquartered institution directory | Source-data functions, optional research, Fetch data command | Real source previously verified; not a branch directory |
| Treasury Debt to the Penny API | Dated national-debt baseline for a sourced hypothetical shock story | Context subsequently visible to policy analyst | Live source/preview/apply workflow verified |
| CRS sandbox | Optional fraud/identity evidence and credit reports | Bank underwriter and dedicated guarded-payment workflow | Fixtures/controls verified; live sponsor setup missing |
| SpacetimeDB SDK/server | Shared presence, proposals, approvals, receipts and financial-event subscriptions | Collaboration layer around the economy | Real local two-session workflow verified |
| x402 Python SDK + public facilitator | Paid snapshot-specific research request | Optional policy research tool; explicit test harness | Real one-cent Base Sepolia payment verified |
| Base Sepolia RPC | Verify chain, receipt and exact USDC Transfer log | x402 buyer | Real transaction independently verified |
| Circle public faucet | Fund the development test buyer | Setup for x402 only | 20 test USDC requested and funding verified |
| Local FastAPI | World state, tools, background jobs, reports and settlement | All application workflows/gateway | Working and tested |
| SQLite | Persistent snapshots, journals, reports, jobs and idempotency | Deterministic financial execution and saved workflow evidence | Working and tested; not a sponsor API |

### Source endpoints

```text
Nebius: https://api.tokenfactory.nebius.com/v1/chat/completions
Optional ASI: https://api.asi1.ai/v1/chat/completions
Census: https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv
FDIC: https://api.fdic.gov/banks/institutions
Agentverse authenticated agents: https://agentverse.ai/v2/agents
Agentverse public discovery: https://agentverse.ai/v1/search/agents
Agentverse mailbox delivery: https://agentverse.ai/v2/agents/mailbox/submit
x402 facilitator: https://x402.org/facilitator
Base Sepolia RPC: https://sepolia.base.org
Local app/API: http://127.0.0.1:5173 / http://127.0.0.1:8000
```

Provider credentials stay in ignored private configuration. The document lists endpoints and setting names, never their credential values. Check source-specific dates and current official documentation before changing integrations.

## 12. Supporting services and their tasks

### Apify public-input collector

Custom private limited-permission Actor `economy-public-sf` reads allowlisted public sources, checks robots rules, parses actual observations and writes the run's dataset. It does not make financial decisions.

App opening initializes public inputs automatically. Existing valid cache is returned immediately; missing or more-than-six-hour-old data triggers bounded background collection. Reloads/tabs reuse durable work rather than issuing uncontrolled crawls. New UI worlds default to those public inputs. Each world freezes its source/provenance/checksum so a later collection cannot change the experiment.

Tracks: **Apify Best Use**, potentially **Best Actor**, and supporting realism evidence for Hyphenate/Microsoft. Actor Store publication has not occurred; confirm whether Best Actor requires it. One cafe and a statutory wage floor do not constitute a calibrated city economy.

### SpacetimeDB shared control room

Stores presence, source context, shock proposals, independent-identity reviews and execution receipts. Reducers enforce membership, state transitions and publisher-only receipt/context updates. Clients subscribe directly to real tables.

A second browser identity can approve a proposal; approval does not move money. Separate backend execution rechecks the proposal's source SHA inside the SQLite transaction. `room_<proposal_id>` is the financial transaction key; replay or a lost shared acknowledgement cannot apply a second loss.

This collaboration coordinates human/browser participants and shared simulation state. The core LLM tool loops still use backend snapshots; do not claim every LLM role directly subscribes to SpacetimeDB. SQLite remains the accounting source of truth, while SpacetimeDB owns the collaborative workflow.

Track: **SpacetimeDB**. Real local two-browser demo completed. Anonymous identities are not verified separate people or production roles. See [SPACETIME_SUBMISSION.md](./SPACETIME_SUBMISSION.md).

### x402 paid research merchant and buyer

The merchant charges 0.01 test USDC for a three-day trailing-employment projection bound to the exact requested synthetic world/SHA. The buyer checks asset, network, recipient, amount, authorization validity, returned snapshot and on-chain transfer.

Real verified transaction:

https://sepolia.basescan.org/tx/0xf003b24fbbd32c3171161e8026615a8efa851591174db961ee1025c431906e86

The actual payment used the SDK verification harness. A separate live policy run enabled the optional purchase tool but did not choose it. Do not claim that the successful transfer was an autonomous model choice. The seller and buyer are separate project-controlled test identities; no customer revenue or mainnet payment is claimed.

Track: **Coinbase x402**. See [X402_SUBMISSION.md](./X402_SUBMISSION.md). Do not delete the durable saved attempt marker to repeat a payment merely for a demo.

### Job workers, playback and financial execution

Background workers claim policy/credit/procurement jobs, record progress/heartbeats and return saved reports. Playback advances deterministic ticks. The ledger checks/audits/posting and separate settlements execute validated financial actions.

These services are essential orchestration and enforcement infrastructure. They are not extra LLM agents and should not be added to an AI-agent count.

## 13. Agent-to-agent interactions

### Policy workflow

```text
User / Fetch command
  -> policy analyst inspects captured economy
  -> comparison tool calculates three isolated futures
  -> analyst recommends a tested strategy
  -> report saved
  -> separate user application, if authorized and still valid
```

### Credit workflow

```text
Business borrower inspects payroll shortfall
  -> proposes bounded credit
  -> bank underwriter inspects and optionally retrieves CRS evidence
  -> deterministic assessment
  -> bank approves/counteroffers/declines
  -> borrower reviews exact offer and accepts/declines
  -> human gate when required
  -> separate validated loan settlement
```

### Procurement workflow

```text
Supplier 1 inspects/quotes  +  Supplier 2 inspects/quotes
  -> buyer compares actual offers
  -> optional single counteroffer to a quoted supplier
  -> supplier accepts/declines revision
  -> final buyer selection/decline
  -> separate contract confirmation and atomic delivery/down payment
  -> deterministic future invoice collection and production
```

These interactions are coordinated by backend handlers using structured tool results and saved reports. They are not unconstrained agents messaging one another over an external social network.

## 14. Track mapping and remaining work

| Track | Our strongest implemented story | Relevant agents/services | What remains |
| --- | --- | --- | --- |
| Hyphenate autonomous finance | Payroll negotiation, human escalation, safe settlement, compare/explain rescue policies | Policy, borrower, bank, buyer, suppliers; ledger safeguards | Final submission and judging rehearsal |
| Apify Best Use | Real observations automatically load and initialize actual simulation inputs | Custom Actor, frozen calibration, downstream agent observations | Final submission/judge access |
| Apify Best Actor | Custom bounded limited-permission Actor with successful real runs | Actor itself, not another LLM | Confirm publication requirements; currently private |
| Microsoft Built for the Real World | End-to-end analyst/credit workflows, auditable reports and measured simulation evaluation | All financial roles and report/approval infrastructure | Submission; customer interviews and production impact not established |
| Most Technically Complex Hack | Accounting invariants, reproducible forks, bounded tools, jobs, safeguards and realtime collaboration | Whole system | Submission and focused technical presentation |
| Fetch.ai | Registered agent completes a full primary workflow inside ASI:One | Gateway and policy workflow | Required event submission paths and accessible judging setup |
| SpacetimeDB | Shared financial simulation with transactional proposals/reviews and instant subscriptions | Control room, publisher/executor and event feed | Submission and remote access if needed |
| Coinbase x402 | Bounded real paid API request with independently verified chain receipt | Optional policy tool, buyer, merchant and RPC verifier | Submission; keep SDK-vs-model-choice distinction |
| CRS | Evidence-backed credit/fraud controls with enforced blocks/escalation | Bank underwriter and CRS adapters | Real sponsor credentials, product config, test profiles and field mappings; live verification |
| Separate Nebius/NVIDIA event | Actual NVIDIA model runtime through Nebius | All five financial AI role types | Team license, hosted/test access, public video and separate submission |

Microsoft is a product/judging category here; we have not integrated Azure or a Microsoft agent API. Most Technically Complex Hack likewise has no required API integration in our implementation. The separate Nebius event is not another Cal Hacks sponsor category. Nessie is not implemented. No formal event submissions have been made.

Requirements and eligibility are determined by organizers. Existing guides record the official materials previously checked; verify current instructions before entering:

- [Official Cal Hacks prize board](https://hive.hackberkeley.org/prizes).
- [Fetch hackpack](https://www.fetch.ai/events/hackathons/calhacks-13-0/hackpack).
- [Hyphenate/Apify guide](./HYPHENATE_APIFY_SUBMISSION.md).
- [Microsoft/technical guide](./MICROSOFT_TECHNICAL_SUBMISSION.md).
- [Separate Nebius readiness](./NEBIUS_SUBMISSION_READINESS.md).

## 15. Proof and known limits

### Current verification baseline

- 176 backend tests passed, one optional skip.
- 74 frontend tests passed.
- Nine isolated x402 regression tests passed, plus the real payment/receipt verification.
- SpacetimeDB module check and production build passed.
- Real two-browser collaboration checks passed.
- Live Nebius policy, credit and procurement workflows verified.
- Registered Fetch mailbox and ASI:One UI workflow/follow-up verified.
- Actual Apify observations and automatic loading verified.
- CRS is fixture-tested and incomplete live.

### Important evidence locations

These are ignored local artifacts, not automatically available in a fresh clone:

| Artifact | Proof |
| --- | --- |
| `artifacts/hyphenate-apify-2026-10-25T03-52-13-456Z/` | Readable live credit/human-gate/settlement/public-input/policy video and evidence |
| `artifacts/fetch-mailbox-verification.json` | Actual signed ACP transport and experiment |
| `artifacts/fetch-asi-one/evidence.json` | Actual UI response/follow-up witness plus backend report |
| `artifacts/control-room/evidence.json` | Shared room, approval, execution, replay and authorization |
| `artifacts/x402-live-verification.json` | Real payment, forecast binding and independently verified receipt |
| `artifacts/x402-live-agent.json` | Optional paid tool enabled; model did not buy |
| `artifacts/microsoft-technical-evaluation/` | Thirty-branch scenario evaluation, including unfavorable results |

### Claims to keep precise

- The economy is synthetic, with selected observed public inputs.
- Real API usage does not make policy behavior calibrated or economically optimal.
- Five public-reference seeds produced zero jobs/eight defaults across all three strategies at the evaluated final day; do not hide that behind a favorable seeded demo.
- Model rationales can exceed numerical evidence; use recorded metrics and deltas to support claims.
- Human approval and different browser identities are useful prototype controls, not production authentication.
- Financial analysis does not automatically apply support; approval does not automatically settle.
- A successful x402 testnet purchase is not a mainnet/customer-payment claim.
- API adapters and unit fixtures do not establish live sponsor usage.
- Role counts, entity counts, external registered agents and animation counts are different quantities.

## 16. A precise way to describe the project

> Economy God Mode uses task-specific financial agents powered by NVIDIA Nemotron through Nebius. A central-bank analyst compares rescue strategies, business and bank roles negotiate payroll credit, and a buyer negotiates with two suppliers. Their tools operate on captured synthetic financial state, while deterministic policies and an audited ledger control execution. A registered Fetch agent exposes the stress-test workflow in ASI:One. Apify supplies selected observed price and wage inputs, SpacetimeDB coordinates a shared review/control room, and an optional x402 tool provides paid snapshot-specific research. We have verified the live model workflows, real public collection, ASI:One conversation, realtime collaboration and a real Base Sepolia test payment. CRS controls exist but still need live sponsor configuration.

For operational restart instructions, private configuration locations, repository history and continuation steps, read [the detailed continuation brief](./LLM_CONTINUATION_BRIEF.md) and [the latest session handoff](./SESSION_HANDOFF.md).
