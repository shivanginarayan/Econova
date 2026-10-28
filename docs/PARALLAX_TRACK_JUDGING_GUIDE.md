# Parallax: how we use each track

Parallax is a simulated economy where financial agents investigate bank shocks, negotiate credit, and compare rescue policies. The sections below are written as words we can say directly to judges. Sections 1–7 describe our main sponsor work. Sections 8–11 describe broader awards we can explain using the same product; they are not additional API integrations. Implementing a technology does not by itself mean its award submission is complete.

## 1\. Hyphenate — The Hyphenated Enterprise: Autonomous Systems for Finance

We built Parallax to explore the work of a bank-risk analyst and a credit officer: understand a financial problem, check the evidence, and decide what needs attention.  
When a simulated bank loses money on its investments, our agents inspect the economy and compare possible rescue plans before recommending what to do.  
In the credit workflow, a business agent asks for money to cover a payroll gap, and a bank agent checks whether lending that amount fits the bank’s financial limits.  
The system asks a person to review large loans or uncertain credit evidence, and approving a proposal is a separate step from actually issuing the loan.  
For the demo, we can show the recorded tool steps, the human-review screen, and the separate settlement action, so judges can follow how a proposal becomes a financial action.  
Our use of this track is about accountable financial agents; Hyphenate is the challenge we are addressing, and we do not claim to use a Hyphenate API or to operate a real bank.

## 2\. Fetch.ai — Best Use of Fetch.ai

We use Fetch.ai to give Parallax an agent that people can talk to through ASI:One, alongside our own web interface.  
Our registered gateway uses the uAgents framework and Agentverse to receive a message, pass the supported request to our backend, and send the result back.  
For example, we can ask, “stress-test bank 1 with a 40% loss and compare rescue plans,” and the workflow creates a simulated experiment and compares three futures.  
We can then ask, “why did you pick that?”, and the agent returns the saved explanation and tool evidence from that experiment instead of inventing a new result.  
We verified this through both the actual messaging connection and the ASI:One interface; the financial analysis uses our configured Nemotron model through Nebius.  
We have one externally registered gateway, and chatting with it does not automatically apply financial support; the ten local economic services are not ten separately verified public agents.

## 3\. CRS — Financial Intelligence Challenge, especially Best Financial AI Agent

We use CRS to give the bank agent credit evidence before it assesses a simulated business owner’s loan request.  
The agent calls the CRS sandbox for an Experian credit report using a test person supplied by the sponsor, so we are not requesting credit information about a real applicant.  
In our live test, the sponsor’s small-business-owner profile returned a credit score of 770, and the bank agent retrieved that report before assessing the proposed loan.  
The workflow keeps raw identity details and credentials private, while the agent and the interface receive a smaller result containing the score, review status, and evidence reference.  
We showed that result in the app and stopped at “Human approval required,” because a credit score alone does not prove that identity and fraud checks have passed; no loan was issued in that verification.  
For judges, we can select the sponsor owner profile under Credit safeguards, run the live review, and show how actual CRS sandbox evidence affects the decision rather than simply appearing on an unrelated screen.

## 4\. Apify — Best Use of Apify

We use Apify to bring a small, clearly defined set of real public observations into the simulated economy.  
Our collector reads posted drink prices from Cafe Seventy8 in San Francisco and the city’s official minimum-wage page, then saves the numbers with their source links and collection times.  
When the app opens, it automatically loads saved public inputs and refreshes missing or old inputs through bounded collection runs, so a user does not have to enter those values by hand.  
A new world uses the collected prices and wage references, and it freezes that input sample so a later website update cannot silently change an experiment that already exists.  
For the demo, we can open the public-input panel, show an actual collected number and its source, and explain how that input is used when a world is created.  
These observations cover one cafe’s posted prices and a legal wage floor, not average earnings or the whole city’s economy; households, banks, opening balances, and financial behavior are still simulated.

## 5\. Apify — Best Actor

For the Best Actor category, our contribution is the custom collector itself, which we built and published on Apify Store.  
It accepts a simple choice between prices and wages, visits the fixed public source for that choice, and returns records with the item, value, unit, source link, and collection time.  
We added a README and input and output schemas so another person can understand what it does, choose an input, and find the results without reading our application code.  
The Actor uses limited permissions, checks the source’s collection rules, and reports a failure if the expected data cannot be found rather than making up replacement values.  
We verified that the public Store page opens and that a run of the published build succeeded with 29 valid price observations; judges can open the listing and run it in their own Apify account.  
This is the same collector used by our Best Use entry, viewed as a reusable tool; publishing it makes it accessible for review, while the final award decision remains with the organizers.

## 6\. Spacetime — shared real-time simulation control room

