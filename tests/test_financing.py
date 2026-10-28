"""Working capital is scaled and bounded; settlement never repairs insolvency."""
from copy import deepcopy
import pytest
from backend.engine import Economy
from backend.ledger import LedgerError
from backend.store import Store


def create(**kwargs):
    return Economy.create('financial-test',financial_model='working_capital_v2',**kwargs)


def test_opening_cash_and_credit_scale_with_actual_payroll_and_balance():
    world=create()
    for business in world.state['entities'].values():
        if business['kind']!='business':continue
        assert world.ledger.balance(business['deposit_account'])==world.payroll(business)*5
        assert world.borrower_limit(business)==world.payroll(business)*20
    assert world.audit()['balanced']


def test_credit_above_old_nominal_cap_still_has_a_real_limit():
    world=create();business=world.customer('business_1');limit=world.borrower_limit(business)
    amount=min(limit,600000)
    world.loan('larger-business','business_1',amount)
    assert world.ledger.balance(business['debt_account'])==amount
    assert business['loan_due_tick']==20
    with pytest.raises(LedgerError,match='Borrower credit limit'):
        world.loan('above-scaled-cap','business_1',limit-amount+1)


def test_atomic_liquidation_funds_payment_without_adding_equity():
    world=create();payer=world.customer('business_1')
    receiver=next(e for e in world.state['entities'].values() if e['kind']=='household' and e['bank_id']!=payer['bank_id'])
    bank=payer['bank_id'];sheet=world.ledger.sheet(bank);reserves=sheet['assets']['reserves']
    world.ledger.post('test-allocate',[(bank+':reserves',-reserves),(bank+':risky_assets',reserves)])
    equity=world.ledger.sheet(bank)['equity_cents'];assets=world.ledger.sheet(bank)['assets_cents']
    entry=world.pay('payroll',payer['id'],receiver['id'],1000,'salary')
    assert any(x['account_id']==bank+':risky_assets' and x['signed_cents']==-1000 for x in entry['lines'])
    assert world.ledger.sheet(bank)['equity_cents']==equity
    assert world.ledger.sheet(bank)['assets_cents']==assets-1000
    assert world.pay('payroll',payer['id'],receiver['id'],1000,'salary')==entry
    assert world.audit()['balanced']


def test_failed_customer_payment_does_not_liquidate_bank_assets():
    world=create();payer=world.customer('business_1');bank=payer['bank_id']
    receiver=next(e for e in world.state['entities'].values() if e['kind']=='household' and e['bank_id']!=bank)
    reserves=world.ledger.balance(bank+':reserves')
    world.ledger.post('allocate-before-invalid',[(bank+':reserves',-reserves),(bank+':risky_assets',reserves)])
    before=deepcopy(world.state)
    with pytest.raises(LedgerError):
        world.pay('invalid-payment',payer['id'],receiver['id'],world.ledger.balance(payer['deposit_account'])+1)
    assert world.state==before


def test_liquidation_never_unfreezes_insolvent_bank():
    world=create(scenario='credit_crunch');world.shock('loss','bank_1',10000);assert world.bank_health('bank_1')['status']=='insolvent'
    payer=world.customer('business_1');before=deepcopy(world.state)
    with pytest.raises(LedgerError,match='insolvent'):
        world.pay('blocked',payer['id'],'household_1',100)
    assert world.state==before


def test_legacy_limit_and_due_dates_are_preserved():
    world=Economy.create('old');assert world.borrower_limit(world.customer('business_1'))==500000
    world.loan('old-credit','business_1',1000);assert world.customer('business_1')['loan_due_tick']==5


def test_reset_freezes_financing_conventions(tmp_path):
    world=create(financial_assumptions={'opening_payroll_days':7,'credit_payroll_days':15,'loan_review_days':10})
    store=Store(tmp_path/'test.sqlite3');store.create(world);result=store.reset_world('financial-test','reset')
    fresh=store.get(result['simulation_id'])
    assert fresh.state['financial_model']==world.state['financial_model']
    assert fresh.state['financial_assumptions']==world.state['financial_assumptions']
    assert fresh.state['entities']==world.state['entities']


def test_nonpositive_or_unbounded_financing_assumptions_rejected():
    for value in [0,-1,True,261]:
        with pytest.raises(LedgerError,match='Invalid financing'):
            create(financial_assumptions={'credit_payroll_days':value})


def test_cash_ratio_is_separate_from_assumed_settlement_capacity():
    world=create();bank='bank_1';reserves=world.ledger.balance(bank+':reserves')
    world.ledger.post('hold-investments',[(bank+':reserves',-reserves),(bank+':risky_assets',reserves)])
    health=world.bank_health(bank)
    assert health['liquidity_ratio']==0
    assert health['settlement_liquidity_ratio']>.1
    assert health['lending_available']


def test_agent_facts_use_engine_limit_and_review_date():
    from backend.credit_policy import business_facts,assess_credit
    world=create();facts=business_facts(world,'business_1')
    assert facts['credit_headroom_cents']==world.borrower_limit(world.customer('business_1'))
    assert facts['loan_review_days']==20
    result=assess_credit(world,'business_1',1)
    assert result['due_tick']==20
    assert not result['eligible'] # No actual payroll gap; a larger limit does not create a request.
