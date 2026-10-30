import json
import httpx
from fastapi.testclient import TestClient
from backend import tavily_research, agents, coordination
from backend.main import create_app


def evidence():
    return {'banks':[{'bank_id':'private-bank','capital_ratio':.01,'reserves_cents':123456789}]}


def test_bounded_request_and_sourced_sanitized_response(monkeypatch):
    monkeypatch.setenv('TAVILY_API_KEY','test-private-key')
    original=httpx.Client;calls=[]
    def handle(request):
        calls.append(request);body=json.loads(request.content)
        assert request.url=='https://api.tavily.com/search'
        assert request.headers['authorization']=='Bearer test-private-key'
        assert body['search_depth']=='basic' and body['max_results']==3
        assert body['include_raw_content'] is False and body['include_answer'] is False
        assert 'private-bank' not in request.content.decode() and '123456789' not in request.content.decode()
        return httpx.Response(200,json={'results':[
            {'title':'FDIC','url':'https://www.fdic.gov/resources','content':'Context test-private-key','published_date':'2026-10-01'},
            {'title':'unsafe','url':'javascript:alert(1)','content':'bad'},
            {'title':'wrong host','url':'https://fdic.gov.evil.example/','content':'bad'}]})
    monkeypatch.setattr(tavily_research.httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(handle),**kw))
    result=tavily_research.collect_context(evidence())
    assert len(calls)==1 and result['status']=='completed'
    assert len(result['sources'])==1 and result['sources'][0]['published_date']=='2026-10-01'
    assert result['retrieved_at'] and 'test-private-key' not in json.dumps(result)


def test_missing_key_does_not_claim_research(monkeypatch):
    monkeypatch.delenv('TAVILY_API_KEY',raising=False)
    assert tavily_research.collect_context(evidence())['status']=='not_configured'


def test_errors_are_not_retried_or_exposed(monkeypatch):
    monkeypatch.setenv('TAVILY_API_KEY','test-private-key');original=httpx.Client;calls=[]
    def handle(request):
        calls.append(request)
        return httpx.Response(401,text='test-private-key upstream private details')
    monkeypatch.setattr(tavily_research.httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(handle),**kw))
    result=tavily_research.collect_context(evidence())
    assert len(calls)==1 and result['status']=='unavailable'
    assert 'test-private-key' not in json.dumps(result)


def test_live_handoff_preserves_research_and_source_world(tmp_path,monkeypatch):
    request={'request_id':'research-test','mode':'live','agent_review':True,'ticks':1,'max_experiments':1,'budget_cap_cents':100000}
    research={'provider':'tavily','status':'completed','retrieved_at':'2026-10-30T00:00:00Z','sources':[{'title':'FDIC','url':'https://www.fdic.gov/resources','excerpt':'Public context','published_date':None}],'warning':tavily_research.WARNING}
    searches=[];planner_messages=[];review_messages=[]
    monkeypatch.setattr(tavily_research,'collect_context',lambda e:searches.append(e) or research)
    class Model(agents.DemoModel):
        def complete(self,messages,tools):
            if any('Captured evidence: ' in (m.get('content') or '') for m in messages):planner_messages.extend(messages)
            return super().complete(messages,tools)
    class Reviewer:
        provider='mock';model='mock'
        def complete(self,messages,tools):
            review_messages.extend(messages)
            return {'tool_calls':[{'function':{'name':'submit_review','arguments':json.dumps({'passed':True,'rationale':'Tested evidence checked.'})}}]}
    monkeypatch.setattr(agents,'build_model',lambda r:Model(r));monkeypatch.setattr(coordination,'NebiusModel',Reviewer)
    with TestClient(create_app(tmp_path/'research.sqlite3')) as client:
        world=client.post('/api/worlds',json={}).json();path='/api/worlds/'+world['simulation_id']
        before=client.get(path).json()
        response=client.post(path+'/agent-runs',json=request)
        assert response.status_code==200,response.text
        report=response.json()
        assert len(searches)==1 and report['external_research']==research
        assert report['trace'][0]['result']['external_context']==research
        assert 'https://www.fdic.gov/resources' in json.dumps(planner_messages)
        assert 'https://www.fdic.gov/resources' in json.dumps(review_messages)
        assert client.get(path).json()==before
        assert report['supervision']['status']=='passed'
