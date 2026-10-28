import json
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend import coordination, agents, credit_agents
from backend.agents import DemoModel
from backend.credit_agents import DemoCreditModel
from backend.provider import ProviderError

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'coordination.sqlite3')) as client:
        yield client

def create(client, drain=False):
    w=client.post('/api/worlds',json={'scenario':'standard'}).json()
    base='/api/worlds/'+w['simulation_id']
    if drain:
        cash=next(e for e in w['entities'] if e['id']=='business_1')['balance_sheet']['assets']['deposit']
        assert client.post(base+'/payments',json={'transaction_id':'gap','payer_id':'business_1','receiver_id':'business_2','amount_cents':cash}).status_code==200
    return base

def request(**kw):
    return {'request_id':'reviewed','mode':'demo','agent_review':True,**kw}

def test_policy_handoff_review_and_no_mutation(client):
    base=create(client);before=client.get(base).json()
    response=client.post(base+'/agent-runs',json=request(max_experiments=1,ticks=2))
    assert response.status_code==200,response.text
    r=response.json();assert r['supervision']['status']=='passed',r['supervision']
    assert [e['sequence'] for e in r['activity']]==list(range(1,len(r['activity'])+1))
    assert any(e['actor']=='investigator' and e['target']=='policy' for e in r['activity'])
    assert {e['actor'] for e in r['activity']}=={'investigator','policy','supervisor'}
    assert all(c['passed'] for c in r['supervision']['checks'])
    assert client.get(base).json()==before
    assert client.post('/api/agent-runs/'+r['run_id']+'/apply',json={'transaction_id':'apply'}).status_code==200

def test_credit_round_trip_supervised_then_separate_settlement(client):
    base=create(client,True);before=client.get(base).json()
    r=client.post(base+'/businesses/business_1/credit-runs',json=request()).json()
    assert r['status']=='approved' and r['supervision']['status']=='passed',r
    assert any(e['actor']=='business' and e['target']=='bank' for e in r['activity'])
    assert any(e['actor']=='bank' and e['target']=='business' for e in r['activity'])
    assert client.get(base).json()==before
    paid=client.post('/api/credit-runs/'+r['run_id']+'/settle',json={'transaction_id':'settle'})
    assert paid.status_code==200 and paid.json()['audit']['balanced']

def test_supply_agents_and_supervisor(client):
    base=create(client);before=client.get(base).json()
    r=client.post(base+'/businesses/business_1/procurement-runs',json=request()).json()
    assert r['supervision']['status']=='passed',r
    assert {e['actor'] for e in r['activity']}=={'buyer','business_2','business_3','supervisor'}
    assert client.get(base).json()==before
    assert client.post('/api/procurement-runs/'+r['run_id']+'/settle',json={'transaction_id':'supply'}).status_code==200

class Reviewer:
    provider='test_independent_model';model='review-model'
    verdict=True;fail=False
    def complete(self,messages,tools):
        assert tools[0]['function']['name']=='submit_review'
        evidence=json.loads(messages[1]['content'])
        assert evidence['trace'] and evidence['checks']
        if self.fail:raise ProviderError('Review service unavailable')
        return {'tool_calls':[{'function':{'name':'submit_review','arguments':json.dumps({'passed':self.verdict,'rationale':'Checked the recorded handoffs against the evidence.'})}}]}

@pytest.mark.parametrize('kind',['central_bank','credit','procurement'])
def test_review_gate_blocks_unreviewed_reports(kind):
    from backend.ledger import LedgerError
    for status in [None,'running','blocked','failed']:
        with pytest.raises(LedgerError):
            coordination.require_review({'request':{'agent_review':True},'supervision':{'status':status}})

@pytest.mark.parametrize('verdict,fail,expected',[(True,False,'passed'),(False,False,'blocked'),(True,True,'failed')])
def test_independent_live_review_cannot_move_funds_or_be_bypassed(client,monkeypatch,verdict,fail,expected):
    monkeypatch.setattr(agents,'build_model',lambda r:DemoModel(r))
    monkeypatch.setattr(Reviewer,'verdict',verdict);monkeypatch.setattr(Reviewer,'fail',fail)
    monkeypatch.setattr(coordination,'NebiusModel',Reviewer)
    base=create(client);before=client.get(base).json()
    r=client.post(base+'/agent-runs',json=request(mode='live',max_experiments=1,ticks=2)).json()
    assert r['supervision']['status']==expected,r
    assert client.get(base).json()==before
    applied=client.post('/api/agent-runs/'+r['run_id']+'/apply',json={'transaction_id':'apply'})
    assert applied.status_code==(200 if expected=='passed' else 409),applied.text

def test_supervisor_cannot_override_financial_check_failure(client,monkeypatch):
    original=coordination.review_checks
    monkeypatch.setattr(coordination,'review_checks',lambda *args:original(*args)+[{'name':'Injected mismatch','passed':False}])
    monkeypatch.setattr(agents,'build_model',lambda r:DemoModel(r))
    monkeypatch.setattr(coordination,'NebiusModel',Reviewer)
    base=create(client)
    r=client.post(base+'/agent-runs',json=request(mode='live',max_experiments=1,ticks=2)).json()
    assert r['supervision']['status']=='blocked'
    assert client.post('/api/agent-runs/'+r['run_id']+'/apply',json={'transaction_id':'apply'}).status_code==409


def test_passed_gate_is_published_only_once_after_all_activity(client, monkeypatch):
    store = client.app.state.store
    original = store.save_credit
    passed_saves = []
    def save(report):
        if (report.get('supervision') or {}).get('status') == 'passed':
            passed_saves.append(json.loads(json.dumps(report)))
        original(report)
    monkeypatch.setattr(store, 'save_credit', save)
    base = create(client, True)
    result = client.post(base+'/businesses/business_1/credit-runs', json=request()).json()
    assert result['supervision']['status'] == 'passed'
    assert len(passed_saves) == 1
    assert passed_saves[0]['active_agent'] is None
    assert passed_saves[0]['activity'][-1]['target'] == 'human'
