# Live Nemotron integration

The backend is configured locally for `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` through Nebius Token Factory. Its availability was discovered from the authenticated `/models` API, and real function calling was verified. The account key lives only in the ignored root `.env`; it is not needed by the browser.

## Start

```powershell
.\.venv\Scripts\python.exe -m scripts.run_backend --reload
```

The launcher reads `NEBIUS_API_KEY`, `NEBIUS_MODEL`, `NEBIUS_BASE_URL` and the supported economy settings from `.env`. Existing shell values take precedence. The default API base is `https://api.tokenfactory.nebius.com/v1`. To rotate the key, replace the private `NEBIUS_API_KEY` value and restart this command. Do not put it in a Vite variable.

Start `npm run dev` in another terminal and open http://127.0.0.1:5173. Create or reload a world. The UI selects live mode when `/api/agents/status` reports configured credentials/model, displays the model ID, and labels the resulting report provider/model. Deterministic demo remains a separate explicit choice. There is no automatic demo fallback after provider failure.

## Verified behavior

A real single-function probe succeeded. Full live workflow checks then completed with:

| Workflow | Result | Public tool calls |
| --- | --- | --- |
| Central-bank analysis | Completed, with a tested recommendation | 3 |
| Business/bank credit | Approved financing; awaiting explicit settlement | 7 |
| Supplier procurement | Declined; no financial settlement | 6 |

All three world audits were balanced. These are observed results from a small live check, not a guarantee that every model run recommends support or accepts a contract. Supplier roles have also returned valid selected terms in a separate live check. No automatic settlement was requested during these provider checks.

Nemotron requests use function tools, a bounded 4,096-token output, and `chat_template_kwargs.enable_thinking=false`. The initial default-thinking configuration sometimes consumed its output without reaching a function call; the corrected setting was verified through actual economic workflows. Every live role receives explicit integer-cent instructions and is asked to keep monetary rationales qualitative; exact amounts are rendered from verified backend fields. Hidden reasoning is not persisted. Validated observations, accepted/rejected tool calls, public rationales and computed outcomes remain inspectable.

## Repeat checks

```powershell
.\.venv\Scripts\python.exe -m scripts.check_nebius
.\.venv\Scripts\python.exe -m scripts.check_nebius --probe
.\.venv\Scripts\python.exe -m scripts.smoke_live
```

Discovery prints only model IDs. The probe makes one real tool-call request. The workflow smoke check creates separate local worlds and queues all three live workflows with automatic financial settlement disabled; it writes a non-secret summary under ignored `data/`. Live checks consume inference usage. Failed runs remain failed and inspectable; they are not silently retried with another model.

Applying recommendations and settling accepted loans/contracts still require the existing explicit UI actions, unchanged-snapshot checks and exactly-once ledger receipts. See [the connected UI guide](./UI_INTEGRATION.md), [central-bank workflow](./CENTRAL_BANK_AGENT.md), [credit workflow](./BUSINESS_BANK_AGENTS.md) and [supplier workflow](./SUPPLIER_PAYMENTS.md).

Reference: [Nebius's official Nemotron catalog](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference). External x402 and real-money settlement are not part of this integration.


## October 26: independent review and visible handoffs

New jobs from the UI request `agent_review: true`. Policy analysis uses an inspection-only investigator, a fresh planner context receiving its evidence, and an independent supervisor context. Credit retains business/bank/acceptance conversations plus supervision; procurement retains buyer/two suppliers plus supervision. The same configured NVIDIA model serves these distinct conversations through Token Factory. See [coordination](../backend/coordination.py) and the [event readiness audit](./NEBIUS_SUBMISSION_READINESS.md).

The interactive workspace shows the actual active role, timestamped handoffs and selected tool request/response data. Supervisor review checks the recorded result after the worker agents finish; deterministic handlers validate every tool call. New reviewed workflows cannot apply or settle until review passes. AI criticism can still be imperfect and does not replace accounting checks.

A bounded live investigator/planner/supervisor policy run completed on October 26. The supervisor held the proposed bank-lending response; the source economy remained unchanged, and the API rejected an application attempt with HTTP409. The UI also disabled the action. This verifies a real disagreement and enforced gate, rather than guaranteeing that recommendations or critiques are correct. No financial action was applied. Existing API callers keep explicit opt-in compatibility; deterministic mode remains separately labeled.
