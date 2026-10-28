"""Actual x402 middleware and EIP-3009 signing with a mocked facilitator, never a chain transfer."""
import asyncio
import json

import httpx
import pytest

pytest.importorskip("x402", reason="Optional x402 SDK lives in .venv-x402")

from eth_account import Account
from x402.schemas import PaymentRequirements, SettleResponse, SupportedKind, SupportedResponse, VerifyResponse
from x402_service.buyer import buy, choose_requirement
from x402_service.server import NETWORK, USDC, create_app


MERCHANT = "0x" + "2" * 40
# Public, deterministic test-only private key. Never funded or used outside this unit test.
TEST_KEY = "0x" + "1" * 64
SNAPSHOT = "a" * 64


class MockFacilitator:
    def __init__(self):
        self.settlements = 0

    def get_supported(self):
        return SupportedResponse(kinds=[SupportedKind(x402_version=2, scheme="exact", network=NETWORK)])

    async def verify(self, payment_payload, payment_requirements):
        assert payment_requirements.network == NETWORK
        assert payment_payload.payload["authorization"]["value"] == "10000"
        assert payment_payload.payload["signature"].startswith("0x")
        return VerifyResponse(is_valid=True, payer=Account.from_key(TEST_KEY).address)

    async def settle(self, payment_payload, payment_requirements):
        self.settlements += 1
        return SettleResponse(success=True, transaction="0x" + "3" * 64, network=NETWORK, payer=Account.from_key(TEST_KEY).address)


def test_actual_402_challenge_signed_retry_and_receipt(monkeypatch):
    monkeypatch.setenv("X402_MERCHANT_ADDRESS", MERCHANT)
    monkeypatch.setenv("X402_WALLET_PRIVATE_KEY", TEST_KEY)
    monkeypatch.setenv("X402_FORECAST_URL", "http://127.0.0.1:8402")
    facilitator = MockFacilitator()
    async def inputs(simulation_id):
        return {"simulation_id": simulation_id, "snapshot_sha256": SNAPSHOT, "source_tick": 0, "history": [],
                "metrics": {"employment_rate": 1., "business_defaults": 0, "stressed_banks": 0}}
    app = create_app(facilitator=facilitator, input_fetcher=inputs)
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8402") as client:
            first = await client.get("/market-forecast/test_world", params={"snapshot": SNAPSHOT})
            assert first.status_code == 402 and first.headers.get("payment-required")
            assert facilitator.settlements == 0
        async def mocked_receipt(transaction, payer, merchant, amount):
            assert amount == "10000" and merchant == MERCHANT
            return True
        result = await buy({"simulation_id": "test_world", "snapshot_sha256": SNAPSHOT}, transport=httpx.ASGITransport(app=app), receipt_checker=mocked_receipt)
        assert result["transaction_hash"] == "0x" + "3" * 64
        assert result["forecast"]["method"] == "trailing_daily_employment_trend"
        assert result["simulated_ledger_affected"] is False and facilitator.settlements == 1
    asyncio.run(check())


@pytest.mark.parametrize("changes", [{"network": "eip155:8453"}, {"amount": "10001"}, {"asset": "0x" + "4" * 40}, {"pay_to": "0x" + "5" * 40}, {"max_timeout_seconds": 3600}])
def test_buyer_rejects_mainnet_excess_spend_wrong_asset_or_receiver(changes):
    data = {"scheme": "exact", "network": NETWORK, "amount": "10000", "asset": USDC, "pay_to": MERCHANT,
            "max_timeout_seconds": 120, "extra": {"name": "USDC", "version": "2"}, **changes}
    assert choose_requirement([PaymentRequirements(**data)], MERCHANT) is None


@pytest.mark.parametrize("chain,amount,valid", [("0x14a34", "0x2710", True), ("0x2105", "0x2710", False), ("0x14a34", "0x1", False)])
def test_receipt_checker_requires_correct_chain_and_usdc_transfer(monkeypatch, chain, amount, valid):
    from x402_service.buyer import verify_chain_receipt
    payer = Account.from_key(TEST_KEY).address
    real = httpx.AsyncClient
    def handler(request):
        method = json.loads(request.content)["method"]
        result = chain if method == "eth_chainId" else {"status": "0x1", "logs": [{"address": USDC,
            "topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef", "0x" + "0"*24 + payer[2:], "0x" + "0"*24 + MERCHANT[2:]], "data": amount}]}
        return httpx.Response(200, json={"result": result})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    if valid:
        assert asyncio.run(verify_chain_receipt("0x" + "3"*64, payer, MERCHANT, "10000")) is True
    else:
        with pytest.raises(ValueError):
            asyncio.run(verify_chain_receipt("0x" + "3"*64, payer, MERCHANT, "10000"))
