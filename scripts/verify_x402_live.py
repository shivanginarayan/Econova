"""Make one bounded real testnet purchase; an attempt marker prevents reruns.

Run with .venv-x402 after starting the backend and merchant service.
No real-money network is supported. This is SDK evidence, not an LLM decision.
"""
import asyncio
import json
from pathlib import Path

import httpx

from scripts.run_backend import load_environment
from x402_service.buyer import buy


async def main():
    load_environment()
    marker = Path('data/x402-live-verification.json')
    if marker.exists():
        raise SystemExit('An attempt is already recorded. Inspect its receipt and wallet before any new purchase.')
    async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
        response = await client.post('http://127.0.0.1:8000/api/worlds', json={'seed': 42, 'scenario': 'credit_crunch'})
        response.raise_for_status()
        sid = response.json()['simulation_id']
        response = await client.get(f'http://127.0.0.1:8000/api/worlds/{sid}/research-input')
        response.raise_for_status()
        snapshot = response.json()['snapshot_sha256']
    evidence = {'status': 'attempted', 'simulation_id': sid, 'snapshot_sha256': snapshot,
                'testnet_only': True, 'origin': 'explicit_sdk_verification_not_model_choice'}
    marker.parent.mkdir(exist_ok=True)
    with marker.open('x') as file:
        json.dump(evidence, file)
    try:
        evidence['result'] = await buy(evidence)
        evidence['status'] = 'completed'
    except Exception as exc:
        evidence['error_type'] = type(exc).__name__
        print('Purchase failed or uncertain; no automatic retry. Inspect the testnet wallet.')
    marker.write_text(json.dumps(evidence, indent=2))
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/x402-live-verification.json').write_text(json.dumps(evidence, indent=2))
    print(json.dumps({'status': evidence['status'], 'error_type': evidence.get('error_type'),
                      'transaction_hash': evidence.get('result', {}).get('transaction_hash')}))
    if evidence['status'] != 'completed':
        raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(main())
