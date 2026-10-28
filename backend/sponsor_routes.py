"""Small integrations exposed to the dashboard and Fetch chat agent."""
import os
from typing import Literal

from fastapi import APIRouter, BackgroundTasks
from pydantic import Field

from backend import fraud, research, spacetime
from backend.forks import snapshot_hash
from backend.models import Request, PaymentRequest
from backend.provider import ProviderNotConfigured
from backend import shock_stories
from backend import apify_collection


class ScreenRequest(Request):
    entity_id: str = Field(min_length=1, max_length=128)
    profile_id: str = Field(min_length=1, max_length=128)
    mode: Literal["demo", "live"] = "live"


class GuardedPayment(PaymentRequest):
    fraud_report_id: str = Field(min_length=1, max_length=128)


def router(store):
    api = APIRouter(prefix="/api", tags=["Sponsor integrations"])
    apify_collection.init(store)

    @api.get("/calibrations/collection/status")
    def collection_status():
        return {"configured": apify_collection.configured(), "latest": apify_collection.get(store)}

    @api.post("/calibrations/collect", status_code=202)
    def start_collection(body: apify_collection.CollectRequest, background: BackgroundTasks):
        job, started = apify_collection.enqueue(store, body.request_id)
        if started:
            background.add_task(apify_collection.execute, store, job["job_id"])
        return job

    @api.post("/calibrations/ensure")
    def ensure_public_inputs(background: BackgroundTasks):
        result, started = apify_collection.ensure(store)
        if started:
            background.add_task(apify_collection.execute, store, result["job"]["job_id"])
        return result

    @api.get("/calibrations/collection/{job_id}")
    def collection_job(job_id: str):
        return apify_collection.get(store, job_id)

    @api.get("/calibrations/{calibration_id}")
    def calibration_detail(calibration_id: str):
        from backend.calibration import load, checksum
        value = load(calibration_id)
        return {**value, "sha256": checksum(value)}

    @api.post("/worlds/{simulation_id}/shock-stories/preview")
    def preview_shock_story(simulation_id: str, body: shock_stories.DebtStress):
        return shock_stories.preview(store, simulation_id, body)

    @api.get("/worlds/{simulation_id}/shock-stories")
    def shock_story_history(simulation_id: str):
        return shock_stories.history(store, simulation_id)

    @api.post("/worlds/{simulation_id}/shock-stories/apply")
    def apply_shock_story(simulation_id: str, body: shock_stories.ApplyStory):
        return shock_stories.apply(store, simulation_id, body.report_id)

    @api.get("/integrations/status")
    def status():
        return {"fetch": {"configured": bool(os.getenv("ASI1_API_KEY")), "model": os.getenv("ASI1_MODEL", "asi1-mini"),
                          "agentverse_registration": "Verify the separately running Fetch chat agent in Agentverse"},
                "crs": fraud.status(),
                "spacetime": {"configured": bool(os.getenv("SPACETIMEDB_DATABASE") and os.getenv("SPACETIMEDB_TOKEN")),
                              "database": os.getenv("SPACETIMEDB_DATABASE") or None}}

    @api.get("/worlds/{simulation_id}/data-context")
    def contexts(simulation_id: str):
        world = store.get(simulation_id)
        return {"origin": "seeded_synthetic", "config": world.state["config"],
                "reports": store.sponsor_reports(simulation_id, "research")}

    @api.get("/worlds/{simulation_id}/research-input")
    def research_input(simulation_id: str):
        world = store.get(simulation_id)
        return {"simulation_id": simulation_id, "snapshot_sha256": snapshot_hash(world.state),
                "source_tick": world.state["tick"], "metrics": world.metrics(), "history": world.state["history"][-5:]}

    @api.get("/calibrations")
    def calibrations():
        from backend.calibration import load
        from pathlib import Path
        result = []
        for path in sorted(Path(os.getenv("APIFY_CALIBRATION_DIR", "data/calibrations")).glob("*.json"))[:50]:
            try:
                value = load(path.stem)
                result.append({"calibration_id": value["calibration_id"], "geography": value["geography"],
                               "collected_at": value["collected_at"], "provider": value["provider"]})
            except ProviderNotConfigured:
                continue
        return result

    @api.post("/worlds/{simulation_id}/data-context/research")
    def run_research(simulation_id: str):
        return research.research(store, simulation_id)

    @api.post("/worlds/{simulation_id}/data-context/sources")
    def source_data(simulation_id: str):
        return research.retrieve_sources(store, simulation_id)

    @api.get("/fraud/profiles")
    def profiles():
        error = None
        try:
            configured = fraud.profiles()
        except ProviderNotConfigured as exc:
            configured, error = {}, str(exc)
        return {"profiles": [{"profile_id": key} for key, value in configured.items()
                             if isinstance(value, dict) and value.get("sponsor_test_identity") is True],
                "demo_profiles": ["demo_clear", "demo_identity_mismatch"], "configuration_error": error}

    @api.get("/credit/profiles")
    def credit_profiles():
        try:
            values = fraud.profiles()
        except ProviderNotConfigured:
            values = {}
        return {"profiles": [key for key, value in values.items() if isinstance(value, dict) and value.get("sponsor_test_identity") is True and isinstance(value.get("credit_request"), dict) and value["credit_request"]]}

    @api.post("/worlds/{simulation_id}/fraud/screens")
    def screen(simulation_id: str, body: ScreenRequest):
        return fraud.screen(store, simulation_id, **body.model_dump())

    @api.get("/worlds/{simulation_id}/fraud/screens")
    def screens(simulation_id: str):
        return store.sponsor_reports(simulation_id, "fraud")

    @api.post("/worlds/{simulation_id}/fraud/payments")
    def payment(simulation_id: str, body: GuardedPayment):
        return store.guarded_payment(simulation_id, body.fraud_report_id, body.model_dump(exclude={"fraud_report_id"}))

    @api.post("/worlds/{simulation_id}/spacetime/enable")
    def enable(simulation_id: str):
        return spacetime.enable(store, simulation_id)

    @api.post("/worlds/{simulation_id}/control-room")
    def open_control_room(simulation_id: str):
        return spacetime.open_room(store, simulation_id)

    @api.get("/worlds/{simulation_id}/economic-services")
    def economic_services(simulation_id: str):
        from backend.fetch_agents.agents import ROLES
        from backend.fetch_agents.service import EconomyAgentService
        from backend.fetch_agents import protocols as p
        service = EconomyAgentService(store)
        return {"mode": "deterministic_saved_state", "services": list(ROLES), "funds_applied": False,
                "reports": {name: service.handle(model(world_id=simulation_id)).model_dump() for name, model in [
                    ("ledger", p.InvarianceAuditRequest), ("welfare", p.WelfareAuditRequest),
                    ("interbank", p.InterbankExposureAuditRequest)]}}

    @api.post("/worlds/{simulation_id}/control-room/{proposal_id}/execute")
    def execute_control_proposal(simulation_id: str, proposal_id: str):
        return spacetime.execute_proposal(store, simulation_id, proposal_id)

    @api.get("/worlds/{simulation_id}/spacetime")
    def sync_status(simulation_id: str):
        return spacetime.sync_status(store, simulation_id)

    @api.get("/worlds/{simulation_id}/spacetime/events")
    def shared_events(simulation_id: str):
        store.get(simulation_id)
        return spacetime.shared_events(simulation_id)

    return api
