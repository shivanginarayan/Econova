"""Sponsor evidence is separate from the financial ledger; no raw identity data."""
import json
import time
from uuid import uuid4

from backend.ledger import LedgerError


class SponsorStore:
    @staticmethod
    def init_sponsor_tables(connection):
        connection.execute("""CREATE TABLE IF NOT EXISTS sponsor_reports (
            id TEXT PRIMARY KEY, source_id TEXT NOT NULL, kind TEXT NOT NULL,
            created REAL NOT NULL, report TEXT NOT NULL)""")
        connection.execute("""CREATE TABLE IF NOT EXISTS spacetime_sync (
            source_id TEXT PRIMARY KEY, cursor INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1, error TEXT, updated REAL NOT NULL)""")

    def save_sponsor_report(self, simulation_id, kind, report):
        report = {**report, "report_id": "evidence_" + uuid4().hex,
                  "simulation_id": simulation_id, "created_at": time.time()}
        with self.connection() as connection:
            self.load(connection, simulation_id)
            connection.execute("INSERT INTO sponsor_reports VALUES (?, ?, ?, ?, ?)",
                               (report["report_id"], simulation_id, kind, report["created_at"], json.dumps(report)))
        return report

    def sponsor_reports(self, simulation_id, kind):
        with self.connection() as connection:
            self.load(connection, simulation_id)
            rows = connection.execute("SELECT report FROM sponsor_reports WHERE source_id=? AND kind=? ORDER BY created DESC LIMIT 50",
                                      (simulation_id, kind)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def guarded_payment(self, simulation_id, report_id, body):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            world = self.load(connection, simulation_id)
            row = connection.execute("SELECT report FROM sponsor_reports WHERE id=? AND source_id=? AND kind='fraud'",
                                     (report_id, simulation_id)).fetchone()
            if not row:
                raise KeyError(report_id)
            report = json.loads(row[0])
            if report["decision"] != "clear" or report["provider"] != "crs":
                raise LedgerError("Payment held: a live, explicitly clear CRS screen is required")
            if report["entity_id"] != body["receiver_id"]:
                raise LedgerError("Fraud screen belongs to a different receiver")
            # Return successful retries even after expiry or playback advancement.
            previous = world.ledger._transactions.get(body["transaction_id"])
            if previous:
                if previous["metadata"].get("fraud_report_id") != report_id:
                    raise LedgerError("Transaction ID already used with a different fraud screen")
                return world.pay(**body)
            if world.state["tick"] != report["source_tick"] or time.time() - report["created_at"] > 900:
                raise LedgerError("Fraud screen expired or world advanced; screen again")
            result = world.pay(**body)
            result["metadata"]["fraud_report_id"] = report_id
            world.emit("fraud_screened_payment", body["payer_id"], body["receiver_id"],
                       body["amount_cents"], body["transaction_id"], {"fraud_report_id": report_id})
            world.audit()
            connection.execute("UPDATE worlds SET state=? WHERE id=?", (json.dumps(world.state), simulation_id))
            return result
