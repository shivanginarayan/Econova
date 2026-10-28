"""Register the running Fetch agent with Agentverse using a confirmed user token."""
import os

import httpx

from scripts.run_backend import load_environment


def main():
    load_environment()
    token = os.getenv("FETCH_AGENTVERSE_TOKEN")
    if not token:
        raise SystemExit("Set a service-specific FETCH_AGENTVERSE_TOKEN first")
    try:
        with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as client:
            response = client.post("http://127.0.0.1:8002/connect", json={
                "user_token": token, "agent_type": "mailbox" if not os.getenv("FETCH_AGENT_ENDPOINT") else "custom",
                "endpoint": os.getenv("FETCH_AGENT_ENDPOINT") or None})
    except httpx.HTTPError:
        raise SystemExit("Fetch gateway unavailable on localhost:8002. Start scripts.run_fetch_agent, then retry.") from None
    if response.is_error:
        raise SystemExit(f"Agentverse connection failed (HTTP {response.status_code}); token not displayed")
    result = response.json()
    if not result.get("success"):
        raise SystemExit("Agentverse did not confirm registration; inspect the account and service-specific token")
    print("Agentverse registration confirmed. Verify discoverability and complete the workflow in ASI:One.")


if __name__ == "__main__":
    main()
