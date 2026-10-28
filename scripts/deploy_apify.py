"""Deploy a fixed-source Actor; leaves account limits and other Actors untouched."""
import json
import os
import re
from pathlib import Path
import httpx
from scripts.run_backend import ENV_PATH, load_environment


def main():
    load_environment()
    if not os.getenv("APIFY_TOKEN"):
        raise SystemExit("Set APIFY_TOKEN in private .env")
    root = Path(__file__).resolve().parent.parent / "apify_actor"
    files = [{"name": name, "format": "TEXT", "content": (root / name).read_text(encoding="utf-8")}
             for name in ("Dockerfile", "main.py", "README.md", ".actor/actor.json")]
    version = {"versionNumber": "0.1", "sourceType": "SOURCE_FILES", "buildTag": "latest", "sourceFiles": files}
    with httpx.Client(headers={"Authorization": "Bearer " + os.environ["APIFY_TOKEN"]}, timeout=40, trust_env=False) as client:
        actor = os.getenv("APIFY_ACTOR_ID", "").strip()
        if not actor:
            response = client.post("https://api.apify.com/v2/actors", json={
                "name": "economy-public-sf", "title": "Economy God Mode public SF inputs", "isPublic": False,
                "versions": [version], "defaultRunOptions": {"build": "latest", "timeoutSecs": 120, "memoryMbytes": 128, "restartOnError": False}})
            if not response.is_success:
                raise SystemExit(f"Actor creation rejected (HTTP {response.status_code}); inspect Apify Console. No retry was made.")
            data = response.json()["data"]
            actor = data["id"]
            text = ENV_PATH.read_text(encoding="utf-8-sig") if ENV_PATH.exists() else ""
            text = re.sub(r"^APIFY_ACTOR_ID=.*$", "APIFY_ACTOR_ID=" + actor, text, flags=re.M) if re.search(r"^APIFY_ACTOR_ID=", text, re.M) else text.rstrip() + "\nAPIFY_ACTOR_ID=" + actor + "\n"
            ENV_PATH.write_text(text, encoding="utf-8")
            print("Created private Actor:", actor)
        else:
            if not re.fullmatch(r"[A-Za-z0-9_~.-]{1,128}", actor):
                raise SystemExit("Invalid configured Actor ID")
            response = client.put(f"https://api.apify.com/v2/actors/{actor}/versions/0.1", json=version)
            response.raise_for_status()
        response = client.post(f"https://api.apify.com/v2/actors/{actor}/builds", params={"version": "0.1", "tag": "latest"})
        response.raise_for_status()
        build = response.json()["data"]
        target = Path("data/apify-build.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"actor_id": actor, "build_id": build["id"]}, indent=2))
        print("Build started:", build["id"], "status", build["status"])


if __name__ == "__main__":
    main()
