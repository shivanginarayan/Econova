> Historical Parallax / Cal Hacks material. The current product is Econova. For current readiness and limitations, see [the priority audit](./PRIORITY_READINESS_AUDIT.md). External registrations may still use their original names.

# Parallax, explained from beginning to end

This guide explains the integrated Parallax project in plain language. It follows the implementation and verified work on `parallax-rename-v2`. Examples with round numbers explain the mechanism; they are not promised results for a particular saved world.

## 1. What Parallax is

Parallax is a simulated economy where financial agents investigate bank shocks, negotiate credit, and compare rescue policies.

Imagine a small economy on a tabletop. People work for businesses. Businesses sell goods and pay wages. Banks hold deposits, lend money, own investments, and owe money to one another. A government and central bank can provide different kinds of support.

Now imagine one bank loses money on an investment. The question becomes: who depends on that bank, what happens next, and which response helps under the assumptions of this experiment?

Parallax gives that question a visible world, a set of financial rules, and AI workers that can investigate it. It is designed around the work of a bank-risk analyst and a credit officer. That intended customer is a hypothesis; customer interviews and production use remain future work.

The core experience is:

**Create a world → introduce a financial shock → inspect its consequences → compare responses → review the evidence → confirm an action.**

## 2. The three parts you should keep separate

The **simulation** calculates what happens. It contains the rules for money, lending, wages, production, purchases, defaults, and support. Think of it as the rulebook and calculator.

The **AI workflows** investigate and propose. They inspect facts, call tools, negotiate bounded offers, and explain recommendations. Think of them as workers using the calculator, with specific permissions.

The **interface** helps a person see and control the process. The globe, city, network, charts, reports, and review screens present information from the backend. Think of it as the workspace.

Pressing Play advances the simulation. It does not mean every person and business starts making a separate AI request every day. Requesting a policy, credit, or procurement analysis starts a specific agent workflow.

## 3. What exists inside one world

A default world has 40 households, 8 businesses, 5 commercial banks, a government, and a central bank: 55 economic entities.

A **household** represents a simulated worker and consumer. It has a bank account, a spending budget, and an employment relationship or unemployment status.

A **business** has money, employees, debt, raw materials, and finished goods. It attempts to pay its obligations and payroll, produces goods, and receives payments from customers.

A **commercial bank** holds reserves, customer deposits, loans, investment assets, and interbank obligations. Its financial condition determines whether it can continue lending.

The **government** records fiscal support and public debt created by the modeled support operation. The **central bank** records reserve creation and public loans.

These are generated entities. Bank 1 is a simulated institution, not an actual named bank from the FDIC directory. The 40 households are not 40 identifiable San Francisco residents.

## 4. The starting scenarios

**Standard** starts with relatively well-capitalized banks. A loss that causes serious trouble in another scenario may be absorbed here.

**Credit crunch** starts with a more fragile financial network. It is useful for examining how investment losses and lending constraints can spread through connected institutions.

**Supply crunch** gives the first business a material shortage. It lets the procurement workflow address a concrete operational problem: restoring inputs for production.

A scenario is a starting condition, not a predetermined ending. Public input choices, the seed, the size of the shock, and the observation period all matter. A successful rescue in one world does not establish that it works in all worlds.

## 5. Real observations, assumptions, and simulated state

These are three different kinds of information.

**Real observations** are values retrieved from an external source. Examples are a cafe’s posted price, the statutory minimum wage, a dated Treasury debt observation, a Census population estimate, or an FDIC institution record.

**Assumptions** are choices we make about an experiment. Examples are a 40% loss on risky bank investments, an eight-hour conversion of hourly wage to a daily reference, or the model’s layoff limits.

**Simulated state** is what exists inside the model: deposits, employment links, debt, bank portfolios, inventory, and calculated outcomes.

Using some real observations does not turn every generated balance and relationship into real city data. In Parallax, public observations have a named scope and source so users can see exactly what they support.

## 6. How money is recorded

All financial amounts are calculated in integer cents. A balance of 10,000 cents is displayed as $100. This avoids small rounding errors from repeatedly doing accounting with decimal dollar values.

The ledger is the financial record book. Each operation creates matching accounting entries. The system checks that the accounting balances and that obligations agree across counterparties.

For example, when a household has a $100 deposit, it has an asset: the bank owes it $100. The bank records a matching deposit liability. The household’s balance and the bank’s obligation describe the same relationship from opposite sides.

Opening balances are explicit model endowments recorded when the world is created. They are not imported personal balances or money collected from real users.

An audit checks the recorded financial relationships. A balanced audit means the accounting rules hold; it does not establish that the model perfectly represents a real economy.

Source: [ledger](../backend/ledger.py), [economy](../backend/engine.py), and [public interventions](../backend/interventions.py).

## 7. Payments, reserves, loans, and equity

A **deposit** is money a customer can use in its bank account. **Reserves** are the settlement assets banks use when money moves between banks in this simulation.

If a household pays a business at the same bank, customer deposits change inside that bank. If their accounts are at different banks, the corresponding reserve transfer also has to work. A payment can fail even when the payer appears to have a deposit if the relevant bank cannot meet the settlement requirements.

A **loan** creates matching claims. If a bank lends a business $100, the business gains a $100 deposit and owes $100. The bank gains a $100 loan asset and a $100 deposit liability. The business has cash to use, together with a repayment obligation.

**Equity** is the difference between assets and liabilities. If a bank has $1,000 of assets and owes $900, its equity is $100. If its investments lose $80, equity falls to $20 while those existing obligations remain.

**Liquidity** means being able to meet payments when due. **Solvency** means having enough asset value to cover liabilities. A bank can have a liquidity problem, a solvency problem, or both. This distinction explains why providing a loan is different from replacing lost equity.

## 8. What the bank shock actually changes

The main shock removes a chosen percentage of a selected simulated bank’s risky investment assets.

For an explanatory example, if those investments are worth $1,000 and the selected loss is 40%, the modeled investment loss is $400. That is not a 40% reduction in every customer’s deposit. The investment value and the bank’s equity are affected through accounting entries.

The bank’s health is then recalculated. The current model treats nonpositive equity as insolvency. It treats capital below 8% of assets, reserves below 10% of customer deposits, or an interbank payment default as lending stress. These are prototype rules, not a complete statement of banking regulation.

