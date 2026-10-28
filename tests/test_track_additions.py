import asyncio
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import credit_agents, crs_credit
from backend.calibration import checksum
from backend.credit_agents import run_credit
from backend.engine import Economy
from backend.forks import snapshot_hash
from backend.main import create_app
from backend.models import CreditRunRequest
from backend.provider import ProviderNotConfigured
from backend.store import Store
from scripts.apify_calibrate import cents


@pytest.fixture
def store(tmp_path):
    result = Store(tmp_path / "tracks.sqlite3")
    world = Economy.create("tracks", households=8, businesses=2, banks=2)
    cash = world.ledger.balance(world.customer("business_1")["deposit_account"])
    world.pay("initial-supplier-expense", "business_1", "business_2", cash)
    result.create(world)
    return result


def request(**changes):
    return CreditRunRequest.model_validate({"request_id": "review", "mode": "demo", **changes}).model_dump()


def test_large_credit_requires_human_then_separate_settlement(store):
    before = snapshot_hash(store.get("tracks").state)
    report = run_credit(store, "tracks", "business_1", request(human_approval_threshold_cents=1, auto_settle=True))
    assert report["status"] == "needs_human_approval" and report["settlement"] is None
    assert snapshot_hash(store.get("tracks").state) == before
    with pytest.raises(Exception, match="approved"):
        store.settle_credit(report["run_id"], "too-soon")
    approved = store.approve_credit(report["run_id"], "approve", "Reviewed the bounded payroll gap and bank limits")
    assert approved["status"] == "approved"
    assert store.approve_credit(report["run_id"], "approve", approved["human_approval"]["rationale"]) == approved
    assert snapshot_hash(store.get("tracks").state) == before
    settled = store.settle_credit(report["run_id"], "human-confirmed")
    assert settled["audit"]["balanced"]
    assert store.settle_credit(report["run_id"], "human-confirmed") == settled


@pytest.mark.parametrize("risk,score,expected", [("blocked", 780, "declined"), ("review", 780, "needs_human_approval"), ("clear", 550, "needs_human_approval"), ("clear", 750, "approved")])
def test_bank_must_pull_crs_and_apply_risk_controls(store, monkeypatch, risk, score, expected):
    evidence = {"provider": "crs", "report_id": "crs_evidence", "risk_decision": risk, "score": score, "created_at": time.time(), "cached": False}
    monkeypatch.setattr(credit_agents, "pull_credit_report", lambda *args: evidence)
    before = snapshot_hash(store.get("tracks").state)
    report = run_credit(store, "tracks", "business_1", request(require_crs=True, crs_profile_id="sponsor_a"))
    assert report["status"] == expected
    names = [t["tool"] for t in report["trace"]]
    assert names.index("pull_credit_report") < names.index("assess_credit")
    assert report["risk_evidence"]["score"] == score
    assert snapshot_hash(store.get("tracks").state) == before
    if expected == "declined":
        with pytest.raises(Exception):
            store.approve_credit(report["run_id"], "approve", "Attempt to bypass fraud block")


def test_stale_world_cannot_receive_human_approval(store):
    report = run_credit(store, "tracks", "business_1", request(human_approval_threshold_cents=1))
    store.mutate("tracks", lambda w: w.step())
    with pytest.raises(Exception, match="changed"):
        store.approve_credit(report["run_id"], "approve", "Reviewed")


def test_crs_missing_profile_does_not_fall_back_to_approval(store):
    report = run_credit(store, "tracks", "business_1", request(require_crs=True))
    assert report["status"] == "failed" and not report["settlement"]


def test_crs_credit_normalization_cache_and_no_pii(store, monkeypatch, tmp_path):
    profile = tmp_path / "profiles.json"
    profile.write_text(json.dumps({"sponsor_a": {"sponsor_test_identity": True, "credit_request": {"ssn": "PRIVATE_TEST_SSN"}}}))
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps({"score_path": "credit.score", "risk_rules": [{"path": "fraud.result", "clear_values": ["clear_fixture"], "blocked_values": ["blocked_fixture"]}]}))
    for key, value in {"CRS_TEST_PROFILES_PATH": str(profile), "CRS_CREDIT_RULES_PATH": str(rules),
                       "CRS_CREDIT_PRODUCT_CONFIG": "sponsor-config", "CRS_ACCESS_TOKEN": "PRIVATE_TOKEN"}.items():
        monkeypatch.setenv(key, value)
    real = httpx.Client
    calls = []
    def handler(req):
        calls.append(req.url.path)
        return httpx.Response(200, json={"credit": {"score": "745"}, "fraud": {"result": "clear_fixture"}, "ssn": "PRIVATE_TEST_SSN"})
    monkeypatch.setattr(httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handler)))
    first = crs_credit.pull_credit_report(store, "tracks", "business_1", "sponsor_a")
    second = crs_credit.pull_credit_report(store, "tracks", "business_1", "sponsor_a")
    assert first["score"] == 745 and first["risk_decision"] == "clear"
    assert second["cached"] and calls == ["/api/experian/credit-report/standard/sponsor-config"]
    assert "PRIVATE_TEST_SSN" not in json.dumps(first) and "PRIVATE_TOKEN" not in json.dumps(first)



