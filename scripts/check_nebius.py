"""Discover available Nemotron models or verify a configured tool call. Never print secrets."""

import argparse
import json
import os
from urllib.parse import urlsplit

import httpx

from scripts.run_backend import load_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true", help="Make one billable tool-call request to the configured model")
    args = parser.parse_args()
    load_environment()
    if args.probe:
        from backend.provider import NebiusModel, ProviderError
        try:
            model = NebiusModel()
            message = model.complete([{"role": "user", "content": "Call connection_check with ok=true."}], [
                {"type": "function", "function": {"name": "connection_check", "description": "Verify function calling",
                 "parameters": {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"], "additionalProperties": False}}}])
            calls = message["tool_calls"]
            valid = any(call.get("function", {}).get("name") == "connection_check" and
                        json.loads(call["function"]["arguments"]).get("ok") is True for call in calls)
            print(json.dumps({"model": model.model, "tool_call_verified": valid}))
            return 0 if valid else 1
        except (ProviderError, ValueError, KeyError, TypeError):
            print("Live tool-call check failed; inspect model access and configuration. No credential values were logged.")
            return 1
    key = os.getenv("NEBIUS_API_KEY", "").strip()
    if not key:
        print("Set NEBIUS_API_KEY in the private root .env or shell first.")
        return 1
    base = os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1").rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname or parsed.query or parsed.fragment:
        print("NEBIUS_BASE_URL must be an HTTPS API base without credentials, query, or fragment.")
        return 1
    try:
        with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as client:
            response = client.get(base + "/models", headers={"Authorization": f"Bearer {key}"})
            if response.status_code != 200:
                print(json.dumps({"catalog_http_status": response.status_code, "base_url": base}))
                return 1
            models = [model["id"] for model in response.json()["data"] if "nemotron" in model.get("id", "").lower()]
            print(json.dumps({"base_url": base, "nemotron_models": models}, indent=2))
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        print("Model discovery failed; check connectivity and endpoint configuration.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
