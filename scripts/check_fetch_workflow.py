"""Verify the chat-to-backend workflow with live Nemotron; not an ASI:One registration check."""
import argparse
import asyncio
import json

from backend.fetch_chat import handle_command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True, help="Explicitly authorize live model inference usage")
    args = parser.parse_args()
    result = json.loads(asyncio.run(handle_command("stress-test bank 1 with a 40% loss and compare rescue plans")))
    assert result["status"] == "completed" and result["provider"] == "nebius"
    assert len(result["three_futures"]) == 3 and not result["funds_applied"]
    follow = json.loads(asyncio.run(handle_command("why did you pick that?", previous={"job_id": result["job_id"]})))
    assert follow["saved_public_trace"] and follow["recommendation"] == result["recommendation"]
    print(json.dumps({"backend_chat_workflow": "verified", "agentverse_registration": "not_verified", "provider": result["provider"],
                      "model": result["model"], "three_futures": len(result["three_futures"]),
                      "public_tool_calls": result["tool_calls"], "saved_evidence_follow_up": True, "funds_applied": False}, indent=2))


if __name__ == "__main__":
    main()
