"""Fetch ASI:One calls bounded data tools. Source responses supply every number."""
import json
import os
import csv
import io
from datetime import datetime, timezone

import httpx

from backend.provider import ProviderError, ProviderNotConfigured

CENSUS_URL = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv"
FDIC_URL = "https://api.fdic.gov/banks/institutions"


def population():
    with httpx.Client(timeout=20, trust_env=False, follow_redirects=False) as client:
        response = client.get(CENSUS_URL)
        response.raise_for_status()
        row = next(r for r in csv.DictReader(io.StringIO(response.text)) if r["STATE"] == "06" and r["COUNTY"] == "075")
    count = int(row["POPESTIMATE2024"])
    if count <= 0:
        raise ValueError("Unexpected Census geography")
    return {"tool": "get_population", "source": "US Census Bureau county population estimates, Vintage 2024",
            "source_url": str(response.url), "geography": row["CTYNAME"] + ", " + row["STNAME"], "population_estimate": count,
            "reference_period": "2024-07-01", "unit": "people", "retrieved_at": datetime.now(timezone.utc).isoformat()}


def bank_directory():
    with httpx.Client(timeout=20, trust_env=False, follow_redirects=False) as client:
        response = client.get(FDIC_URL, params={"filters": 'ACTIVE:1 AND STALP:CA AND CITY:"San Francisco"',
                                              "fields": "NAME,CERT,CITY,STALP", "limit": 100, "format": "json"})
        response.raise_for_status()
        data = response.json()
    banks = [{"name": r["data"]["NAME"], "fdic_certificate": r["data"]["CERT"]} for r in data["data"]]
    total = int(data["meta"]["total"])
    return {"tool": "get_bank_directory", "source": "FDIC BankFind institutions",
            "source_url": str(response.url), "scope": "Active FDIC-insured institutions headquartered in San Francisco, CA; not branch locations",
            "total_institutions": total, "institutions": banks, "truncated": total > len(banks),
            "retrieved_at": datetime.now(timezone.utc).isoformat()}


TOOLS = [{"type": "function", "function": {"name": name, "description": description,
          "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}}
         for name, description in [("get_population", "Retrieve sourced San Francisco population estimate from US Census"),
                                   ("get_bank_directory", "Retrieve active FDIC-insured banks headquartered in San Francisco")]]


def retrieve_sources(store, simulation_id):
    world = store.get(simulation_id)
    results = []
    for function, name in [(population, "get_population"), (bank_directory, "get_bank_directory")]:
        try:
            results.append(function())
        except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, StopIteration):
            results.append({"tool": name, "error": "Source unavailable or invalid; no figures inferred"})
    return store.save_sponsor_report(simulation_id, "research", {
        "provider": "public_sources", "status": "partial" if any("error" in r for r in results) else "completed",
        "source_tick": world.state["tick"], "observations": results, "trace": [], "simulation_config": world.state["config"],
        "interpretation": "External reference context only; simulation households, banks and financial balances remain synthetic."})


def research(store, simulation_id):
    world = store.get(simulation_id)
    key = os.getenv("ASI1_API_KEY")
    if not key:
        raise ProviderNotConfigured("Set ASI1_API_KEY for Fetch.ai ASI:One data research")
    messages = [{"role": "system", "content": "You are the Economy God Mode data research agent. Call both supplied tools, once each. Never invent figures. Real-world context does not calibrate the synthetic economy. Do not call other tools."},
                {"role": "user", "content": "Retrieve San Francisco population and the bank directory with source provenance."}]
    results, trace = {}, []
    functions = {"get_population": population, "get_bank_directory": bank_directory}
    try:
        with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as client:
            for _ in range(3):
                remaining = [t for t in TOOLS if t["function"]["name"] not in results]
                if not remaining:
                    break
                response = client.post("https://api.asi1.ai/v1/chat/completions", headers={"Authorization": "Bearer " + key},
                                       json={"model": os.getenv("ASI1_MODEL", "asi1-mini"), "messages": messages,
                                             "tools": remaining, "tool_choice": "required", "max_tokens": 1024})
                response.raise_for_status()
                message = response.json()["choices"][0]["message"]
                calls = message.get("tool_calls", [])
                if not calls or len(calls) > 2:
                    raise ValueError("Missing or excessive tool calls")
                messages.append({"role": "assistant", "content": None, "tool_calls": calls})
                for call in calls:
                    name = call["function"]["name"]
                    if name not in functions or name in results or json.loads(call["function"]["arguments"]) != {}:
                        raise ValueError("Invalid or duplicate data tool")
                    try:
                        result = functions[name]()
                        trace.append({"tool": name, "status": "completed"})
                    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, StopIteration):
                        result = {"tool": name, "error": "Source unavailable or response invalid; no data inferred"}
                        trace.append({"tool": name, "status": "failed"})
                    results[name] = result
                    messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
    except httpx.HTTPStatusError as error:
        raise ProviderError(f"ASI:One returned HTTP {error.response.status_code}; no demo substitution was used") from None
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        raise ProviderError("ASI:One failed to execute the bounded research workflow") from None
    return store.save_sponsor_report(simulation_id, "research", {
        "provider": "fetch_asi1", "model": os.getenv("ASI1_MODEL", "asi1-mini"),
        "status": "completed" if len(results) == 2 and all("error" not in r for r in results.values()) else "partial",
        "source_tick": world.state["tick"], "observations": list(results.values()), "trace": trace,
        "simulation_config": world.state["config"],
        "interpretation": "External reference context only. Household agents are synthetic households, not individual residents. Bank names and balance sheets in the simulation remain synthetic."})
