import asyncio
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import fraud, research, spacetime
from backend.engine import Economy
from backend.fetch_chat import handle_command
from backend.ledger import LedgerError
from backend.main import create_app
from backend.models import AgentRunRequest
from backend.provider import ProviderError
from backend.store import Store


@pytest.fixture
def store(tmp_path):
    instance = Store(tmp_path / "sponsors.sqlite3")
    instance.create(Economy.create("world_test", households=8, businesses=2, banks=2))
    return instance


def test_unknown_fraud_decisions_never_clear():
    rules = [{"path": "verification.result", "clear_values": ["PASS"], "blocked_values": ["FRAUD"]}]
    assert fraud.normalize({}, rules)[0] == "review"
    assert fraud.normalize({"verification": {"result": "new_vendor_code"}}, rules)[0] == "review"
    assert fraud.normalize({"verification": {"result": "PASS"}}, rules)[0] == "clear"
    assert fraud.normalize({"verification": {"result": "FRAUD"}}, rules)[0] == "blocked"
    assert fraud.normalize({"verification": {"result": "PASS"}}, [*rules, {"path": "missing"}])[0] == "review"
    assert fraud.normalize({"anything": "PASS"}, [])[0] == "review"


def clear_screen(store, **changes):
    return store.save_sponsor_report("world_test", "fraud", {
        "provider": "crs", "decision": "clear", "entity_id": "business_2", "source_tick": 0, **changes})


PAYMENT = {"transaction_id": "screened-test", "payer_id": "business_1", "receiver_id": "business_2", "amount_cents": 100}


def test_guarded_payment_binds_receiver_and_retries_exactly_once(store):
    report = clear_screen(store)
    wrong = {**PAYMENT, "receiver_id": "household_1"}
    with pytest.raises(LedgerError):
        store.guarded_payment("world_test", report["report_id"], wrong)
    initial = len(store.get("world_test").ledger.state["journal"])
    first = store.guarded_payment("world_test", report["report_id"], PAYMENT)
    assert first["metadata"]["fraud_report_id"] == report["report_id"]
    assert store.guarded_payment("world_test", report["report_id"], PAYMENT) == first
    assert len(store.get("world_test").ledger.state["journal"]) == initial + 1
    store.mutate("world_test", lambda w: w.step())
    assert store.guarded_payment("world_test", report["report_id"], PAYMENT) == first
    with pytest.raises(LedgerError):
        store.guarded_payment("world_test", report["report_id"], {**PAYMENT, "amount_cents": 101})
    assert store.get("world_test").audit()["balanced"]


@pytest.mark.parametrize("changes", [{"decision": "review"}, {"decision": "blocked"}, {"provider": "local_demo"}, {"source_tick": 1}])
def test_held_or_stale_screens_cannot_move_money(store, changes):
    report = clear_screen(store, **changes)
    before = store.get("world_test").state
    with pytest.raises(LedgerError):
        store.guarded_payment("world_test", report["report_id"], PAYMENT)
    assert store.get("world_test").state == before


def test_expired_screen_holds_payment(store, monkeypatch):
    report = clear_screen(store)
    monkeypatch.setattr(time, "time", lambda: report["created_at"] + 901)
    with pytest.raises(LedgerError):
        store.guarded_payment("world_test", report["report_id"], PAYMENT)


def mock_client(monkeypatch, module, handler):
    real = httpx.Client
    monkeypatch.setattr(module.httpx, "Client", lambda **kwargs: real(transport=httpx.MockTransport(handler)))


def configure_crs(tmp_path, monkeypatch):
    profile = tmp_path / "profiles.json"
    profile.write_text(json.dumps({"test_a": {"sponsor_test_identity": True, "request": {"firstName": "SPONSOR_FIXTURE", "ssn": "never-persist-this"}}}))
    rules = tmp_path / "rules.json"
    rules.write_text(json.dumps([{"path": "verification.result", "clear_values": ["PASS"], "blocked_values": ["FRAUD"]}]))
    for key, value in {"CRS_USERNAME": "test", "CRS_PASSWORD": "private-password", "CRS_PRODUCT_CONFIG": "test-config",
                       "CRS_TEST_PROFILES_PATH": str(profile), "CRS_DECISION_RULES_PATH": str(rules)}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("CRS_ACCESS_TOKEN", raising=False)


def test_crs_auth_screen_and_redacted_persistence(store, tmp_path, monkeypatch):
    configure_crs(tmp_path, monkeypatch)
    paths = []
    def handler(request):
        paths.append(request.url.path)
        if request.url.path.endswith("/users/login"):
            return httpx.Response(200, json={"token": "private-token"})
        assert request.headers["Authorization"] == "Bearer private-token"
        return httpx.Response(200, json={"verification": {"result": "PASS"}, "ssn": "never-persist-this"})
    mock_client(monkeypatch, fraud, handler)
    result = fraud.screen(store, "world_test", "business_2", "test_a")
    assert result["decision"] == "clear"
    assert paths == ["/api/users/login", "/api/transunion/identity-manager-verification/basic/test-config"]
    persisted = json.dumps(store.sponsor_reports("world_test", "fraud"))
    assert all(secret not in persisted for secret in ("never-persist-this", "private-token", "private-password"))


