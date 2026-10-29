import base64
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setenv('ECONOMY_PUBLIC_MODE','1');monkeypatch.setenv('ECONOMY_ACCESS_PASSWORD','example-test-password-only')
    monkeypatch.setenv('ECONOMY_SESSION_SECRET','example-test-session-secret-not-for-deployment');monkeypatch.setenv('ECONOMY_COOKIE_SECURE','0')
    app=create_app(tmp_path/'public.sqlite3');headers={'Authorization':'Basic '+base64.b64encode(b'econova:example-test-password-only').decode()}
    return app,headers


def test_authentication_and_world_isolation(setup):
    app,headers=setup
    with TestClient(app) as first,TestClient(app) as second:
        assert first.get('/health').status_code==200
        assert first.get('/api/agents/status').status_code==401
        first.headers.update(headers);second.headers.update(headers)
        response=first.post('/api/worlds',json={});assert response.status_code==201,response.text
        world=response.json();path='/api/worlds/'+world['simulation_id']
        assert 'httponly' in response.headers['set-cookie'].lower()
        assert first.get(path).status_code==200
        assert second.get(path).status_code==404
        assert second.post(path+'/step',json={'ticks':1}).status_code==404
        assert first.post(path+'/step',json={'ticks':1},headers={'Origin':'https://untrusted.example'}).status_code==403
        reset=first.post(path+'/reset',json={'request_id':'reset'}).json()
        assert first.get('/api/worlds/'+reset['simulation_id']).status_code==200
        assert second.get('/api/worlds/'+reset['simulation_id']).status_code==404


def test_fork_ownership_follows_parent(setup):
    app,headers=setup
    with TestClient(app,headers=headers) as first,TestClient(app,headers=headers) as second:
        world=first.post('/api/worlds',json={}).json();path='/api/worlds/'+world['simulation_id']
        result=first.post(path+'/forks',json={'request_id':'fork','ticks':1,'budget_cents':10000}).json()
        assert first.get('/api/forks/'+result['fork_id']).status_code==200
        assert second.get('/api/forks/'+result['fork_id']).status_code==404
        branch=result['branches'][0]['simulation_id']
        assert first.get('/api/worlds/'+branch).status_code==200
        assert second.get('/api/worlds/'+branch).status_code==404


def test_public_limits_and_disabled_paid_integrations(setup,monkeypatch):
    app,headers=setup;monkeypatch.setenv('ECONOMY_JOBS_PER_HOUR','1')
    with TestClient(app,headers=headers) as c:
        assert c.post('/api/worlds',json={'households':201}).status_code==422
        world=c.post('/api/worlds',json={}).json();path='/api/worlds/'+world['simulation_id']
        assert c.post('/api/calibrations/collect',json={}).status_code==403
        assert c.post(path+'/agent-runs',json={}).status_code==403
        assert c.post(path+'/agent-jobs',json={'mode':'demo','request_id':'a'}).status_code==422
        request={'mode':'demo','request_id':'a','agent_review':True,'ticks':1,'max_experiments':1}
        assert c.post(path+'/agent-jobs',json={**request,'allow_paid_research':True}).status_code==403
        assert c.post(path+'/agent-jobs',json=request).status_code==202
        assert c.post(path+'/agent-jobs',json={**request,'request_id':'b'}).status_code==429
        store=app.state.store
        def advance_to_limit(w):w.state['tick']=240
        store.mutate(world['simulation_id'],advance_to_limit)
        assert c.post(path+'/step',json={'ticks':1}).status_code==409
        assert c.post(path+'/reset',json={'request_id':'again'}).status_code==200


def test_hosted_settings_fail_closed(tmp_path,monkeypatch):
    monkeypatch.setenv('ECONOMY_PUBLIC_MODE','1');monkeypatch.delenv('ECONOMY_ACCESS_PASSWORD',raising=False)
    with pytest.raises(ValueError,match='Hosted mode requires'):create_app(tmp_path/'no.sqlite3')


def test_static_ui_is_served_behind_access_gate(setup,tmp_path,monkeypatch):
    _,headers=setup;static=tmp_path/'dist';static.mkdir();(static/'index.html').write_text('<h1>Econova</h1>')
    monkeypatch.setenv('ECONOMY_STATIC_DIR',str(static));app=create_app(tmp_path/'static.sqlite3')
    with TestClient(app) as c:
        assert c.get('/').status_code==401
        assert c.get('/',headers=headers).text=='<h1>Econova</h1>'
