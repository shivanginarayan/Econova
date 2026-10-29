"""Single-process hosted UI/API with persistent SQLite and a frozen public sample."""
import json
import os
from pathlib import Path
from backend.calibration import validate
from backend.benchmarks import save as save_benchmark,latest


def seed_inputs():
    bundle=Path(os.getenv('ECONOMY_INPUT_BUNDLE','deployment/public-inputs.json'))
    if not bundle.exists():raise ValueError('Public observation bundle missing; run scripts.prepare_hosted_inputs before building')
    data=json.loads(bundle.read_text(encoding='utf-8-sig'));sample=validate(data['calibration'])
    directory=Path(os.getenv('APIFY_CALIBRATION_DIR','data/calibrations'));directory.mkdir(parents=True,exist_ok=True)
    target=directory/(sample['calibration_id']+'.json')
    if not target.exists():target.write_text(json.dumps(sample,indent=2)+'\n',encoding='utf-8')
    if latest() is None:save_benchmark(data['benchmark'])


def main():
    os.environ.setdefault('ECONOMY_PUBLIC_MODE','1');os.environ.setdefault('ECONOMY_STATIC_DIR','dist')
    # Never load a developer .env on the public service. The hosting secret store supplies credentials.
    if not os.getenv('NEBIUS_API_KEY') or not os.getenv('NEBIUS_MODEL'):raise ValueError('Hosted live agents require NEBIUS_API_KEY and NEBIUS_MODEL')
    seed_inputs()
    import uvicorn
    uvicorn.run('backend.main:app',host='0.0.0.0',port=int(os.getenv('PORT','8000')),workers=1,
        access_log=False,proxy_headers=True,forwarded_allow_ips=os.getenv('ECONOMY_TRUSTED_PROXIES','127.0.0.1'))

if __name__=='__main__':main()
