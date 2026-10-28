"""Start the local API with private root .env settings, without extra dependencies."""

import argparse
import os
from pathlib import Path


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
ALLOWED = {"NEBIUS_API_KEY", "NEBIUS_MODEL", "NEBIUS_BASE_URL", "ECONOMY_DB_PATH", "ECONOMY_CORS_ORIGINS"}
ALLOWED.update({"ASI1_API_KEY", "ASI1_MODEL", "CRS_USERNAME", "CRS_PASSWORD", "CRS_ACCESS_TOKEN",
                "CRS_PRODUCT_CONFIG", "CRS_TEST_PROFILES_PATH", "CRS_DECISION_RULES_PATH",
                "SPACETIMEDB_URL", "SPACETIMEDB_DATABASE", "SPACETIMEDB_TOKEN",
                "FETCH_AGENT_SEED", "FETCH_AGENTVERSE_TOKEN", "FETCH_AGENT_ENDPOINT"})
ALLOWED.update({"CRS_CREDIT_PRODUCT_CONFIG", "CRS_CREDIT_REPORT_VARIANT", "CRS_CREDIT_RULES_PATH",
                "CREDIT_APPROVAL_THRESHOLD_CENTS", "APIFY_TOKEN", "APIFY_CALIBRATION_DIR",
                "X402_WALLET_PRIVATE_KEY", "X402_MERCHANT_ADDRESS", "X402_FORECAST_URL", "X402_PYTHON", "APIFY_ACTOR_ID"})


def load_environment(path=ENV_PATH, environ=None):
    target = os.environ if environ is None else environ
    path = Path(path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not separator or key not in ALLOWED:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        target.setdefault(key, value)


def main():
    import faulthandler
    import signal
    faulthandler.enable()
    if hasattr(signal, "SIGUSR1"):
        faulthandler.register(signal.SIGUSR1, all_threads=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    load_environment()
    import uvicorn
    uvicorn.run("backend.main:app", host=args.host, port=args.port, reload=args.reload, access_log=False)


if __name__ == "__main__":
    main()
