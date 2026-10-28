# Hyphenate and Apify submission guide

Economy God Mode is a financial stress-testing prototype for regional-bank risk teams and bank-supervision analysts. Live AI agents inspect financial facts, test interventions on isolated copies, and propose bounded decisions. Deterministic accounting and policy checks control settlement. Public price and wage observations collected with a custom Apify Actor initialize selected inputs; the economy itself remains simulated.

## Target categories and official requirements

The [official Cal Hacks 13.0 listing](https://cal-hacks-13-0.devpost.com/) lists **The Hyphenated Enterprise: Autonomous Systems for Finance**, **Best Use of Apify**, and **Best Actor sponsored by Apify**. Checked October 24, 2026. The event requires a project image, GitHub repository, and a live or prerecorded demonstration; the listed pitch format is three minutes plus two minutes for questions. The submission deadline is October 25 at 9 AM Pacific.

Apify's listing explicitly requires meaningful use and evaluates project quality. We collect with a deployed custom Actor and use its actual numerical observations in the running economy. The [official Hive prize board](https://hive.hackberkeley.org/prizes), read after its dynamic cards loaded on October 24, independently confirms the four Hyphenate criteria reflected below and the requirement to open a demo video with the moment, bring a live demo, name the seats filled and distinguish real from simulated evidence. Whether Best Actor requires Store publication remains unresolved by these listings; confirm that detail with the sponsor before entering that category.

## What to demonstrate

| Track argument | Visible proof | Limit |
| --- | --- | --- |
| Hyphenate: financial workflow that works | Live business and bank agents inspect a payroll shortfall, assess eligibility and propose exact loan principal. | A deliberately configured synthetic expense creates the demonstration's shortfall. |
| Hyphenate: knows when to ask | The same live review stops at human approval. Approval changes no money; a separate confirmation settles once. | Local operator approval is not authenticated production access control. |
| Hyphenate: a useful new workflow | The central-bank agent tests rescue plans on isolated snapshots and recommends from calculated employment/default/cost results. | This is a synthetic experiment, not a calibrated forecast or validated financial advice. |
| Hyphenate: explain the decision | Public tool trace shows observations, tested alternatives and the actual saved rationale. | Hidden model reasoning is neither displayed nor recorded. |
| Apify: meaningful platform usage | App loads public inputs automatically; real run/dataset/source IDs are inspectable. New business prices and wage references come from those values. | Cached observations retain collection dates; a new app open does not imply a fresh crawl. |
| Apify: custom Actor | Repository source and a successful private Actor run are available for inspection. | The Actor is private, not published to the Store. |

## Three-minute demonstration and narration

**0:00–0:35 — Open with the approval moment.** Start with the prepared credit world, show live Nebius/Nemotron mode and the human-review gate. Say: “The agents found a payroll funding gap and assessed a loan. The approval limit stops settlement here. This gap is deliberate scenario setup on a simulated balance sheet.” Show the recorded financial checks. “The AI can propose; our policy and ledger decide what can execute.”

**0:35–1:00 — Approve, then settle.** Enter a reason and approve. Show the separate settlement button. “Approval records my decision and moves no money. Confirming settlement posts the exact loan once and preserves a balanced ledger.” Show the resulting receipt/entries.

**1:00–1:30 — Show Apify's contribution.** Open Real public inputs. “Our custom Apify Actor collected posted drink prices from one San Francisco cafe and the official minimum wage. These values actually initialize the business prices and wage references. The legal wage floor is not average earnings; we explicitly assume eight hours per day. Every world freezes its data and provenance, so refreshing sources cannot rewrite an experiment.” Open source/run links and collected values. Keep account credentials off screen.

**1:30–2:10 — Trigger a crisis and compare futures.** Use a new credit-crunch world with public inputs. Apply a 40% loss to Bank 1's risky assets. “This is a hypothetical investment loss, not a 40% haircut to deposits.” Open Fork Reality, move to day 12 and compare employment, defaults and gross support. “These are separately calculated outcomes from the same snapshot and random stream.” Quote the actual displayed values, never predetermined benefits.

**2:10–2:40 — Show the live policy decision.** Run Test rescue policies in live mode while paused, or reopen the saved completed report if latency is high. “The agent can inspect, test and recommend, but analysis leaves the source untouched. Applying support requires a separate action.” Show the tested alternatives and saved rationale. Distinguish the rule-based fork ranking from the model's recommendation.

**2:40–3:00 — Customer and limits.** “We designed this for the stress-testing analyst and credit-officer workflows at smaller banks. The prototype measures simulated defaults, jobs and support costs. Production work includes validated bank data, authentication and policy evaluation.” We have not conducted customer interviews or measured actual customer savings.

For a two-minute pitch, use the completed reports to avoid inference waits and shorten the source explanation. Keep the source scope and scenario-setup labels. A prerecorded run is a backup; do not present playback as fresh inference.

In the first successful combined run on October 24, the public-input credit-crunch experiment ended with zero employment and eight business defaults in all three branches at day 12. Both support branches disbursed $10,000 gross support; the live agent recommended no intervention. This is a useful **defend a decision** example: the tested support did not improve those final metrics, so the agent declined to recommend spending. Do not claim jobs were saved in this experiment, or that no intervention is generally optimal. Earlier seeded demonstrations had different outcomes; public inputs do not calibrate the remaining behavioral assumptions.

## Copy-ready submission text

### Short description

An interactive economic stress test where live AI agents negotiate credit, ask for approval, and compare rescue policies on an audited simulated economy grounded in selected public price and wage observations.

### Hyphenate

Economy God Mode explores autonomous stress-testing analyst and credit-officer workflows. Business and bank agents use live Nemotron on Nebius to inspect financial state, assess lending constraints and propose payroll financing. A configured approval threshold escalates large loans to a human; approval and financial settlement are separate actions. The engine validates every settlement and posts balanced integer-cent journal entries with retry protection.

Our central-bank agent tests rescue proposals on isolated copies of the same economy before recommending an intervention. Judges can inspect the observations, alternatives, calculated outcomes and public rationale. Entities and balances are synthetic; selected public observations come from Apify. We demonstrate bounded financial autonomy and auditable human oversight in a prototype, without claiming production access controls or calibrated forecasting accuracy.

### Apify

Our custom Python Actor collects public menu-price options from Cafe Seventy8 and the general statutory minimum wage from San Francisco's official page. Each observation includes its source and collection time; the wage also includes its effective date. The app automatically loads saved inputs on open and refreshes missing or stale inputs through bounded Apify runs. Collected prices and wage references are actually used to initialize new worlds.

We preserve Actor, run and dataset provenance and freeze the entire dataset with a checksum inside each experiment. Forks and resets retain the same observations so later collection cannot change historical outcomes. The Actor checks robots.txt, ignores script content and fails when expected observations cannot be parsed. One cafe and a statutory wage floor are limited public references, not citywide calibration. Actor source is included in the repository; the deployed Actor remains private.

## Reproduce and record proof

Start the backend with the existing private root environment and start Vite as documented in the [README](../README.md). Existing user worlds are preserved. The combined verification creates separate worlds, uses live model calls and can trigger automatic Apify refresh if its cache is missing/stale. It never purchases paid research or applies a policy recommendation.

```powershell
# Install the recording encoder once; keep downloads within ignored artifacts.
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) 'artifacts/playwright'
npx playwright install ffmpeg
node scripts/qa-hyphenate-apify.mjs --live
```

The command prints its timestamped output directory under ignored `artifacts/`. It records a silent WebM backup, six screenshots and `evidence.json` containing real source IDs, financial receipts, public tool traces, provider/model labels and assertions. The video has real inference latency and no narration; add the narration above for a concise final submission. Failure is recorded as failure; no demo provider is substituted. Keep the successful original as evidence and review any edited version for consistent labels.

Final readable capture: `artifacts/hyphenate-apify-2026-10-25T03-52-13-456Z/`. All six check groups passed with zero browser errors. The live credit principal was $784.40. In this capture the live policy model recommended $10,000 household support, whereas the earlier successful run recommended no intervention. Both reports retain their own tested evidence; do not promise a fixed model answer, equate recommendation with optimality, or claim final employment improved when the branch metrics do not show it. The recording preserves analysis without applying the policy.

The opening shortage is constructed with a simulated supplier expense through the normal payment API. It is explicitly scenario setup, not a real observed business or Apify-derived distress. The credit gate, approval, settlement, crisis controls, forks and policy request are exercised through the UI. An exact settlement retry is checked through the API. Tests create no on-chain payments or live CRS usage.

## Final submission checklist

- Use the latest successful evidence directory and replay the video before uploading.
- Select Hyphenate and Best Use of Apify in Devpost. Review Best Actor requirements with the sponsor and show the custom Actor if entering that category.
- Upload a readable project image and a narrated demo, or prepare the live demo. Include the repository and clear run instructions.
- Publish the intended code changes before sharing the repository as evidence. The saved working tree contains uncommitted work; this guide does not imply it has been pushed.
- Keep private environment files, ignored datasets, wallets and account credentials out of the public repository and recording.
- Add all teammates, check any sponsor-specific forms and submit before the official deadline. No submission has been made by this guide or verification script.

Related evidence: [implementation status](./TRACK_IMPLEMENTATION.md), [submission limitations](./SUBMISSION_EVIDENCE.md), [Apify setup](./APIFY.md), [Actor source instructions](../apify_actor/README.md).
