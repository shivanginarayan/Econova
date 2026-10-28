# Submission evidence and demo outline

## Customer and seats

The current [Microsoft and technical-complexity guide](./MICROSOFT_TECHNICAL_SUBMISSION.md) contains copy-ready descriptions, the complete five-seed evaluation methodology and the new downloadable comparison report. [Nebius × NVIDIA readiness](./NEBIUS_SUBMISSION_READINESS.md) covers the separate online event; it is not an additional Cal Hacks sponsor category.

Our customer hypothesis is risk teams at regional/community banks and bank-supervision teams that need an understandable way to explore liquidity shocks. We have not conducted customer interviews or measured production savings. The prototype fills stress-testing analyst and credit-officer workflows: inspect financial facts, test scenarios, explain decisions and escalate exceptions.

## Opening demonstration

The [Hyphenate and Apify submission guide](./HYPHENATE_APIFY_SUBMISSION.md) provides the timed pitch, copy-ready sponsor descriptions, source limitations and live recording command. Use that guide for the current automatic-loading UI. The combined live check creates separate worlds and records public traces and financial receipts; it does not substitute scripted agents for live calls.

1. Create a standard world. Use a prearranged supplier expense to give a business a real observed payroll shortfall; label this as scenario setup.
2. Inspect the business, open Credit safeguards and set a threshold below that shortfall. Request a review. Show `needs_human_approval`, its reasons, and that no loan settled even if automatic settlement was requested.
3. Enter a review rationale and approve. Show that approval still moves no money. Confirm settlement separately and inspect the balanced audit and transaction receipt.
4. For CRS-specific judging, repeat using actual sponsor test profiles: show a live credit report pull and a flag-driven block/review. Until those credentials work, describe this portion as fixture-tested, not live CRS usage.
5. Trigger a bank asset-loss shock, compare the three futures, inspect costs/defaults/employment, and explain the recommendation from the saved trace. The shock controls accept a bank and loss percentage for a judge-provided scenario.

For a deterministic recovery rehearsal, run `scripts/hyphenate_demo.py`. It deliberately exceeds a budget, displays the engine rejection, then recovers. Its agent is explicitly scripted; do not present it as a live model making a mistake and learning. The normal policy and credit workflows support live Nemotron and are separately verified.

## What is real and what is simulated

| Component | Current evidence |
| --- | --- |
| Accounting, settlement, production, clearing and forks | Real calculations on synthetic state, tested with balance and replay invariants. |
| Households, businesses, banks and opening balances | Seeded simulation; city geography is decorative. |
| Census and FDIC context | Actual sourced population/institution records, with dates/scope; not a fully calibrated local economy. |
| Apify price/wage calibration | Live private limited-permission Actor verified: 29 listed drink-price options at one SF cafe and the official general minimum wage, with run/dataset/source/date provenance. Values seed new worlds; remaining entities/balances/behavior are synthetic. See [Apify evidence and scope](./APIFY.md). |
| CRS owner credit reports and fraud flags | Adapter and enforced underwriting controls implemented and fixture-tested; live credentials/config/test profiles still required. |
| Agent decisions | Live Nemotron on Nebius verified. Demo and scripted rehearsal providers are labeled separately. |
| Fetch conversation workflow | Complete backend conversation and evidence follow-up verified with live Nemotron; ACP SDK validated. Agentverse registration, active public discovery and full signed ACP mailbox workflow verified. Full ASI:One UI stress-test and saved-evidence follow-up also verified. |
| x402 paid research | Real x402 SDK/facilitator purchase completed for 0.01 Base Sepolia test USDC, with independent receipt/transfer verification. Separate live policy run enabled the optional tool but did not choose to purchase. See [transaction evidence](./X402_SUBMISSION.md). |
| SpacetimeDB | Real shared control room: direct subscriptions, two-session presence, second-identity approval, snapshot-bound exactly-once execution, persistent receipts and reducer authorization verified. See [SpacetimeDB demo](./SPACETIME_SUBMISSION.md). |
| Nessie | Optional and not implemented; no usage claimed. |

## Measurable usefulness

Use calculated branch differences: employment preserved, business defaults avoided, bank stress and gross public support. In the deterministic rehearsal with seed 42 and a 40% asset loss at Bank 1, a household-support branch preserved five additional jobs and avoided one business default versus no intervention, at $10,000 gross support. These are simulation outcomes for that scenario, not measured customer benefits or real-world forecasts. Liquidity lending also creates debt; gross support is not net fiscal loss.

## Path to production and limitations

Replace synthetic balance sheets and behavior assumptions with validated inputs, authenticate users and operator approvals, add role-based permissions, evaluate the model/policies, and test deployment/scale. The current local API has no authentication. Owner credit evidence uses sponsor test identities only. Testnet research payments are isolated from the virtual ledger and require explicit per-run permission. No mainnet payments are supported.

## Submission checklist

- Record a smooth end-to-end demo with labeled providers and a balanced audit.
- Include repository/run instructions, a project image, the live demo or recording and a concise customer/limitations section.
- Claim sponsor usage only where a live integration is demonstrated; sponsor eligibility is separate from code completion.
- For Fetch, record the actual agent address, discoverability and full workflow in ASI:One; complete both required submission paths described in the official hackpack.
- For x402, include the verified Base Sepolia transfer hash and explorer link after the wallet is funded and the payment succeeds.
- Preserve a backup recording. Confirm final deadlines and rules with the official event/sponsor materials.
