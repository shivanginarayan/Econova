from copy import deepcopy
from backend.engine import Economy
from backend.business_evidence import decision_finances

def test_decision_finances_are_observed_without_mutation():
    source=Economy.create('evidence',scenario='standard')
    source.step(2)
    before=deepcopy(source.state)
    facts=decision_finances(source,'business_1')
    assert source.state==before
    assert facts['net_worth_cents']==source.ledger.sheet('business_1')['equity_cents']
    purchases=[e for e in source.state['events'] if e['event_type']=='purchase' and e['counterparty_id']=='business_1']
    assert facts['sales_cents']==sum(e['amount_cents'] for e in purchases)
    assert facts['sales_start_tick']==1 and facts['sales_end_tick']==2
    assert 'credit_score' not in facts

def test_rejections_retain_decision_time_finances():
    source=Economy.create('rejected',scenario='credit_crunch')
    source.shock('loss','bank_1',loss_bps=4000)
    source.step(6)
    rejections=[e for e in source.state['events'] if e['event_type']=='credit_rejected']
    assert rejections
    for event in rejections:
        facts=event['details']['finances']
        assert facts['captured_tick']==event['simulation_tick']
        assert facts['sales_end_tick']==event['simulation_tick']
        assert isinstance(facts['net_worth_cents'],int)
        assert facts['debt_cents']>=0
    assert source.audit()['balanced']