Once a bank becomes constrained, its borrowers may struggle to obtain credit or refinance. Interbank claims create another route for the effects to spread. Business financing problems can become payroll problems, then unemployment and reduced spending.

The size and timing of the consequences are calculated from the current world. They are not selected by the AI to produce a dramatic result.

Source: [crisis rules](../backend/crisis.py).

## 9. What one simulated day does

One tick is one simulated day. The engine advances its financial and operational rules in a defined order.

It settles due interbank obligations, refreshes bank health, and handles due supplier contracts. Businesses prepare for their obligations, including loan repayment or refinancing and payroll funding. Households with employers then receive attempted wage payments.

Repeated incomplete payroll can cause a business to default. Gradual layoffs are evaluated under their own rules. Active businesses turn available materials into finished goods, and households attempt purchases subject to their budgets, available money, and actual seller inventory.

The system records events, refreshes the relevant state, and captures metrics. A quiet day can have few visible changes because the rules did not generate a major event. The passage of time is not itself an AI-generated story.

The controlled random streams make repeated experiments reproducible. The same seed, state, and rules produce the same modeled choices. The seed is a reproducibility setting, not evidence that a simulated trajectory is a forecast.

## 10. Employment and the gradual-layoff rules

Employment measures workers in this simulated world. It is different from the real current San Francisco employment rate.

The current branch starts with an assumed unemployment share of 4%, converted to a whole number of households. With 40 households, rounding can produce two unemployed households, which is 5% of the small modeled population. The displayed rate is calculated from the actual household count.

Stressed businesses can lay off workers gradually. The model uses a 35% chance for a stressed business to shed a worker on a day, a limit of one worker per business per day, and an economy-wide limit of 5% of households per day. These are seeded simulation assumptions.

The gradual-layoff mechanism pauses at its 30% unemployment ceiling. That is not a ceiling on all unemployment: business defaults can still remove jobs. The stress memory covers recent problems such as rejected credit, missed payroll, supplier defaults, and insufficient materials.

Source: [labor model](../backend/labor.py).

## 11. Production and supplier contracts

A business needs raw materials and workers to produce goods. In the current production rule, it can use up to one material unit per employee per day and produces ten finished goods per material unit used. These conversion rates are assumptions of the model.

A household can buy only goods that are available. If it wants five items and the shop has two, inventory limits what can be sold. A material shortage can therefore reduce sales even when customers have money.

The procurement workflow addresses that shortage. Two supplier role instances provide offers. The buyer can compare full costs, request one counteroffer round, and select an eligible offer. Supplier policy limits what a supplier can accept.

An offer includes the full invoice, upfront payment, and deferred-payment terms. A small upfront price does not make a large total obligation affordable. Confirming settlement creates the contract and its financial/inventory effects; due bills can later settle or default under the simulation rules.

Source: [production](../backend/production.py), [procurement agents](../backend/procurement.py), and [supplier workflow](./SUPPLIER_PAYMENTS.md).

## 12. Fork Reality: comparing three futures fairly

A fork is a separate copy of the saved economy. Parallax creates three branches: no intervention, emergency lending to a bank, and direct support to households.

All branches begin with the same financial state, source observations, and controlled randomness. Each support branch uses the selected budget. The ordinary interface comparison uses a $10,000 support budget and a twelve-day horizon.

The source world stays unchanged by the comparison. This is important: looking at a possible future should not silently turn it into the real current experiment.

The branches calculate employment, defaults, stressed banks, household cash, production, and public support. The ranking first favors higher final employment, then fewer business defaults, fewer insolvent banks, fewer stressed banks, and less gross support. That ranking is rule-based.

An AI recommendation is a separate result with a recorded explanation. The model and the rule-based ranking can differ. Neither can establish the best response for every possible real-world crisis.

Source: [fork calculations](../backend/forks.py).

## 13. What the two support policies mean

**Emergency bank lending** adds reserves to the selected bank and creates matching debt to the central bank. It can help a liquidity shortage, but it also creates a liability. It does not replace lost equity, so it cannot automatically solve insolvency.

**Household support** distributes money across households and records the corresponding public financing and bank entries. The implementation divides integer cents so the allocations exactly match the authorized total.

The displayed public intervention cost is **gross support disbursed**. It is not a claim that the government permanently lost that entire amount. Outstanding public loans and fiscal transfers are recorded separately.

An intervention can fail to improve final employment or defaults. That is a valid result to explain, rather than something the system should hide. Each result belongs to its seed, assumptions, inputs, engine version, and time horizon.

## 14. What an AI tool call means

Instead of allowing the model to write a new financial result directly, we give it a small list of named functions. These are its tools.

For example, a bank agent can request credit evidence or ask the financial rules to assess a proposed loan amount. It sends structured arguments. The backend checks the argument format and permissions, runs the calculation, and returns a result.

The model then uses that result to choose its next allowed step or explain its proposal. This is a loop of observation, tool request, validated result, and response.

A **tool trace** is the saved public record of those steps. It contains tool names, arguments, results, and concise explanations. It is not a transcript of hidden model reasoning.

The AI cannot gain new financial permissions by writing convincing prose. A proposal still has to satisfy the executable financial checks and any human-review requirement.

## 15. The five financial AI roles

**The policy analyst** investigates the economy, tests rescue choices, and recommends a supported response. It can inspect, compare, and recommend. It does not automatically apply its recommendation to the source world.

**The business borrower** examines a payroll funding gap and asks for useful credit within the authorized amount. After the bank responds, it can accept or reject the actual offer.

**The bank underwriter** checks the request against financial limits and, when requested, retrieves CRS credit evidence. It can approve an eligible amount, offer a smaller eligible amount, or decline. Review requirements still apply.

**The procurement buyer** compares supplier offers, considers future payment obligations, negotiates within the allowed process, and chooses an eligible offer or declines.

**The supplier role** quotes stock and payment terms and responds to a counteroffer within supplier policy. A procurement run uses two competing supplier instances.

These are five role types and six typical task participants across one policy run, one credit run, and one procurement run. They share the configured model but have different jobs, tools, and permissions. They are not six permanent external agent services.

## 16. What Nebius and NVIDIA each provide

**NVIDIA Nemotron** is the language model used by the live financial roles. The verified configured model is `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.

**Nebius Token Factory** hosts access to that model through an API. Our backend sends the role’s instructions, relevant observations, conversation steps, and available tool definitions. It receives the model’s response and tool requests.

The endpoint uses the chat-completions request format at `https://api.tokenfactory.nebius.com/v1/chat/completions`. That format does not mean the financial model is an OpenAI model; the configured provider is Nebius and the model is Nemotron.

