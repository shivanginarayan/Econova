# Economy God Mode — Fetch.ai ACP agent

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

The agent retrieves sourced city context and performs bounded financial stress testing in our synthetic economy. It does not transfer real money or apply interventions through chat.

## Commands

- `data <world_id>` retrieves Census population and the FDIC bank directory with provenance. It requires no separate ASI inference key: the ACP agent executes the backend tools directly.
- `stress <world_id>` queues live Nemotron policy analysis, waits up to 120 seconds and returns the tested recommendation/provider/tool-call count. It never applies the recommendation.
- `status <job_id>` waits for and returns a queued analysis. Use this if the earlier conversation returned a still-running job.

You can also say `stress-test bank 1 with a 40% loss and compare rescue plans` to create the entire experiment inside the conversation. It creates a fresh world, applies that shock, compares futures and runs live Nemotron without applying an intervention. Ask `why did you pick that?` to retrieve the saved public evidence. The agent stores the last job per sender. Unsupported wording returns help; arbitrary instructions are not inferred. [Full setup and limits](./TRACK_IMPLEMENTATION.md).

## Setup

Run the FastAPI backend on localhost:8000. Keep Fetch dependencies separate:

```powershell
python -m venv .venv-fetch
.\.venv-fetch\Scripts\python.exe -m pip install -r requirements-fetch.lock.txt
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_agent --check
```

The check validates the actual SDK ACP protocol offline, without starting an agent or loading credentials. Verified SDK: uagents 0.25.5. Protocol digest: `proto:30a801ed3a83f9a0ff0a9f1e6fe958cb91da1fc2218b153df7b6cbf87bd33d62`.

In ignored root `.env`, set a stable private `FETCH_AGENT_SEED` and a confirmed service-specific `FETCH_AGENTVERSE_TOKEN`. These are distinct from `ASI1_API_KEY`. Then:

```powershell
.\.venv-fetch\Scripts\python.exe -m scripts.run_fetch_agent
```

Keep that process running. In another terminal, register/connect the mailbox through the SDK's `/connect` handshake:

```powershell
.\.venv-fetch\Scripts\python.exe -m scripts.connect_fetch_agent
```

Alternatively configure `FETCH_AGENT_ENDPOINT` with a reachable `/submit` URL and register that external agent. The inspector runs on port 8002; keep it private and use the mailbox for external access.

## Verified registration and conversation transport

Public agent address: `agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm`.

On October 25, 2026 UTC, a replacement Agentverse credential authenticated successfully. The SDK mailbox registration succeeded. Public Agentverse discovery returns this agent as active and searchable with the actual ACP protocol. The stable identity seed and token are stored only in ignored private configuration. This token is not an ASI inference key.

The entire workflow also passed through the real Agentverse mailbox: signed ACP delivery and acknowledgement, a fresh synthetic bank-loss experiment, three futures, completed live Nebius/Nemotron analysis and a saved-evidence follow-up. No recommendation was applied. Reproduce this bounded integration check while the backend and gateway are running:

```powershell
.\.venv-fetch\Scripts\python.exe -m scripts.verify_fetch_mailbox
```

The check uses port 8003 for a temporary local peer and writes ignored `artifacts/fetch-mailbox-verification.json`. It creates a separate synthetic world and consumes live inference. The peer publishes only an ephemeral Almanac callback, not a marketplace profile. The product agent and backend must stay running to answer external conversations.

**ASI:One UI verification completed:** opened the agent's actual profile by address, sent the full stress-test prompt, received a completed live Nemotron response with three futures, then asked why and received the same job's three-call saved trace. Job `job_9f21d7b98d9e41c697effc754e7a04da`, synthetic world `world_c4824167313f4dbe`, no funds applied. Evidence is ignored `artifacts/fetch-asi-one/evidence.json`. The model's prose is a recommendation; the returned metrics remain the quantitative evidence. This does not establish real-world policy effectiveness.

Open [the agent on ASI:One](https://asi1.ai/ai/agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm) to reproduce it. The recipient autocomplete did not find the address; the direct profile did. An account login is required, and chat history is account-scoped. The optional separate ASI inference API remains unverified and is not needed for this ACP workflow. Event submissions and publication of subsequent local changes remain outstanding.

The [official hackpack](https://www.fetch.ai/events/hackathons/calhacks-13-0/hackpack) requires Agentverse registration, ACP, ASI:One discoverability, the primary workflow within the conversation, public code/run instructions and its additional submission process. An inference call alone is insufficient.
