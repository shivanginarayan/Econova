"""Verify public data and optionally real SpacetimeDB, Fetch inference or CRS screening."""
import argparse
import json
from uuid import uuid4

from scripts.run_backend import load_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spacetime", action="store_true")
    parser.add_argument("--research", action="store_true", help="Makes paid/live ASI:One inference requests")
    parser.add_argument("--crs-profile", help="Sponsor profile ID for a real sandbox call")
    args = parser.parse_args()
    load_environment()
    from backend import fraud, research, spacetime
    from backend.engine import Economy
    from backend.store import Store
    store = Store("data/integration-check.sqlite3")
    world = Economy.create("check_" + uuid4().hex[:16], households=8, businesses=2, banks=2)
    store.create(world)
    sid = world.state["simulation_id"]
    report = research.retrieve_sources(store, sid)
    summary = {"public_data": report["status"], "world_id": sid}
    if args.spacetime:
        spacetime.enable(store, sid)
        store.mutate(sid, lambda w: w.step())
        while spacetime.sync_status(store, sid)["last_sequence"] < len(store.get(sid).state["events"]):
            spacetime.sync_world(store, sid)
        first = spacetime.shared_events(sid)
        with store.connection() as connection:
            connection.execute("UPDATE spacetime_sync SET cursor=0 WHERE source_id=?", (sid,))
        spacetime.sync_world(store, sid)
        second = spacetime.shared_events(sid)
        assert first[0]["rows"] == second[0]["rows"], "Duplicate replay changed the shared feed"
        import httpx
        base, headers = spacetime.settings()
        row = first[0]["rows"][0]
        conflicting = dict(zip(["key", "simulation_id", "sequence", "tick", "event_type", "actor_id", "counterparty_id", "amount_cents"], row))
        conflicting["event_type"] = "conflicting_replay"
        denied = httpx.post(base + "/call/ingest_events", json=[json.dumps([conflicting])], timeout=15)
        conflict = httpx.post(base + "/call/ingest_events", headers=headers, json=[json.dumps([conflicting])], timeout=15)
        assert denied.is_error and conflict.is_error, "Unauthorized write or conflicting replay was accepted"
        assert spacetime.shared_events(sid)[0]["rows"] == first[0]["rows"]
        summary["spacetime"] = {"events": len(first[0]["rows"]), "duplicate_replay_verified": True,
                                "unauthorized_write_rejected": True, "conflicting_replay_rejected": True}
    if args.research:
        result = research.research(store, sid)
        summary["fetch"] = {"status": result["status"], "tool_calls": len(result["trace"])}
    if args.crs_profile:
        result = fraud.screen(store, sid, "business_2", args.crs_profile)
        summary["crs"] = {"decision": result["decision"], "report_id": result["report_id"]}
    summary["balanced"] = store.get(sid).audit()["balanced"]
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
