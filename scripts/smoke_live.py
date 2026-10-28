"""Verify all three live workflows through the local API; no automatic settlement."""

import json
import time
from pathlib import Path
from uuid import uuid4

import httpx


def main():
    results = []
    sources = {}
    started = {}
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30, trust_env=False) as client:
        def call(path, body=None):
            response = client.get(path) if body is None else client.post(path, json=body)
            response.raise_for_status()
            return response.json()

        status = call("/api/agents/status")
        if not status["live_configured"]:
            raise SystemExit("Start scripts.run_backend with live credentials first")
        print(json.dumps({"provider": status["provider"], "model": status["model"]}), flush=True)
        queued = []
        for kind in ("central_bank", "credit", "procurement"):
            world = call("/api/worlds", {"seed": 42, "scenario": "supply_crunch" if kind == "procurement" else "standard"})
            base = "/api/worlds/" + world["simulation_id"]
            request = {"request_id": "live-check-" + uuid4().hex, "mode": "live", "agent_review": True}
            if kind == "central_bank":
                endpoint = base + "/agent-jobs"
                request.update(ticks=2, max_experiments=1, budget_cap_cents=100000)
            elif kind == "credit":
                business = next(e for e in world["entities"] if e["id"] == "business_1")
                call(base + "/payments", {"transaction_id": "setup-" + uuid4().hex,
                     "payer_id": "business_1", "receiver_id": "business_2",
                     "amount_cents": business["balance_sheet"]["assets"]["deposit"]})
                endpoint = base + "/businesses/business_1/credit-jobs"
                request["auto_settle"] = False
            else:
                endpoint = base + "/businesses/business_1/procurement-jobs"
                request.update(auto_settle=False, quantity=20, max_total_cents=100000)
            sources[world["simulation_id"]] = call(base)
            started[world["simulation_id"]] = time.monotonic()
            job = call(endpoint, request)
            queued.append(job)
            print(json.dumps({"kind": kind, "job_id": job["job_id"], "status": job["status"]}), flush=True)
        deadline = time.monotonic() + 480
        while queued and time.monotonic() < deadline:
            for job in queued[:]:
                current = call("/api/agent-jobs/" + job["job_id"])
                if current["status"] in ("completed", "failed", "cancelled"):
                    report = call(current["report_url"]) if current["report_url"] else None
                    result = {"kind": current["kind"], "job_id": current["job_id"],
                        "simulation_id": current["simulation_id"], "status": current["status"],
                        "report_status": current["report_status"], "run_id": report["run_id"] if report else None,
                        "trace_count": len(report["trace"]) if report else 0,
                        "supervision_status": (report.get("supervision") or {}).get("status") if report else None,
                        "activity_count": len(report.get("activity", [])) if report else 0,
                        "actors": sorted({a["actor"] for a in report.get("activity", [])}) if report else [],
                        "elapsed_seconds": round(time.monotonic() - started[current["simulation_id"]], 2),
                        "source_unchanged": call("/api/worlds/" + current["simulation_id"]) == sources[current["simulation_id"]],
                        "provider": report.get("provider", report.get("providers")) if report else None,
                        "model": report.get("model", report.get("models")) if report else None,
                        "error": current["error"] or (report.get("error") if report else None),
                        "audit": call("/api/worlds/" + current["simulation_id"] + "/audit")}
                    results.append(result)
                    queued.remove(job)
                    print(json.dumps(result), flush=True)
            if queued:
                time.sleep(1)
        destination = Path(__file__).resolve().parent.parent / "data" / "live-smoke-report.json"
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps({"results": results, "pending_jobs": queued}, indent=2) + "\n", encoding="utf-8")
        return 0 if len(results) == 3 and all(r["status"] == "completed" and r["source_unchanged"] and r["audit"]["balanced"]
            and r["supervision_status"] in ("passed", "blocked") and r["activity_count"] > 0 for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