The adapter keeps provider credentials out of prompts and public traces. Live inference needs account access and can consume inference credits. Explicit demo mode uses scripted controllers with the same financial tools instead of calling a live model.

Source: [model provider adapter](../backend/provider.py).

## 17. The complete credit review, including CRS

First, the borrower inspects its simulated financial situation. A payroll gap means it lacks enough available funding for its wage bill. It requests an amount within the caller’s limit.

The bank inspects the request. When the user selects a CRS owner profile, the workflow requires a credit-report pull before assessment. It uses a sponsor-provided synthetic identity and the CRS sandbox, rather than a real applicant.

The adapter authenticates through `/users/login`, then calls `/experian/credit-report/standard/{config}`. The verified configuration is `exp-prequal-vantage4`. CRS provides access to the Experian report in CRS Standard Format; it is one connected evidence path, not two separate model providers.

The real sandbox verification returned **770** for the sponsor’s synthetic small-business-owner profile P19. The score is read from `scores.0.scoreValue`. Only normalized evidence is saved for the workflow; credentials and the raw identity request remain private.

CRS can return a product error inside an HTTP 200 response. The adapter therefore checks the body as well as the HTTP status. A successful network request is not automatically a valid credit report.

The bank then checks eligible principal against simulated borrower and bank constraints. The current model caps borrower debt at $5,000, limits bank loans relative to equity, and applies capital/liquidity checks. These are prototype lending policies.

Unknown or missing evidence requires review. The current private risk mapping deliberately leaves identity/fraud clearance at review; a score of 770 alone does not prove that those checks passed. A score below the illustrative 620 review threshold also requires review. Explicitly blocked evidence prevents the credit proposal from proceeding through a human override.

The verified live credit workflow showed the score and stopped at human review. No loan was issued during that check. Separate optional TruValidate screening has code and its own configuration, but has not been verified live as part of this completion.

Evidence can be reused within a fifteen-minute cache window for the same bound payload and rules. Fresh financial-state and approval checks remain separate from that external-data cache.

Source: [CRS adapter and controls](../backend/crs_credit.py), [credit agents](../backend/credit_agents.py), and [configuration details](./TRACK_IMPLEMENTATION.md).

## 18. Why approval and settlement are separate

**Proposal** means an agent has suggested something. **Approval** means a reviewer has recorded a decision. **Settlement** means the financial operation has actually been posted.

For example, approving a $100 loan does not itself create the loan. A separate settlement confirmation executes the recorded, approved terms, provided they still pass current checks.

A **snapshot** is a saved picture of the world at a moment in time. Its **hash** is a digital fingerprint. If the relevant state changes after review, an old approval can be rejected because its evidence is stale.

An **idempotent** request means repeating the same operation identifier returns its existing result instead of creating a second payment or loan. This is useful after a timeout, when a browser cannot tell whether the first request succeeded.

These protections make the prototype more accountable. The current development API still needs production authentication and stronger real-person role verification before use with real financial decisions.

## 19. Apify and the two public websites

An **Apify Actor** is a program packaged to run on Apify’s platform. Our Actor is a small Python collector, not a language model.

It accepts one of two categories. `prices` reads Cafe Seventy8’s public menu at `https://www.cafeseventy8.com/`. `wages` reads the official page at `https://www.sf.gov/information/understanding-minimum-wage-ordinance`.

The Actor checks source robots rules, retrieves the known page, parses expected values, and writes records into its default Apify dataset. The record includes the item, numeric value, unit, meaning, source URL, and collection timestamp. Some records also include a menu variant or effective date.

The app uses the Apify API to run the collector and retrieve its results. Opening the app serves saved valid observations and can start a bounded refresh when data is missing or more than six hours old. Request deduplication and collection limits prevent every browser reload from becoming an uncontrolled crawl.

The UI’s new-world flow waits for the selected public sample. An explicitly seeded option is available when creating a synthetic-only experiment. An existing world keeps its frozen observations even after new data is collected.

The Actor is published at https://apify.com/shivanginarayan/economy-public-sf. The published build was verified with a successful run returning 29 price observations. That count describes the run, not a permanent guarantee about the source page.

The menu is one venue’s posted options, with sizes/taxes limited to what the source states. The wage is the legal minimum, not average pay. The hourly-to-daily conversion is our explicit eight-hour assumption. Apify supplies neither national debt nor household employment relationships.

The two Apify track stories use the same implementation: one concerns how collected data matters to Parallax; the other concerns the reusable Actor, its input/output contract, and public availability.

Source: [collector](../apify_actor/main.py), [automatic loading](../backend/apify_collection.py), and [collection guide](./APIFY.md).

## 20. Fetch.ai, Agentverse, and ASI:One

**Fetch.ai** provides the ecosystem we use for external agent access. **uAgents** is its Python framework for constructing agents and their message protocols. **Agentverse** supports registration, discovery, and message delivery. **ASI:One** is the conversational interface through which a person can reach the registered agent.

Our public gateway receives an ACP message, recognizes a supported command, calls the local Parallax backend, and sends the result back. ACP means **Agent Chat Protocol**, the shared message format that makes the interaction work.

For example, “stress-test bank 1 with a 40% loss and compare rescue plans” launches the supported experiment. “Why did you pick that?” retrieves the saved explanation and trace from the associated result.

The gateway uses bounded command parsing. It is not a new unrestricted financial-planning model. The actual live policy analysis still uses Nemotron through Nebius. Agentverse registration and the financial model provider serve different purposes.

We verified the signed messaging workflow and the user workflow inside ASI:One. One gateway is externally registered under the older name `economy-god-mode`, with address `agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm`. Preserving that identity avoids breaking its established registration when the project name changes.

A public agent profile is different from a public shared-chat link. A profile identifies the service. A shared chat publishes a conversation result. An ordinary private `/chat/` URL is different from a `/shared-chat/` URL.

You reported completing the Fetch submission. That is a user-reported submission status, separate from our technical verification of the product conversation.

Source: [gateway message handler](../scripts/run_fetch_agent.py), [supported commands](../backend/fetch_chat.py), and [Fetch guide](./FETCH_AGENT.md).

## 21. The ten local economic services

