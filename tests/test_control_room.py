import json

import httpx
import pytest

from backend import spacetime
from backend.engine import Economy
from backend.forks import snapshot_hash
from backend.ledger import LedgerError
from backend.provider import ProviderError
from backend.store import Store


@pytest.fixture
def room(tmp_path, monkeypatch):
    store = Store(tmp_path / 'room.sqlite3')
    store.create(Economy.create('room_world', households=8, businesses=2, banks=2))
    row = ['room_world', snapshot_hash(store.get('room_world').state), 'bank_1', 4000, 'approved']
    monkeypatch.setenv('SPACETIMEDB_DATABASE', 'test')
    monkeypatch.setenv('SPACETIMEDB_TOKEN', 'test-publisher')
    calls = []
    fail = {'completion': False}

    def handle(request):
        calls.append(request.url.path)
        if request.url.path.endswith('/sql'):
            return httpx.Response(200, json=[{'rows': [row]}])
        if request.url.path.endswith('/complete_proposal') and fail['completion']:
            return httpx.Response(503)
        return httpx.Response(200, json={})

    original = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(handle)))
    monkeypatch.setattr(spacetime, 'sync_world', lambda *_: None)
    return store, row, fail, calls


@pytest.mark.parametrize('field,value', [(0, 'another_world'), (4, 'pending'), (4, 'rejected')])
def test_unapproved_or_wrong_world_cannot_execute(room, field, value):
    store, row, _, _ = room
    before = snapshot_hash(store.get('room_world').state)
    row[field] = value
    with pytest.raises(LedgerError):
        spacetime.execute_proposal(store, 'room_world', 'proposal_1')
    assert snapshot_hash(store.get('room_world').state) == before


def test_stale_snapshot_is_rejected_under_store_lock(room):
    store, _, _, _ = room
    store.mutate('room_world', lambda world: world.shock('other_shock', 'bank_2', 1000))
    before = snapshot_hash(store.get('room_world').state)
    with pytest.raises(LedgerError, match='World changed'):
        spacetime.execute_proposal(store, 'room_world', 'proposal_1')
    assert snapshot_hash(store.get('room_world').state) == before


def test_lost_database_acknowledgement_replays_financial_receipt(room):
    store, _, fail, _ = room
    fail['completion'] = True
    with pytest.raises(ProviderError):
        spacetime.execute_proposal(store, 'room_world', 'proposal_1')
    committed = snapshot_hash(store.get('room_world').state)
    fail['completion'] = False
    receipt = spacetime.execute_proposal(store, 'room_world', 'proposal_1')
    assert receipt['transaction_id'] == 'room_proposal_1'
    assert snapshot_hash(store.get('room_world').state) == committed
    assert store.get('room_world').audit()['balanced']
