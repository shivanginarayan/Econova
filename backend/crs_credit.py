"""Redacted CRS credit evidence for bank underwriting; no balances are modified."""
import hashlib
import json
import os
import re
import time
from pathlib import Path

import httpx

from backend import fraud
from backend.provider import ProviderError, ProviderNotConfigured


def field(value, path):
    for part in path.split("."):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def pull_credit_report(store, simulation_id, business_id, profile_id, force_refresh=False):
    world = store.get(simulation_id)
    if world.customer(business_id)["kind"] != "business":
        raise ProviderNotConfigured("CRS underwriting requires a business owner test profile")
    profile = fraud.profiles().get(profile_id, {})
    if not isinstance(profile, dict) or profile.get("sponsor_test_identity") is not True or not isinstance(profile.get("credit_request"), dict) or not profile["credit_request"]:
        raise ProviderNotConfigured("The selected sponsor test profile needs its documented credit_request payload")
    config = os.getenv("CRS_CREDIT_PRODUCT_CONFIG", "")
    variant = os.getenv("CRS_CREDIT_REPORT_VARIANT", "standard")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", config) or variant != "standard":
        raise ProviderNotConfigured("Set CRS_CREDIT_PRODUCT_CONFIG and the documented standard variant")
    try:
        rules = json.loads(Path(os.environ["CRS_CREDIT_RULES_PATH"]).read_text(encoding="utf-8-sig"))
        if not isinstance(rules, dict) or not isinstance(rules.get("score_path"), str) or not rules["score_path"] or not isinstance(rules.get("risk_rules", []), list):
            raise ValueError
        if any(not isinstance(r, dict) or not isinstance(r.get("path"), str) for r in rules.get("risk_rules", [])):
            raise ValueError
    except (KeyError, OSError, ValueError):
        raise ProviderNotConfigured("Configure CRS_CREDIT_RULES_PATH with the sponsor's score and risk-code mapping") from None
    cache_key = hashlib.sha256(json.dumps([profile["credit_request"], config, variant, rules], sort_keys=True).encode()).hexdigest()
    if not force_refresh:
        for report in store.sponsor_reports(simulation_id, "credit_profile"):
            if report["business_id"] == business_id and report["cache_key"] == cache_key and time.time() - report["created_at"] < 900:
                return {**report, "cached": True}
    try:
        with httpx.Client(timeout=25, trust_env=False, follow_redirects=False) as client:
            token = os.getenv("CRS_ACCESS_TOKEN")
            if not token:
                if not os.getenv("CRS_USERNAME") or not os.getenv("CRS_PASSWORD"):
                    raise ProviderNotConfigured("Set CRS sandbox login credentials or access token")
                response = client.post(fraud.CRS_BASE + "/users/login", json={"username": os.environ["CRS_USERNAME"], "password": os.environ["CRS_PASSWORD"]})
                response.raise_for_status()
                token = response.json()["token"]
            response = client.post(fraud.CRS_BASE + f"/experian/credit-report/{variant}/{config}",
                                   headers={"Authorization": "Bearer " + token, "Accept": "application/json"}, json=profile["credit_request"])
            response.raise_for_status()
            raw = response.json()
            if not isinstance(raw, dict) or raw.get("errorMessages"):
                raise ProviderError("CRS credit report contains product or bureau errors; underwriting remains held")
            decision, signals = fraud.normalize(raw, rules.get("risk_rules", []))
            score = None
            try:
                value = field(raw, rules["score_path"])
                if isinstance(value, str) and value.isascii() and value.isdigit():
                    value = int(value)
                if type(value) is int and 300 <= value <= 850:
                    score = value
            except (KeyError, IndexError, TypeError, ValueError):
                pass
            if score is None and decision != "blocked":
                decision = "review"
    except httpx.HTTPStatusError as error:
        raise ProviderError(f"CRS credit sandbox returned HTTP {error.response.status_code}; underwriting remains held") from None
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise ProviderError("CRS credit report unavailable or invalid; no clearance was inferred") from None
    return store.save_sponsor_report(simulation_id, "credit_profile", {
        "provider": "crs", "business_id": business_id, "profile_id": profile_id, "score": score,
        "risk_decision": decision, "signals": signals, "cache_key": cache_key, "cached": False,
        "source_tick": world.state["tick"], "product": "experian_credit_profile", "sandbox": True})


def credit_controls(request, evidence, amount):
    required = bool(request.get("require_crs") or request.get("crs_profile_id"))
    reasons, blocks = [], []
    if required:
        if evidence is None:
            reasons.append("CRS credit evidence has not been retrieved")
        elif evidence.get("risk_decision") == "blocked":
            blocks.append("CRS sandbox identity/fraud risk flags block this credit proposal")
        elif evidence.get("risk_decision") != "clear" or evidence.get("score") is None:
            reasons.append("CRS evidence requires human review; no automatic clearance")
        elif evidence["score"] < 620:
            reasons.append("CRS score is below the illustrative sandbox review threshold of 620")
    threshold = request.get("human_approval_threshold_cents")
    configured = os.getenv("CREDIT_APPROVAL_THRESHOLD_CENTS", "")
    if configured:
        try:
            limit = int(configured)
            if limit < 1:
                raise ValueError
            threshold = min(threshold, limit) if threshold is not None else limit
        except ValueError:
            reasons.append("Server approval threshold is invalid; human review required")
    if threshold is not None and amount > threshold:
        reasons.append("Principal exceeds the human-approval threshold")
    return {"required": required, "blocked": bool(blocks), "reasons": reasons + blocks,
            "needs_human_approval": bool(reasons) and not blocks,
            "evidence_report_id": evidence.get("report_id") if evidence else None,
            "threshold_cents": threshold}
