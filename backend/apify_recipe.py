"""Fixed recipe for the project private limited-permission Actor."""
import os
from backend.provider import ProviderNotConfigured
MENU_URL = "https://www.cafeseventy8.com/"
WAGE_URL = "https://www.sf.gov/information/understanding-minimum-wage-ordinance"

def recipe(category):
    if category not in ("prices", "wages"):
        raise ValueError("Unknown source category")
    actor = os.getenv("APIFY_ACTOR_ID", "").strip()
    if not actor:
        raise ProviderNotConfigured("Deploy the public-data Actor and set APIFY_ACTOR_ID")
    return {"actor_id": actor, "source_url": MENU_URL if category == "prices" else WAGE_URL,
            "value_path": "value", "unit": "usd_item" if category == "prices" else "usd_hour",
            "run_options": {"timeout": 120, "memory": 128, "maxTotalChargeUsd": 0.25},
            "input": {"category": category}}
