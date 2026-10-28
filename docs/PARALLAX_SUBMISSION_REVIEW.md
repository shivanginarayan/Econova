# Parallax — individual track submission review

Prepared for team review. Devpost completion was confirmed by the team. All entries below await approval before they are sent or confirmed.

## Submission routes checked

Fetch requires Devpost plus registration through its ASI:One submission agent. Its process collects project and lead details, creates a Team ID, and requires teammates to join before the entry reaches Submitted status.

Coinbase requests a project summary, working example, architecture, and builder feedback. Its supplied brief does not specify an additional submission URL or recipient. Confirm the delivery route with the Coinbase representative before sending the prepared material.

The inspected material for Apify, CRS, Hyphenate, Spacetime, and Microsoft does not identify an additional registration form. Their project descriptions are prepared below for any required supplementary fields or sponsor-requested material. MLH's Gen AI submission route needs organizer confirmation if the category is absent from the team’s selector.

## Shared links

- Project: Parallax
- Repository: https://github.com/shivanginarayan/CalHacks
- Integrated code and instructions: https://github.com/shivanginarayan/CalHacks/tree/parallax-rename-v2
- Published Actor: https://apify.com/shivanginarayan/economy-public-sf
- Registered agent: https://asi1.ai/ai/agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm
- Payment receipt: https://sepolia.basescan.org/tx/0xf003b24fbbd32c3171161e8026615a8efa851591174db961ee1025c431906e86

### Details needed before completing the Fetch fields

- Final Devpost project URL
- Final video URL
- Team lead’s name and email
- Team size
- Teammate names and emails for their join steps
- Table number, if the team wants to provide it

## 1. Fetch.ai — proposed entry

### Project name

Parallax

### Problem and solution

Parallax is a simulated economy where financial agents investigate bank shocks, negotiate credit, and compare rescue policies. We are building for the risk-analyst and credit-officer workflows at regional and community banks. The problem we explore is how to compare financial responses while keeping the evidence, assumptions, and approval decisions easy to follow.

Our Fetch.ai agent lets a user request a financial stress test directly in ASI:One. A request such as “stress-test bank 1 with a 40% loss and compare rescue plans” creates a synthetic experiment, introduces the selected bank investment loss, and compares three calculated futures. A follow-up such as “why did you pick that?” retrieves the saved explanation and tool evidence for that experiment.

The gateway uses uAgents, Agentverse, and the Agent Chat Protocol. It connects the conversation to our Python financial backend and live NVIDIA Nemotron inference through Nebius. The simulation calculates financial outcomes, and the agent uses those results to explain its recommendation. Financial execution has a separate confirmation step.

The messaging path and complete stress-test conversation were verified through Agentverse and the ASI:One interface. Each result includes recorded evidence, while saved-state checks keep a proposal tied to the experiment it analyzed.

### Agent details

Registered name: economy-god-mode, the preserved gateway identity for Parallax.

Address: `agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm`

Public profile: https://asi1.ai/ai/agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm

Implementation: one externally registered gateway and ten local typed economic services. The gateway handles public conversations; the local services read validated financial state and support the economic workflows.

### Code and setup

https://github.com/shivanginarayan/CalHacks/tree/parallax-rename-v2

The branch README contains installation instructions, required service configuration, the agent address, and example requests. The local API, gateway, private account configuration, and live inference access support the conversational workflow.

## 2. Coinbase — proposed Payment Agents entry

### Project summary

Parallax helps financial analysts investigate a simulated economy and compare possible responses to a bank shock. Its optional paid-research workflow uses Coinbase’s x402 protocol to purchase analysis tied to a specific saved simulation state.

Our financial agents run in a Python backend using NVIDIA Nemotron through Nebius. A separate FastAPI research service issues an HTTP 402 payment request for 0.01 test USDC on Base Sepolia. The buyer checks the requested network, token, recipient, and amount, completes the x402 payment flow, and verifies the blockchain receipt before accepting the returned analysis.

### Working example

An actual purchase through the x402 Python SDK settled 0.01 test USDC on Base Sepolia. An independent blockchain check confirmed the successful receipt and matching USDC transfer. The response contained a simple synthetic employment-trend projection bound to the requested world and its saved-state fingerprint.

Receipt: https://sepolia.basescan.org/tx/0xf003b24fbbd32c3171161e8026615a8efa851591174db961ee1025c431906e86

Code and setup: https://github.com/shivanginarayan/CalHacks/tree/parallax-rename-v2

Technical guide: https://github.com/shivanginarayan/CalHacks/blob/parallax-rename-v2/docs/X402_SUBMISSION.md

### Architecture and controls

The workflow connects a financial-analysis job, an x402 buyer, a paid research endpoint, a settlement facilitator, and the Base Sepolia network. The research request includes the simulated world and the fingerprint of its saved state. The merchant returns a payment requirement, and the buyer accepts only the configured payment terms.

The spending limit is 0.01 test USDC. A recorded payment attempt protects against repeated spending after an uncertain response. Receipt checks establish what settled, and the response check establishes which simulation state the analysis describes. The test wallet and the simulation’s accounting ledger are separate.

The verified transaction was an explicit SDK purchase. The live financial-agent workflow also exposes the research tool through per-run authorization. In a separate live run, the model completed its analysis using inspection and comparison tools. The research output is a bounded synthetic trend calculation based on simulation history. Both payment identities are project-controlled test accounts.

### Builder feedback — proposed wording awaiting team review

