"""Bounded, persistent agent jobs. Interrupted work is never automatically replayed."""

import asyncio
import json
import logging
import time
from uuid import uuid4

from backend.ledger import LedgerError


class QueueFull(LedgerError):
    pass


class JobStore:
    @staticmethod
    def init_job_tables(connection):
        connection.execute("""CREATE TABLE IF NOT EXISTS agent_jobs (
            id TEXT PRIMARY KEY, source_id TEXT NOT NULL, kind TEXT NOT NULL,
            actor_id TEXT NOT NULL, request_id TEXT NOT NULL, request TEXT NOT NULL,
            status TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
            owner TEXT, lease_until REAL, error TEXT,
            UNIQUE(source_id, kind, actor_id, request_id))""")

    @staticmethod
    def recover_jobs(connection, now):
        connection.execute("""UPDATE agent_jobs SET status='failed', updated=?, error=?
            WHERE status='running' AND lease_until < ?""",
            (now, "Worker heartbeat expired. Inspect the linked report and any settlement before starting a new request; work was not replayed.", now))

    @staticmethod
    def job_view(connection, row):
        (job_id, source, kind, actor, request_id, request, status, created, updated,
         owner, lease_until, error) = row
        # Identifiers come exclusively from the fixed workflow mapping.
        table, actor_column, prefix = {
            "central_bank": ("agent_runs", None, "agent-runs"),
            "credit": ("credit_runs", "business_id", "credit-runs"),
            "procurement": ("procurement_runs", "buyer_id", "procurement-runs")}[kind]
        query = f"SELECT id, report FROM {table} WHERE source_id=? AND request_id=?"
        params = [source, request_id]
        if actor_column:
            query += f" AND {actor_column}=?"
            params.append(actor)
        report = connection.execute(query, params).fetchone()
        return {"job_id": job_id, "simulation_id": source, "kind": kind,
                "actor_id": actor or None, "request": json.loads(request), "status": status,
                "created_at": created, "updated_at": updated, "error": error,
                "run_id": report[0] if report else None,
                "report_url": f"/api/{prefix}/{report[0]}" if report else None,
                "report_status": json.loads(report[1])["status"] if report else None}

    def enqueue_job(self, simulation_id, kind, actor_id, request, now=None):
        now = time.time() if now is None else now
        actor_id = actor_id or ""
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            world = self.load(connection, simulation_id)
            if actor_id and world.customer(actor_id)["kind"] != "business":
                raise LedgerError("Agent jobs require a business actor")
            row = connection.execute("""SELECT * FROM agent_jobs
                WHERE source_id=? AND kind=? AND actor_id=? AND request_id=?""",
                (simulation_id, kind, actor_id, request["request_id"])).fetchone()
            if row:
                saved = json.loads(row[5])
                if kind == "credit":
                    from backend.models import CreditRunRequest
                    equivalent = CreditRunRequest.model_validate(saved) == CreditRunRequest.model_validate(request)
                elif kind == "central_bank":
                    from backend.models import AgentRunRequest
                    equivalent = AgentRunRequest.model_validate(saved) == AgentRunRequest.model_validate(request)
                else:
                    equivalent = saved == request
                if not equivalent:
                    raise LedgerError("Job request ID already used with different contents")
                return self.job_view(connection, row)
            self.recover_jobs(connection, now)
            if connection.execute("SELECT COUNT(*) FROM agent_jobs WHERE status IN ('queued','running')").fetchone()[0] >= 32:
                raise QueueFull("Agent queue is full; retry later with the same request ID")
            job_id = f"job_{uuid4().hex}"
            connection.execute("INSERT INTO agent_jobs VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?, NULL, NULL, NULL)",
                               (job_id, simulation_id, kind, actor_id, request["request_id"], json.dumps(request), now, now))
            return self.job_view(connection, connection.execute("SELECT * FROM agent_jobs WHERE id=?", (job_id,)).fetchone())

    def get_job(self, job_id):
        with self.connection() as connection:
            row = connection.execute("SELECT * FROM agent_jobs WHERE id=?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            return self.job_view(connection, row)

    def list_jobs(self, simulation_id, limit=50):
        with self.connection() as connection:
            self.load(connection, simulation_id)
            rows = connection.execute("SELECT * FROM agent_jobs WHERE source_id=? ORDER BY created DESC, rowid DESC LIMIT ?",
                                      (simulation_id, limit)).fetchall()
            return [self.job_view(connection, row) for row in rows]

    def cancel_job(self, job_id):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT status FROM agent_jobs WHERE id=?", (job_id,)).fetchone()
            if row is None:
                raise KeyError(job_id)
            if row[0] not in ("queued", "cancelled"):
                raise LedgerError("Only queued jobs can be cancelled; running work may already have settled funds")
            connection.execute("UPDATE agent_jobs SET status='cancelled', updated=? WHERE id=?", (time.time(), job_id))
            return self.job_view(connection, connection.execute("SELECT * FROM agent_jobs WHERE id=?", (job_id,)).fetchone())

    def claim_job(self, owner, now=None):
        now = time.time() if now is None else now
        with self.connection() as connection:
            has_work = connection.execute(
                "SELECT 1 FROM agent_jobs WHERE status='queued' OR (status='running' AND lease_until <= ?) LIMIT 1",
                (now,)
            ).fetchone()
            if not has_work:
                return None
            connection.execute("BEGIN IMMEDIATE")
            self.recover_jobs(connection, now)
            if connection.execute("SELECT COUNT(*) FROM agent_jobs WHERE status='running'").fetchone()[0] >= 2:
                return None
            row = connection.execute("SELECT id FROM agent_jobs WHERE status='queued' ORDER BY created, rowid LIMIT 1").fetchone()
            if row is None:
                return None
            connection.execute("UPDATE agent_jobs SET status='running', owner=?, lease_until=?, updated=? WHERE id=?",
                               (owner, now + 60, now, row[0]))
            return self.job_view(connection, connection.execute("SELECT * FROM agent_jobs WHERE id=?", row).fetchone())

    def heartbeat_job(self, job_id, owner):
        now = time.time()
        with self.connection() as connection:
            connection.execute("""UPDATE agent_jobs SET lease_until=?, updated=?
                WHERE id=? AND owner=? AND status='running'""", (now + 60, now, job_id, owner))

    def finish_job(self, job_id, owner, error=None):
        with self.connection() as connection:
            connection.execute("""UPDATE agent_jobs SET status=?, error=?, updated=?
                WHERE id=? AND owner=? AND status='running'""",
                ("failed" if error else "completed", error, time.time(), job_id, owner))


def execute_job(store, job):
    from backend.agents import run_agent
    from backend.credit_agents import run_credit
    from backend.procurement import run_procurement

    args = (store, job["simulation_id"])
    if job["kind"] == "central_bank":
        return run_agent(*args, job["request"])
    if job["kind"] == "credit":
        return run_credit(*args, job["actor_id"], job["request"])
    return run_procurement(*args, job["actor_id"], job["request"])


async def job_worker(store, stop):
    owner = uuid4().hex
    while not stop.is_set():
        had_job = False
        try:
            job = await asyncio.to_thread(store.claim_job, owner)
            if job:
                had_job = True
                task = asyncio.create_task(asyncio.to_thread(execute_job, store, job))
                while not task.done():
                    await asyncio.wait({task}, timeout=5)
                    try:
                        await asyncio.to_thread(store.heartbeat_job, job["job_id"], owner)
                    except Exception:
                        logging.getLogger(__name__).exception("Agent job heartbeat could not be saved")
                try:
                    report = task.result()
                    error = "Agent workflow failed; inspect its report" if report["status"] == "failed" else None
                except Exception:
                    logging.getLogger(__name__).exception("Agent job failed: %s", job["job_id"])
                    error = "Agent job could not complete; inspect its report and any settlement before retrying"
                await asyncio.to_thread(store.finish_job, job["job_id"], owner, error)
        except Exception:
            logging.getLogger(__name__).exception("Agent job worker could not access storage")
        try:
            await asyncio.wait_for(stop.wait(), timeout=0.05 if had_job else 0.5)
        except TimeoutError:
            pass
