import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


@pytest.fixture
def setup(tmp_path,monkeypatch):
    monkeypatch.setenv('ECONOMY_PUBLIC_MODE','1');monkeypatch.delenv('ECONOMY_ACCESS_PASSWORD',raising=False)
    monkeypatch.setenv('ECONOMY_SESSION_SECRET','example-test-session-secret-not-for-deployment');monkeypatch.setenv('ECONOMY_COOKIE_SECURE','0')
    app=create_app(tmp_path/'public.sqlite3');headers={}
    return app,headers


def test_anonymous_access_and_world_isolation(setup):
    app,headers=setup
    with TestClient(app) as first,TestClient(app) as second:
        assert first.get('/health').status_code==200
        initial=first.get('/api/agents/status');assert initial.status_code==200
        assert 'httponly' in initial.headers['set-cookie'].lower()
        assert 'samesite=strict' in initial.headers['set-cookie'].lower()
        first.headers.update(headers);second.headers.update(headers)
        response=first.post('/api/worlds',json={});assert response.status_code==201,response.text
        world=response.json();path='/api/worlds/'+world['simulation_id']
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
    monkeypatch.setenv('ECONOMY_PUBLIC_MODE','1');monkeypatch.delenv('ECONOMY_SESSION_SECRET',raising=False)
    with pytest.raises(ValueError,match='Hosted mode requires'):create_app(tmp_path/'no.sqlite3')


def test_static_ui_is_served_anonymously(setup,tmp_path,monkeypatch):
    _,headers=setup;static=tmp_path/'dist';static.mkdir();(static/'index.html').write_text('<h1>Econova</h1>')
    monkeypatch.setenv('ECONOMY_STATIC_DIR',str(static));app=create_app(tmp_path/'static.sqlite3')
    with TestClient(app) as c:
        response=c.get('/');assert response.status_code==200
        assert 'www-authenticate' not in response.headers
        assert 'httponly' in response.headers['set-cookie'].lower()
        assert c.get('/',headers=headers).text=='<h1>Econova</h1>'


@pytest.mark.parametrize('secret',['','too-short'])
def test_missing_or_short_session_secret_is_rejected(tmp_path,monkeypatch,secret):
    monkeypatch.setenv('ECONOMY_PUBLIC_MODE','1')
    monkeypatch.setenv('ECONOMY_SESSION_SECRET',secret)
    with pytest.raises(ValueError,match='ECONOMY_SESSION_SECRET'):
        create_app(tmp_path/'invalid.sqlite3')


def test_tampered_cookie_cannot_access_another_visitor(setup):
    app,_=setup
    with TestClient(app) as owner,TestClient(app) as stranger:
        world=owner.post('/api/worlds',json={}).json()
        cookie=owner.cookies.get('econova-visitor')
        visitor,signature=cookie.split('.')
        stranger.cookies.set('econova-visitor',visitor+'.'+('0' if signature[0]!='0' else '1')+signature[1:],domain='testserver.local',path='/')
        assert stranger.get('/api/worlds/'+world['simulation_id']).status_code==404
        assert stranger.cookies.get('econova-visitor')!=cookie


def test_default_inference_budgets_and_environment_overrides(setup,monkeypatch):
    from fastapi import HTTPException
    from starlette.requests import Request
    import asyncio
    app,_=setup;access=app.state.hosted_access
    monkeypatch.delenv('ECONOMY_JOBS_PER_HOUR',raising=False)
    monkeypatch.delenv('ECONOMY_GLOBAL_JOBS_PER_HOUR',raising=False)
    async def attempt(visitor):
        import json
        body=json.dumps({'agent_review':True}).encode()
        async def receive():return {'type':'http.request','body':body,'more_body':False}
        request=Request({'type':'http','method':'POST','scheme':'https','server':('testserver',443),'path':'/api/worlds/test/agent-jobs','headers':[], 'query_string':b'', 'state':{'visitor':visitor},'path_params':{}},receive)
        await access.authorize(request)
    asyncio.run(attempt('visitor0'));asyncio.run(attempt('visitor0'))
    with pytest.raises(HTTPException) as error:asyncio.run(attempt('visitor0'))
    assert error.value.status_code==429
    for i in range(1,5):
        asyncio.run(attempt('visitor'+str(i)));asyncio.run(attempt('visitor'+str(i)))
    with pytest.raises(HTTPException) as error:asyncio.run(attempt('visitor5'))
    assert error.value.status_code==429
    monkeypatch.setenv('ECONOMY_JOBS_PER_HOUR','3');monkeypatch.setenv('ECONOMY_GLOBAL_JOBS_PER_HOUR','11')
    asyncio.run(attempt('visitor0'))


def test_anonymous_https_cookie_is_secure(setup,monkeypatch):
    app,_=setup;monkeypatch.delenv('ECONOMY_COOKIE_SECURE',raising=False)
    with TestClient(app,base_url='https://testserver') as visitor:
        response=visitor.get('/api/agents/status')
        assert response.status_code==200
        cookie=response.headers['set-cookie'].lower()
        assert '; secure' in cookie and '; httponly' in cookie and 'samesite=strict' in cookie


def test_anonymous_provider_status_never_exposes_key(setup,monkeypatch):
    app,_=setup
    monkeypatch.setenv('NEBIUS_API_KEY','test-private-provider-key-not-real')
    monkeypatch.setenv('NEBIUS_MODEL','test-Nemotron-model')
    with TestClient(app) as visitor:
        response=visitor.get('/api/agents/status')
        assert response.status_code==200
        assert 'test-private-provider-key-not-real' not in response.text
        assert 'test-private-provider-key-not-real' not in str(response.headers)
