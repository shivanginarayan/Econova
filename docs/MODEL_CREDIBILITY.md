> **October28update:** The structural operating mismatch below has now been addressed for new economies with versioned cashflow_v2. All20matchedno-shock cases have zero business defaults atday60 and92.5–95%employment, without public support; severe shocks still cause failures. See [the current operating model and480-checkpoint evidence](./OPERATING_MODEL.md). Earlier collapse numbers below are retained as the pre-revision diagnosis, not current default behavior. This does not close human usability validation, empirical calibration, hosting, licensing or final submission requirements.

# Model credibility and remaining validation

Checked October 27, 2026. Local working changes; no published release commit yet.

## Product and intended use

Econova remains a simulated economy where financial agents investigate bank shocks, negotiate credit and compare rescue policies. The first intended task is helping finance learners/instructors follow a bank loss into recorded lending/payroll problems and compare responses. This is a proposed audience, not demonstrated customer demand. No private bank data is needed for the synthetic task.

## Defect addressed

The previous scheduled interbank clearing protected the entire deposit balance out of liquid resources at maturity, even when customers had not requested withdrawals. With frozen public references and fragile starting banks, that could trigger a network-wide credit stop on day5 and complete business failure by day6 without an additional shock. Existing seeded-only regression cases did not cover this input combination.

New economies carry settlement_model=scheduled_liquidity_v2. Solvent banks retain a ceiling-rounded10%deposit liquidity buffer while making scheduled interbank payments; insolvent banks retain the earlier full-deposit protection assumption. The clearing algorithm, integer-cent journal, reciprocal claims and explicit approvals remain. Recorded risky assets may be converted at their current carrying value for net payments. This is a simplified going-concern settlement assumption, not a complete bank-resolution or depositor-protection framework.

Old states without the version marker retain full_deposit_protection_v1. Comparisons clone and inherit the source state version. The UI flags earlier saved economies instead of silently changing them. New/current versions are exposed in world responses and model assumptions. No old balances or results were rewritten.

## Matched experiments

The evaluator runs both settlement versions; seeded and one frozen public input sample; standard and credit_crunch; seeds41–45; losses0%,10%,40%,80%on Bank1riskyassets; checkpoints3,6,12days. That is160branches and480checkpoint observations. Every checkpoint audit balanced, with source snapshots unchanged. All outcomes, including identical and deteriorating controls, are retained in [the machine-readable evidence](./evidence/model-sensitivity.json). No model calls or fresh data collection occur in this evaluator.

Frozen input identity: {'id': 'sf_public_20261027_213300_75f87b', 'sha256': 'e16508b555915d13dea9e06e382669b465bbcdbce304bc680325ddfe45e49fe7', 'collected_at': '2026-10-27T21:33:00.793236+00:00'}.

For seed42 with the frozen public sample in the fragile scenario, the revised model produced:

- Day6, 0%loss: 95.0%employment, 0business defaults.
- Day6, 10%loss: 57.5%employment, 3business defaults.
- Day6, 40%loss: 35.0%employment, 5business defaults.
- Day6, 80%loss: 35.0%employment, 5business defaults.
- Day12, 0%loss: 0.0%employment, 8business defaults.
- Day12, 10%loss: 0.0%employment, 8business defaults.
- Day12, 40%loss: 0.0%employment, 8business defaults.
- Day12, 80%loss: 0.0%employment, 8business defaults.

Across all five seeds at day6, revised well-capitalized cases retained95%employment for all tested loss severities. Revised seeded fragile controls retained95%;10%loss cases ended70–72.5%;40%and80%cases ended35–62.5%. Public-reference fragile no-shock controls ranged70–95%;10%loss47.5–57.5%;40%and80%35–57.5%. These ranges are a small, predefined sensitivity set, not statistical confidence intervals. A larger shock need not produce a different endpoint once a modeled bank has crossed the same failure threshold.

## Important remaining weakness

At day12, all five fragile public-reference no-shock cases still end at0%employment. The scheduled-settlement correction does not solve longer-run operational viability. Public wages/prices combined with fixed production, spending, borrowing caps and compressed default rules can produce systematic deficits. Short-window stability cannot be presented as evidence of a sustainable or calibrated long-run economy. The standard scenario stays employed through the tested horizon, but this also is not an equilibrium proof.

Do not increase buffers, sales or productivity solely until a chosen story wins. A future operating-model revision needs a coherent stated budget/production rationale, versioned assumptions and renewed controls. Current UI tells users to inspect no-additional-loss results and exposes limitations.

## What this evidence establishes

Repeatability, accounting consistency, preservation of source worlds, and differentiated outcomes across bank strength/shock scenarios. It does not establish empirical accuracy, predictive probability, appropriate real bank policy, fairness or customer value. Independent model supervision is another review layer, not proof of financial correctness.

## Reproduce

Run `python -m scripts.evaluate_model_readiness` for synthetic-only checks. To include a locally available frozen public sample, run `python -m scripts.evaluate_model_readiness --calibration-id <saved-public-id>`. Missing/invalid selected public samples fail explicitly. Output defaults to ignored artifacts/model-readiness. The recorded evidence above is from the stated frozen sample; a newer collection may yield different outcomes.

Run `python -m pytest tests` and `npm test -- --exclude "artifacts/**"`, then `npm run build`. The new settlement regression suite covers legacy replay, full scheduled settlement at solvent banks, reserve conservation, exactly-once behavior, five seeded matched controls and five public-fixture well-capitalized controls. Test fixture observations are explicit and are not passed off as fresh live data.

## Release gates still open

Observe an unfamiliar representative user completing one investigation and explaining it without narration. Agree contributor licensing and asset rights, publish the tested commit, provide protected external access and verify it independently, rerun relevant live agents on the released build, finish the current public walkthrough/testing instructions and review the final entry. These steps are not completed by model tests.

## Verification on October 27

Full active backend suite passed251tests/1optional skip after the settlement correction and test updates. Frontend96tests/16files and production build passed (existing bundle-size warning). A subsequent reset-version/original-anchor correction passed31targetedtests covering settlement, playback and alternate worlds, including two additional reset-version cases; do not treat251as a full rerun including those two newer cases. Chrome verified new public-input world version, matched95%no-loss versus35%40%-loss employment atday6, unchanged source, accessible assumptions and mobile nooverflow/noexceptions. Live policy/credit/supplier checks on new worlds all completed and balanced; policy/credit passed review, supplierdeclined/reviewblocked. No funds applied.

Reset preserves the source settlement version and atomically stores a fresh original scenario-comparison anchor. Ordinary New experiment uses the revised version. The local API was restarted with the final compatibility fix. Code remains uncommitted and unpublished.
