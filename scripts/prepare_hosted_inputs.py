"""Package validated public observations only; credentials and runtime databases stay local."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from backend.apify_collection import latest_data
from backend.calibration import validate
from backend.benchmarks import latest


def main():
    sample,_=latest_data();benchmark=latest()
    if not sample or not benchmark:raise SystemExit('Collect verified public inputs before packaging')
    sample.pop('sha256',None);sample=validate(sample)
    for source in sample['sources']:
        url=urlsplit(source['source_url'])
        if url.username or url.password or url.query or url.fragment:raise ValueError('Only credential-free public source URLs can be packaged')
    destination=Path('deployment/public-inputs.json');destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps({'scope':'Frozen public price/wage observations and economic benchmarks; not live feeds or real customer records.',
        'calibration':sample,'benchmark':benchmark},indent=2)+'\n',encoding='utf-8')
    print('Validated public observation bundle prepared; no runtime credentials or databases included.')

if __name__=='__main__':main()
