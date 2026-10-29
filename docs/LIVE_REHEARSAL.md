# Live Nemotron rehearsal and hosting status

Checked October 28, 2026. Latest verification: the supplier HTTP400 history defect is fixed, all seven post-fix live cases completed, and the full backend suite passed299tests with one optional skip. External deployment is still pending an accessible hosting account.

Core product: a simulated economy where financial agents investigate bank shocks, negotiate credit, and compare rescue policies.

## What is verified

A fresh Chrome session used the built UI and a separate deployment-style API with real NVIDIA Nemotron inference through Nebius Token Factory. It created a dated FDIC/Census experimental economy, applied an investment shock, followed consequences, ran the investigator, policy planner and supervisor, opened the handoff evidence and compared rescue policies. The original world remained unchanged. The latest run completed with a supervisor hold; attempting to apply that held recommendation returned HTTP 409. This is a completed investigation with a held recommendation, not an approved rescue.

Separate visitors could not read each other's worlds. Refresh/resume worked. A service restart preserved the world and signed visitor access. The mobile viewport had no horizontal overflow or browser exceptions. This is automated browser verification, not an unfamiliar-person usability study. See [the browser record](./evidence/hosted-live-ui.json) and [restart record](./evidence/hosted-restart.json). The [final revision restart check](./evidence/hosted-final-restart.json) also passed after the supplier fix.

Nemotron supplies the investigation tool calls, policy proposal and supervisory assessment. The deterministic simulation computes balances and consequences; it does not outsource accounting to the language model. Stage-specific tools expose actual caps, observed comparison IDs and integer-cent amounts. Review sees the request limits and selected-offer budget checks. Review occurs before settlement; an unexecuted proposal is expected. Human approval and settlement guards remain in place.

## Representative cases and resolved protocol failure

All live batches are retained separately. They used the same seven case definitions: control, absorbed investment loss, fragile investment loss, payroll credit gap, no credit gap, unaffordable supplier request and ordinary supplier request. No automatic settlement was requested. These small, sequential development batches are not a statistical reliability estimate.

1. [Initial batch](./evidence/agent-working-capital-initial.json): five completed, two failed. It exposed transient provider availability, monetary-unit mistakes and supplier tool protocol problems.
2. [Stage-tool batch](./evidence/agent-working-capital-stage-tools.json): seven completed, one review passed and six held. The holds exposed ambiguous review evidence and unsupported claims. Completion alone did not mean correctness.
3. [Review-scope batch](./evidence/agent-working-capital-review-scope.json): five completed and two failed. The planner repeated invalid calls; a supplier returned no function call. Three reviews passed and two held.
4. [Targeted policy/supplier check](./evidence/agent-working-capital-targeted.json): policy completed with review held; supplier failed with an invalid call batch.
5. [Targeted protocol-correction check](./evidence/agent-working-capital-protocol-correction.json): supplier still failed, with provider HTTP 400 after a rejected inspection call. The underlying HTTP validation cause was unresolved at that checkpoint; the later reproduction below identifies it. No financial action was applied; the source remained unchanged and accounting balanced.

The provider retries at most three times only for explicit transient HTTP rejection statuses. It never retries settlement, timeouts or successful financial tool execution. Supplier batches containing more than one call are rejected as a whole before handlers execute, with visible rejected traces and correction allowed only within the existing six-turn bound. Duplicate call IDs fail before execution. There is no deterministic substitute presented as a live model answer.

The supplier HTTP400 was reproduced independently: including a previous malformed JSON argument string in the next request makes Nebius reject the conversation before a correction can occur. Supplier sessions now record the rejected attempt and use a plain protocol-error message for the next bounded turn. No handler executes for malformed JSON or multi-call batches. This also fixes the prior behavior that could accept a terminal decision while silently skipping subsequent conflicting calls in the same batch. Duplicate IDs and malformed envelopes still fail closed.

A [real-provider recovery probe](./evidence/agent-malformed-json-recovery.json) injected one malformed call, then let real Nemotron correct it. The trace recorded two rejections and one acceptance; the inspection handler executed once and no financial handler ran. The extra rejection was retained.

The [post-fix seven-case batch](./evidence/agent-working-capital-json-history-fixed.json) completed all seven workflows: three reviews passed and four were held. Credit with a payroll gap produced an approved proposal; ordinary supplier procurement produced a ready offer. The unaffordable supplier case was declined. All source worlds stayed unchanged and audits balanced. Queue-inclusive times were13.22?62.08seconds, with median37.39seconds; these are local observations, not a service guarantee. Earlier failed batches remain above. This closes the reproduced protocol failure, not general model correctness or a statistical reliability claim. Supervisor holds remain binding.

## Hosting preparation and remaining deployment work

The [hosting guide](../deployment/README.md), [container build](../Dockerfile), persistent startup script and public-input bundle are prepared. Hosted mode protects UI/API access, scopes worlds and derived resources by signed visitor cookie, limits costly jobs and simulation requests, disables optional private integrations and preserves data across restarts. Source observations are dated and cached; this build does not automatically spend Apify credits. Local development is unchanged unless hosted mode is enabled.

The runtime was tested on loopback port 8001. It is not an external application URL. Docker was not available locally, so the container image has not been built or deployed. Hosting provider/account selection is pending from the user. The real deployment still needs a persistent volume, server-side Nebius secrets, stable access/session secrets, HTTPS, an image build, independent external access and restart checks, and hosting/model credit coverage for the required availability period.

No license, video upload, hackathon submission, commit or push was performed in this rehearsal. Public FDIC/Census calibration remains experimental because financing sensitivity still has failed acceptance cases; the deployment work does not promote it.

## Regression checks

The final full backend suite passed299tests with one optional skip. The supplier/tool-loop targeted suite passed21tests. The bare pytest command also discovered preserved teammate preview checkouts under ignored artifacts; the correct full-suite command is `python -m pytest tests -q`. No preview files were modified. The current frontend suite passed96tests using `npm test -- --exclude artifacts/**`, which excludes preserved teammate previews. The frontend build passed with the existing bundle-size warning. Container image build and external checks remain pending.
