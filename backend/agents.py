"""Bounded observe–test–revise agent, with persisted public decision traces."""

import json

from pydantic import ValidationError

from backend.ledger import LedgerError
from backend.coordination import activity, review_report
from backend.models import CompareArguments, InspectArguments, RecommendArguments
from backend.provider import NebiusModel, ProviderError


TOOLS = [{"type": "function", "function": {"name": name, "description": description,
                                           "parameters": schema.model_json_schema()}}
         for name, description, schema in [
             ("inspect_economy", "Inspect the captured financial world before testing policies.", InspectArguments),
             ("compare_interventions", "Test all three strategies from the same snapshot at this budget and target bank.", CompareArguments),
             ("recommend_intervention", "Finish with a strategy from one of this run's tested comparisons and a concise public rationale.", RecommendArguments)]]


def observations(source):
    banks = []
    for entity in source.state["entities"].values():
        if entity["kind"] == "bank":
            sheet = source.ledger.sheet(entity["id"])
            banks.append({"bank_id": entity["id"], **source.bank_health(entity["id"]),
                          "equity_cents": sheet["equity_cents"], "assets_cents": sheet["assets_cents"],
                          "reserves_cents": sheet["assets"].get("reserves", 0)})
    return {"metrics": source.metrics(), "banks": banks,
            "shock_stories": [event["details"] for event in source.state["events"]
                              if event["event_type"] == "sourced_debt_stress_applied"][-3:],
            "warning": "Liquidity loans add debt; they do not restore equity. Household support may remain frozen at insolvent banks."}


def compact_comparison(result):
    return {"fork_id": result["fork_id"], "snapshot_sha256": result["snapshot_sha256"],
            "request": result["request"], "recommended_strategy": result["recommended_strategy"],
            "branches": [{"strategy": branch["strategy"], "metrics": branch["metrics"],
                          "delta_vs_no_intervention": branch["delta_vs_no_intervention"]}
                         for branch in result["branches"]]}


