import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from apify_actor.main import parse
from backend import apify_collection as collection
from backend.apify_recipe import recipe
from backend.calibration import load
from backend.engine import Economy
from backend.main import create_app
from backend.provider import ProviderNotConfigured
from backend.store import Store
from scripts.apify_calibrate import collect


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv('APIFY_TOKEN', 'private-test-token')
    monkeypatch.setenv('APIFY_ACTOR_ID', 'PrivateActor123')
    monkeypatch.setenv('APIFY_CALIBRATION_DIR', str(tmp_path / 'calibrations'))
    store = Store(tmp_path / 'apify.sqlite3')
    collection.init(store)
    return store


def fake_collect(spec, client, wait_seconds, on_run):
    category = spec['input']['category']
    on_run('RunPrices' if category == 'prices' else 'RunWages')
    value = 425 if category == 'prices' else 15688
    return [value], {'actor_id': 'PrivateActor123', 'dataset_id': 'Dataset123', 'run_id': 'Run' + category,
                     'source_url': spec['source_url'], 'observations': [{'item': 'fixture', 'value': 4.25 if category == 'prices' else 19.61,
                     'unit': spec['unit'], 'observed_at': datetime.now(timezone.utc).isoformat()}], 'usage_total_usd': 0.001}


def test_concurrent_collection_clicks_claim_once_and_reuse_completed_data(store, monkeypatch):
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda i: collection.enqueue(store, f'click-{i}'), range(8)))
    assert len({row[0]['job_id'] for row in results}) == 1
    assert sum(row[1] for row in results) == 1
    monkeypatch.setattr(collection, 'collect', fake_collect)
    job = results[0][0]
    collection.execute(store, job['job_id'])
    finished = collection.get(store, job['job_id'])
    assert finished['status'] == 'completed'
    assert set(finished['runs']) == {'prices', 'wages'}
    assert collection.enqueue(store, 'another-click')[0] == finished
    def no_replay(*args, **kwargs):
        raise AssertionError('Completed collection replayed')
    monkeypatch.setattr(collection, 'collect', no_replay)
    collection.execute(store, job['job_id'])
    data = load(finished['calibration_id'])
    assert data['price_cents'] == [425] and data['daily_wage_cents'] == [15688]
    assert data['sources'][1]['scope'].startswith('General statutory minimum')
    world = Economy.create('public-world', calibration_id=data['calibration_id'])
    assert all(e['price_cents'] == 425 for e in world.state['entities'].values() if e['kind'] == 'business')
    assert all(e['wage_cents'] == 15688 for e in world.state['entities'].values() if e['kind'] == 'household')
    world.step(2)
    assert world.audit()['balanced']


def test_failed_or_interrupted_collection_never_publishes_substitute(store, monkeypatch):
    job, _ = collection.enqueue(store, 'fail')
    def fail(spec, client, **kwargs):
        kwargs['on_run']('KnownRun123')
        raise ValueError('private-test-token should not appear')
    monkeypatch.setattr(collection, 'collect', fail)
    collection.execute(store, job['job_id'])
    result = collection.get(store, job['job_id'])
    assert result['status'] == 'failed' and result['runs']['prices'] == 'KnownRun123'
    assert result['calibration_id'] is None and 'private-test-token' not in result['error']
    assert collection.enqueue(store, 'fail')[1] is False
    next_job, _ = collection.enqueue(store, 'interrupted')
    next_job['updated_at'] = time.time() - 700
    with store.connection() as conn:
        conn.execute('UPDATE apify_collections SET report=? WHERE id=?', (json.dumps(next_job), next_job['job_id']))
    assert collection.get(store, next_job['job_id'])['status'] == 'failed'


def test_collection_api_returns_saved_data_and_rejects_custom_scrapes(store, monkeypatch, tmp_path):
    monkeypatch.setattr(collection, 'collect', fake_collect)
    with TestClient(create_app(tmp_path / 'api.sqlite3')) as client:
        assert client.get('/api/calibrations/collection/status').json()['configured']
        response = client.post('/api/calibrations/collect', json={'request_id': 'ui-click'})
        assert response.status_code == 202
        job_id = response.json()['job_id']
        job = client.get('/api/calibrations/collection/' + job_id).json()
        assert job['status'] == 'completed'
        data = client.get('/api/calibrations/' + job['calibration_id']).json()
        assert data['sources'][0]['observations'][0]['item'] == 'fixture'
        assert len(data['sha256']) == 64
        assert client.post('/api/calibrations/collect', json={'request_id': 'bad', 'url': 'https://example.com'}).status_code == 422
        monkeypatch.delenv('APIFY_TOKEN')
        assert client.post('/api/calibrations/collect', json={'request_id': 'missing-token'}).status_code == 503