The project also contains ten typed economic service roles. Typed means they accept a defined message shape and return a defined result. They are deterministic adapters around saved state and existing calculations, distinct from the live AI role types above.

1. **Central-bank service:** computes a hypothetical bank-shock comparison and returns the calculated branch outcomes.
2. **Commercial-bank service:** evaluates credit against saved borrower and bank facts.
3. **Corporate-borrower service:** reports the actual payroll funding situation; a caller cannot create an authorized settlement by claiming it accepted an offer.
4. **Procurement-buyer service:** provides validated procurement information from the existing workflow and world.
5. **Supplier-quotation service:** handles supported quote and counteroffer checks against supplier policy.
6. **Treasury/macro service:** retrieves a dated debt baseline or calculates a bounded hypothetical bond-loss estimate.
7. **Apify wage/menu service:** reads saved validated public observations for wage and menu-price questions.
8. **Clearinghouse service:** reports actual interbank exposures; it does not execute a made-up netting settlement from a caller message.
9. **Household-welfare service:** calculates welfare/distribution information from the saved world rather than assuming a demand multiplier.
10. **Auditor service:** reports accounting invariants and recorded screening information; an audit report is not a certification of real-world compliance.

The uAgents SDK can construct these identities and register their local handlers. The completed verification covers identities, typed callbacks, calculations, and errors. It does not establish ten public deployments or ten independent AI models.

Some unsupported commands deliberately fail. A service must obtain the required state and inputs before returning a result. This prevents plausible-looking sample numbers from being presented as computed financial facts.

Source: [role definitions](../backend/fetch_agents/agents.py), [service calculations](../backend/fetch_agents/service.py), and [service guide](./FETCH_ECOSYSTEM.md).

## 22. Census and FDIC: contextual public information

The **US Census Bureau** path retrieves the Vintage 2024 county population estimate for San Francisco from a public CSV. It records the geography, reference period, source, and retrieval time. It is a dated population estimate, not today’s live headcount.

The **FDIC BankFind API** retrieves active FDIC-insured institutions headquartered in San Francisco. It provides names and certificate identifiers. A headquarters directory is different from a list of all bank branches in the city.

These values are saved as contextual research. They do not turn our five generated banks into those real institutions or scale the forty generated households into the full population. They also do not initialize actual bank portfolios.

There are two ways the implementation can obtain these observations: direct bounded source functions, and an optional ASI model-directed research workflow using the same functions.

The direct sources were verified previously. The separate ASI inference workflow calls `https://api.asi1.ai/v1/chat/completions` and requires its own `ASI1_API_KEY`. Successful use of the registered Fetch gateway does not prove that this optional inference path is configured or live verified.

An interface status for optional ASI research can therefore differ from the registration status of the working public Fetch agent. They check different connections.

Source: [public research functions](../backend/research.py).

## 23. US Treasury: dated debt and a hypothetical transmission example

The Treasury Fiscal Data API provides the Debt to the Penny observation. The application retrieves the latest available dated record, which can be older than the current clock time.

The optional story lets a user choose a hypothetical debt increase and separate bond-market assumptions, including a yield change, modified duration, and portfolio exposure. It previews the corresponding synthetic bank investment loss before a separate apply step.

A simplified duration estimate says that a bond with duration five can lose approximately 10% when yields rise by two percentage points: five multiplied by 0.02. If only half of a portfolio has that exposure, the estimated effect on the full portfolio is approximately 5%. Those numbers explain a formula, not a forecast.

The hypothetical debt increase does not automatically determine the chosen yield increase. The external national debt observation is different from the government debt created inside our small simulated economy. There is no automatic model of war, oil prices, inflation, trade, and national employment behind a short event description.

Source: [Treasury story calculation](../backend/shock_stories.py).

## 24. SpacetimeDB: shared coordination between people

SQLite stores the financial truth. SpacetimeDB stores the shared room’s participants, proposals, review status, and execution receipts. This is why the project uses two databases without giving both authority to invent financial balances.

A browser joins the room and subscribes to its shared data. Subscriptions deliver changes as they happen. A server-side **reducer** is a function that validates and updates that shared state.

One participant proposes a bank shock. Another browser identity reviews it. Approval changes the proposal state, while execution is a separate step. The Python backend checks the shared approval and saved-world fingerprint, applies the financial operation through the ledger, and records the execution result.

If the world changes after the proposal, the snapshot check can reject it. If the execution response is lost, replaying the same proposal must not apply a second loss. Its receipt survives a reload.

Two independent browser sessions verified these behaviors. The prototype uses anonymous browser identities, which are separate technical identities rather than proof of separate real people. Strong organizational identity and authorization would be part of a production deployment.

Source: [financial bridge](../backend/spacetime.py), [shared module](../spacetimedb/src/index.ts), and [control-room UI](../apps/web/src/ui/ControlRoom.tsx).

## 25. Coinbase x402, Base Sepolia, USDC, Circle, and the explorer

**x402** is the protocol for paying for an HTTP resource. A paid server can respond with HTTP 402 and payment requirements. A compatible buyer can make the required payment and receive the resource.

Our **merchant** is a separate FastAPI research service. It charges 0.01 test USDC for analysis tied to a particular simulation snapshot. Its returned projection is based on synthetic employment history, not a live market-data subscription or a national forecast.

The **x402 Python SDK** implements the buyer/server payment flow. The public **facilitator** at `https://x402.org/facilitator` supports verification and settlement. Our buyer separately checks the expected network, token, amount, recipient, and returned snapshot.

**Base Sepolia** is the test blockchain used for the payment. **Test USDC** is the token transferred there. This is different from dollar balances recorded inside our simulated bank ledger.

The **Circle faucet** supplied test USDC to the development buyer wallet. It was a setup tool, not the source of economic observations or a continuous dependency for every experiment.

The **Base Sepolia RPC** endpoint lets software query blockchain state. We used it to independently verify the transaction receipt and matching USDC transfer. **BaseScan** provides the public human-readable receipt page. The explorer is evidence of the payment, not the service that runs the financial simulation.

The verified SDK purchase settled 0.01 test USDC. Both wallet identities were project-controlled test identities. The record is available at https://sepolia.basescan.org/tx/0xf003b24fbbd32c3171161e8026615a8efa851591174db961ee1025c431906e86.

The live policy workflow can expose the paid tool when explicitly authorized for that run. In the separately verified live model run, the model used inspection and comparison and did not choose to purchase. The successful payment therefore proves the actual SDK payment path, not an autonomous model-selected purchase.

