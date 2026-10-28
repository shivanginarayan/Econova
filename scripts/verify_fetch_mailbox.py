"""Exercise the published ACP agent through Agentverse, using a temporary local peer.

Run in the Fetch virtualenv while the backend and product agent are running.
The peer publishes only an ephemeral Almanac API callback, not a marketplace profile.
"""
import asyncio
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents.registration import AlmanacApiRegistrationPolicy
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement, ChatMessage, EndSessionContent, TextContent, chat_protocol_spec,
)

TARGET = "agent1qwv9gf04ag4echzl3fpgnc889lpsk8vgatysq07yz7zpwm9480zxslyxkgm"


async def main():
    done = asyncio.get_running_loop().create_future()
    evidence = {"target": TARGET, "transport": "Agentverse mailbox", "acknowledged": False, "responses": []}
    peer = Agent(name="economy-mailbox-verification", seed=secrets.token_hex(32), port=8003,
                 endpoint="http://127.0.0.1:8003/submit", publish_agent_details=False,
                 registration_policy=AlmanacApiRegistrationPolicy())
    protocol = Protocol(spec=chat_protocol_spec)

    async def send(ctx, text):
        return await ctx.send(TARGET, ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
                              content=[TextContent(type="text", text=text), EndSessionContent(type="end-session")]))

    @peer.on_event("startup")
    async def start(ctx: Context):
        await asyncio.sleep(8)
        status = await send(ctx, "stress-test bank 1 with a 40% loss and compare rescue plans")
        evidence["delivery"] = status.model_dump(mode="json")

    @protocol.on_message(ChatAcknowledgement)
    async def ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
        if sender == TARGET:
            evidence["acknowledged"] = True

    @protocol.on_message(ChatMessage)
    async def receive(ctx: Context, sender: str, msg: ChatMessage):
        if sender != TARGET:
            return
        await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
        text = " ".join(item.text for item in msg.content if isinstance(item, TextContent))
        payload = json.loads(text)
        evidence["responses"].append(payload)
        if len(evidence["responses"]) == 1:
            if payload.get("status") in ("queued", "running"):
                await send(ctx, "status " + payload["job_id"])
            else:
                await send(ctx, "why did you pick that?")
        elif "saved_public_trace" not in payload:
            await send(ctx, "why did you pick that?")
        elif not done.done():
            done.set_result(True)

    peer.include(protocol)
    async def finish():
        try:
            await asyncio.wait_for(done, timeout=240)
            final = evidence["responses"][-1]
            assert evidence["acknowledged"]
            assert final["status"] == "completed", final.get("error")
            assert final["provider"] == "nebius"
            assert len(final["three_futures"]) == 3
            assert final["funds_applied"] is False
            assert final["saved_public_trace"]
            evidence["passed"] = True
        except Exception as exc:
            evidence["passed"] = False
            evidence["failure"] = type(exc).__name__
        finally:
            Path("artifacts").mkdir(exist_ok=True)
            Path("artifacts/fetch-mailbox-verification.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
            # SDK 0.25.5 cancels every other loop task during shutdown. Keep
            # run_async in the root task and stop its Uvicorn server normally,
            # avoiding a cancellation cycle between parent and child tasks.
            if peer._server.server:
                peer._server.server.should_exit = True

    asyncio.create_task(finish())
    await peer.run_async()
    if not evidence.get("passed"):
        raise SystemExit("ACP mailbox verification failed; see ignored artifact evidence.")
    print("ACP mailbox experiment, three futures, live analysis and saved-evidence follow-up passed.")


if __name__ == "__main__":
    asyncio.run(main())
