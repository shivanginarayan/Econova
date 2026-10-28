> **October28update:** The structural operating mismatch below has now been addressed for new economies with versioned cashflow_v2. All20matchedno-shock cases have zero business defaults atday60 and92.5–95%employment, without public support; severe shocks still cause failures. See [the current operating model and480-checkpoint evidence](./OPERATING_MODEL.md). Earlier collapse numbers below are retained as the pre-revision diagnosis, not current default behavior. This does not close human usability validation, empirical calibration, hosting, licensing or final submission requirements.

# Econova priority readiness audit

Checked October 27, 2026 Pacific. Changes in this audit are local and have not been pushed. This assesses readiness; it does not certify the model, user experience, uptime or submission.

## 1. Critical — long-run simulation behavior

**Open. Root cause substantially identified; not fixed by this audit.**

Ran five predefined seeds with synthetic versus frozen public references, no added shock, fragile starting finances, and checkpoints at days6,12,30. Source: [operating-audit.json](./evidence/operating-audit.json). Repeat: `python -m scripts.audit_operating_assumptions --calibration-id <saved-public-id>`.

In seed42, public-reference payroll starts at$5,961.44perday while household spending budgets total$2,813.89, or47.2%ofpayroll. With fixed ten units per worker per day, all eight businesses have maximum potential daily sales of only28.4–35.4%ofpayroll. Even full sales cannot cover wages. This calculation excludes other costs and does not assume the maximum sales actually occur. The no-shock economy is therefore structurally cash-negative. It retains95%employment atday6 but falls to0%byday12 and remains there atday30. Existing banks/borrowing caps can delay deficits, not repair them.

The seeded case differs: spending caps are89.5%ofpayroll, and maximum sales are110.7–161.6%ofpayroll. Seed42 retains95%employment throughday12 and87.5%atday30 without business defaults. This is not proof of equilibrium; different assumptions produce very different dynamics.

The scheduled-settlement correction remains valid as a separate versioned change, but did not solve this operating mismatch. Recommended next implementation: define a coherent unit of output, productivity, household income/spending rule and working-capital budget together; version that operating model; preserve old snapshots; rerun no-shock, supply-limited, borrower-constrained, absorbable-shock and severe-shock cases across seeds and horizons. Do not just increase cash, remove default or tune until a preferred result appears. Keep observed prices/wages separate from any derived assumptions.

Closure evidence should include a stated accounting/budget rationale, version-preservation tests, matched outcomes and sensitivity to the assumed parameters. Long-run stability alone would still not establish empirical accuracy.

## 2. Critical — complete UI experience

**Automated end-to-end functional check passed; unfamiliar-person validation still open.**

A fresh Chrome session completed: introduction, create world,40%shock, six-step observation and explicit ending, business lending evidence, three alternate worlds, deterministic supervised agents and payload inspection, rescue-policy comparison, refresh to introduction/resume and mobile layout. No page exceptions, horizontal overflow or source-world mutation from comparisons/investigation. The deterministic UI run was explicit; separate live checks below cover real NVIDIA/Nebius conversations. Reproducible browser script is local ignored artifacts/submission-prep/qa-full-econova-flow.mjs.

An automated agent can find controls without proving that an unfamiliar person understands them. [FIRST_USER_VALIDATION.md](./FIRST_USER_VALIDATION.md) remains a prepared, unperformed task script. Observe an unfamiliar learner/instructor without narrating answers; record assistance and misconceptions about the40%loss, employment denominator, counterfactual, agent contribution, completion and separate approval. No user interviews or completion-rate claims are established.

## 3. High — representative agent reliability

**Expanded evidence collected; reliability and supervisor correctness not established.**

Seven one-attempt live cases used nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B through Nebius Token Factory: policy without shock, strong-bank80%loss, fragile-bank40%loss, credit with/without cash gap, supplier normal/insufficient budget. No automatic settlement. Seven completed conversations; four reviews passed and three held. No-gap credit correctly did not request a loan; both supplier purchases were declined/held. There was one rejected tool attempt out of33, with32accepted. Every source economy stayed unchanged and accounting audits balanced.

Queue-inclusive observed times ranged14.56–68.09seconds, median37.81seconds. Nearest-rank95thpercentile is68.09seconds, which is simply the maximum of this small sample. These are not model-only performance or a production SLA. Held reviews are not counted as cleared actions or evidence that the reviewer is correct. See [NEBIUS_EVALUATION.md](./NEBIUS_EVALUATION.md) and [agent-reliability.json](./evidence/agent-reliability.json). Repeat `python -m scripts.evaluate_agent_reliability`; it consumes inference and creates isolated worlds.

Still needed: repeated trials rather than one per case, positive supplier acceptance/settlement coverage, human review of recommendation/reviewer correctness, provider/reviewer outage behavior, stale-source guards and inference cost/usage measurements. Existing offline tests cover some guards but do not establish provider reliability.

## 4. High — deployment

**Open. No independently verified hosted application established.**

Current verified application is localhost. A Vercel CLI is available, but an authenticated hosting account, working remote API, persistent storage and funded service availability have not been established. Hosting preference was requested; no choice is inferred from silence. Frontend-only publishing would not supply the Python financial engine or its live inference.

Before external release: choose the host, provide server-side Nebius credentials through its secret store, persistent SQLite storage with a supported single-instance deployment/backup plan, HTTPS and correct API/event routing. Add visitor/world access control and protect live inference and optional external-service endpoints; the current local API is not a production multi-user service and CORS is not authorization. Verify create, automatic public references, model jobs/polling, persistence after restart, isolation, review gates and spending behavior from an external browser. Establish availability for the required judging access period. No external deployment or chargeable service was created in this audit.

## 5. High — branding and submission

**Active product branding updated locally; final materials and release still open.**

Landing, workspace header, loading view, browser title, active plain-language summary, model assumptions, frontend README, root README, API title and current NVIDIA/Nebius drafts now say Econova. Existing browser-storage keys and API identifiers retain their old internal names to preserve saved worlds. Historical Cal Hacks/Parallax guides are explicitly labeled historical. Registered third-party agents keep their actual legacy names; their accounts were not silently renamed.

Frontend96tests and production build passed; eight API tests passed after title change. No new full backend run is claimed for this branding/documentation-only change; earlier full251pass/1skip and later31targetedreset checks remain dated evidence.

Still needed: contributor-approved open-source license and asset rights, publish reviewed changes, current public walkthrough under three minutes, confirmed working test URL/testing instructions, correct model/provider explanation and development history, team/representative details, and final entry review. The draft remains a draft; no submission performed. The public repository snapshot alone does not close these requirements.

## Next decision

The critical engineering work is the operating-model revision. The critical usability work is an observed unfamiliar-person test. Deployment requires the hosting-account choice. The revised branding and evidence can be reviewed now; they do not justify calling all five priorities complete.