class DemoModel:
    provider = "deterministic_demo"
    model = "demo-policy-v1"

    def __init__(self, request):
        self.request = request

    def complete(self, messages, tools):
        results = [json.loads(message["content"]) for message in messages if message["role"] == "tool"]
        if not results:
            name, args = "inspect_economy", {}
        else:
            compared = [result for result in results if "fork_id" in result]
            if len(compared) < self.request["max_experiments"]:
                bank = self.request.get("target_bank_id") or min(results[0]["banks"], key=lambda item: item["capital_ratio"])["bank_id"]
                budget = max(1, self.request["budget_cap_cents"] // (2 ** len(compared)))
                name, args = "compare_interventions", {"bank_id": bank, "budget_cents": budget}
            else:
                choices = [(report, branch) for report in compared for branch in report["branches"]]
                def rank(choice):
                    metrics = choice[1]["metrics"]
                    return (-metrics["employed_households"], metrics["business_defaults"],
                            metrics["insolvent_banks"], metrics["stressed_banks"], metrics["public_support_disbursed_cents"])
                report, branch = min(choices, key=rank)
                name, args = "recommend_intervention", {
                    "fork_id": report["fork_id"], "strategy": branch["strategy"],
                    "rationale": "Deterministic demo: compare tested budgets by employment, defaults, bank stress, and gross support. This is not an AI-generated recommendation."}
        return {"role": "assistant", "content": None,
                "tool_calls": [{"id": f"demo_{len(results)}", "type": "function",
                                "function": {"name": name, "arguments": json.dumps(args)}}]}


def build_model(request):
    return DemoModel(request) if request["mode"] == "demo" else NebiusModel()


def run_agent(store, simulation_id, request):
    previous = store.find_agent(simulation_id, request)
    if previous is not None:
        return previous
    model = build_model(request)
    report, source = store.claim_agent(simulation_id, request, model)
    comparisons = {}
    inspected = False
    tools = TOOLS
    if request.get("allow_paid_research") and request["mode"] == "live":
        tools = TOOLS + [{"type": "function", "function": {"name": "buy_market_forecast",
            "description": "Optionally buy one external three-day trend analysis for at most 0.01 Base Sepolia test USDC. Uses a separate test wallet, never simulation balances. Purchase failures must not stop policy testing.",
            "parameters": InspectArguments.model_json_schema()}}]
    planner_tools = tools
    if request.get('agent_review'):
        tools = [tool for tool in TOOLS if tool['function']['name'] == 'inspect_economy']
    messages = [{"role": "system", "content":
                 "You are the central bank in a simulated economy. First inspect_economy, then compare_interventions. "
                 "You may test revised budgets/targets within the supplied cap and experiment limit. Finish with "
                 "recommend_intervention from a comparison returned in THIS run. Use only these tools. "
                 "Do not request settlement, create money, or invent results. Distinguish solvency from liquidity. "
                 "Explain the financial tradeoff briefly using observed evidence, not hidden reasoning. "
                 "Public cost means gross disbursement, not net fiscal loss. "
                 f"Limits: {json.dumps(request)}"}]
    policy_handoff = False
    activity(report, store.save_agent, 'investigator', 'Inspecting the captured economy before handing evidence to the policy planner.')
    try:
        for _ in range(10):
            message = model.complete(messages, tools)
            if not isinstance(message, dict):
                raise ProviderError("Model returned an invalid tool-call message")
            calls = message.get("tool_calls")
            if not isinstance(calls, list) or not calls or len(calls) > 4:
                raise ProviderError("Model must return between one and four tool calls per turn")
            for call in calls:
                if (not isinstance(call, dict) or not isinstance(call.get("id"), str)
                        or not call["id"] or not isinstance(call.get("function"), dict)
                        or not isinstance(call["function"].get("name"), str)
                        or not isinstance(call["function"].get("arguments"), str)):
                    raise ProviderError("Model returned a malformed function-call envelope")
            # Ordered batches remain in protocol order; final recommendation
            # stops execution before any later calls can cause side effects.
            messages.append(message)
            for call in calls:
                name = call.get("function", {}).get("name", "unknown")
                arguments = {}
                try:
                    arguments = json.loads(call["function"]["arguments"])
                    if not isinstance(arguments, dict):
                        raise ValueError("Tool arguments must be an object")
                    if request.get('agent_review') and not policy_handoff and name != 'inspect_economy':
                        raise LedgerError('Investigator must hand its captured evidence to the policy planner before policy tools can run')
                    if name == "inspect_economy":
                        InspectArguments.model_validate(arguments)
                        result = observations(source)
                        inspected = True
                    elif name == "compare_interventions":
                        args = CompareArguments.model_validate(arguments)
                        if not inspected:
                            raise LedgerError("Inspect the economy before testing an intervention")
                        if args.budget_cents > request["budget_cap_cents"]:
                            raise LedgerError("Proposed budget exceeds the run's budget cap")
                        if request.get("target_bank_id") and args.bank_id != request["target_bank_id"]:
                            raise LedgerError("This run must test the caller's selected bank")
                        if len(comparisons) >= request["max_experiments"]:
                            raise LedgerError("Experiment limit reached; recommend a tested strategy")
                        params = {"request_id": f"agent:{report['run_id']}:{len(comparisons)}",
                                  "bank_id": args.bank_id, "budget_cents": args.budget_cents, "ticks": request["ticks"]}
                        comparison = store.fork(simulation_id, params, source=source)
                        comparisons[comparison["fork_id"]] = comparison
                        report["comparison_ids"].append(comparison["fork_id"])
                        result = compact_comparison(comparison)
                    elif name == "buy_market_forecast" and request.get("allow_paid_research") and request["mode"] == "live":
                        InspectArguments.model_validate(arguments)
                        if not inspected:
                            raise LedgerError("Inspect the economy before purchasing external research")
                        from backend.paid_research import buy_market_forecast
                        try:
                            result = buy_market_forecast(store, report)
                        except ProviderError as error:
                            raise LedgerError(str(error)) from None
                    elif name == "recommend_intervention":
                        args = RecommendArguments.model_validate(arguments)
                        if args.fork_id not in comparisons:
                            raise LedgerError("Recommendation must reference a comparison tested in this run")
                        comparison = comparisons[args.fork_id]
                        branch = next(b for b in comparison["branches"] if b["strategy"] == args.strategy)
                        recommendation = {"fork_id": args.fork_id, "strategy": args.strategy,
                                          "bank_id": comparison["request"]["bank_id"] if args.strategy == "bank_lending" else None,
                                          "amount_cents": 0 if args.strategy == "no_intervention" else comparison["request"]["budget_cents"],
                                          "rationale": args.rationale, "metrics": branch["metrics"],
                                          "delta_vs_no_intervention": branch["delta_vs_no_intervention"]}
                        report["recommendation"] = recommendation
                        report["status"] = "completed"
                        result = recommendation
                    else:
                        raise LedgerError("Unknown tool; only inspect, compare, and recommend are allowed")
                    status = "accepted"
                except (LedgerError, ValidationError, ValueError, KeyError, TypeError, StopIteration) as error:
                    # Validation detail is useful, but do not expose provider
                    # bodies, credentials, or arbitrary exception strings.
                    status = "rejected"
                    reason = str(error) if isinstance(error, LedgerError) else (
                        "Invalid tool arguments; match the schema and use observed bank IDs and tested comparison IDs")
                    result = {"error": reason}
                    if not isinstance(arguments, dict):
                        arguments = {}
                report["trace"].append({"sequence": len(report["trace"]) + 1, "tool": name,
                                        "arguments": arguments, "status": status, "result": result})
                actor = 'investigator' if name == 'inspect_economy' and not policy_handoff else 'policy'
                activity(report, store.save_agent, actor, f"{name.replace('_', ' ')}: {status}", tool=name, trace_sequence=len(report['trace']))
                store.save_agent(report)
                messages.append({"role": "tool", "tool_call_id": call.get("id", "invalid"), "content": json.dumps(result)})
                if report["status"] == "completed":
                    return review_report(store, report, source, 'central_bank', store.save_agent)
            if inspected and not policy_handoff and request.get('agent_review'):
                policy_handoff = True
                tools = planner_tools
                activity(report, store.save_agent, 'investigator', 'Handed the observed bank health and economy metrics to the policy planner.', target='policy', trace_sequence=len(report['trace']))
                activity(report, store.save_agent, 'policy', 'Received the captured evidence. Testing bounded rescue alternatives.')
                if request['mode'] == 'live':
                    model = build_model(request)
                    messages = [dict(messages[0]), {'role': 'user', 'content': 'You are the policy planner receiving evidence from the investigator. Inspection is complete. Compare interventions, then recommend only a policy tested in this run. Captured evidence: ' + json.dumps(observations(source))}]
        raise ProviderError("Agent turn limit reached without a validated recommendation")
    except ProviderError as error:
        report["status"] = "failed"
        report["error"] = str(error)
        store.save_agent(report)
        return report