A durable attempt record prevents blind repayment after an uncertain result. A completed per-run result can be reused; an ambiguous attempt is held for inspection. Deleting the record and retrying could spend again.

Source: [buyer](../x402_service/buyer.py), [merchant](../x402_service/server.py), [per-run spending guard](../backend/paid_research.py), and [payment evidence](./X402_SUBMISSION.md).

## 26. The application services and libraries

**Python** is the backend language. **FastAPI** exposes our HTTP endpoints. **Pydantic** checks the shape and bounds of incoming requests. **Uvicorn** runs the local web server. **HTTPX** makes requests to external APIs. **SQLite** persists worlds, reports, requests, events, and financial records.

**React** builds the interface. **TypeScript** checks frontend code and data types. **Zustand** holds the browser’s application state. **Vite** serves the app during development and produces its frontend build. **Node.js/npm** run the frontend tooling and install its packages.

**Three.js** and **three-globe** support the globe. The city also has custom canvas drawing, generated layout geometry, building hit-testing, and decorative movers. **Lucide** provides interface icons. Geographic assets and layout files are different from live financial inputs.

The browser normally reaches the Python API through Vite’s development proxy. The backend uses **server-sent events** and polling for saved-world and job updates. The Spacetime client has its own real-time subscription connection for shared room state. Those are distinct update paths.

The default local services use web port 5173, backend port 8000, SpacetimeDB port 3000, gateway port 8002, and optional paid-research port 8402. Ports describe the usual configuration, not a guarantee that every process is currently running.

**Pytest** tests Python behavior. **Vitest** tests frontend logic. **Playwright with Chrome** exercises real browser workflows. They help verify the system; they are not economic or AI providers.

**Git/GitHub** preserve and publish code. **Devpost** records the team’s project entry. **ASI:One’s event submission flow** records the separate Fetch entry. These submission services are separate from the product’s calculation engine.

**OpenAI Codex** assisted development, debugging, testing, integration, and documentation. It is a development tool used in building the project; the verified runtime financial model is Nemotron through Nebius. Team members can separately disclose the development tools they actually used.

## 27. Background jobs, memory, and the saved record

A live model request can take longer than an ordinary page click. Instead of making the interface wait silently, the backend creates a job and returns its ID. A worker runs the workflow while the interface polls its progress and reads the linked report.

The job queue limits concurrent work, records status, and handles cancellation of queued jobs. Worker ownership and heartbeat checks prevent an expired worker from publishing a result as though it still owned the job.

The useful memory here is saved application state: the source world, report, tool results, and conversation context needed for a follow-up. Parallax does not require a separate vector database or model training pipeline for these workflows.

The browser stores the active world ID so reopening the app can restore it. That explains why a landing session can show an earlier experiment. Creating a new world gives a fresh ID; reset preserves the earlier world’s history rather than rewriting it.

Private configuration supplies API credentials and service identities. Credentials are different from public agent addresses and source URLs. They should stay out of source control, public reports, and presentations.

Source: [job system](../backend/jobs.py), [persistence](../backend/store.py), and [frontend state](../apps/web/src/state/store.ts).

## 28. How the tracks connect to the same product

**Hyphenate** connects to the financial-agent work: risk analysis, credit decisions, bounded permissions, recorded evidence, human escalation, and separate execution. It is a challenge theme served by our implementation, rather than a provider API called by the backend.

**Fetch.ai** connects to registered agent access, ACP messaging, ASI:One requests, and retrieval of the resulting saved explanation.

**CRS** connects directly to the bank’s underwriting evidence. The retrieved sandbox report is an input to a credit workflow, not a disconnected credit-score display.

**Apify’s application-use track** connects to the price/wage input pipeline and its effect on new worlds. **Apify’s Actor track** connects to the collector as a public reusable program with defined inputs, outputs, and documentation.

**Spacetime** connects to people coordinating decisions in one persistent world, with live shared state and execution receipts.

**Coinbase’s Payment Agents path** connects to the x402 paid-analysis endpoint, bounded spending, receipt validation, and snapshot-bound delivery.

**Microsoft’s real-world and customer-impact themes** connect to the intended analyst workflow, useful report, approval design, and path toward validated customer use. There is no Azure integration required to explain this product fit, and we have not established actual customer savings.

**Technical complexity** connects to the interaction of reproducible forks, validated agents, an audited ledger, persistent jobs, shared coordination, and external services.

**General Gen AI** connects to actual model use in financial investigation and negotiation. **Nebius/NVIDIA** provide the verified model foundation. **Claude/Anthropic** is not currently part of the verified runtime implementation.

One feature can support several track explanations. That does not mean the same action has to be implemented again for every track, or that each track corresponds to a separate external API.

## 29. A complete story through the system

We open the app and it loads the saved Apify public references. We create a credit-crunch world using the selected sample. The backend generates its households, businesses, banks, balances, and employment relationships, then saves the world.

We apply a hypothetical loss to Bank 1’s risky investments. The ledger records the loss, bank health changes, and the interface refreshes the affected state. Advancing days allows credit, settlement, payroll, production, and consumption rules to generate further consequences.

We ask for a policy investigation. A background job captures the source snapshot. The Nemotron policy role inspects the state and uses bounded comparison tools. Three branches calculate possible outcomes. The result records what was tested and why the agent recommended its chosen action.

We can separately investigate a business that has a payroll gap. The borrower requests credit, the bank retrieves the selected CRS test-owner report, and the financial checks assess a proposed amount. Uncertain evidence stops the process for human review. Approval records a decision; settlement is another action.

If the problem is materials rather than money, procurement agents negotiate supplier offers. Confirming an eligible contract changes inventory and obligations, and later days determine whether production and sales improve.

A second participant can join the shared room. SpacetimeDB synchronizes a proposed shock and review. The accounting backend controls whether the approved proposal still matches the current source and can execute once.

The supported stress-test request is also available through the registered Fetch agent in ASI:One. Optional paid research has a separate x402 wallet and explicit authorization. A comparison report carries the saved evidence out of the application.

That is the overall product: multiple entry points and supporting services around one controlled simulated economy.

## 30. Questions and straightforward answers

**Does the AI decide what happens to employment?** The engine calculates employment from its rules. AI agents inspect and explain the results and propose supported actions.

