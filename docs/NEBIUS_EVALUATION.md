# Current NVIDIA / Nebius workflow checks



Checked October 26, 2026, against the local working tree on parallax-rename-v2. These changes are not yet published as a fixed commit.



## Configuration and method



Model: nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B through Nebius Token Factory. Each request used live mode and agent_review=true. Each workflow received an isolated synthetic economy, with automatic settlement disabled. No existing user economy was changed. Source JSON was compared after investigation and ledger/counterparty audits were checked.



The supplier case uses supply_crunch; the other two use standard. Credit deliberately transfers the test business’s cash to another test business before recording the starting snapshot, creating a financing gap. These are controlled synthetic cases, with no new public collection, CRS pull or external payment requested by the runner.



## Observations



### central_bank

Job: job_bca73ef6022a48fa8006ce9a3605d565. Run: agent_10007c34c91f4ac8a1700dffb40d40a0.

Workflow: completed; report: completed; independent review: passed.

Recorded tool calls: 3; activity events: 9; participants: investigator, policy, supervisor.

Observed elapsed time: 8.78 seconds, measured from before queue submission to terminal polling; includes queueing and polling, not a model-only latency benchmark.

Source unchanged: True. Audit balanced: True.



### credit

Job: job_a5248c845cd24915bacc5d3ec58e8535. Run: credit_d1a89e2351e645e2ac350269d852fc89.

Workflow: completed; report: approved; independent review: passed.

Recorded tool calls: 7; activity events: 15; participants: bank, business, supervisor.

Observed elapsed time: 22.06 seconds, measured from before queue submission to terminal polling; includes queueing and polling, not a model-only latency benchmark.

Source unchanged: True. Audit balanced: True.



### procurement

Job: job_d02004bd38b248bab99bcebb759f5165. Run: supply_6899a5dc09e04d048a4f5338104e6c21.

Workflow: completed; report: declined; independent review: blocked.

Recorded tool calls: 6; activity events: 14; participants: business_2, business_3, buyer, supervisor.

Observed elapsed time: 29.0 seconds, measured from before queue submission to terminal polling; includes queueing and polling, not a model-only latency benchmark.

Source unchanged: True. Audit balanced: True.



## Interpretation and remaining limits



Policy and credit returned passed reviews. Supplier negotiation declined, and the supervisor blocked its result while questioning whether budget failures were represented consistently. Deterministic checks passed. A check confirming that a selected offer is valid can pass when no offer is selected; this does not mean every quoted offer was affordable. The model critique is not proof of an accounting defect or proof that the supervisor is correct. No action was applied in these live checks.



A completed workflow means the bounded conversation produced a terminal report; it does not mean a purchase was accepted, a policy was applied or every review passed. No attempts were rerun to obtain a preferred verdict. Three runs cannot establish general reliability. Absorbable versus insolvency shocks, stale-source and unavailable-reviewer behavior still need a defined live evaluation set; offline guards cover some of these paths.



Focused regression verification in this audit: 22 passed across test_coordination.py, test_alternate_scenarios.py and test_business_evidence.py. The review suite includes held/unavailable supervision, deterministic check failures, no premature publication and separate settlement gates. Offline tests use controlled test models; they are not additional NVIDIA inference runs.



## Repeat



Start the configured local API, then run `python -m scripts.smoke_live`. This consumes live inference and creates three new isolated test economies. It writes the latest summary to ignored data/live-smoke-report.json. It succeeds only when all jobs complete, supervision reaches passed/blocked, activities exist, sources are unchanged and audits balance. Failed or timed-out jobs remain reported; they do not silently become deterministic successes.



Raw local report contents and account configuration are not part of this document. Preserve the current evidence before repeating, because the runner replaces the latest summary.


## October 27 — revised settlement model

Fresh isolated standard/supply cases used scheduled_liquidity_v2. These live runs verify integration, not severe-shock outcome accuracy. All sources stayed unchanged and all audits balanced. No financial action was settled.

- central_bank: workflow completed; report completed; supervisor passed; 4 tool calls; 10 activity events; 25.44 seconds including queueing/polling. Run agent_04a67c7366764b33bf1a5788d10fce5b.
- credit: workflow completed; report approved; supervisor passed; 7 tool calls; 15 activity events; 35.69 seconds including queueing/polling. Run credit_72a207b55ec8441795c066300430cb73.
- procurement: workflow completed; report declined; supervisor blocked; 6 tool calls; 14 activity events; 57.23 seconds including queueing/polling. Run supply_ac5bb9a171544f7ca636d0eba17a16f5.

No reruns were made to obtain preferred verdicts. A held supplier result remains a held result. The broader model sensitivity evidence is in [MODEL_CREDIBILITY.md](./MODEL_CREDIBILITY.md).


## Seven representative live cases — October 27 Pacific

Three policy cases (no shock, well-capitalized80%loss, fragile40%loss), credit with/without a cash gap, and supplier normal/insufficient budget. All use frozen public references, live Nemotron/Nebius, independent review and no automatic settlement. Seven terminal completions; four reviews passed and three were held. Policy fragile and both supplier cases were held. Credit with no gap correctly ended not_requested. One invalid tool attempt was rejected;32accepted/33totaltool calls. None of these statuses implies the supervisor was necessarily correct.

Queue-inclusive median37.81seconds; empirical nearest-rank95thpercentile68.09seconds (the maximum in this seven-case sample). These are local service observations, not model-only latency or a reliability SLA. Every source stayed unchanged and every audit balanced. No reruns to obtain preferred outcomes. Machine-readable case evidence: [agent-reliability.json](./evidence/agent-reliability.json). Reproduce with `python -m scripts.evaluate_agent_reliability`; it consumes live inference and creates seven isolated worlds.


## October28cashflow_v2 live checks

Seven representative live cases rerun once against the revised model; all completed, with3passed and4heldreviews. The no-gap credit case correctly requested no loan but its review was held after one rejected tool attempt. Both supplier cases declined/held. The fragile policy was also held. These are observed outcomes, not proof of review correctness. Every source stayed unchanged, every audit balanced and no funds were automatically settled. Queue-inclusive median24.45seconds; nearest-rank95thpercentile38.91seconds (sample maximum). Timing is not a comparative performance claim. See [the exact case record](./evidence/agent-reliability-cashflow-v2.json).