def test_fixed_recipe_and_actor_parser_preserve_source_meaning(monkeypatch):
    monkeypatch.setenv('APIFY_ACTOR_ID', 'PrivateActor123')
    spec = recipe('prices')
    assert spec['input'] == {'category': 'prices'}
    assert spec['run_options']['timeout'] == 120 and spec['run_options']['memory'] == 128
    with pytest.raises(ValueError):
        recipe('arbitrary-url')
    monkeypatch.delenv('APIFY_ACTOR_ID')
    with pytest.raises(ProviderNotConfigured):
        recipe('prices')
    wage = parse('<p>minimum wage, currently $19.61 as of July 1, 2026.</p><p>Special exception $17.35</p>', 'wages')
    assert len(wage) == 1 and wage[0]['value'] == 19.61
    assert wage[0]['kind'] == 'statutory_wage_floor_not_average_pay'
    with pytest.raises(ValueError):
        parse('<script>minimum wage, currently $99.00 as of July 1, 2026</script>', 'wages')
    with pytest.raises(ValueError):
        parse('<p>minimum wage, currently $99.00 as of July 1, 2099</p>', 'wages')
    with pytest.raises(ValueError):
        parse('<p>LATTE 5.00 & 5.55</p><p>Address 78 Phone 415-123</p>', 'prices')


def test_collector_keeps_run_cost_observations_and_bearer_only_auth():
    def handle(request):
        assert request.headers['Authorization'] == 'Bearer private-test-token'
        assert 'token' not in request.url.params
        if request.method == 'POST':
            assert request.url.params['timeout'] == '120'
            return httpx.Response(201, json={'data': {'id': 'Run123'}})
        if '/actor-runs/' in request.url.path:
            return httpx.Response(200, json={'data': {'status': 'SUCCEEDED', 'defaultDatasetId': 'Dataset123', 'usageTotalUsd': .001}})
        return httpx.Response(200, json=[{'value': 19.61, 'unit': 'usd_hour', 'kind': 'statutory_wage_floor_not_average_pay', 'effective_date': '2026-07-01'}])
    spec = {'actor_id': 'PrivateActor123', 'input': {'category': 'wages'}, 'value_path': 'value', 'unit': 'usd_hour', 'source_url': 'https://www.sf.gov/', 'run_options': {'timeout': 120}}
    runs = []
    with httpx.Client(headers={'Authorization': 'Bearer private-test-token'}, transport=httpx.MockTransport(handle)) as client:
        values, evidence = collect(spec, client, on_run=runs.append)
    assert values == [15688] and runs == ['Run123']
    assert evidence['observations'][0]['effective_date'] == '2026-07-01'
    assert evidence['usage_total_usd'] == .001


def test_opening_app_uses_fresh_cache_without_another_run(store, monkeypatch):
    monkeypatch.setattr(collection, 'collect', fake_collect)
    job, _ = collection.enqueue(store, 'initial-data')
    collection.execute(store, job['job_id'])
    result, started = collection.ensure(store)
    assert started is False and result['state'] == 'fresh'
    assert result['data']['price_cents'] == [425]
    monkeypatch.delenv('APIFY_TOKEN')
    result, started = collection.ensure(store)
    assert result['data'] and not started  # Saved public data remains usable without credentials.


def test_first_open_across_tabs_starts_one_automatic_collection(store):
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: collection.ensure(store), range(8)))
    assert sum(started for _, started in results) == 1
    assert len({result['job']['job_id'] for result, _ in results}) == 1
    assert all(result['data'] is None for result, _ in results)


def test_stale_cache_served_during_refresh_and_failure_not_replayed(store, monkeypatch):
    monkeypatch.setattr(collection, 'collect', fake_collect)
    job, _ = collection.enqueue(store, 'old-data')
    collection.execute(store, job['job_id'])
    completed = collection.get(store, job['job_id'])
    from pathlib import Path
    path = Path(__import__('os').environ['APIFY_CALIBRATION_DIR']) / (completed['calibration_id'] + '.json')
    data = json.loads(path.read_text())
    data['collected_at'] = datetime.fromtimestamp(time.time() - 7 * 3600, timezone.utc).isoformat()
    path.write_text(json.dumps(data))
    completed['updated_at'] = time.time() - 7 * 3600
    with store.connection() as connection:
        connection.execute('UPDATE apify_collections SET report=? WHERE id=?', (json.dumps(completed), job['job_id']))
    result, started = collection.ensure(store)
    assert started and result['state'] == 'refreshing'
    assert result['data']['calibration_id'] == completed['calibration_id']
    automatic = result['job']
    def fail(*args, **kwargs):
        raise ValueError('Source unavailable')
    monkeypatch.setattr(collection, 'collect', fail)
    collection.execute(store, automatic['job_id'])
    again, started = collection.ensure(store)
    assert not started and again['state'] == 'failed'
    assert again['job']['job_id'] == automatic['job_id']
    assert again['data']['calibration_id'] == completed['calibration_id']
