"""Run the Fetch.ai ACP gateway. Install requirements-fetch.txt in a separate venv."""
import os
import argparse
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from scripts.run_backend import load_environment


def build_protocol():
    from uagents import Context, Protocol
    from uagents_core.contrib.protocols.chat import (
        ChatAcknowledgement, ChatMessage, EndSessionContent, TextContent, chat_protocol_spec)
    from backend.fetch_chat import handle_command

    chat = Protocol(spec=chat_protocol_spec)

    @chat.on_message(ChatMessage)
    async def message(ctx: Context, sender: str, msg: ChatMessage):
        await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
        text = " ".join(item.text for item in msg.content if isinstance(item, TextContent))
        if not text:
            return
        context_key = "economy_chat_" + hashlib.sha256(sender.encode()).hexdigest()
        result = await handle_command(text, previous=ctx.storage.get(context_key))
        try:
            payload = json.loads(result)
            if isinstance(payload, dict) and payload.get("job_id"):
                ctx.storage.set(context_key, {"job_id": payload["job_id"]})
        except ValueError:
            pass
        await ctx.send(sender, ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(),
                                          content=[TextContent(type="text", text=result), EndSessionContent(type="end-session")]))

    @chat.on_message(ChatAcknowledgement)
    async def acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
        pass

    return chat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate the ACP protocol locally; no agent launch or registration")
    args = parser.parse_args()
    chat = build_protocol()
    if args.check:
        print("Fetch ACP protocol validated locally:", chat.digest)
        return
    load_environment()
    from uagents import Agent
    seed = os.getenv("FETCH_AGENT_SEED")
    if not seed:
        raise SystemExit("Set a stable private FETCH_AGENT_SEED; this determines your agent identity")
    token = os.getenv("FETCH_AGENTVERSE_TOKEN")
    endpoint = os.getenv("FETCH_AGENT_ENDPOINT")
    if not token and not endpoint:
        raise SystemExit("Set FETCH_AGENTVERSE_TOKEN for mailbox, or FETCH_AGENT_ENDPOINT for a reachable endpoint")
    # SDK 0.25 uses a separate /connect handshake; api_key in agentverse={} is ignored.
    agent = Agent(name="economy-god-mode", seed=seed, port=8002, mailbox=bool(token), endpoint=endpoint or None,
                  description="Sourced population and bank research, plus bounded financial stress testing. Commands: data <world_id>, stress <world_id>, status <job_id>.",
                  readme_path="docs/FETCH_AGENT.md")

    agent.include(chat, publish_manifest=True)
    agent.run()


if __name__ == "__main__":
    main()
