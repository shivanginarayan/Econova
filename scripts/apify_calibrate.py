"""Collect explicit Actor datasets into an opt-in, immutable SF price/wage calibration."""
import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

import httpx

from backend.calibration import validate
from scripts.run_backend import load_environment


def cents(value, unit):
    if unit not in ("usd_item", "usd_hour", "usd_day", "usd_year", "usd_month_rent"):
        raise ValueError("Choose explicit units; salary/price strings are not guessed")
    if isinstance(value, bool):
        raise ValueError("Invalid numeric amount")
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Amounts must be numeric USD, without ranges or currency text") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amounts must be positive and finite")
    if unit == "usd_hour":
        amount *= 8
    elif unit == "usd_year":
        amount /= 260
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def collect(spec, client, wait_seconds=180, on_run=None):
    actor = spec["actor_id"]
    if not re.fullmatch(r"[a-zA-Z0-9_~.-]{1,128}", actor):
        raise ValueError("Invalid Actor ID; use the owner~actor form")
    url = f"https://api.apify.com/v2/actors/{actor}/runs"
    if spec.get("run_id"):
        run_id = spec["run_id"]
    else:
        response = client.post(url, params=spec.get("run_options", {}), json=spec.get("input", {}))
        response.raise_for_status()
        run_id = response.json()["data"]["id"]
    if not re.fullmatch(r"[A-Za-z0-9]{1,128}", run_id):
        raise ValueError("Invalid Apify run ID")
    if on_run:
        on_run(run_id)
    deadline = time.monotonic() + wait_seconds
    while True:
        response = client.get(f"https://api.apify.com/v2/actor-runs/{run_id}")
        response.raise_for_status()
        run = response.json()["data"]
        if run["status"] == "SUCCEEDED":
            break
        if run["status"] in ("FAILED", "ABORTED", "TIMED-OUT") or time.monotonic() >= deadline:
            raise ValueError(f"Actor run {run_id} did not finish successfully; no calibration published. Reuse this run_id when checking later.")
        time.sleep(2)
    dataset = run["defaultDatasetId"]
    if not re.fullmatch(r"[A-Za-z0-9]{1,128}", dataset):
        raise ValueError("Invalid dataset ID")
    response = client.get(f"https://api.apify.com/v2/datasets/{dataset}/items", params={"format": "json", "clean": "true", "limit": 1000})
    response.raise_for_status()
    samples, skipped, observations = [], 0, []
    for row in response.json():
        try:
            value = row
            for part in spec["value_path"].split("."):
                value = value[part]
            samples.append(cents(value, spec["unit"]))
            observations.append({k: row[k] for k in ("item", "variant", "value", "unit", "source_url", "observed_at", "effective_date", "kind", "venue") if k in row})
        except (ValueError, KeyError, TypeError):
            skipped += 1
    if not samples:
        raise ValueError("No numeric observations matched the configured field/unit")
    return samples, {"actor_id": run.get("actId", actor), "requested_actor_id": actor, "run_id": run_id, "dataset_id": dataset,
                     "source_url": spec["source_url"], "unit": spec["unit"], "value_path": spec["value_path"],
                     "accepted": len(samples), "skipped": skipped, "source_finished_at": run.get("finishedAt"),
                     "observations": observations, "usage_total_usd": run.get("usageTotalUsd")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="Private JSON spec with calibration_id, prices, wages and optional rent Actor definitions")
    args = parser.parse_args()
    load_environment()
    if not os.getenv("APIFY_TOKEN"):
        raise SystemExit("Set APIFY_TOKEN in ignored .env")
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    result = {"calibration_id": spec["calibration_id"], "geography": "San Francisco, CA", "provider": "apify",
              "collected_at": datetime.now(timezone.utc).isoformat(), "sources": [], "rental_context": []}
    with httpx.Client(timeout=30, trust_env=False, follow_redirects=False,
                      headers={"Authorization": "Bearer " + os.environ["APIFY_TOKEN"]}) as client:
        for name, allowed in [("prices", ("usd_item",)), ("wages", ("usd_hour", "usd_day", "usd_year")), ("rent", ("usd_month_rent",))]:
            if name == "rent" and name not in spec:
                continue
            if spec[name]["unit"] not in allowed:
                raise ValueError("Actor units do not match the selected data category")
            samples, provenance = collect(spec[name], client)
            result["sources"].append(provenance)
            if name == "rent":
                result["rental_context"] = [{"monthly_rent_cents": v} for v in samples[:100]]
            else:
                result["price_cents" if name == "prices" else "daily_wage_cents"] = samples
    result = validate(result)
    root = Path(os.getenv("APIFY_CALIBRATION_DIR", "data/calibrations"))
    root.mkdir(parents=True, exist_ok=True)
    path = root / (result["calibration_id"] + ".json")
    # Never overwrite a calibration ID that an existing world may reference.
    with path.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
    print(f"Saved {path}; {len(result['price_cents'])} price and {len(result['daily_wage_cents'])} daily-wage samples. Rent remains reference context only.")


if __name__ == "__main__":
    main()
