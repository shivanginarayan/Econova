from copy import deepcopy
from datetime import datetime, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from backend import shock_stories as stories
from backend.agents import observations
from backend.engine import Economy
from backend.ledger import LedgerError
from backend.main import create_app
from backend.provider import ProviderError
from backend.store import Store


@pytest.fixture
def store(tmp_path, monkeypatch):
    store = Store(tmp_path / 'stories.sqlite3')
    store.create(Economy.create('world', scenario='credit_crunch'))
    monkeypatch.setattr(stories, 'debt_baseline', lambda: {
        'provider': 'US Treasury Fiscal Data', 'series': 'Total public debt outstanding',
        'value_usd': '40000000000000.01', 'observation_date': '2026-10-22',
        'retrieved_at': '2026-10-24T00:00:00+00:00', 'source_url': stories.DEBT_PAGE,
        'age_days': 2, 'stale': False, 'unit': 'USD'})
    return store


def test_preview_preserves_source_and_keeps_debt_and_yield_independent(store):
    before = deepcopy(store.get('world').state)
    report = stories.preview(store, 'world', stories.DebtStress())
    assert report['hypothetical_debt_usd'] == '50000000000000.01'
    assert report['loss_bps'] == 500  # 50% exposure * 5 years * 200 bps
    assert report['estimated_loss_cents'] == report['portfolio_cents'] * 500 // 10000
    assert store.get('world').state == before
    more_debt = stories.preview(store, 'world', stories.DebtStress(debt_increase_percent=50))
    assert more_debt['loss_bps'] == report['loss_bps']
    zero_yield = stories.preview(store, 'world', stories.DebtStress(yield_increase_bps=0))
    assert zero_yield['loss_bps'] == 0
    with pytest.raises(LedgerError, match='no bank loss'):
        stories.apply(store, 'world', zero_yield['report_id'])


def test_apply_once_preserves_deposits_and_provenance_and_retries_after_tick(store):
    report = stories.preview(store, 'world', stories.DebtStress())
    before = store.get('world')
    deposits = before.metrics()['household_cash_cents']
    equity = before.ledger.sheet('bank_1')['equity_cents']
    result = stories.apply(store, 'world', report['report_id'])
    assert stories.apply(store, 'world', report['report_id']) == result
    after = store.get('world')
    assert after.metrics()['household_cash_cents'] == deposits
    assert after.ledger.sheet('bank_1')['equity_cents'] == equity - report['estimated_loss_cents']
    assert after.audit()['balanced']
    assert observations(after)['shock_stories'][0]['report_id'] == report['report_id']
    assert stories.history(store, 'world')[0]['status'] == 'applied'
    store.mutate('world', lambda world: world.step())
    assert stories.apply(store, 'world', report['report_id']) == result
    assert stories.history(Store(store.path), 'world')[0]['status'] == 'applied'


def test_stale_running_and_cross_world_previews_rejected(store):
    report = stories.preview(store, 'world', stories.DebtStress())
    store.control_playback('world', 'running')
    with pytest.raises(LedgerError, match='Pause'):
        stories.apply(store, 'world', report['report_id'])
    store.control_playback('world', 'paused')
    store.create(Economy.create('other'))
    with pytest.raises(KeyError):
        stories.apply(store, 'other', report['report_id'])
    store.mutate('world', lambda world: world.step())
    with pytest.raises(LedgerError, match='changed since preview'):
        stories.apply(store, 'world', report['report_id'])


def test_forks_inherit_applied_story_and_keep_source_unchanged(store):
    report = stories.preview(store, 'world', stories.DebtStress())
    stories.apply(store, 'world', report['report_id'])
    before = deepcopy(store.get('world').state)
    result = store.fork('world', {'request_id': 'story-fork', 'bank_id': 'bank_1', 'budget_cents': 1000000, 'ticks': 2})
    for branch in result['branches']:
        assert branch['audit']['balanced']
        assert observations(store.get(branch['simulation_id']))['shock_stories'][0]['report_id'] == report['report_id']
    assert store.get('world').state == before


def test_invalid_bank_and_api_inputs_fail(store, tmp_path):
    with pytest.raises(LedgerError, match='commercial bank'):
        stories.preview(store, 'world', stories.DebtStress(bank_id='household_1'))
    client = TestClient(create_app(tmp_path / 'api.sqlite3'))
    world = client.post('/api/worlds', json={}).json()['simulation_id']
    base = f'/api/worlds/{world}/shock-stories'
    for invalid in [{'yield_increase_bps': -1}, {'yield_increase_bps': 501}, {'modified_duration_years': 0}, {'debt_increase_percent': 101}, {'portfolio_exposure_percent': 101}, {'source_url': 'https://example.com'}]:
        assert client.post(base + '/preview', json=invalid).status_code == 422
    report = client.post(base + '/preview', json={}).json()
    assert client.post(base + '/apply', json={'report_id': report['report_id']}).status_code == 200
    assert client.get(base).json()[0]['status'] == 'applied'


def test_treasury_adapter_validates_dated_decimal_observation(monkeypatch):
    # Restore actual adapter (the store fixture is deliberately not used here).
    real_client = httpx.Client
    today = datetime.now(timezone.utc).date().isoformat()
    payload = {'data': [{'record_date': today, 'tot_pub_debt_out_amt': '40000000000000.01'}]}
    def handle(request):
        assert request.url.host == 'api.fiscaldata.treasury.gov'
        assert request.url.params['sort'] == '-record_date'
        return httpx.Response(200, json=payload)
    monkeypatch.setattr(stories.httpx, 'Client', lambda **kwargs: real_client(transport=httpx.MockTransport(handle)))
    baseline = stories.debt_baseline()
    assert baseline['value_usd'] == '40000000000000.01'
    assert baseline['observation_date'] == today
    assert baseline['stale'] is False
    for invalid in ['NaN', 'Infinity', '-1', 'not a number']:
        payload['data'][0]['tot_pub_debt_out_amt'] = invalid
        with pytest.raises(ProviderError, match='No substitute'):
            stories.debt_baseline()
    payload['data'] = []
    with pytest.raises(ProviderError):
        stories.debt_baseline()
