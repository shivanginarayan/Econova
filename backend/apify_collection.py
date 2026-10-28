"""Persistent, bounded collection jobs; financial worlds change only on explicit creation."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from pydantic import Field

from backend.apify_recipe import recipe
from backend.calibration import validate
from backend.ledger import LedgerError
from backend.models import Request
from backend.provider import ProviderNotConfigured
from scripts.apify_calibrate import collect


class CollectRequest(Request):
    request_id: str = Field(min_length=1, max_length=128)


def init(store):
    with store.connection() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS apify_collections (
            id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, created REAL NOT NULL,
            report TEXT NOT NULL)""")
        connection.execute("CREATE TABLE IF NOT EXISTS apify_collection_requests (request_id TEXT PRIMARY KEY, job_id TEXT NOT NULL)")


def configured():
    return bool(os.getenv("APIFY_TOKEN", "").strip() and os.getenv("APIFY_ACTOR_ID", "").strip())


AUTO_REFRESH_SECONDS = 6 * 60 * 60


def latest_data():
    from backend.calibration import load, checksum
    root = Path(os.getenv("APIFY_CALIBRATION_DIR", "data/calibrations"))
    values = []
    for path in root.glob("*.json"):
        try:
            value = load(path.stem)
            observed = datetime.fromisoformat(value["collected_at"].replace("Z", "+00:00"))
            if observed.tzinfo is None or observed.timestamp() > time.time() + 60:
                continue
            values.append((observed.timestamp(), value))
        except (ProviderNotConfigured, ValueError, OSError):
            continue
    if not values:
        return None, None
    timestamp, value = max(values, key=lambda item: item[0])
    return {**value, "sha256": checksum(value)}, timestamp


