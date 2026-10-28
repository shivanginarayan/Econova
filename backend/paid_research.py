"""Durably reserve at most one external testnet research purchase per agent run."""
import json
import os
import subprocess
import time
from pathlib import Path

from backend.provider import ProviderError, ProviderNotConfigured


def buy_market_forecast(store, report):
    if not report["request"].get("allow_paid_research") or report["request"]["mode"] != "live":
        raise ProviderNotConfigured("Paid research needs explicit live-run authorization")
    root = Path(__file__).resolve().parent.parent
    executable = Path(os.getenv("X402_PYTHON", str(root / ".venv-x402" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))))
    if not executable.is_file() or not os.getenv("X402_WALLET_PRIVATE_KEY") or not os.getenv("X402_MERCHANT_ADDRESS"):
        raise ProviderNotConfigured("Configure the isolated x402 SDK environment, testnet wallet and merchant")
    with store.connection() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS paid_research (run_id TEXT PRIMARY KEY, status TEXT NOT NULL, created REAL NOT NULL, result TEXT)")
        connection.execute("BEGIN IMMEDIATE")
        previous = connection.execute("SELECT status,result FROM paid_research WHERE run_id=?", (report["run_id"],)).fetchone()
        if previous:
            if previous[0] == "completed":
                return json.loads(previous[1])
            raise ProviderError("A purchase was already attempted in this run; inspect the wallet before retrying")
        connection.execute("INSERT INTO paid_research VALUES (?, 'attempted', ?, NULL)", (report["run_id"], time.time()))
    payload = {"simulation_id": report["simulation_id"], "snapshot_sha256": report["snapshot_sha256"]}
    try:
        completed = subprocess.run([str(executable), "-m", "x402_service.buyer"], cwd=root, input=json.dumps(payload),
                                   text=True, capture_output=True, timeout=65, check=False)
        output = json.loads(completed.stdout)
        if completed.returncode or not output.get("ok"):
            raise ValueError
        result = output["result"]
        with store.connection() as connection:
            connection.execute("UPDATE paid_research SET status='completed',result=? WHERE run_id=?", (json.dumps(result), report["run_id"]))
        return result
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, TypeError):
        raise ProviderError("Paid research failed or payment is uncertain; this run will not automatically pay again. Inspect the testnet wallet.") from None
