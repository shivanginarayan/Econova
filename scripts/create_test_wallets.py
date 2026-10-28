"""Create new local test-only wallet identities without overwriting configured keys."""
import json
import os
from pathlib import Path

from eth_account import Account

from scripts.run_backend import load_environment


def main():
    load_environment()
    path = Path(".env")
    text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    updates = {}
    buyer = Account.from_key(os.environ["X402_WALLET_PRIVATE_KEY"]) if os.getenv("X402_WALLET_PRIVATE_KEY") else Account.create()
    if not os.getenv("X402_WALLET_PRIVATE_KEY"):
        updates["X402_WALLET_PRIVATE_KEY"] = buyer.key.hex()
    merchant_address = os.getenv("X402_MERCHANT_ADDRESS")
    if not merchant_address:
        merchant_file = Path("data/x402-merchant-wallet.json")
        if merchant_file.exists():
            merchant = Account.from_key(json.loads(merchant_file.read_text())["private_key"])
        else:
            merchant = Account.create()
            merchant_file.parent.mkdir(exist_ok=True)
            with merchant_file.open("x", encoding="utf-8") as output:
                json.dump({"network": "eip155:84532", "testnet_only": True, "address": merchant.address, "private_key": merchant.key.hex()}, output)
        merchant_address = merchant.address
        updates["X402_MERCHANT_ADDRESS"] = merchant_address
    if updates:
        lines = [line for line in text.splitlines() if line.partition("=")[0].strip() not in updates]
        path.write_text("\n".join(lines + [key + "=" + value for key, value in updates.items()]) + "\n", encoding="utf-8")
    print(json.dumps({"buyer_address": buyer.address, "merchant_address": merchant_address,
                      "network": "Base Sepolia only", "funding": "Not funded by this helper. Add Base Sepolia test USDC to the buyer before a live payment.",
                      "private_keys": "Saved only in ignored local files; not displayed"}, indent=2))


if __name__ == "__main__":
    main()
