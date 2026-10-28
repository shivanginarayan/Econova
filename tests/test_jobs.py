import asyncio
import time
from threading import Event
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.engine import Economy
from backend.jobs import QueueFull, execute_job, job_worker
from backend.ledger import LedgerError
from backend.main import create_app
from backend.models import AgentRunRequest, CreditRunRequest, ProcurementRequest
from backend.store import Store


def request(request_id="job-test"):
    return AgentRunRequest(request_id=request_id, mode="demo", ticks=2, max_experiments=1).model_dump()


@pytest.fixture
def store(tmp_path):
    instance = Store(tmp_path / "jobs.sqlite3")
    instance.create(Economy.create("world", households=8, businesses=3, banks=2))
    return instance


def test_concurrent_enqueue_retries_and_conflicts(store):
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = list(pool.map(lambda _: store.enqueue_job("world", "central_bank", None, request()), range(8)))
    assert all(job == jobs[0] for job in jobs)
    assert len(store.list_jobs("world")) == 1
    with pytest.raises(LedgerError, match="different contents"):
        store.enqueue_job("world", "central_bank", None, {**request(), "ticks": 3})
    assert store.get("world").state["tick"] == 0


def test_fifo_claim_and_global_concurrency_cap(store):
    jobs = [store.enqueue_job("world", "central_bank", None, request(str(i)), now=10) for i in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        claimed = list(pool.map(lambda i: store.claim_job(str(i), now=11), range(8)))
    assert {job["job_id"] for job in claimed if job} == {job["job_id"] for job in jobs[:2]}
    assert len([job for job in store.list_jobs("world") if job["status"] == "running"]) == 2


def test_queued_cancel_and_running_cancel_rejection(store):
    job = store.enqueue_job("world", "central_bank", None, request())
    assert store.cancel_job(job["job_id"])["status"] == "cancelled"
    assert store.cancel_job(job["job_id"])["status"] == "cancelled"
    assert store.enqueue_job("world", "central_bank", None, request())["status"] == "cancelled"
    assert store.claim_job("worker") is None
    job = store.enqueue_job("world", "central_bank", None, request("second"))
    store.claim_job("worker")
    with pytest.raises(LedgerError, match="Only queued"):
        store.cancel_job(job["job_id"])


def test_queue_bounds_and_retry_when_capacity_available(store):
    jobs = [store.enqueue_job("world", "central_bank", None, request(str(i))) for i in range(32)]
    with pytest.raises(QueueFull):
        store.enqueue_job("world", "central_bank", None, request("overflow"))
    assert store.enqueue_job("world", "central_bank", None, request("0"))["job_id"] == jobs[0]["job_id"]
    store.cancel_job(jobs[0]["job_id"])
    assert store.enqueue_job("world", "central_bank", None, request("overflow"))["status"] == "queued"


def test_expired_worker_is_failed_and_never_replayed(store):
    job = store.enqueue_job("world", "central_bank", None, request(), now=10)
    store.claim_job("old", now=10)
    assert Store(store.path).claim_job("new", now=71) is None
    assert store.get_job(job["job_id"])["status"] == "failed"
    store.finish_job(job["job_id"], "old")
    store.heartbeat_job(job["job_id"], "old")
    assert store.get_job(job["job_id"])["status"] == "failed"
    assert store.enqueue_job("world", "central_bank", None, request())["status"] == "failed"


def test_heartbeat_and_owner_fencing(store):
    job = store.enqueue_job("world", "central_bank", None, request())
    store.claim_job("owner", now=10)
    store.finish_job(job["job_id"], "wrong")
    assert store.get_job(job["job_id"])["status"] == "running"
    store.heartbeat_job(job["job_id"], "owner")
    assert store.claim_job("other", now=time.time()) is None
    store.finish_job(job["job_id"], "owner")
    assert store.get_job(job["job_id"])["status"] == "completed"


@pytest.mark.parametrize("kind", ["central_bank", "credit", "procurement"])
def test_real_workflow_dispatch_progress_and_idempotent_settlement(store, kind):
    body = request()
    actor = None
    if kind == "credit":
        body = CreditRunRequest(request_id="credit-job", mode="demo", auto_settle=True).model_dump()
        actor = "business_1"
        def drain(world):
            world.pay("setup-drain", actor, "business_2", world.ledger.balance(f"{actor}:deposit"))
        store.mutate("world", drain)
    elif kind == "procurement":
        body = ProcurementRequest(request_id="supply-job", mode="demo", auto_settle=True).model_dump()
        actor = "business_1"
    job = store.enqueue_job("world", kind, actor, body)
    claimed = store.claim_job("worker")
    report = execute_job(store, claimed)
    assert report["status"] == {"central_bank": "completed", "credit": "settled", "procurement": "contracted"}[kind]
    assert execute_job(store, claimed) == report
    store.finish_job(job["job_id"], "worker")
    result = store.get_job(job["job_id"])
    assert result["run_id"] == report["run_id"]
    assert result["report_status"] == report["status"]
    assert result["report_url"].endswith(report["run_id"])
    assert store.get("world").audit()["balanced"]
    if kind == "procurement":
        assert len(store.get("world").state["contracts"]) == 1


def test_worker_sanitizes_unexpected_errors_and_continues(store, monkeypatch):
    import backend.jobs as jobs_module
    job = store.enqueue_job("world", "central_bank", None, request())
    def fail(*args):
        raise RuntimeError("sensitive test diagnostic")
    monkeypatch.setattr(jobs_module, "execute_job", fail)
    async def exercise():
        stop = asyncio.Event()
        worker = asyncio.create_task(job_worker(store, stop))
        for _ in range(100):
            if store.get_job(job["job_id"])["status"] == "failed":
                break
            await asyncio.sleep(0.02)
        stop.set()
        await worker
    asyncio.run(exercise())
    result = store.get_job(job["job_id"])
    assert result["status"] == "failed"
    assert "sensitive" not in result["error"]


def test_job_api_accepts_and_polls_background_run(tmp_path):
    with TestClient(create_app(tmp_path / "api.sqlite3")) as client:
        world = client.post("/api/worlds", json={"households": 8, "businesses": 3, "banks": 2}).json()
        base = f"/api/worlds/{world['simulation_id']}"
        response = client.post(base + "/agent-jobs", json=request())
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            job = client.get(f"/api/agent-jobs/{job_id}").json()
            if job["status"] in ("completed", "failed"):
                break
            time.sleep(0.03)
        assert job["status"] == "completed"
        assert client.get(job["report_url"]).json()["status"] == "completed"
        assert client.post(base + "/agent-jobs", json=request()).json()["job_id"] == job_id
        assert client.post(f"/api/agent-jobs/{job_id}/cancel").status_code == 409
        assert len(client.get(base + "/agent-jobs").json()) == 1
        assert client.get(base + "/agent-jobs?limit=101").status_code == 422
        assert client.post(base + "/businesses/household_1/credit-jobs", json={"request_id": "bad"}).status_code == 409
        assert client.get("/api/agent-jobs/missing").status_code == 404


def test_http_queue_limit_and_cancel_without_workers(tmp_path):
    # Without a lifespan context no worker runs, so the queue stays deterministic.
    client = TestClient(create_app(tmp_path / "queue.sqlite3"))
    world = client.post("/api/worlds", json={}).json()
    base = f"/api/worlds/{world['simulation_id']}"
    for index in range(32):
        assert client.post(base + "/agent-jobs", json=request(str(index))).status_code == 202
    response = client.post(base + "/agent-jobs", json=request("overflow"))
    assert response.status_code == 429
    assert response.headers["retry-after"] == "5"
    job = client.get(base + "/agent-jobs").json()[0]
    assert client.post(f"/api/agent-jobs/{job['job_id']}/cancel").json()["status"] == "cancelled"


def test_slow_model_does_not_block_http_or_progress(tmp_path, monkeypatch):
    from backend.agents import DemoModel
    entered, release = Event(), Event()
    original = DemoModel.complete
    def slow_complete(self, messages, tools):
        entered.set()
        assert release.wait(timeout=5)
        return original(self, messages, tools)
    monkeypatch.setattr(DemoModel, "complete", slow_complete)
    with TestClient(create_app(tmp_path / "slow.sqlite3")) as client:
        world = client.post("/api/worlds", json={"households": 8, "businesses": 3, "banks": 2}).json()
        try:
            response = client.post(f"/api/worlds/{world['simulation_id']}/agent-jobs", json=request())
            assert response.status_code == 202
            assert entered.wait(timeout=3)
            job = client.get(f"/api/agent-jobs/{response.json()['job_id']}").json()
            assert job["status"] == "running"
            assert client.get("/health").status_code == 200
            assert client.get(job["report_url"]).json()["status"] == "running"
        finally:
            release.set()


def test_failed_report_marks_job_failed(store, monkeypatch):
    import backend.jobs as jobs_module
    job = store.enqueue_job("world", "central_bank", None, request())
    monkeypatch.setattr(jobs_module, "execute_job", lambda *_: {"status": "failed"})
    async def exercise():
        stop = asyncio.Event()
        worker = asyncio.create_task(job_worker(store, stop))
        for _ in range(100):
            if store.get_job(job["job_id"])["status"] == "failed":
                break
            await asyncio.sleep(0.02)
        stop.set()
        await worker
    asyncio.run(exercise())
    assert store.get_job(job["job_id"])["status"] == "failed"
