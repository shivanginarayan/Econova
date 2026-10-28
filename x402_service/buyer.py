"""One bounded x402 handshake. No automatic payment retries or mainnet support."""
import asyncio
import json
import os
import re
import sys
from urllib.parse import urlsplit

import httpx

from x402_service.server import NETWORK, USDC


def choose_requirement(requirements, merchant):
    return next((r for r in requirements if r.network == NETWORK and r.scheme == "exact" and
                 r.asset.lower() == USDC.lower() and r.pay_to.lower() == merchant.lower() and
                 r.amount.isascii() and r.amount.isdigit() and 0 < int(r.amount) <= 10000 and
                 0 < r.max_timeout_seconds <= 300 and
                 (r.extra or {}).get("name") == "USDC" and (r.extra or {}).get("version") == "2"), None)


async def verify_chain_receipt(transaction, payer, merchant, amount):
    async with httpx.AsyncClient(timeout=15, trust_env=False, follow_redirects=False) as client:
        async def rpc(method, params):
            response = await client.post("https://sepolia.base.org", json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise ValueError("RPC error")
            return result["result"]
        if int(await rpc("eth_chainId", []), 16) != 84532:
            raise ValueError("Wrong chain")
        for _ in range(5):
            receipt = await rpc("eth_getTransactionReceipt", [transaction])
            if receipt is not None:
                break
            await asyncio.sleep(1)
        if not receipt or receipt.get("status") != "0x1":
            raise ValueError("No successful on-chain receipt")
        transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        for log in receipt.get("logs", []):
            topics = log.get("topics", [])
            if (log.get("address", "").lower() == USDC.lower() and len(topics) == 3 and topics[0].lower() == transfer_topic and
                    topics[1][-40:].lower() == payer[2:].lower() and topics[2][-40:].lower() == merchant[2:].lower() and
                    int(log.get("data", "0x0"), 16) == int(amount)):
                return True
        raise ValueError("Receipt does not contain the expected test USDC transfer")


async def buy(payload, transport=None, receipt_checker=None):
    from eth_account import Account
    from x402 import x402Client
    from x402.http import x402HTTPClient
    from x402.mechanisms.evm import EthAccountSigner
    from x402.mechanisms.evm.exact.client import ExactEvmScheme

    merchant = os.getenv("X402_MERCHANT_ADDRESS", "")
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", merchant):
        raise ValueError("Missing merchant")
    account = Account.from_key(os.environ["X402_WALLET_PRIVATE_KEY"])
    if account.address.lower() == merchant.lower():
        raise ValueError("Buyer and service must use different testnet identities")
    base = os.getenv("X402_FORECAST_URL", "http://127.0.0.1:8402").rstrip("/")
    parts = urlsplit(base)
    if (parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in ("localhost", "127.0.0.1"))) or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Invalid configured forecast service URL")
    sid, snapshot = payload["simulation_id"], payload["snapshot_sha256"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", sid) or not re.fullmatch(r"[0-9a-f]{64}", snapshot):
        raise ValueError("Invalid source")
    client = x402Client()
    client.register(NETWORK, ExactEvmScheme(EthAccountSigner(account)))
    helper = x402HTTPClient(client)
    async with httpx.AsyncClient(timeout=30, trust_env=False, follow_redirects=False, transport=transport) as http:
        # Plain HTTP here intentionally avoids SDK transports with recovery retries.
        response = await http.get(base + f"/market-forecast/{sid}", params={"snapshot": snapshot})
        if response.status_code != 402:
            raise ValueError("Expected a real HTTP 402 challenge")
        required = helper.get_payment_required_response(response.headers.get, response.json())
        if required.x402_version != 2:
            raise ValueError("Only x402 v2 is supported")
        chosen = choose_requirement(required.accepts, merchant)
        if chosen is None:
            raise ValueError("No approved Base Sepolia USDC requirement within the one-cent cap")
        required = required.model_copy(update={"accepts": [chosen]})
        signature = await client.create_payment_payload(required)
        headers = helper.encode_payment_signature_header(signature)
        paid = await http.get(str(response.url), headers=headers)
        paid.raise_for_status()
        settlement = helper.get_payment_settle_response(paid.headers.get)
        if not settlement.success or settlement.network != NETWORK or not re.fullmatch(r"0x[0-9a-fA-F]{64}", settlement.transaction):
            raise ValueError("Missing confirmed testnet settlement receipt")
        await (receipt_checker or verify_chain_receipt)(settlement.transaction, account.address, merchant, chosen.amount)
        data = paid.json()
        if data.get("snapshot_sha256") != snapshot or data.get("simulation_id") != sid:
            raise ValueError("Paid report does not match the source snapshot")
        return {"provider": "x402", "network": NETWORK, "amount_atomic_usdc": chosen.amount,
                "transaction_hash": settlement.transaction, "explorer_url": "https://sepolia.basescan.org/tx/" + settlement.transaction,
                "forecast": data, "onchain_receipt_verified": True, "simulated_ledger_affected": False}


def main():
    from scripts.run_backend import load_environment
    load_environment()
    try:
        payload = json.loads(sys.stdin.read())
        result = asyncio.run(buy(payload))
        print(json.dumps({"ok": True, "result": result}))
    except Exception:
        # Provider bodies and signing exceptions never reach traces or stdout.
        print(json.dumps({"ok": False, "error": "Paid research failed or settlement is uncertain. Inspect the testnet wallet before any new purchase."}))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