**Are all the data live?** No. Public observations have their own dates and scopes. Bank balances, households, and economic relationships are generated simulation state.

**Does a 40% bank shock remove 40% of deposits?** No. The selected percentage applies to the bank’s risky investment assets.

**Why can a cash injection fail to rescue a bank?** A loan can improve available reserves while adding equal debt. It does not automatically repair lost equity.

**Why compare branches from the same snapshot?** Otherwise an apparent policy benefit could come from different starting conditions rather than the policy itself.

**Why is a 770 credit score still held for review?** Credit score and identity/fraud clearance are different evidence. Our current mapping leaves unknown risk at review.

**Is CRS receiving real customer applications?** The completed workflow uses sponsor-provided synthetic test identities in the sandbox.

**Is there one AI for each household?** No. Households follow simulation rules. Live agent workflows are requested for specific financial tasks.

**Did we deploy ten public Fetch agents?** One gateway is externally registered and verified. The ten typed local services are a separate implementation layer.

**Does SpacetimeDB hold the bank ledger?** The financial ledger is in SQLite. SpacetimeDB manages shared room coordination and receipts.

**Did an AI independently make our recorded USDC purchase?** The payment was verified through an explicit x402 SDK test. A separate live model run had the optional tool and chose other tools.

**Is the city a live geographic map of actual banks?** It is a stylized visual world. Backend-bound institutions reflect simulated state, and extra scenery profiles are illustrative.

**What needs work before real bank use?** Validated data and economic assumptions, customer research, proper authentication and authorization, stronger review identity, deployment operations, and systematic evaluation.

## 31. How to read the evidence

After the integrated branch merge, the active backend suite passed 217 tests with one optional module skipped. Frontend tests and the TypeScript/production build passed. The integrated Chrome check verified branding, sponsor controls, CRS profile availability, three futures, and comparison download.

Separate real-service checks established live Nemotron workflows, CRS sandbox evidence, a published Apify Actor run, Fetch messaging and ASI:One access, two-browser Spacetime coordination, and the x402 testnet payment. Historical success proves the checked interaction happened; it does not guarantee that an external service is online at every later moment.

Older reports can have different numerical outcomes because the source sample, scenario, or engine version changed. In particular, the integrated branch added baseline unemployment and gradual layoffs. Read the current experiment’s output instead of memorizing an older ending.

You reported that Devpost and Fetch were submitted. Submission status and technical verification are different facts; an account signup or published Actor alone is not a final event-entry receipt.

The detailed verification history is in [the session handoff](./SESSION_HANDOFF.md). The shorter speaking version is in [the track guide](./PARALLAX_TRACK_JUDGING_GUIDE.md).

## 32. A compact explanation to remember

Parallax is a small simulated economy with people, businesses, and banks that depend on each other. We introduce a bank investment loss and calculate how it affects lending, payroll, production, and defaults. AI agents investigate the financial facts, negotiate bounded credit or supplier terms, and explain rescue options. Apify supplies scoped public inputs, CRS supplies sandbox credit evidence, Fetch gives the system a conversational agent interface, Spacetime supports shared review, and x402 supports an optional paid-analysis path. The financial engine calculates outcomes and validates execution, while people retain explicit review and confirmation steps.

## 33. Hyphenate in depth: the financial job our system performs

Start with the job rather than the sponsor name. A risk analyst needs to understand what could happen after a financial institution is hit. A credit officer needs to decide whether a business can borrow, under which limits, and with whose approval. Parallax brings those jobs into one controlled experiment.

The policy agent can inspect bank conditions and calculate alternative responses. The borrower agent can ask for funding based on its payroll shortfall. The bank agent can assess the actual request. The system gives each role a small set of tools instead of unrestricted permission to change balances.

Consider a made-up business with $300 available and $500 payroll due. The funding problem is $200. Its borrower agent can ask for that gap. The bank's tools check the proposed principal and what the bank would look like after issuing it. A convincing sentence from the model cannot make an ineligible loan pass.

A configured amount limit or uncertain evidence can hold the proposal for review. A person records an approval or decline with a reason. Approval records a decision, and settlement separately posts the loan. If the source financial state changes, the old proposal may need a fresh assessment.

This is why the work fits the financial-agent theme: the agents do a defined financial job, obtain evidence, stay within permissions, keep a record, and escalate uncertainty. Hyphenate supplies the challenge theme. Our code does not call a Hyphenate endpoint.

A useful answer to “What makes this autonomous?” is: the requested workflow can carry out multiple inspection, testing, and negotiation steps without a person choosing each tool. The user still initiates these workflows and confirms financial actions. The system has bounded autonomy within a task, rather than continuous control of a real economy.

Read next: [policy workflow](../backend/agents.py), [credit workflow](../backend/credit_agents.py), and [credit controls](../backend/crs_credit.py).

## 34. Fetch.ai in depth: the doorway, the address book, and the message format

There are three names here because they have different jobs. **uAgents** is the framework used to construct the gateway and its message handlers. **Agentverse** is where that agent has a registered identity and connection information. **ASI:One** is the conversation interface through which a person reaches it.

Think of Agentverse as an address book, the gateway as a receptionist, and ASI:One as the place you speak to that receptionist. ACP, the Agent Chat Protocol, gives the messages a shared structure, including chat content and acknowledgements. An acknowledgement confirms message handling; it is different from a completed financial result.

A supported stress-test message reaches the gateway. Its bounded command parser extracts the bank and loss. It asks the backend to create the experiment and start analysis, waits for the background job, and returns the recorded result. Nemotron through Nebius supplies the financial model inference used by that analysis. Fetch messaging and the financial inference provider are separate parts of this path.

The gateway remembers the sender's previous analysis so the explanation follow-up can retrieve its saved evidence. This is a narrow piece of application memory. It is not training a model or remembering an unrestricted personal history.

Our verified public identity is `agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm`. A profile URL points to this registered identity. A shared-chat URL points to a publicly shared conversation. The ordinary signed-in chat URL and the shared URL serve different purposes.

The ten local services add typed economic operations around saved state. For example, the household-welfare service computes a balance distribution, and the clearinghouse service reads outstanding interbank obligations. They are deterministic services. Our live evidence establishes one public gateway, not ten public registrations.

The separate optional ASI inference adapter asks an ASI model to retrieve Census and FDIC references. Its successful live inference has not been verified. The working ASI:One gateway conversation does not depend on claiming that optional path succeeded.

