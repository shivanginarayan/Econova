"""Fetch dated official observations; never refresh an existing world's inputs."""
import json
from scripts.run_backend import load_environment
from backend.benchmarks import collect,save

if __name__=='__main__':
    load_environment()
    snapshot=save(collect())
    print(json.dumps({'benchmark_id':snapshot['benchmark_id'],'observations':len(snapshot['observations']),'status':snapshot['status']},indent=2))
