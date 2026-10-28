# Microsoft and technical complexity submission guide

These are two additional **Cal Hacks** categories: Microsoft **Built for the Real World** and Cal Hacks **Most Technically Complex Hack**. The [official prize board](https://hive.hackberkeley.org/prizes), inspected October 24, 2026 after its dynamic cards loaded, lists both. Microsoft's challenge is a production-minded AI agent addressing a meaningful problem. Its five criteria cover customer understanding, measurable usefulness, the route to production, responsible design and complete functionality.

The Nebius × NVIDIA competition is a separate event, not another Cal Hacks prize. See [separate-event readiness](./NEBIUS_SUBMISSION_READINESS.md); do not count a working model integration as a completed submission to that event.

## Microsoft customer and workflow

Our initial customer hypothesis is a risk analyst at a regional/community bank, with a credit officer reviewing proposed lending. The prototype explores whether an analyst can use one workflow to configure a shock, inspect connected exposures, compare rescue alternatives, review an agent's proposal and share the supporting experiment.

The problem hypothesis is that stress-test results become hard to assess when assumptions, alternative scenarios, model prose and financial settlement are mixed together. Our workflow preserves a saved source snapshot, calculates isolated alternatives, shows bounded live-agent actions and requires a separate financial confirmation. A downloadable report now lets an analyst carry the calculated comparison and its provenance outside the app.

We have not interviewed customers or established willingness to pay, time savings or production suitability. Customer discovery is a next step, not a completed validation claim. Suggested interview questions: How do you reproduce a scenario today? Which assumptions and approvals must accompany a result? What makes a recommendation unusable? Which decisions require escalation? What would a report need before another reviewer could rely on it? Record actual responses before changing this status.

## Measurable usefulness and evidence

Run the evaluation from the repository root using an existing collected calibration:

```powershell
.\.venv\Scripts\python.exe -m scripts.evaluate_track_scenarios --calibration-id YOUR_EXISTING_CALIBRATION_ID
node scripts/qa-comparison-report.mjs
```

Neither command makes model calls or requests a manual collection. Opening the app during browser verification can automatically refresh missing/stale public inputs under the existing bounded collection policy.

The evaluated dataset `sf_public_20261025_031613_cd6326` was used for five seeds (41–45), alongside five explicitly synthetic seeded worlds. Each experiment compares three matched branches for 12 simulated days after a hypothetical 40% Bank 1 risky-asset loss. Intervention branches receive $10,000 gross support. All 30 final branch audits balanced; all ten source snapshots stayed unchanged. Complete tables and immutable comparison details are generated under ignored `artifacts/microsoft-technical-evaluation/`.

| Observed mode | What the evaluation found | Meaning |
| --- | --- | --- |
| Explicit synthetic inputs, seed 42 | No intervention: 15 final employed households and five defaults. Household support: 20 employed and four defaults, at $10,000 gross support. | Five additional simulated jobs and one fewer default for this experiment. Not measured customer benefit. |
| Explicit synthetic inputs, all five seeds | Outcomes vary; emergency lending has zero additional final jobs in seed 42, while household support has zero additional final jobs in seeds 43 and 44. | Neither policy works uniformly. Keep all seeds visible. |
| Collected public references, all five seeds | Every branch ends with zero employment and eight business defaults at day 12; support does not improve those final metrics. | The remaining behavioral assumptions are not calibrated to these narrow observations. Public data alone does not validate this model. |

The useful demonstrated capability is reproducible comparison and visible limits, not a claim that this engine has discovered the right economic policy. Gross support is not net fiscal loss; public lending also creates debt. The rule-based ranking and live model recommendation are separate. Live runs have recommended different policies from similar evidence; no agent-optimality claim is established.

## Analyst report export

Open Fork Reality and select **Download comparison report**. The standalone HTML file opens in a browser and supports ordinary browser printing. It includes final jobs/defaults/stress/support, differences from the no-intervention baseline, branch audits, snapshot identity, experiment parameters, source scope and recorded shock context. The report describes an incomplete retrieved event window rather than assuming an absence of prior shocks.

Export changes no balances and authorizes no policy. A live-agent recommendation is included only when it is completed and matches both this exact comparison ID and its source snapshot. Otherwise the report explicitly says that no AI recommendation is linked. Source text is escaped before insertion into HTML; the file contains no scripts or remote dependencies.

Public-input and seeded reports are verified separately by the browser check. Their source labels remain different; a zero-benefit experiment says so explicitly.

## Route from prototype to production

| Stage | Concrete work | Evidence required before claiming completion |
| --- | --- | --- |
| Customer discovery | Interview risk analysts and credit reviewers; test exported reports against their actual workflow. | Recorded interviews, unmet requirements and adoption criteria. |
| Validated economics | Replace synthetic starting accounts with authorized institution-level data; calibrate behavior and validate held-out scenarios. | Provenance, calibration methodology, sensitivity analysis and forecast/error evaluation. |
| Access and privacy | Authenticate users/reviewers; isolate tenants and authorize reads, tool access and settlement. | Cross-tenant denial tests, reviewer permissions, audit logs and retention controls. |
| Agent evaluation | Test malformed actions, stale evidence, repeated failure and decision quality across scenarios. | Reproducible evaluation results; no claim that balanced accounting establishes policy quality. |
| Operations | Package deployment, backups, migrations, quotas, monitoring and durable job recovery; measure representative load. | Restore exercise, measured latency/throughput and bounded inference costs. |

These are remaining production tasks. The development API currently has no authentication. SQLite full-world checkpoints favor correctness and simple reproducibility; they are not evidence of production scale. We have not demonstrated 2,000 live LLM agents or citywide forecasting.

## Responsible design

Financial amounts use integer cents and balanced journals. Model proposals pass deterministic validation; tools do not directly edit balances. Credit thresholds require a human rationale, and approval remains separate from settlement. Source changes make old proposals stale. Transaction identifiers prevent duplicate posting. Private credentials remain on the backend, and hidden reasoning is not recorded. The UI and exports distinguish actual public observations, hypothetical shocks and simulated accounts.

The earlier [live recorded demonstration](./HYPHENATE_APIFY_SUBMISSION.md) proves the approval gate, separate $784.40 credit settlement and retry protection using actual Nemotron calls. The new comparison export adds a shareable analyst deliverable to that workflow. This does not establish authenticated human governance, real CRS use, on-chain settlement or regulatory compliance.

## Technical complexity argument

The engineering centerpiece is a deterministic financial engine with a constrained live-agent interface. Financial effects come from double-entry journals, bank credit, cross-bank reserve settlement, inventory recognition, supplier obligations, defaults and interbank clearing. Fork Reality deep-copies the same source into isolated strategies with aligned randomness and retains balanced per-branch audits. Persistent background jobs, replayable events and immutable reports make long-running agent actions inspectable and retryable.

Show one journaled credit transaction, its exact retry, a stale proposal rejection, and the three branch outcomes. Explain why a rejected tool call cannot create money. Present the matched-seed evaluation and an export whose displayed values agree with the backend. Technical depth is supported by invariants and observed behavior, not the number of SDK imports.

Verification after the report-export change: **42 frontend tests and production build passed**, including four new regressions covering failed-rescue wording, cents conversion, report/snapshot binding, source labels and HTML escaping. The final browser check passed public and seeded downloads, exact outcome/funding values, source preservation, mobile layout and zero runtime errors. Backend logic was unchanged this milestone; the earlier full 171-pass/one-optional-skip result remains the backend baseline. Existing bundle-size and Starlette deprecation warnings remain.

## Copy-ready submission descriptions

### Microsoft

Economy God Mode is a production-minded prototype for stress-testing analyst and credit-officer workflows at smaller banks. An analyst can configure a hypothetical bank shock, inspect financial relationships, compare three reproducible futures, review a live AI proposal and export the supporting experiment. An approval threshold escalates large loans; approval records a reason and settlement remains a separate validated action.

We measure calculated employment, defaults, bank stress and gross support across matched scenarios. Our evaluation includes all five fixed seeds under both synthetic and collected public-reference inputs, including experiments where intervention does not improve final outcomes. The exported report carries assumptions, provenance, snapshot identity and audit results so a reviewer can understand what was actually tested.

Customer demand and real-world savings remain unvalidated. Our path to production includes customer interviews, authorized bank data, economic calibration, authenticated reviewer roles, tenant isolation and operational evaluation. Public observations ground selected inputs; accounts and behavior remain synthetic. We demonstrate complete, auditable decision support without claiming production forecasting or autonomous authority over real funds.

### Most Technically Complex

Economy God Mode combines an integer-cent double-entry financial engine, interbank clearing, default contagion, material-constrained production and matched-snapshot scenario forks with live tool-using agents. Models inspect facts and propose actions; deterministic checks enforce permissions, budgets, bank eligibility and atomic settlement. Persistent jobs and ordered events expose progress, saved evidence supports explanations, and transaction keys prevent duplicate postings.

The prototype verifies each branch with ledger invariants and compares outcomes from the same source snapshot and aligned randomness. A 30-branch seed evaluation and downloadable analyst report expose both successful and unsuccessful interventions. Financial correctness, source provenance and model decision quality are kept distinct rather than hidden behind a visualization.

## Three-minute demonstration

1. **0:00–0:35:** State the intended analyst/reviewer workflow and show the live human-approval moment from the existing recording. Name the synthetic scenario setup.
2. **0:35–1:05:** Approve, settle separately and inspect the balanced result. Explain retry protection and bounded model tools.
3. **1:05–1:45:** Show a hypothetical crisis and three calculated futures. Distinguish gross support from net cost. Use actual outcomes, including lack of benefit.
4. **1:45–2:20:** Download and open the comparison report. Show exact outcome differences, snapshot identity, public-source scope and the distinction between ranking and agent decision.
5. **2:20–2:40:** Show all 30 evaluated branches. Contrast the synthetic seed-42 result with the public-reference failures; do not cherry-pick.
6. **2:40–3:00:** State the customer hypothesis and concrete production gates. Do not imply interviews, actual customer savings or authenticated reviewer access have been completed.

Final publishing and event submission remain separate: include the intended current repository, project image and video, add all teammates and select the appropriate categories. No prize selection or submission has been performed by these scripts.