@pytest.mark.parametrize("raw", [{"errorMessages": [{"code": "E1005"}]}, []])
def test_crs_http_200_error_payload_never_becomes_evidence(store, monkeypatch, tmp_path, raw):
    from backend.provider import ProviderError
    profile = tmp_path / "profiles.json"
    profile.write_text(json.dumps({"sponsor_a": {"sponsor_test_identity": True, "credit_request": {"test": "synthetic"}}}))
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps({"score_path": "scores.0.scoreValue", "risk_rules": []}))
    for key, value in {"CRS_TEST_PROFILES_PATH": str(profile), "CRS_CREDIT_RULES_PATH": str(rules),
                       "CRS_CREDIT_PRODUCT_CONFIG": "sponsor-config", "CRS_ACCESS_TOKEN": "TEST_TOKEN"}.items():
        monkeypatch.setenv(key, value)
    real = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(lambda req: httpx.Response(200, json=raw))))
    with pytest.raises(ProviderError, match="underwriting remains held"):
        crs_credit.pull_credit_report(store, "tracks", "business_1", "sponsor_a")
    assert store.sponsor_reports("tracks", "credit_profile") == []

def calibration():
    return {"calibration_id": "test_apify", "geography": "San Francisco, CA", "collected_at": "2026-10-24T00:00:00Z", "provider": "apify",
            "price_cents": [1200, 1500], "daily_wage_cents": [16000, 22000],
            "sources": [{"actor_id": "fixture~actor", "run_id": "fixtureRun", "dataset_id": "fixtureData", "source_url": "https://example.com/public-fixture"}]}


def test_calibrated_world_freezes_samples_for_reset_and_forks(tmp_path, monkeypatch):
    root = tmp_path / "calibrations"
    root.mkdir()
    payload = calibration()
    (root / "test_apify.json").write_text(json.dumps(payload))
    monkeypatch.setenv("APIFY_CALIBRATION_DIR", str(root))
    with TestClient(create_app(tmp_path / "calibration.sqlite3")) as client:
        created = client.post("/api/worlds", json={"calibration_id": "test_apify", "households": 8, "businesses": 2, "banks": 2})
        assert created.status_code == 201
        world = created.json()
        assert world["calibration"]["provider"] == "apify"
        store = client.app.state.store
        original = store.get(world["simulation_id"])
        assert all(e["price_cents"] in [1200, 1500] for e in original.state["entities"].values() if e["kind"] == "business")
        assert all(e["wage_cents"] in [16000, 22000] for e in original.state["entities"].values() if e["kind"] == "household")
        (root / "test_apify.json").unlink()
        reset = client.post(f"/api/worlds/{world['simulation_id']}/reset", json={"request_id": "reset"}).json()
        fresh = client.get(f"/api/worlds/{reset['simulation_id']}").json()
        assert fresh["calibration"] == world["calibration"]
        fork = store.fork(world["simulation_id"], {"request_id": "f", "bank_id": "bank_1", "budget_cents": 1000, "ticks": 2})
        assert all(checksum(store.get(b["simulation_id"]).state["calibration"]) == checksum(original.state["calibration"]) for b in fork["branches"])
        assert client.post("/api/worlds", json={"calibration_id": "test_apify"}).status_code == 503


def test_apify_units_are_explicit_and_no_annual_salary_in_daily_wages():
    assert cents(20, "usd_hour") == 16000
    assert cents(52000, "usd_year") == 20000
    assert cents("12.49", "usd_item") == 1249
    with pytest.raises(ValueError):
        cents("$20–$30/hr", "usd_hour")
    with pytest.raises(ValueError):
        cents(100, "unknown")