def test_crs_http_errors_are_sanitized(store, tmp_path, monkeypatch):
    configure_crs(tmp_path, monkeypatch)
    mock_client(monkeypatch, fraud, lambda request: httpx.Response(401, text="private-password ssn"))
    with pytest.raises(ProviderError) as exc:
        fraud.screen(store, "world_test", "business_2", "test_a")
    assert "401" in str(exc.value) and "private-password" not in str(exc.value)
    assert not store.sponsor_reports("world_test", "fraud")


def test_fetch_research_numbers_come_from_tools(store, monkeypatch):
    monkeypatch.setenv("ASI1_API_KEY", "test-private-key")
    monkeypatch.setattr(research, "population", lambda: {"tool": "get_population", "population_estimate": 123, "source": "Census fixture"})
    monkeypatch.setattr(research, "bank_directory", lambda: {"tool": "get_bank_directory", "total_institutions": 5, "source": "FDIC fixture"})
    def handler(request):
        assert request.headers["Authorization"] == "Bearer test-private-key"
        return httpx.Response(200, json={"choices": [{"message": {"content": "Population is 999999999", "tool_calls": [
            {"id": "p", "type": "function", "function": {"name": "get_population", "arguments": "{}"}},
            {"id": "b", "type": "function", "function": {"name": "get_bank_directory", "arguments": "{}"}}]}}]})
    mock_client(monkeypatch, research, handler)
    report = research.research(store, "world_test")
    assert report["status"] == "completed" and len(report["trace"]) == 2
    assert report["observations"][0]["population_estimate"] == 123
    assert "999999999" not in json.dumps(report)
    assert "test-private-key" not in json.dumps(report)


def test_failed_data_source_is_not_fabricated(store, monkeypatch):
    monkeypatch.setattr(research, "population", lambda: (_ for _ in ()).throw(ValueError("bad source")))
    monkeypatch.setattr(research, "bank_directory", lambda: {"total_institutions": 5})
    report = research.retrieve_sources(store, "world_test")
    assert report["status"] == "partial" and "error" in report["observations"][0]


def test_spacetime_failure_retries_without_advancing_cursor(store, monkeypatch):
    monkeypatch.setenv("SPACETIMEDB_DATABASE", "test-db")
    monkeypatch.setenv("SPACETIMEDB_TOKEN", "private-token")
    received = []
    healthy = False
    def handler(request):
        received.append(json.loads(json.loads(request.content)[0]))
        return httpx.Response(200 if healthy else 503)
    mock_client(monkeypatch, spacetime, handler)
    before = store.get("world_test").state
    with pytest.raises(ProviderError):
        spacetime.enable(store, "world_test")
    assert spacetime.sync_status(store, "world_test")["last_sequence"] == 0
    healthy = True
    spacetime.sync_world(store, "world_test")
    assert spacetime.sync_status(store, "world_test")["last_sequence"] == 1
    assert received[0] == received[1]
    assert store.get("world_test").state == before


def test_public_api_keeps_demo_and_live_separate(store):
    with TestClient(create_app(store.path)) as client:
        path = "/api/worlds/world_test"
        response = client.post(path + "/fraud/screens", json={"entity_id": "business_2", "profile_id": "demo_identity_mismatch", "mode": "demo"})
        report = response.json()
        assert response.status_code == 200 and report["decision"] == "blocked"
        assert client.post(path + "/fraud/payments", json={**PAYMENT, "fraud_report_id": report["report_id"]}).status_code == 409
        assert client.get(path + "/data-context").json()["origin"] == "seeded_synthetic"
        assert client.get(path + "/fraud/screens").json()[0]["report_id"] == report["report_id"]


def test_optional_missing_crs_profile_file_does_not_break_dashboard(store, monkeypatch):
    monkeypatch.setenv("CRS_TEST_PROFILES_PATH", "data/nonexistent-sponsor-profiles.json")
    with TestClient(create_app(store.path)) as client:
        result = client.get("/api/fraud/profiles")
        assert result.status_code == 200
        assert result.json()["profiles"] == [] and result.json()["configuration_error"]


def test_fetch_chat_runs_actual_job_schema_and_returns_recommendation(monkeypatch):
    real = httpx.AsyncClient
    def handler(request):
        if request.url.path.endswith("/agent-jobs"):
            AgentRunRequest.model_validate(json.loads(request.content))
            return httpx.Response(202, json={"job_id": "job_test", "status": "completed", "report_url": "/api/agent-runs/run_test"})
        return httpx.Response(200, json={"provider": "nebius", "recommendation": {"strategy": "no_intervention"}, "trace": []})
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real(transport=httpx.MockTransport(handler), **kwargs))
    result = json.loads(asyncio.run(handle_command("stress world_test")))
    assert result["funds_applied"] is False
    assert result["recommendation"]["strategy"] == "no_intervention"
    assert "data <world_id>" in asyncio.run(handle_command("delete everything"))
