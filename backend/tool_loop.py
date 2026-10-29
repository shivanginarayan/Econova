"""Bounded function-tool conversations with public trace callbacks."""

import json

from pydantic import ValidationError

from backend.ledger import LedgerError
from backend.provider import ProviderError


def tool_session(model, tools, handler, trace_callback, instruction):
    messages = [{"role": "system", "content": instruction +
        " Use only the supplied function tools. Do not invent balances or settlement. "
        "Provide exactly one function call per turn, with valid JSON object arguments. "
        "Provide brief public rationales, not hidden reasoning."}]
    for _ in range(6):
        available = tools() if callable(tools) else tools
        message = model.complete(messages, available)
        calls = message.get("tool_calls") if isinstance(message, dict) else None
        if not isinstance(calls, list) or not 1 <= len(calls) <= 32:
            raise ProviderError("Supplier workflow returned an invalid tool-call batch (expected exactly one call)")
        for call in calls:
            if (not isinstance(call, dict) or not isinstance(call.get("id"), str) or not call["id"]
                    or not isinstance(call.get("function"), dict)
                    or not isinstance(call["function"].get("name"), str)
                    or not isinstance(call["function"].get("arguments"), str)):
                raise ProviderError("Supplier workflow returned a malformed function call")
        if len({call["id"] for call in calls}) != len(calls):
            raise ProviderError("Supplier workflow returned duplicate function-call IDs")
        if len(calls) != 1:
            # Never execute one of several contradictory decisions or resend a
            # malformed batch as accepted function-call history.
            result = {"error": "Entire batch rejected: provide exactly one function call. No tool in this batch was executed."}
            for call in calls:
                trace_callback(call["function"]["name"], {}, "rejected", result)
            messages.append({"role": "user", "content": json.dumps(result)})
            continue
        call = calls[0]
        try:
            parsed = json.loads(call["function"]["arguments"])
            if not isinstance(parsed, dict):
                raise ValueError("Arguments must be an object")
        except (ValueError, TypeError):
            result = {"error": "Function call rejected before execution: arguments must be a valid JSON object. Retry with the supplied schema."}
            trace_callback(call["function"]["name"], {}, "rejected", result)
            # Nebius validates JSON in historical function calls. Retaining an
            # invalid raw call causes HTTP400 before the model can correct it.
            messages.append({"role": "user", "content": json.dumps(result)})
            continue
        messages.append(message)
        for call in calls:
            args, done = {}, False
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"])
                if not isinstance(args, dict):
                    raise ValueError("Arguments must be an object")
                result, done = handler(name, args)
                status = "accepted"
            except (LedgerError, ValidationError, ValueError, KeyError, TypeError) as error:
                status = "rejected"
                result = {"error": str(error) if isinstance(error, LedgerError) else "Tool arguments do not match the allowed schema"}
                if not isinstance(args, dict):
                    args = {}
            trace_callback(name, args, status, result)
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
            if done:
                return
    raise ProviderError("Supplier workflow turn limit reached without a decision")
