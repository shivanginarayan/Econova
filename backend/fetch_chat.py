"""Explicit chat commands for Fetch ACP. Analysis completes without the custom UI."""
import json
import re
import time
from uuid import uuid4

import httpx

HELP = ('Economy God Mode: use "data <world_id>" for sourced population/banks; '
        '"stress <world_id>" to test rescue policies with live Nemotron (no funds applied); '
        '"status <job_id>" to inspect an analysis. World IDs come from the dashboard. '
        'Or say "stress-test bank 1 with a 40% loss and compare rescue plans" to create the entire experiment in chat. '
        'Ask "why did you pick that?" after an analysis for its saved evidence. '
        'The economy is synthetic; retrieved city statistics are reference context.')


async def job_result(client, result, wait_seconds, explain=False):
    import asyncio
    deadline = time.monotonic() + wait_seconds
    while result["status"] in ("queued", "running") and time.monotonic() < deadline:
        await asyncio.sleep(1)
        response = await client.get(f"/api/agent-jobs/{result['job_id']}")
        response.raise_for_status()
        result = response.json()
    if result.get("report_url"):
        response = await client.get(result["report_url"])
        response.raise_for_status()
        report = response.json()
        outcome = {"job_id": result["job_id"], "simulation_id": report.get("simulation_id"), "status": result["status"],
                   "provider": report.get("provider"), "model": report.get("model"), "snapshot_sha256": report.get("snapshot_sha256"),
                   "recommendation": report.get("recommendation"), "error": report.get("error"),
                   "tool_calls": len(report.get("trace", [])), "funds_applied": False, "amount_unit": "USD cents"}
        comparison_ids = report.get("comparison_ids", [])
        if comparison_ids:
            comparison = await client.get(f"/api/forks/{comparison_ids[0]}")
            comparison.raise_for_status()
            data = comparison.json()
            outcome["three_futures"] = [{"strategy": b["strategy"], "metrics": b["metrics"],
                                          "delta_vs_no_intervention": b["delta_vs_no_intervention"]} for b in data["branches"]]
        if explain:
            outcome["saved_public_trace"] = report.get("trace", [])
        return outcome
    return result


async def handle_command(text, backend_url="http://127.0.0.1:8000", wait_seconds=120, previous=None):
    match = re.fullmatch(r"\s*(data|stress|status)\s+([A-Za-z0-9_-]{1,128})\s*", text, re.I)
    natural = re.search(r"stress[- ]?test\s+bank\s+(\d{1,2})\b.*?(\d{1,3}(?:\.\d{1,2})?)\s*%", text, re.I)
    explain = bool(re.search(r"\bwhy\b|defend|explain.*decision", text, re.I))
    if explain and previous and previous.get("job_id"):
        action, identifier = "status", previous["job_id"]
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identifier):
            return HELP
    elif match:
        action, identifier = match.groups()
        action = action.lower()
    elif natural:
        action, identifier = "experiment", None
    else:
        return HELP
    try:
        async with httpx.AsyncClient(base_url=backend_url, timeout=120, trust_env=False, follow_redirects=False) as client:
            if action == "experiment":
                from decimal import Decimal
                bank_number = int(natural.group(1))
                loss_bps = int(Decimal(natural.group(2)) * 100)
                if not 1 <= bank_number <= 10 or not 1 <= loss_bps <= 10000:
                    return "Choose a bank from 1 to 10 and an asset loss above 0% and at most 100%."
                response = await client.post("/api/worlds", json={"seed": 42, "scenario": "credit_crunch", "banks": max(5, bank_number)})
                response.raise_for_status()
                identifier = response.json()["simulation_id"]
                response = await client.post(f"/api/worlds/{identifier}/shocks", json={"transaction_id": "fetch_shock_" + uuid4().hex,
                                             "bank_id": f"bank_{bank_number}", "loss_bps": loss_bps})
                response.raise_for_status()
                response = await client.post(f"/api/worlds/{identifier}/forks", json={"request_id": "fetch_fork_" + uuid4().hex,
                                             "bank_id": f"bank_{bank_number}", "budget_cents": 1_000_000, "ticks": 12})
                response.raise_for_status()
            if action == "data":
                response = await client.post(f"/api/worlds/{identifier}/data-context/sources")
            elif action in ("stress", "experiment"):
                response = await client.post(f"/api/worlds/{identifier}/agent-jobs", json={
                    "request_id": "fetch_" + uuid4().hex, "mode": "live",
                    "budget_cap_cents": 1_000_000, "ticks": 12, "max_experiments": 2,
                    **({"target_bank_id": f"bank_{bank_number}"} if action == "experiment" else {})})
            else:
                response = await client.get(f"/api/agent-jobs/{identifier}")
            if response.is_error:
                return f"Workflow unavailable (HTTP {response.status_code}). No payment or policy was applied. Check backend configuration."
            result = response.json()
            if action in ("stress", "status", "experiment"):
                result = await job_result(client, result, wait_seconds, explain)
                if action == "experiment":
                    result["created_world_id"] = identifier
                    result["shock"] = {"bank_id": f"bank_{bank_number}", "loss_bps": loss_bps}
            return json.dumps(result, ensure_ascii=False)
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return "Backend unavailable or returned an invalid response. No automatic retry or settlement was attempted."