The main integration work was making payment and delivery verifiable as separate steps. A successful request needed to establish both that the expected USDC transfer settled and that the returned analysis matched the requested financial state. We added an independent receipt check, a saved-state check, and a durable payment-attempt record.

A capability we would find useful is a single documented recovery flow that reports payment and delivery status together after a timeout. That would make it easier to determine whether to retrieve an existing result or begin a new request safely.

## 3. Apify — proposed project description

Parallax uses a custom Apify Actor to collect public price and wage references for new economic simulations. The Actor reads posted drink prices from Cafe Seventy8 and the official San Francisco minimum-wage page. Each record includes a numeric value, unit, source URL, interpretation, and collection time.

The application automatically loads saved public inputs and refreshes missing or stale inputs through bounded Actor runs. Each new world freezes its chosen sample and provenance, making experiments reproducible when public pages change later. The collected values initialize business prices and wage references in the synthetic economy.

The Actor is published with documentation and input and output schemas. A verified run of its published build returned 29 valid price observations. It uses fixed public sources and limited permissions, checks collection rules, and reports source failures explicitly.

Public Actor: https://apify.com/shivanginarayan/economy-public-sf

Actor source: https://github.com/shivanginarayan/CalHacks/tree/parallax-rename-v2/apify_actor

The data represents one venue’s posted menu options and a statutory wage floor. Financial identities, opening balances, employment relationships, and economic behavior come from the simulation.

## 4. CRS — proposed project description

Parallax uses CRS credit evidence inside an AI-assisted business-loan review. A business agent identifies a simulated payroll gap, and the bank agent retrieves a sponsor-provided synthetic owner’s Experian report from the CRS sandbox before assessing the loan.

The verified live workflow returned a score of 770 for sponsor persona P19. The application stores a redacted evidence record, and the interface displays the score and review status. Raw identity details and API credentials stay in private backend configuration.

The bank combines the credit evidence with the simulated borrower’s needs and the bank’s lending limits. Uncertain identity or fraud evidence requires human review. The verified request stopped at that review gate, preserving the financial transaction history. Approval and loan settlement are separate actions.

Implementation and verification: https://github.com/shivanginarayan/CalHacks/blob/parallax-rename-v2/docs/TRACK_IMPLEMENTATION.md

## 5. Hyphenate — proposed project description

Parallax explores the work of a bank-risk analyst and a credit officer through bounded financial agents. The agents inspect a saved economy, investigate a bank investment loss, negotiate payroll credit, and compare rescue policies using recorded financial facts.

The policy workflow calculates three futures from a shared starting state and saves the evidence behind its recommendation. The credit workflow brings together a business request, bank assessment, owner credit evidence, and an explicit human-review gate. Separate confirmation controls financial execution.

Our core design makes responsibility visible: tool traces record the work, saved-state checks tie decisions to their evidence, and the accounting ledger validates each financial action. Real public price and wage observations have source provenance, while households, portfolios, and economic outcomes belong to the synthetic simulation.

Roles addressed: risk analyst and credit officer.

## 6. Spacetime — proposed project description

Parallax uses SpacetimeDB to coordinate shared decisions in a persistent simulated economy. Connected participants receive room presence, proposed bank shocks, review decisions, and execution receipts through real-time subscriptions.

One browser identity proposes a shock and another identity reviews it. The financial backend checks that the approved proposal still matches the saved world before executing it. A proposal can execute once, and its receipt remains available after a reload.

Two independent browser sessions verified shared updates, second-identity review, approval without financial execution, rejection of outdated proposals, and protection against repeated execution. SpacetimeDB stores the shared coordination state, and SQLite stores the financial accounting state. The prototype uses anonymous browser identities.

Technical guide: https://github.com/shivanginarayan/CalHacks/blob/parallax-rename-v2/docs/SPACETIME_SUBMISSION.md

## 7. Microsoft — proposed project description

Parallax is an AI-assisted financial stress-testing prototype for regional-bank risk analysts and credit officers. It connects a simulated bank shock to a clear workflow for inspecting financial relationships, comparing responses, reviewing explanations, and approving actions.

The user can compare employment, defaults, bank stress, and support costs across three futures from the same starting state. A downloadable report preserves the calculated outcomes and source provenance. Live financial agents use tools to inspect the evidence and propose a response, with separate controls for approval and settlement.

The implementation uses integer-cent accounting, balanced ledger entries, saved-state validation, and protection against duplicate financial execution. The next stage is customer research with risk analysts, validated institution data, authenticated roles, and evaluation of the workflow in a real review process. The current usefulness measurements describe simulated outcomes.

## 8. General Gen AI — proposed project description

Parallax uses NVIDIA Nemotron-3-Nano-30B-A3B through the Nebius API to power financial agents. They investigate simulated bank shocks, negotiate credit and supplier terms, and explain rescue-policy comparisons.

The model obtains evidence through tools and proposes actions. A deterministic financial simulation calculates the outcomes, and an audited ledger validates execution. Saved traces connect recommendations to the evidence used, while human-review gates handle uncertainty and configured approval limits.

## Source instructions

Fetch submission instructions: https://www.fetch.ai/events/hackathons/calhacks-13-0/hackpack

Fetch team-entry guide: https://docs.google.com/document/d/1UDW-X1C24hxZviFOQzjTeh0pXRNAoflMb8lhJqZP9Z0/edit

Coinbase submission brief: https://drive.google.com/file/d/12TnPLguduV3gh1zY_TJ176XmVDz2RGW9/view

Event track requirements: https://hive.hackberkeley.org/prizes
