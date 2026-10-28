import copy,csv,io,json,zipfile
import httpx
import pytest
from fastapi.testclient import TestClient
from backend import benchmarks as b
from backend.engine import Economy
from backend.main import create_app
from backend.store import Store


def sample():
    # Deliberately synthetic fixture values, never presented as fetched observations.
    data={'profile':{'fdic':{'capital_bps':1000,'cash_bps':800,'deposit_bps':8000},'census_cbp':[
        {'code':'72----','label':'Fixture industry','employees':100,'establishments':20,'daily_wage_cents':12000}]},
        'observations':[], 'assumptions':[], 'collected_at':'fixture','scope':'synthetic test fixture','status':{}}
    return dict(data,benchmark_id='bench_'+b.digest(data)[:24])


def test_mapping_balanced_scaled_and_frozen(tmp_path,monkeypatch):
    monkeypatch.setenv('ECONOMY_BENCHMARK_DIR',str(tmp_path));data=b.save(sample())
    w=Economy.create('w',benchmark_id=data['benchmark_id']);assert w.audit()['balanced']
    for bank in w.state['benchmark_mapping']['banks']:
        assert bank['achieved_capital_ratio']==pytest.approx(.1,abs=1e-6)
        assert bank['achieved_cash_ratio']==pytest.approx(.08,abs=1e-6)
    assert {e['wage_cents'] for e in w.state['entities'].values() if e['kind']=='household'}=={12000}
    data['profile']['fdic']['capital_bps']=3000
    assert w.state['public_benchmark']['profile']['fdic']['capital_bps']==1000
    w.step(12);assert w.audit()['balanced']


def test_reset_uses_frozen_snapshot_without_source_file(tmp_path,monkeypatch):
    monkeypatch.setenv('ECONOMY_BENCHMARK_DIR',str(tmp_path/'bench'));data=b.save(sample())
    w=Economy.create('w',benchmark_id=data['benchmark_id']);store=Store(tmp_path/'world.sqlite3');store.create(w)
    (b.root()/(data['benchmark_id']+'.json')).unlink()
    result=store.reset_world('w','reset');fresh=store.get(result['simulation_id'])
    for field in ['public_benchmark','benchmark_mapping','operating_assumptions']:
        assert fresh.state[field]==w.state[field]


def test_api_provenance_and_cache(tmp_path,monkeypatch):
    monkeypatch.setenv('ECONOMY_BENCHMARK_DIR',str(tmp_path/'bench'));data=b.save(sample())
    with TestClient(create_app(tmp_path/'api.sqlite3')) as c:
        assert c.get('/api/public-benchmarks/latest').json()['snapshot']==data
        r=c.post('/api/worlds',json={'benchmark_id':data['benchmark_id']});assert r.status_code==201,r.text
        world=r.json();assert world['public_benchmark']==data
        assert c.get('/api/worlds/'+world['simulation_id']+'/public-benchmarks').json()['snapshot']==data
        assert c.post('/api/worlds',json={'benchmark_id':'../../invalid'}).status_code==422


def test_tamper_and_missing_data_never_fall_back(tmp_path,monkeypatch):
    monkeypatch.setenv('ECONOMY_BENCHMARK_DIR',str(tmp_path));data=b.save(sample());path=b.root()/(data['benchmark_id']+'.json')
    altered=copy.deepcopy(data);altered['profile']['fdic']['capital_bps']=2000;path.write_text(json.dumps(altered))
    with pytest.raises(ValueError,match='integrity'):b.load(data['benchmark_id'])
    assert b.latest() is None
    data['profile'].pop('census_cbp')
    with pytest.raises(ValueError,match='incomplete'):Economy.create('w',benchmark_id=data['benchmark_id'],benchmark=data)


def test_fdic_complete_cohort_exclusions_and_ratios():
    def transport(request):
        if request.url.params.get('limit')=='1':return httpx.Response(200,json={'data':[{'data':{'REPDTE':'20260630'}}]})
        rows=[{'CERT':i,'REPDTE':'20260630','ASSET':1000,'EQ':eq,'DEP':800,'CHBAL':100} for i,eq in enumerate([100,200,-10])]
        return httpx.Response(200,json={'meta':{'total':3},'data':[{'data':r} for r in rows]})
    with httpx.Client(transport=httpx.MockTransport(transport)) as client:records,profile=b.fdic(client)
    assert profile['capital_bps']==1500
    assert records[0]['excluded_count']==1
    assert all(r['classification']=='derived' for r in records)


def test_fdic_incomplete_not_accepted():
    def transport(request):
        if request.url.params.get('limit')=='1':return httpx.Response(200,json={'data':[{'data':{'REPDTE':'20260630'}}]})
        return httpx.Response(200,json={'meta':{'total':3},'data':[]})
    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        with pytest.raises(ValueError,match='incomplete'):b.fdic(client)


def test_cbp_units_and_suppression():
    def archive(value):
        f=io.StringIO();writer=csv.DictWriter(f,fieldnames=['naics','lfo','emp','ap','est']);writer.writeheader()
        for code in b.SECTORS:writer.writerow(dict(naics=code,lfo='-',emp=10,ap=value,est=2))
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:z.writestr('cbp23us.txt',f.getvalue())
        return buf.getvalue()
    for value in ['260','D']:
        with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,content=archive(value)))) as c:
            if value=='D':
                with pytest.raises(ValueError,match='suppressed'):b.cbp(c)
            else:
                records,industries=b.cbp(c);assert industries[0]['daily_wage_cents']==10000
                assert any(r['classification']=='derived' and 'assumed260' in r['conversion'] for r in records)


def test_fred_missing_and_future_rows():
    csv_text='observation_date,FEDFUNDS\n2026-01-01,3.5\n2026-02-01,.\n2027-01-01,9\n'
    with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,text=csv_text))) as c:r=b.fred(c,'FEDFUNDS','2026-10-28')
    assert r['value']==3.5 and r['observation_date']=='2026-01-01'
    assert r['usage']=='validation_context'


def test_acs_does_not_expose_api_key():
    fields=[f'B19001_{n:03}{suffix}' for n in range(1,18) for suffix in ['E','M']]
    with httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=[fields,['10']*len(fields)]))) as c:
        records,status=b.acs(c,'private-test-secret')
    assert status=='available' and len(records)==34
    assert 'private-test-secret' not in json.dumps(records)
    assert b.acs(None,None)==([], 'needs_CENSUS_API_KEY')
