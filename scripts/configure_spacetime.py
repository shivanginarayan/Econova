"""Authenticate the portable CLI locally, keeping its token in ignored .env only."""
import os
import subprocess
from pathlib import Path

import httpx

from scripts.run_backend import load_environment


def main():
    load_environment()
    base = os.getenv("SPACETIMEDB_URL", "http://127.0.0.1:3000").rstrip("/")
    if base not in ("http://127.0.0.1:3000", "http://localhost:3000"):
        raise SystemExit("This helper creates localhost identities only; configure remote deployments separately")
    token = os.getenv("SPACETIMEDB_TOKEN")
    if not token:
        response = httpx.post(base + "/v1/identity", timeout=15)
        response.raise_for_status()
        token = response.json()["token"]
    cli = Path("data/spacetime-bin/spacetimedb-cli.exe").resolve()
    if not cli.is_file():
        raise SystemExit("Extract the official portable Windows CLI to data/spacetime-bin first")
    result = subprocess.run([str(cli), "--root-dir", str(Path("data/spacetime-cli").resolve()), "login", "--token", token],
                            capture_output=True)
    if result.returncode:
        raise SystemExit("Local database login failed; token was not displayed")
    path = Path(".env")
    lines = path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []
    updates = {"SPACETIMEDB_URL": base, "SPACETIMEDB_DATABASE": os.getenv("SPACETIMEDB_DATABASE", "economy-god-mode"), "SPACETIMEDB_TOKEN": token}
    lines = [line for line in lines if line.partition("=")[0].strip() not in updates]
    path.write_text("\n".join(lines + [key + "=" + value for key, value in updates.items()]) + "\n", encoding="utf-8")
    print("Private local publishing identity configured. Restart the backend after publishing.")


if __name__ == "__main__":
    main()