def test_full_fetch_experiment_and_follow_up_use_saved_evidence(monkeypatch):
    from backend.fetch_chat import handle_command
    from backend.models import AgentRunRequest
    real = httpx.AsyncClient
    paths = []
    def handler(req):
        path = req.url.path
        paths.append(path)
        if path == "/api/worlds":
            return httpx.Response(201, json={"simulation_id": "chat_world"})
        if path.endswith("/shocks"):
            assert json.loads(req.content)["loss_bps"] == 4000
            return httpx.Response(200, json={})
        if path.endswith("/agent-jobs"):
            body = AgentRunRequest.model_validate(json.loads(req.content))
            assert body.target_bank_id == "bank_1" and not body.allow_paid_research
            return httpx.Response(202, json={"job_id": "job_chat", "status": "completed", "report_url": "/api/agent-runs/chat"})
        if path == "/api/agent-jobs/job_chat":
            return httpx.Response(200, json={"job_id": "job_chat", "status": "completed", "report_url": "/api/agent-runs/chat"})
        if path == "/api/agent-runs/chat":
            return httpx.Response(200, json={"simulation_id": "chat_world", "provider": "nebius", "comparison_ids": ["fork_chat"],
                   "recommendation": {"strategy": "no_intervention", "rationale": "Saved financial evidence"}, "trace": [{"tool": "compare_interventions"}]})
        if path == "/api/forks/fork_chat":
            return httpx.Response(200, json={"branches": [{"strategy": str(i), "metrics": {"employment_rate": .5}, "delta_vs_no_intervention": {}} for i in range(3)]})
        return httpx.Response(200, json={})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    result = json.loads(asyncio.run(handle_command("stress-test bank 1 with a 40% loss and compare rescue plans")))
    assert result["created_world_id"] == "chat_world" and len(result["three_futures"]) == 3
    assert "/api/worlds/chat_world/shocks" in paths
    follow = json.loads(asyncio.run(handle_command("why did you pick that?", previous={"job_id": "job_chat"})))
    assert follow["saved_public_trace"] and follow["recommendation"]["rationale"] == "Saved financial evidence"
    assert follow["funds_applied"] is False


def test_uncertain_paid_purchase_is_not_automatically_repeated(store, monkeypatch):
    from backend.paid_research import buy_market_forecast
    from backend.provider import ProviderError
    import sys
    import subprocess
    monkeypatch.setenv("X402_PYTHON", sys.executable)
    monkeypatch.setenv("X402_WALLET_PRIVATE_KEY", "unit-test-only")
    monkeypatch.setenv("X402_MERCHANT_ADDRESS", "unit-test-only")
    calls = []
    def uncertain(*args, **kwargs):
        calls.append(args)
        raise subprocess.TimeoutExpired(args[0], 65)
    monkeypatch.setattr(subprocess, "run", uncertain)
    report = {"run_id": "test-paid", "simulation_id": "tracks", "snapshot_sha256": "a"*64,
              "request": {"mode": "live", "allow_paid_research": True}}
    with pytest.raises(ProviderError):
        buy_market_forecast(store, report)
    with pytest.raises(ProviderError, match="already attempted"):
        buy_market_forecast(store, report)
    assert len(calls) == 1
    report["request"]["allow_paid_research"] = False
    with pytest.raises(ProviderNotConfigured):
        buy_market_forecast(store, report)


def test_failed_optional_paid_tool_does_not_break_policy_analysis(store, monkeypatch):
    from backend import agents, paid_research
    from backend.models import AgentRunRequest
    from backend.provider import ProviderError
    class Model(agents.DemoModel):
        def complete(self, messages, tools):
            results = [m for m in messages if m["role"] == "tool"]
            if len(results) == 1:
                return {"role": "assistant", "content": None, "tool_calls": [{"id": "paid-check", "type": "function", "function": {"name": "buy_market_forecast", "arguments": "{}"}}]}
            return super().complete(messages, tools)
    body = AgentRunRequest(request_id="optional-paid", mode="live", allow_paid_research=True, max_experiments=1).model_dump()
    monkeypatch.setattr(agents, "build_model", lambda request: Model(request))
    monkeypatch.setattr(paid_research, "buy_market_forecast", lambda *args: (_ for _ in ()).throw(ProviderError("Testnet research unavailable")))
    before = snapshot_hash(store.get("tracks").state)
    result = agents.run_agent(store, "tracks", body)
    assert result["status"] == "completed"
    assert any(t["tool"] == "buy_market_forecast" and t["status"] == "rejected" for t in result["trace"])
    assert snapshot_hash(store.get("tracks").state) == before


def test_apify_run_dataset_provenance_and_invalid_rows():
    from scripts.apify_calibrate import collect
    def handler(request):
        assert "token" not in request.url.params
        if request.method == "POST":
            return httpx.Response(201, json={"data": {"id": "Run123"}})
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json={"data": {"status": "SUCCEEDED", "defaultDatasetId": "Data123", "actId": "Actor123"}})
        return httpx.Response(200, json=[{"pay": 20}, {"pay": "unparsed salary range"}])
    spec = {"actor_id": "fixture~actor", "input": {"city": "San Francisco"}, "value_path": "pay", "unit": "usd_hour", "source_url": "https://example.com/fixture"}
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        samples, provenance = collect(spec, client)
    assert samples == [16000] and provenance["skipped"] == 1
    assert provenance["actor_id"] == "Actor123" and provenance["dataset_id"] == "Data123"
