import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.engine import Economy
from backend.store import Store

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path/'alternate.sqlite3')) as c:
        yield c

def params(**kw):
    return {'request_id':'scenarios','bank_id':'bank_1','loss_bps':4000,'alternative_loss_bps':1000,'ticks':6,**kw}

def test_new_world_alternatives_use_original_snapshot_and_preserve_current(client):
    initial=client.post('/api/worlds',json={'scenario':'credit_crunch'}).json();base='/api/worlds/'+initial['simulation_id']
    client.post(base+'/shocks',json={'transaction_id':'actual-loss','bank_id':'bank_1','loss_bps':7000})
    client.post(base+'/step',json={'ticks':2});before=client.get(base).json()
    response=client.post(base+'/scenario-comparisons',json=params());assert response.status_code==200,response.text
    report=response.json();assert report['source_origin']=='created' and report['source_tick']==0
    assert {k:report['initial_metrics'][k] for k in initial['metrics']}==initial['metrics']
    assert [b['loss_bps'] for b in report['branches']]==[0,4000,1000]
    assert client.get(base).json()==before
    for branch in report['branches']:
        assert branch['audit']['balanced'] and branch['metrics']['simulation_tick']==6
        saved=client.get('/api/worlds/'+branch['simulation_id']).json()
        assert saved['metrics']=={k:v for k,v in branch['metrics'].items() if k in saved['metrics']}
        assert saved['calibration']==initial['calibration']
        assert branch['metrics']['public_support_disbursed_cents']==0
    assert client.get(base+'/scenario-comparisons/latest').json()==report

def test_retry_is_exact_and_changed_request_rejected(client):
    world=client.post('/api/worlds',json={}).json();base='/api/worlds/'+world['simulation_id']
    original=client.post(base+'/scenario-comparisons',json=params(ticks=2)).json()
    client.post(base+'/step',json={'ticks':1})
    assert client.post(base+'/scenario-comparisons',json=params(ticks=2)).json()==original
    assert client.post(base+'/scenario-comparisons',json=params(ticks=3)).status_code==409

@pytest.mark.parametrize('change',[{'ticks':31},{'ticks':0},{'alternative_loss_bps':4000},{'loss_bps':0}])
def test_invalid_comparison_parameters(client,change):
    world=client.post('/api/worlds',json={}).json()
    assert client.post('/api/worlds/'+world['simulation_id']+'/scenario-comparisons',json=params(**change)).status_code==422

def test_wrong_target_does_not_change_world(client):
    world=client.post('/api/worlds',json={}).json();base='/api/worlds/'+world['simulation_id']
    assert client.post(base+'/scenario-comparisons',json=params(bank_id='business_1')).status_code==409
    assert client.get(base).json()==world

def test_legacy_world_captures_honest_current_anchor(client):
    w=client.post('/api/worlds',json={}).json();store=client.app.state.store;id=w['simulation_id'];base='/api/worlds/'+id
    with store.connection() as c:c.execute('DELETE FROM scenario_starts WHERE source_id=?',(id,))
    client.post(base+'/step',json={'ticks':3});before=client.get(base).json()
    r=client.post(base+'/scenario-comparisons',json=params(ticks=2)).json()
    assert r['source_origin']=='captured_current' and r['source_tick']==3 and r['end_tick']==5
    assert client.get(base).json()==before
    client.post(base+'/step',json={'ticks':1})
    second=client.post(base+'/scenario-comparisons',json=params(request_id='second',ticks=2)).json()
    assert second['snapshot_sha256']==r['snapshot_sha256']

def test_concurrent_retries_do_not_publish_duplicate_branches(tmp_path):
    store=Store(tmp_path/'concurrent.sqlite3');world=Economy.create('source');store.create(world)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:store.compare_scenarios('source',params(ticks=1)),range(2)))
    assert results[0]==results[1]
    with store.connection() as c:
        assert c.execute('SELECT COUNT(*) FROM worlds').fetchone()[0]==4
        assert c.execute('SELECT COUNT(*) FROM scenario_comparisons').fetchone()[0]==1
