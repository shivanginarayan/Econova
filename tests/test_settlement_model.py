"""Versioned settlement regression: preserve legacy worlds, test new controls."""
from copy import deepcopy
import pytest
from backend.engine import Economy

def public_fixture():
    # Explicit test observations; no network or claimed live calibration.
    return {'calibration_id':'settlement_fixture','geography':'Test fixture','collected_at':'2026-10-27T00:00:00Z','provider':'apify','price_cents':[425,550,650],'daily_wage_cents':[15688],'sources':[{'actor_id':'test','run_id':'test','dataset_id':'test','source_url':'https://example.com/fixture'}]}

def test_legacy_absent_version_replays_explicit_legacy_rules():
    original=Economy.create('legacy',scenario='credit_crunch')
    original.state.pop('settlement_model')
    explicit=Economy(original.state);explicit.state['settlement_model']='full_deposit_protection_v1'
    original.step(6);explicit.step(6)
    explicit.state.pop('settlement_model')
    assert original.state==explicit.state
    assert original.view()['settlement_model']=='full_deposit_protection_v1'

def test_new_solvent_network_can_settle_without_a_fictitious_full_deposit_run():
    p=public_fixture();w=Economy.create('new',scenario='credit_crunch',calibration_id=p['calibration_id'],calibration=p)
    assert w.view()['settlement_model']=='scheduled_liquidity_v2'
    deposits={e['id']:sum(v for n,v in w.ledger.sheet(e['id'])['liabilities'].items() if n.startswith('deposit_')) for e in w.state['entities'].values() if e['kind']=='bank'}
    balances={k:w.ledger.balance(k+':reserves') for k in deposits}
    w.state['tick']=5;w.settle_interbank()
    assert not any(e['event_type']=='interbank_default' for e in w.state['events'])
    assert all(w.ledger.balance(k+':reserves')==v for k,v in balances.items())
    assert all(w.ledger.balance(k+':reserves') >= (d+9)//10 for k,d in deposits.items())
    assert w.audit()['balanced']
    journal=deepcopy(w.state['ledger']['journal']);w.settle_interbank()
    assert w.state['ledger']['journal']==journal

@pytest.mark.parametrize('seed',[41,42,43,44,45])
def test_seeded_control_and_severe_shock_remain_distinguishable(seed):
    control=Economy.create('paired',seed=seed,scenario='credit_crunch');shocked=Economy(control.state)
    shocked.shock('loss','bank_1',4000)
    control.step(6);shocked.step(6)
    assert control.metrics()['business_defaults']==0
    assert control.metrics()['employment_rate']==.95
    assert shocked.metrics()['employment_rate']<control.metrics()['employment_rate']
    assert control.audit()['balanced'] and shocked.audit()['balanced']

@pytest.mark.parametrize('seed',[41,42,43,44,45])
def test_well_capitalized_public_reference_control_survives_observation(seed):
    p=public_fixture();w=Economy.create('public',seed=seed,scenario='standard',calibration_id=p['calibration_id'],calibration=p)
    frozen=deepcopy(w.state['calibration']);w.step(12)
    assert w.metrics()['business_defaults']==0
    assert w.metrics()['employment_rate']==.95
    assert w.state['calibration']==frozen
    assert w.audit()['bank_counterparties_match']


@pytest.mark.parametrize('version',[None,'scheduled_liquidity_v2'])
def test_reset_preserves_rule_version_and_original_comparison_anchor(tmp_path,version):
    from backend.store import Store
    store=Store(tmp_path/'reset.sqlite3');source=Economy.create('source',scenario='credit_crunch')
    if version is None:source.state.pop('settlement_model')
    store.create(source)
    result=store.reset_world('source','reset')
    target=result['simulation_id']
    expected=version or 'full_deposit_protection_v1'
    assert store.get(target).view()['settlement_model']==expected
    with store.connection() as c:
        anchor=c.execute('SELECT snapshot,origin FROM scenario_starts WHERE source_id=?',(target,)).fetchone()
    import json
    assert anchor[1]=='created' and json.loads(anchor[0])['settlement_model']==expected
    assert store.reset_world('source','reset')==result
    assert store.get('source').state==source.state