def ensure(store):
    """Serve cached data immediately; at most one automatic request per six-hour window."""
    data, observed = latest_data()
    ready = configured()
    job = get(store)
    if data and time.time() - observed < AUTO_REFRESH_SECONDS:
        return {"configured": ready, "data": data, "job": job, "state": "fresh"}, False
    if not ready:
        return {"configured": False, "data": data, "job": job, "state": "unavailable"}, False
    # A failed/ambiguous automatic request is not replayed on reload or in another tab.
    bucket = int(time.time() // AUTO_REFRESH_SECONDS)
    try:
        job, started = enqueue(store, f"auto-public-inputs-v1:{bucket}")
        state = "refreshing" if job["status"] in ("queued", "running") else job["status"]
        return {"configured": True, "data": data, "job": job, "state": state}, started
    except LedgerError:
        return {"configured": True, "data": data, "job": job, "state": "deferred"}, False


def enqueue(store, request_id):
    if not configured():
        raise ProviderNotConfigured("Configure APIFY_TOKEN and deploy APIFY_ACTOR_ID before collection")
    now = time.time()
    with store.connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT report FROM apify_collections WHERE id=(SELECT job_id FROM apify_collection_requests WHERE request_id=?) OR request_id=?", (request_id, request_id)).fetchone()
        if row:
            return json.loads(row[0]), False
        recent = connection.execute("SELECT report FROM apify_collections ORDER BY created DESC LIMIT 20").fetchall()
        for row in recent:
            report = json.loads(row[0])
            if report["status"] in ("queued", "running"):
                if now - report["updated_at"] < 600:
                    connection.execute("INSERT INTO apify_collection_requests VALUES (?, ?)", (request_id, report["job_id"]))
                    return report, False
                report.update(status="failed", error="Collection interrupted. Inspect recorded Apify runs before starting another; no automatic replay.")
                connection.execute("UPDATE apify_collections SET report=? WHERE id=?", (json.dumps(report), report["job_id"]))
            if report["status"] == "completed" and now - report["updated_at"] < 300:
                connection.execute("INSERT INTO apify_collection_requests VALUES (?, ?)", (request_id, report["job_id"]))
                return report, False
        if sum(now - json.loads(row[0])["created_at"] < 3600 for row in recent) >= 6:
            raise LedgerError("Collection limited to six requests per hour. Reuse the saved dataset or wait.")
        report = {"job_id": "apify_" + uuid4().hex, "status": "queued", "created_at": now,
                  "updated_at": now, "runs": {}, "calibration_id": None, "error": None}
        connection.execute("INSERT INTO apify_collections VALUES (?, ?, ?, ?)",
                           (report["job_id"], request_id, now, json.dumps(report)))
        connection.execute("INSERT INTO apify_collection_requests VALUES (?, ?)", (request_id, report["job_id"]))
        return report, True


def get(store, job_id=None):
    with store.connection() as connection:
        row = connection.execute("SELECT report FROM apify_collections WHERE id=?", (job_id,)).fetchone() if job_id else connection.execute("SELECT report FROM apify_collections ORDER BY created DESC LIMIT 1").fetchone()
    if not row:
        if job_id:
            raise KeyError(job_id)
        return None
    report = json.loads(row[0])
    if report["status"] in ("queued", "running") and time.time() - report["updated_at"] >= 600:
        report.update(status="failed", error="Collection interrupted. Inspect recorded Apify runs before starting another; no automatic replay.")
        save(store, report)
    return report


def save(store, report):
    report["updated_at"] = time.time()
    with store.connection() as connection:
        connection.execute("UPDATE apify_collections SET report=? WHERE id=?", (json.dumps(report), report["job_id"]))


def execute(store, job_id):
    with store.connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT report FROM apify_collections WHERE id=?", (job_id,)).fetchone()
        report = json.loads(row[0])
        if report["status"] != "queued":
            return
        report.update(status="running", updated_at=time.time())
        connection.execute("UPDATE apify_collections SET report=? WHERE id=?", (json.dumps(report), job_id))
    try:
        now = datetime.now(timezone.utc)
        result = {"calibration_id": "sf_public_" + now.strftime("%Y%m%d_%H%M%S_") + job_id[-6:],
                  "geography": "San Francisco, CA — one cafe menu plus official wage floor",
                  "provider": "apify", "collected_at": now.isoformat(), "sources": [], "rental_context": []}
        with httpx.Client(timeout=30, trust_env=False, follow_redirects=False,
                          headers={"Authorization": "Bearer " + os.environ["APIFY_TOKEN"]}) as client:
            for category in ("prices", "wages"):
                def on_run(run_id):
                    report["runs"][category] = run_id
                    save(store, report)
                samples, provenance = collect(recipe(category), client, wait_seconds=150, on_run=on_run)
                provenance["category"] = category
                provenance["scope"] = "Posted drink options at one cafe; not a citywide price index" if category == "prices" else "General statutory minimum wage; not average earnings or observed individual payroll"
                provenance["conversion"] = "Listed USD per menu item; tax/surcharges unspecified" if category == "prices" else "Hourly wage floor × assumed 8-hour day; no actual work schedule inferred"
                result["sources"].append(provenance)
                result["price_cents" if category == "prices" else "daily_wage_cents"] = samples
        result = validate(result)
        root = Path(os.getenv("APIFY_CALIBRATION_DIR", "data/calibrations"))
        root.mkdir(parents=True, exist_ok=True)
        with (root / (result["calibration_id"] + ".json")).open("x", encoding="utf-8") as output:
            json.dump(result, output, indent=2)
        report.update(status="completed", calibration_id=result["calibration_id"],
                      price_count=len(result["price_cents"]), wage_count=len(result["daily_wage_cents"]),
                      usage_total_usd=sum(s.get("usage_total_usd") or 0 for s in result["sources"]))
    except httpx.HTTPStatusError as error:
        report.update(status="failed", error=f"Apify returned HTTP {error.response.status_code}. Inspect recorded runs and Actor permissions in Console; no substitute data or automatic retry was used.")
    except Exception:
        # Arbitrary exception bodies can include tokens or source data; never expose them.
        report.update(status="failed", error="Collection failed or source structure changed. Inspect recorded runs. No calibration was substituted and no automatic retry was made.")
    save(store, report)
