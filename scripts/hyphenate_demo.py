"""Rehearse real guard behavior with explicitly scripted agents; no sponsor success claims."""
import json
from unittest.mock import patch
from uuid import uuid4

from backend.agents import DemoModel, run_agent
from backend.credit_agents import run_credit
from backend.engine import Economy
from backend.forks import snapshot_hash
from backend.models import AgentRunRequest, CreditRunRequest
from backend.store import Store


class RecoveryRehearsal(DemoModel):
    provider = "scripted_rehearsal"
    model = "over-budget-recovery-v1"

    def __init__(self, request):
        super().__init__(request)
        self.rejected_once = False

    def complete(self, messages, tools):
        if not self.rejected_once and any(m["role"] == "tool" for m in messages):
            self.rejected_once = True
            return {"role": "assistant", "content": None, "tool_calls": [{"id": "rehearsal-over-budget", "type": "function",
                    "function": {"name": "compare_interventions", "arguments": json.dumps({"bank_id": "bank_1", "budget_cents": self.request["budget_cap_cents"] + 1})}}]}
        return super().complete(messages, tools)


def main():
    store = Store("data/hyphenate-rehearsal.sqlite3")
    world = Economy.create("rehearsal_" + uuid4().hex[:12], scenario="credit_crunch")
    world.shock("rehearsal-shock", "bank_1", loss_bps=4000)
    store.create(world)
    sid = world.state["simulation_id"]
    before = snapshot_hash(world.state)
    request = AgentRunRequest(request_id="guard-recovery", mode="demo", max_experiments=1).model_dump()
    with patch("backend.agents.build_model", return_value=RecoveryRehearsal(request)):
        report = run_agent(store, sid, request)
    assert report["status"] == "completed"
    assert any(t["status"] == "rejected" and "budget cap" in t["result"].get("error", "") for t in report["trace"])
    assert snapshot_hash(store.get(sid).state) == before
    borrower = Economy.create("review_" + uuid4().hex[:12])
    cash = borrower.ledger.balance(borrower.customer("business_1")["deposit_account"])
    borrower.pay("supplier-invoice", "business_1", "business_2", cash)
    store.create(borrower)
    credit = run_credit(store, borrower.state["simulation_id"], "business_1", CreditRunRequest(
        request_id="human-escalation", mode="demo", human_approval_threshold_cents=1, auto_settle=True).model_dump())
    assert credit["status"] == "needs_human_approval" and credit["settlement"] is None
    print(json.dumps({"provider": "scripted_rehearsal", "recovery_report_id": report["run_id"],
                      "rejected_tools": [t for t in report["trace"] if t["status"] == "rejected"],
                      "completed_recommendation": report["recommendation"], "source_unchanged": True,
                      "credit_status": credit["status"], "approval_reasons": credit["approval_reasons"],
                      "credit_not_settled": True, "balanced": store.get(sid).audit()["balanced"]}, indent=2))


if __name__ == "__main__":
    main()
