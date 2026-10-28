# Coinbase x402 verified testnet purchase

On October 25, 2026 UTC, the actual x402 Python SDK completed a paid research request against our FastAPI merchant and the public facilitator. It settled **10,000 atomic USDC units (0.01 test USDC)** on **Base Sepolia**, and an independent RPC check verified the successful receipt and exact USDC Transfer log from buyer to merchant.

[Verified transaction](https://sepolia.basescan.org/tx/0xf003b24fbbd32c3171161e8026615a8efa851591174db961ee1025c431906e86)

The buyer was funded with 20 test USDC through Circle's public faucet. The purchase returned a three-day trailing-employment projection bound to the requested synthetic world's exact SHA-256 snapshot. No simulated ledger balance was debited. Buyer and merchant are separate project-controlled test identities; this is not external customer revenue or a mainnet payment.

## What was demonstrated

- Real HTTP 402 challenge, x402 v2 signature, facilitator settlement and successful on-chain payment.
- Fixed Base Sepolia USDC contract, exact configured recipient and a one-cent cap.
- Independently verified successful chain receipt and matching transfer amount/parties.
- Returned forecast tied to the source world and snapshot, with synthetic-trend limitations.
- Durable attempt marker in the verification harness prevents accidental reruns after ambiguous outcomes.

The proof is saved privately under ignored `artifacts/x402-live-verification.json`, with the attempt marker in ignored `data/x402-live-verification.json`. Do not delete that marker to repeat a payment without inspecting the wallet first.

`scripts/verify_x402_live.py` is an explicit SDK demonstration, not an LLM-selected purchase. A separate actual live Nebius/Nemotron policy run with `allow_paid_research=true` completed, but chose inspect/compare/recommend and did **not** invoke the optional purchase tool. That permission enables the tool; it does not force spending. Its report is ignored `artifacts/x402-live-agent.json`. The production path reserves at most one attempt per agent run, returns verified payment evidence in the tool trace, and never substitutes a mock payment for success.

## Submission text

Economy God Mode integrates Coinbase's x402 protocol for bounded pay-per-request analysis. A separate research service charges 0.01 Base Sepolia test USDC for a snapshot-specific synthetic employment trend projection. The buyer accepts only the configured USDC asset, network, recipient and amount limit, verifies the settlement receipt against the chain, and checks that the delivered analysis matches its requested world snapshot. Financial agents can opt into this tool through explicit per-run authorization; simulation money is separate from the test wallet. We verified the real challenge/signature/settlement path and published the testnet transaction as evidence.

Confirm the final sponsor submission requirements using [the official prize listing](https://hive.hackberkeley.org/prizes). This milestone does not submit an entry or establish that a live policy agent chose to pay autonomously.
