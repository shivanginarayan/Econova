"""A one-cent testnet paid trend analysis using Coinbase's actual x402 middleware."""
import os
import re

import httpx
from fastapi import FastAPI, HTTPException

NETWORK = "eip155:84532"
USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"


def forecast(data):
    history = data["history"][-5:]
    latest = data["metrics"]
    elapsed = history[-1]["simulation_tick"] - history[0]["simulation_tick"] if history else 0
    rate = (history[-1]["employment_rate"] - history[0]["employment_rate"]) / elapsed if elapsed else 0
    return {"simulation_id": data["simulation_id"], "snapshot_sha256": data["snapshot_sha256"],
            "source_tick": data["source_tick"], "method": "trailing_daily_employment_trend",
            "projection_horizon_days": 3, "projected_employment_rate": round(min(1, max(0, latest["employment_rate"] + 3 * rate)), 6),
            "observed_business_defaults": latest["business_defaults"], "observed_stressed_banks": latest["stressed_banks"],
            "limitations": "Trend extrapolation from synthetic observations, not a causal forecast. Test interventions with the simulation engine."}


def create_app(facilitator=None, input_fetcher=None):
    from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
    from x402.http.middleware.fastapi import PaymentMiddlewareASGI
    from x402.http.types import RouteConfig
    from x402.mechanisms.evm.exact import ExactEvmServerScheme
    from x402.schemas import AssetAmount
    from x402.server import x402ResourceServer

    merchant = os.getenv("X402_MERCHANT_ADDRESS", "")
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", merchant) or int(merchant, 16) == 0:
        raise RuntimeError("Set a valid Base Sepolia X402_MERCHANT_ADDRESS")
    facilitator = facilitator or HTTPFacilitatorClient(FacilitatorConfig(url="https://x402.org/facilitator"))
    resource_server = x402ResourceServer(facilitator)
    resource_server.register(NETWORK, ExactEvmServerScheme())
    app = FastAPI(title="Economy paid research — Base Sepolia only")
    app.add_middleware(PaymentMiddlewareASGI, server=resource_server, routes={
        "GET /market-forecast/*": RouteConfig(accepts=[PaymentOption(scheme="exact", pay_to=merchant, network=NETWORK, max_timeout_seconds=120,
            price=AssetAmount(amount="10000", asset=USDC, extra={"name": "USDC", "version": "2"}))],
            mime_type="application/json", description="Three-day synthetic employment trend analysis; one cent of Base Sepolia test USDC")})

    @app.get("/health")
    def health():
        return {"status": "ok", "network": NETWORK, "price_atomic_usdc": "10000", "testnet_only": True}

    @app.get("/market-forecast/{simulation_id}")
    async def report(simulation_id: str, snapshot: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", simulation_id) or not re.fullmatch(r"[0-9a-f]{64}", snapshot):
            raise HTTPException(422, "Invalid world or snapshot")
        if input_fetcher:
            data = await input_fetcher(simulation_id)
        else:
            try:
                async with httpx.AsyncClient(timeout=15, trust_env=False, follow_redirects=False) as client:
                    response = await client.get(f"http://127.0.0.1:8000/api/worlds/{simulation_id}/research-input")
                    response.raise_for_status()
                    data = response.json()
            except (httpx.HTTPError, ValueError):
                raise HTTPException(503, "Simulation inputs unavailable") from None
        if data["snapshot_sha256"] != snapshot:
            raise HTTPException(409, "Source world changed; no forecast for the requested snapshot")
        return forecast(data)

    return app


def main():
    from scripts.run_backend import load_environment
    load_environment()
    import uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8402, access_log=False)


if __name__ == "__main__":
    main()
