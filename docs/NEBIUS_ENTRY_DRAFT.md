# Parallax — NVIDIA / Nebius entry draft

Working draft for owner review. No entry has been submitted by this work. Audience, published commit, license, test URL and video URL remain to be confirmed.

## Project description

Parallax is a simulated economy where financial AI agents investigate bank shocks, negotiate credit and compare rescue policies. A bank’s loss can affect its ability to lend. A business may then struggle to finance payroll, affecting its workers and production. Parallax lets a user inspect these connections and compare possible responses in one interactive workspace.

The user chooses a hypothetical bank investment loss. The simulation calculates the financial consequences. Charts show employment, bank stress and business defaults as percentages, and individual business views explain recorded credit decisions. Alternate worlds compare different losses from the same saved state. Rescue comparisons test different responses after a shock.

The AI workflow has visible responsibilities. An investigator gathers financial evidence and hands it to a policy planner. The planner tests permitted interventions using simulation tools. An independent supervisor reviews the recorded work and may hold the recommendation. The user can inspect the exchanged data and decides separately whether to apply support. Business and bank agents also negotiate credit, while buyer and supplier agents negotiate purchases.

## NVIDIA and Nebius use

Live agent conversations use nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B through the Nebius Token Factory chat-completions API. The provider runs on the backend, with credentials kept server-side. Distinct agent conversations receive their own responsibilities and tool access; these are not separately trained models.

Nemotron chooses permitted tools, considers their results and proposes actions. The deterministic simulation calculates balances and comparable futures. Financial checks validate tool calls, while the supervisor supplies a separate model review. Failed live calls remain visible. Deterministic mode is a separately labeled option.

Token Factory supports the central multi-step workflow, including evidence gathering, experiments, negotiation and review. The frontend and simulation do not need GPU execution to perform their tasks. No Nebius Serverless deployment is claimed in this build.

## Intended task and users — pending owner choice

Proposed first task: investigate why a hypothetical bank loss interrupts business credit and payroll, compare responses, and inspect the evidence behind a recommendation.

Proposed first audience: finance students and instructors exploring financial contagion through controlled cases. This is a positioning proposal awaiting owner confirmation, not a validated customer claim. No private bank data is required for the existing synthetic cases. The project’s financial agents and simulation remain the same whichever first audience is selected.

## Model evidence and limits

A defined sensitivity set now compares two settlement-rule versions, five seeds, public versus synthetic price/wage references, strong versus fragile banks, four loss severities and three horizons. All480checkpoint audits balanced and source worlds remained unchanged. In the seed42 public-reference fragile case, the revised six-day comparison showed95%employment without the additional loss and35%with a40%loss. These are model observations, not real-world employment estimates. Longer fragile public-reference controls still deteriorate to0%employment by day12. No general realism or forecast-accuracy claim is established by this evidence. See [the full record](./MODEL_CREDIBILITY.md).

## Development history

Parallax was previously developed for Cal Hacks. Work on October 26 added a Nebius-focused supervised agent workflow and visible handoffs, percentage-led charts and focused views, business credit evidence, alternate shock worlds and a descriptive introduction. Earlier work already provided the financial simulation and other integrations. The exact source history and final published commit must be checked before copying this section into the entry; do not describe all work as newly created for this event.

## Observed developer feedback

Token Factory’s chat-completions interface fit our existing tool-based backend. We used structured function calls to connect Nemotron to financial evidence and simulation experiments. With the selected bounded configuration, enabled thinking sometimes used the output budget before a function call was returned. Disabling thinking allowed completed tool calls. This is a setup observation, rather than a comparative performance benchmark.

We also observed invalid attempts to make credit decisions before prerequisites were satisfied. Deterministic checks prevented those actions, and exposing tools only after prerequisites helped the workflow. More financial tool-calling examples covering integer cents, invalid inputs and recoverable failures would be useful.

## Suggested walkthrough — under three minutes

1. Introduce the question: a bank loses money; which businesses and jobs are affected, and which response helps?
2. Create a synthetic economy, apply a hypothetical loss and follow consequences. Show the percentage charts and one recorded credit rejection.
3. Request a live investigation. Show the Nemotron/Nebius mode and the actual investigator-to-planner handoff, tool evidence and independent review.
4. Compare rescue outcomes. Explain the distinction between comparing a response and applying it. If a review holds a recommendation, show the hold accurately.
5. Briefly show alternate shock worlds and close with the use case. Keep supplier negotiation as an additional capability if time permits.

Record actual application behavior. If model work takes longer than the recording window, label an elapsed-time cut and retain the same run; do not present prerecorded results as a new live response.

## Final fields to complete

- Chosen audience and observed user feedback.
- Public source URL, agreed license and exact submitted commit.
- Working application/test-build URL and testing instructions. State any required login and provide access in the entry’s intended testing fields.
- Public YouTube URL for the current version, under three minutes.
- Team and representative confirmation.
- Final verification date, external test result and availability plan through December 15, 2026, noon Pacific.

Requirements: [official rules](https://nebiusglobalaihackathon.devpost.com/rules), [FAQ](https://nebiusglobalaihackathon.devpost.com/details/faqs), [judging guidance](https://nebiusglobalaihackathon.devpost.com/updates/46204-here-s-how-judging-works). Checked October 26, 2026. Best Apps and Agents is the recommended track. Final submission remains subject to owner review.
