"""CRS sandbox identity screening. Unknown vendor decisions always require review."""
import json
import os
import re
from pathlib import Path

import httpx

from backend.provider import ProviderError, ProviderNotConfigured

CRS_BASE = "https://api-sandbox.stitchcredit.com/api"


def profiles():
    path = os.getenv("CRS_TEST_PROFILES_PATH")
    if not path:
        return {}
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (OSError, ValueError):
        raise ProviderNotConfigured("CRS test-profile file is missing or invalid") from None


def status():
    return {"configured": bool((os.getenv("CRS_ACCESS_TOKEN") or
                                (os.getenv("CRS_USERNAME") and os.getenv("CRS_PASSWORD"))) and
                               os.getenv("CRS_PRODUCT_CONFIG") and os.getenv("CRS_TEST_PROFILES_PATH")),
            "sandbox_only": True, "product": "TransUnion TruValidate Identity Manager Verification"}


def normalize(response, rules):
    """Rules come from the sponsor's product-specific code mapping, never an LLM."""
    decisions, evidence = [], []
    for rule in rules:
        value = response
        try:
            for part in rule["path"].split("."):
                value = value[int(part)] if isinstance(value, list) else value[part]
            # Retain only a decision and path, never raw identity values.
            decision = ("blocked" if value in rule.get("blocked_values", []) else
                        "clear" if value in rule.get("clear_values", []) else "review")
        except (KeyError, IndexError, TypeError, ValueError):
            decision = "review"
        decisions.append(decision)
        evidence.append({"field": rule.get("path", "unknown"), "decision": decision})
    decision = "blocked" if "blocked" in decisions else "clear" if decisions and all(x == "clear" for x in decisions) else "review"
    return decision, evidence


def screen(store, simulation_id, entity_id, profile_id, mode="live"):
    world = store.get(simulation_id)
    world.customer(entity_id)
    if mode == "demo":
        if profile_id not in ("demo_clear", "demo_identity_mismatch"):
            raise KeyError(profile_id)
        return store.save_sponsor_report(simulation_id, "fraud", {
            "provider": "local_demo", "entity_id": entity_id, "profile_id": profile_id,
            "source_tick": world.state["tick"], "decision": "review" if profile_id == "demo_clear" else "blocked",
            "signals": [{"field": "local_scenario", "decision": "review" if profile_id == "demo_clear" else "blocked"}],
            "explanation": "Local test scenario only. Cannot authorize a CRS-guarded payment."})
    if not status()["configured"]:
        raise ProviderNotConfigured("Configure CRS sandbox login/token, product config, and sponsor test profiles")
    profile = profiles().get(profile_id)
    if not isinstance(profile, dict) or profile.get("sponsor_test_identity") is not True or not isinstance(profile.get("request"), dict):
        raise ProviderNotConfigured("Choose an explicitly marked sponsor test identity from the private profile file")
    config = os.environ["CRS_PRODUCT_CONFIG"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", config):
        raise ProviderNotConfigured("CRS_PRODUCT_CONFIG must be the sponsor-issued product identifier")
    rules = []
    if path := os.getenv("CRS_DECISION_RULES_PATH"):
        try:
            rules = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            if not isinstance(rules, list) or not all(isinstance(r, dict) and isinstance(r.get("path"), str) for r in rules):
                raise ValueError
        except (OSError, ValueError):
            raise ProviderNotConfigured("Invalid CRS decision rules file") from None
    try:
        with httpx.Client(timeout=25, trust_env=False, follow_redirects=False) as client:
            token = os.getenv("CRS_ACCESS_TOKEN")
            if not token:
                auth = client.post(CRS_BASE + "/users/login", json={"username": os.environ["CRS_USERNAME"], "password": os.environ["CRS_PASSWORD"]})
                auth.raise_for_status()
                token = auth.json()["token"]
            response = client.post(CRS_BASE + "/transunion/identity-manager-verification/basic/" + config,
                                   headers={"Authorization": "Bearer " + token, "Accept": "application/json"}, json=profile["request"])
            response.raise_for_status()
            decision, signals = normalize(response.json(), rules)
    except httpx.HTTPStatusError as error:
        raise ProviderError(f"CRS sandbox returned HTTP {error.response.status_code}; screening did not authorize payment") from None
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise ProviderError("CRS sandbox unavailable or returned an invalid response; payment remains held") from None
    return store.save_sponsor_report(simulation_id, "fraud", {
        "provider": "crs", "entity_id": entity_id, "profile_id": profile_id,
        "source_tick": world.state["tick"], "decision": decision, "signals": signals,
        "explanation": "CRS sandbox result evaluated against configured vendor-code rules. Unknown results require review."})