Read next: [gateway routing](../backend/fetch_chat.py), [gateway setup](./FETCH_AGENT.md), and [local services](./FETCH_ECOSYSTEM.md).

## 35. CRS in depth: credit evidence becomes part of a decision

CRS is a financial-data API provider. In our implemented path it gives access to an Experian credit report in a common response structure. Experian is the source credit product; CRS is the API through which our app requests it. Nemotron is the model that helps review the simulated request. These three names describe different responsibilities.

A private profile identifier such as `sponsor_p19_owner` tells the backend which sponsor-supplied synthetic applicant payload to use. The dropdown contains this identifier, while names, addresses, and identity fields remain on the backend. The current account uses the Cal Hacks sandbox.

Authentication obtains an access token. The report request goes to `/experian/credit-report/standard/exp-prequal-vantage4`. A response has to be checked for product errors as well as a successful HTTP status, because the API can return HTTP 200 with an error in the body.

The parser reads the score from `scores.0.scoreValue`, which means: open the scores list, take its first entry, and read its scoreValue field. The verified P19 request returned 770. Our application stores a smaller evidence record containing the normalized score, risk decision, timing, and report reference.

A score does not answer every question. The application separately handles unknown or blocking risk evidence, the business's current payroll gap, existing debt, bank lending limits, and any human-approval threshold. The current private risk rules deliberately leave identity/fraud clearance unresolved, so the verified 770 result still requires review.

That behavior is useful because it makes the role of evidence visible. The agent must obtain the report before assessment, then use it inside the credit process. It is more meaningful than showing a credit score on a card while approving the loan through unrelated logic.

Credit evidence can be cached for fifteen minutes when its bound request and mapping match. Financial facts still need to match the reviewed state at approval and execution. External-data freshness and financial-state freshness are related but separate checks.

The optional TruValidate identity-screened payment path has its own product, payload, and mappings. Its implementation and fixture tests do not establish a successful live fraud-screening request. Our live CRS claim is the owner credit-report underwriting workflow.

Read next: [report adapter](../backend/crs_credit.py), [lending assessment](../backend/credit_policy.py), and [separate screening implementation](../backend/fraud.py).

## 36. Apify in depth: turning web pages into usable inputs

A public page is written for a reader. The simulation needs a clean number with a unit and an explanation. Our Actor is the bridge between those two formats.

For prices, it fetches Cafe Seventy8's page, extracts the supported posted menu options, and produces records such as a named drink option with a dollar value. For wages, it reads the official city page and identifies the general statutory minimum wage. These are two fixed collection tasks selected by the `category` input.

The output records explain what each number means. The source URL says where it came from. The observation time says when it was collected. The unit distinguishes an item price from an hourly wage. The kind field prevents a legal wage floor from being confused with an average salary.

The application accepts and converts those observations into its price and daily-wage samples. Suppose an hourly reference were $20: the explicit eight-hour assumption would produce a $160 daily reference. That multiplication is our modeling choice, not another value scraped from the source.

A saved calibration is a versioned input bundle. When a world is created, the selected bundle and its fingerprint become part of the saved experiment. A later collection can update the latest bundle for a future world while the existing experiment retains the values it started with.

The **application-use category** concerns this full data path: collection, validation, automatic loading, actual use in initialization, and preserved provenance. The **Actor category** concerns the reusable collector itself: its defined input, output, documentation, limited permissions, and successful execution on Apify.

The Actor checks source collection rules and has fixed sources. Public source requests do not receive the Apify token. Platform requests use the run credentials to read the run's input and write its dataset. Publishing the Actor makes the program runnable by other accounts; it does not automatically expose historical private datasets.

Apify makes part of the input story more grounded and traceable. It does not supply real household bank accounts, real bank portfolios, employment links, war impacts, national debt, or an entire calibrated city economy.

Read next: [collector](../apify_actor/main.py), [Actor definition](../apify_actor/.actor/actor.json), [collection service](../backend/apify_collection.py), and [conversion and calibration](../scripts/apify_calibrate.py).

## 37. Spacetime in depth: sharing a decision, not merely sharing a screen

A normal dashboard can show the same data in two windows while each window maintains separate local choices. Our shared control room stores coordination choices in SpacetimeDB so participants work with the same proposal and review record.

The room contains participants, a reference to the financial world, proposals, review decisions, and receipts. A reducer is server-side logic that changes this shared database through an allowed operation. A subscription tells a client when the rows it follows change.

The proposal records the intended bank shock and the financial snapshot it is based on. A second browser identity reviews that proposal. The shared decision becomes visible across sessions. This is the part where Spacetime's transactional updates and direct subscriptions matter.

A review is still different from executing the accounting operation. The backend checks the approved proposal against the current financial snapshot and applies the shock through the financial engine. It records completion so repeating the request cannot apply the loss a second time.

SQLite remains the financial record. SpacetimeDB owns the shared room and coordination record. This separation lets the established ledger enforce accounting rules while the room coordinates several connected participants. The application includes explicit checks around the cross-service operation; it is not one universal transaction across both databases.

The verified two-browser test exercised real subscriptions and independent browser identities. The prototype treats browser identities as anonymous participants. Production roles, real-person authentication, and organizational approval permissions would require further work.

The meaningful contribution is the shared review process and its durable execution result. It reaches beyond animating the same city in two windows.

Read next: [shared-room module](../spacetimedb/src/index.ts), [backend bridge](../backend/spacetime.py), and [control-room interface](../apps/web/src/ui/ControlRoom.tsx).

## 38. Coinbase x402 in depth: buying one piece of research

The simplest version of this feature is: a service sells a small result, and a compatible client pays for that request using a machine-readable payment flow.

Our research server responds to a protected request with HTTP 402 and the payment terms. The buyer checks those terms. The SDK constructs the appropriate payment authorization, the facilitator verifies and settles it, and the merchant can return the requested result after payment is accepted.

HTTP is the request/response language. x402 is the payment protocol. The Python SDK is the implementation library. The facilitator is the verification and settlement service. Base Sepolia is the test blockchain. USDC is the token transferred on that network. The wallet holds the private signing key. These pieces cooperate, but they are not interchangeable names for one API.

The Circle faucet was used to obtain test USDC for the wallet. The RPC service lets our software inspect chain state. BaseScan gives a person a public receipt page. A successful explorer page proves a particular recorded transaction, while our code also checks the transfer amount and parties.

