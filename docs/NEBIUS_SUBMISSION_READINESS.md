# Parallax: NVIDIA / Nebius readiness audit

Checked October 26, 2026. Current branch: `parallax-rename-v2`. This is a working checklist, not a completed entry or confirmation of eligibility.

Parallax remains a simulated economy where financial agents investigate bank shocks, negotiate credit, and compare rescue policies.

## October 27 — model credibility work

Implemented versioned scheduled settlement for new worlds, preserving old snapshot rules. Five fixed seeds × two input modes × two financial scenarios × four losses × two settlement versions × three checkpoints yielded480retained observations, with balanced audits and unchanged source snapshots. New standard cases absorb the tested shocks; fragile cases show differentiated short-window outcomes. Public-reference fragile controls still collapse by day12, so no long-run calibration or predictive accuracy is claimed. See [model credibility](./MODEL_CREDIBILITY.md) and [the recorded evidence](./evidence/model-sensitivity.json).

UI exposes model assumptions, legacy-world warning and a no-shock-control reminder. Intended first use is learning/instruction; validation remains pending. [First-user validation prompts](./FIRST_USER_VALIDATION.md) are prepared, not conducted. New live reviewed policy/credit/supplier checks completed with preserved sources; supplier declined/review held. Publishing/license, external access, independent user observation and final materials remain open. No automatic entry or release action performed.

## Earlier release audit — rechecked October 26

**Aligned locally; not submission-ready yet.** Official rules and FAQ were rechecked against the current implementation. The required runtime is already central: NVIDIA Nemotron through Nebius Token Factory powers the multi-step policy, credit and supplier conversations. Serverless Jobs/Endpoints are encouraged, not required for Best Apps and Agents. No economic-model replacement or additional framework is necessary for this fit.

Fresh evidence: three reviewed live workflows completed on October 26. Policy and credit passed supervision; procurement declined and was blocked by the supervisor. All three original economies remained unchanged and all accounting audits passed. These are three observations, not a reliability percentage. See [the current evaluation](./NEBIUS_EVALUATION.md). Twenty-two focused regression cases passed in this audit; the earlier full-suite results below remain historical.

Release gates still open:

- [ ] Confirm one first audience and observe an unfamiliar person completing the investigation task. The audience question is pending; no interviews or product-market validation have been established.
- [ ] Agree an open-source license with contributors, verify asset/integration rights and publish the current reviewed changes. No license was added and no code pushed during this audit.
- [ ] Provide a working hosted URL or independently tested build. For hosting, add visitor/world access control and protect inference/optional external-service routes before exposing the local API. Decide hosting, credentials and availability through December 15 noon Pacific.
- [ ] Test from a clean external browser: introduction, create, shock, consequences, alternate worlds, real live agents, review gate, policy comparison and explicit action confirmation; verify restart persistence and automatic public input behavior.
- [ ] Finish the fresh under-three-minute public YouTube video, English description, testing instructions, provider feedback and accurate development history. Review [the submission draft](./NEBIUS_ENTRY_DRAFT.md).
- [ ] Confirm eligible team/representative and review the final entry before submitting by October 30, 10 AM PDT.

Recommended implementation order: audience/task choice, release access design, public licensed build, external end-to-end verification, final media and entry. Existing finance/credit/supplier logic stays intact. The broader six-case live evaluation described below is still unfinished; the new smoke check covers three bounded live workflows plus existing offline regression tests.

## 1. The event fit

Recommended track: **Best Apps and Agents**. This is an agent-powered financial workflow, rather than a coding tool, personal assistant, or robotics system.