We use SpacetimeDB for the part of Parallax where multiple people look at and coordinate actions in the same simulated economy.  
It stores shared room participants, proposed bank shocks, review decisions, and execution receipts, and subscriptions send changes to the connected browsers as they happen.  
One participant can propose a shock and another browser identity can review it, which lets us show a shared decision process instead of two separate copies of a dashboard.  
Approval alone does not apply the shock: the accounting backend checks that the world still matches the reviewed state before executing it, and it prevents the same proposal from being executed twice.  
We tested this with two independent browser sessions, including shared updates, review, execution, repeated requests, and refusal to apply a proposal after the world had changed.  
SpacetimeDB handles the shared coordination, while SQLite remains the financial record; the current room uses anonymous browser identities, so we do not present them as verified human identities.

## 7\. Coinbase — Best Use of x402

We use Coinbase’s x402 protocol for a separate research endpoint that charges a small amount for a response tied to a particular simulation state.  
The service requests 0.01 test USDC on Base Sepolia, and the buyer checks the network, payment token, recipient, and amount before accepting the payment request.  
After payment, the buyer checks the blockchain receipt and makes sure the returned analysis belongs to the exact world snapshot it requested.  
We completed and independently verified a real testnet payment through the x402 SDK, and the returned analysis was a simple synthetic employment-trend projection rather than a real economic forecast.  
For judges, we can show the payment receipt and explain how a financial agent could obtain paid research only when that option has been explicitly allowed; the test wallet is separate from money inside our simulation.  
The successful payment was an explicit SDK test, and a separate live AI run did not choose to buy research, so we do not claim that an AI autonomously made the verified purchase or that we earned real customer revenue.

## 8\. Microsoft — Grand Prize: Built for the Real World

For Microsoft’s challenge, we present Parallax as a prototype for risk analysts and credit officers at regional or community banks.  
The problem we are exploring is how to inspect a financial shock, compare possible responses, and understand an AI recommendation without losing track of the assumptions behind it.  
Our workflow connects the full sequence: create an economy, introduce a shock, inspect the effects, compare rescue plans, review an agent’s explanation, and confirm an action separately.  
A user can download the comparison report with its source information and calculated outcomes, which helps another person review the experiment outside the app.  
Our path toward a real deployment would include validated bank data, secure user accounts, stronger approval permissions, and evaluation with the people who would use it.  
This is a fit with the challenge’s product goals, not a claim that we use Azure or that the prototype is ready for a real bank; our intended users are a customer hypothesis we still need to validate.

## 9\. Microsoft — Customer Impact Award

For this award, we focus on the person using Parallax and how the workflow could help them make sense of a difficult financial situation.  
A risk analyst can see a shock and its consequences in one place, while a credit officer can inspect the evidence behind a proposed loan and see why it needs review.  
We compare the same starting economy under different rescue choices, which makes it easier to explain the trade-off between simulated employment, business defaults, bank stress, and public support costs.  
Those outcomes come from the simulation, and we would show the actual displayed results even when a rescue does not improve them, rather than promise that every intervention works.  
We have a working demonstration and measurable simulation results, but we have not yet interviewed customers or measured real time savings, financial savings, or willingness to pay.  
This is therefore a broader award we can discuss honestly, with a weaker evidence base than our verified integration tracks; our next step is to test the workflow with actual risk analysts.

## 10\. Cal Hacks — Most Technically Complex Hack

For this category, we explain how several working parts come together while keeping financial calculations under clear rules.  
The simulation records money in integer cents and uses accounting entries that must balance, so an agent cannot create a valid loan or payment just by saying it happened.  
Our policy comparison starts three separate futures from the same saved state and controlled randomness, so differences come from the tested choices rather than unrelated starting conditions.  
Background jobs run the AI workflows, saved traces show their tool actions, and checks prevent repeated settlement or execution against an outdated world.  
The city interface, shared Spacetime room, public Apify inputs, CRS evidence, and downloadable report connect these mechanisms into one product that we can demonstrate.  
After integrating this branch, 217 backend tests passed with one optional test skipped, frontend tests and the production build passed, and a browser check verified the main combined workflows; these checks support the prototype without proving production readiness.

## 11\. MLH — Best Use of Gen AI

We use a generative AI model inside Parallax’s working financial workflows, so AI is part of what the product does for a user.  
NVIDIA Nemotron-3-Nano-30B-A3B, accessed through the Nebius API, powers agents that inspect financial facts, negotiate credit and supplier terms, and explain tested rescue choices.  
The model calls tools to obtain evidence and propose actions, while the simulation calculates the financial outcomes and the ledger checks whether an action can execute.  
For judges, we can show a live agent’s provider and model name, the tools it called, the evidence it received, and the recommendation or loan proposal that followed.  
This makes the AI’s role concrete: it helps investigate and explain the situation, while unknown evidence and review limits can still stop an action from being carried out automatically.  
The official Cal Hacks prize page lists this category, but we have not confirmed that it appears in the team’s submission selector; check with the organizers if it is missing, and do not describe it as an already submitted entry.

## 