The purchased output is a small synthetic employment-trend calculation for an exact saved world. We bind the response to the request's state fingerprint so the buyer can detect receiving analysis for the wrong experiment.

A per-run spending limit and a durable attempt record address a difficult failure: a timeout after a payment may leave the caller uncertain whether settlement happened. Repeating blindly can spend again. Our verification harness records its attempt, and the application validates receipts rather than treating every retry as a fresh safe purchase.

The actual recorded transfer was 0.01 test USDC, executed by the SDK verification flow. The live policy model also had an optionally authorized research tool in a separate run and selected other tools. The evidence supports the paid-service integration and explicit purchase, with model-selected spending remaining a separate observation.

This path does not use a Coinbase trading strategy or a Coinbase Wallet MCP account. Its implemented Coinbase technology is x402. Both payment accounts belong to the project, and test tokens are separate from deposits inside the economic simulation.

Read next: [payment evidence](./X402_SUBMISSION.md), [buyer](../x402_service/buyer.py), [merchant](../x402_service/server.py), and [agent spending control](../backend/paid_research.py).

## 39. Microsoft, technical complexity, and general Gen AI in depth

These categories describe qualities of the same product, rather than three new services we installed.

The Microsoft real-world theme concerns the job a person needs done. Our intended risk analyst can inspect the same saved scenario, compare three alternatives, read why an agent chose a response, and carry the evidence into a downloadable report. The credit officer can review a constrained proposal and approve it separately from execution.

The customer-impact explanation must distinguish measured simulation outcomes from actual user outcomes. We can measure employment, defaults, and support amounts within an experiment. We have not measured analyst hours saved, customer revenue, real risk reduction, or willingness to pay. Interviews and user testing would establish that next layer of evidence.

Technical complexity comes from making the pieces agree. The financial engine must keep its ledger balanced. Forks must isolate their source. A model may propose only supported tool actions. Approval must refer to the reviewed state. The shared room must avoid duplicate execution. An external payment must deliver analysis for the correct snapshot. Integrating these checks is more important than simply counting APIs.

The Gen AI role is the use of a language model in actual investigation and negotiation. The model can choose a tool, interpret its returned observations, select an eligible next step, and explain a decision. A scripted deterministic mode exists separately for repeatable local use.

Nebius and NVIDIA provide the verified inference foundation. Codex helped build and test the application. Spacetime, Apify, CRS, and the ledger each have other jobs; calling every dependency an AI model would make the architecture harder to understand.

## 40. What each external dependency changes in the experience

If the live inference account is unavailable, explicit demo mode can still use the simulation's financial tools, while live agent requests report the provider failure.

If Apify is unavailable, an existing world still has its frozen inputs. Creating a new world with automatically collected inputs depends on an available saved bundle and the collection service; an explicitly seeded world is a separate input choice.

If CRS is unavailable during a required credit review, the workflow cannot infer clearance from the missing response. Ordinary financial checks and CRS-required underwriting are distinct choices.

If the Fetch gateway or its mailbox connection is unavailable, the web application can still operate through its own backend. The conversational entry path needs the gateway, the API, and the required provider services running.

If SpacetimeDB is unavailable, the shared coordination feature is affected. It does not become the financial ledger or replace the source world in SQLite.

If the research merchant, facilitator, wallet funding, or blockchain access is unavailable, paid research can fail. The core simulation does not depend on a successful external testnet purchase to advance one day.

Census and FDIC provide reference context. Treasury provides a dated debt baseline for its optional story. None of those three sources replaces the simulation's generated financial network.

GitHub holds source and setup instructions, Devpost holds the submitted project, and ASI:One's event workflow holds the separate Fetch entry. These are delivery and access surfaces. They do not execute the economy merely because a link has been published.

## 41. A plain-language vocabulary for the whole system

An **API** is a defined way for one program to ask another program for data or an operation. An **endpoint** is the particular address for that request. A **payload** is the structured information sent with it.

An **SDK** is a library that implements common steps for using a service. A **framework** supplies reusable building blocks for constructing a program. An **Actor** in Apify means a packaged runnable program; an **agent** in our AI workflows means a role that uses a model and tools to perform a task.

A **tool** is a specific backend operation made available to the model. The model requests the operation, and our code validates and runs it. The returned data becomes evidence for a later step.

A **world** is one saved synthetic economy. A **tick** is one day in its model. A **seed** controls reproducible generated choices. A **snapshot** is its saved state, and a **hash** is a fingerprint of that state.

A **fork** is an isolated alternative future starting from a saved state. A **trace** is a record of tool actions and results. An **event** records something that happened in the economy. A **job** tracks an analysis task while it is queued, running, completed, cancelled, or failed.

**Capital** is the bank's buffer against losses, expressed through its equity and assets in this model. **Liquidity** concerns its ability to meet payments, including reserve transfers. A bank can have a problem with one or both.

**Provenance** means where data came from and how it was obtained or converted. **Calibration** here means the saved set of selected public input samples, rather than proof of a fully fitted city economy.

**Approval** records a permitted decision. **Settlement** posts its financial effect. **Idempotency** protects against executing the same operation twice. **Sandbox** and **testnet** refer to service-specific testing environments; they still make real requests and create test records.

## 42. Where to look when someone asks how you know

For calculated financial behavior, inspect [the engine](../backend/engine.py), [ledger](../backend/ledger.py), [lending assessment](../backend/credit_policy.py), and [fork comparison](../backend/forks.py).

For model permissions and negotiation steps, inspect [policy agents](../backend/agents.py), [credit agents](../backend/credit_agents.py), and [procurement](../backend/procurement.py).

For real inputs, inspect [Apify collection](../backend/apify_collection.py), [Census/FDIC retrieval](../backend/research.py), [Treasury retrieval](../backend/shock_stories.py), and [CRS normalization](../backend/crs_credit.py).

For the shared room, inspect [Spacetime server logic](../spacetimedb/src/index.ts) and [its accounting bridge](../backend/spacetime.py). For paid analysis, inspect [x402 evidence](./X402_SUBMISSION.md).

For public track descriptions, use [the short speaking guide](./PARALLAX_TRACK_JUDGING_GUIDE.md). For current implementation history and verification scope, use [the handoff](./SESSION_HANDOFF.md). The source code, saved evidence, and explicit scope together support an explanation more reliably than a marketing claim alone.