The [official FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs) confirms that NVIDIA inference through Token Factory is sufficient; the frontend and unrelated processing can live elsewhere. The [overview](https://nebiusglobalaihackathon.devpost.com/) encourages Serverless Endpoints and Jobs for this track but does not require them. Migrating the whole simulation to a GPU service would need a product or operational reason.

The [judging update](https://nebiusglobalaihackathon.devpost.com/updates/46204-here-s-how-judging-works) favors multi-step workflows over a single model call. Technology, design, impact, and the idea are equally weighted. Technical depth alone does not establish product value.

## 2. Official submission checks

From the [official rules, sections 1, 3, 4 and 5](https://nebiusglobalaihackathon.devpost.com/rules):

- Deadline: October 30, 2026, 10 AM PDT.
- Runtime: Nebius plus an NVIDIA open model.
- Access: working URL/test build, free judging access through December 15, 2026, noon Pacific; private access needs testing credentials.
- Source: public repository, open-source license, complete assets and setup instructions.
- Materials: English description, selected track, public YouTube demonstration under three minutes, tool feedback, and applicable prior-project improvement explanation.
- Team: confirm eligibility, representative, ownership and integration rights.
- Submit all required fields before the deadline; substantive post-deadline entry edits are restricted.

The physical-hardware footage provision belongs to Physical AI. It is not our selected track. Keep submission claims aligned with the working build and record the submitted commit.

## 3. NVIDIA and Nebius already power the central work

The actual model adapter is [provider.py](../backend/provider.py). It calls Nebius Token Factory chat completions with structured function tools. The verified model is `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. The key stays server-side in private configuration.

The policy workflow in [agents.py](../backend/agents.py) separates an investigator, a policy planner, and a supervisor for new reviewed UI jobs. The investigator captures financial evidence. The planner receives that evidence and tests interventions using the simulation. It must recommend an outcome actually returned by a tool. The supervisor makes an independent model call against the recorded evidence.

The credit workflow in [credit_agents.py](../backend/credit_agents.py) uses business and bank roles. The business identifies a payroll need, the bank assesses the proposed financing, and the business reviews the exact offer. A supervisor then reviews the exchange. The procurement workflow in [procurement.py](../backend/procurement.py) uses a buyer and two supplier instances to quote, negotiate and select terms before supervisor review.

These are separate bounded conversations with distinct tools or contexts, using the same configured model. They are not separately trained models. They run when requested; they are not a continuously scheduled autonomous population. The supervisor performs a final independent review, while deterministic handlers validate each tool call during execution.

[coordination.py](../backend/coordination.py) records the handoffs and checks evidence. Reviewed workflows cannot apply or settle unless supervision passes. A failed model call does not silently become a successful deterministic result. The deterministic mode is explicitly labeled.

[AgentCollaboration.tsx](../apps/web/src/ui/AgentCollaboration.tsx) shows the actual active role, saved exchanges, tool requests and responses, and review result. A user can select a handoff and inspect its data. Main outcomes use percentages and percentage-point differences. This makes the model's contribution inspectable rather than an invisible explanation attached to a chart.

The financial engine remains deterministic. It calculates balances, checks counterparties, and runs comparable futures. This is deliberate: the model chooses and interprets permitted actions; it does not invent accounting results or change balances through prose.

## 4. What has been verified

Historical live checks established policy, business/bank credit, and supplier model calls through Nebius. [NEMOTRON.md](./NEMOTRON.md) records the model setup and their limits.

On October 26 a fresh live reviewed policy run exercised investigator, planner and supervisor roles. The planner proposed bank lending. The supervisor held the result, questioning whether liquidity support addressed insolvency. The source economy stayed unchanged. An application attempt returned HTTP409, and the browser action was disabled. We retained the disagreement rather than rerunning until the model agreed.

That example establishes a functioning review gate, not that the supervisor is always right. Its prose can be imperfect. Independent model critique and deterministic financial checks are different forms of evidence.

Current automated evidence: full active backend suite 227 passed / one optional skip; frontend 80 passed; production build passed. An additional race regression was then added, and the final coordination-specific suite passed all 11 cases. Do not describe the earlier full-suite count as a rerun including that extra case. The race check verifies that publishing the passed review cannot later overwrite a concurrent approval or settlement.

Chrome checks covered real recorded handoffs, selected payload inspection, following the latest exchange, automatic focus on active work, mobile overflow, no automatic settlement, and no page exceptions. The final live block was also checked in Chrome and through the API. Private local evidence lives in ignored artifacts; those files are not yet a published, reproducible evidence package.

## 5. Important unfinished work

### Publish a current and correctly licensed source version

The UI redesign and supervisor implementation are local working changes. The remote branch does not yet contain them. No tracked project license was found. The submission source therefore is not ready yet.

Choose the intended license with the contributors, check third-party asset rights, then publish the reviewed code. Do not license collaborators' work without agreement. Keep provider keys, account-specific CRS information, private datasets and runtime databases out of the repository. Use a fixed source commit for testing and the recorded walkthrough.

### Provide remote access to the actual product

The verified application currently runs on localhost. No working hosted Parallax URL or independently tested downloadable build has been established in this audit.

Recommended path: a hosted web UI and API with persistent storage and server-side Token Factory credentials. Add isolated visitor sessions/worlds and protect expensive model-job routes before exposing the current local API. The current API has no production authentication or per-user isolation; CORS is not access control. Infrastructure safeguards should not deprive judges of the promised working workflow.

Check HTTPS, API routing, job polling, model access, persistence across restarts, automatic source loading, and a fresh user's ability to finish an investigation. Test in a clean browser outside the developer's machine. Arrange sufficient hosting and inference availability for the required access period. Serverless infrastructure is an implementation choice, not a checkbox to add without need.

### Define and validate the first user

The current README names bank-risk analysts and credit officers as intended users. That is an unvalidated audience hypothesis. A working prototype does not establish that banks will supply data, that their controls permit it, or that the model represents their operations.

Select one first audience and one task. Candidate audiences are financial simulation researchers, finance instructors, or risk teams using hypothetical cases. This choice is pending user input. Keep the core economy/agent project whichever audience is selected.

Proposed task to validate: investigate why a bank investment loss interrupts credit and payroll, compare the available responses, and retain an inspectable explanation of the decisions. Run that task with a representative user who has not seen the project. Observe where they hesitate and whether they can explain the result without narration. Record consented feedback and actual observations. Do not invent interviews or claim measured savings without a study.

The default case needs no private bank data. That removes a dependency for using the current simulation, but does not make the case calibrated to an actual bank. A future confidential-data version would require a separate data/access design.

### Show why agents help

The comparison engine can rank simulated futures without AI. The case for agents should therefore be their multi-step investigation, credit/supplier negotiation, explanation of tool evidence, and independent challenge to a proposal. Do not say that the model alone calculates the financial outcomes.

Before freezing the build, evaluate several defined cases: a bank that absorbs a shock, an insolvent bank where liquidity has limits, a payroll financing gap, an unaffordable supplier offer, a stale source, and an unavailable reviewer. For each, retain tool validity, final status, accounting audit, mutation/approval behavior, wall-clock latency and observable failures. Report model reliability honestly rather than promising universal correctness. This evaluation package is planned, not already completed by this audit.

### Prepare materials for this version

The Cal Hacks video describes an older build. A new walkthrough should show the percentage-led workspace, an actual multi-step live agent investigation, an exchanged payload, supervisor findings, and compared outcomes. A supervisor holding a result is valid product behavior; avoid editing it into an apparent approval.

Write a short architecture explanation connecting the user task to the agents, Token Factory calls, simulation tools, review gate and explicit action confirmation. State the exact model and provider. Describe the changes made during the eligible period using accurate dates and commits. Do not imply all work was newly created for this event.

Feedback can describe observed tool-calling setup, thinking/output limits, prerequisites and rejected monetary arguments, without unsupported throughput claims. Existing feedback is preserved below. Final media, testing links, team details and completed entry remain unverified. No automatic submission is authorized.

## 6. Order of work

1. Confirm the first audience and task; test it with a representative person.
2. Finish the small, defined live evaluation set and any material defects it reveals.
3. Confirm license and asset rights, and publish the intended build.
4. Deploy/provide the working build, isolate users, and verify external access and funding.
5. Record the current product, finish the written materials and review the exact links.
6. Complete this event's entry after user review and verify its final status.

Adding Tavily, another NVIDIA framework, a larger model, or additional Cal Hacks integrations is not the present critical path. Use them only for a demonstrated need. The current bottlenecks are coherent usefulness, credible evidence and access to the working build.

## 7. Observed developer feedback draft

Token Factory's chat-completions interface fit the existing tool-oriented backend. Nemotron produced real function calls without replacing the financial engine. In an earlier bounded workflow, enabled thinking could consume the output budget before a tool call; disabling thinking allowed completed calls with the selected configuration. This is an observed behavior, not a comparative performance benchmark.

We also observed repeated attempts to decide credit after an invalid assessment. Financial guards prevented mutation; prerequisite-based tool availability improved the conversation. Examples of bounded tool execution, rejected prerequisites and recoverable integer-cent errors would help builders of financial workflows. The new supervisor review exercises another independent tool-only context and preserves disagreements instead of silently substituting a scripted answer.
