"""Cashflow-v2 accounting/behavior regressions; fixture data is explicitly synthetic."""
from copy import deepcopy
import pytest
from backend.engine import Economy
from backend.store import Store

def fixture():
 return {'calibration_id':'operating_fixture','geography':'Synthetic test observations','collected_at':'2026-10-28T00:00:00Z','provider':'apify','price_cents':[425,550,650],'daily_wage_cents':[15688],'sources':[{'actor_id':'test','run_id':'test','dataset_id':'test','source_url':'https://example.com/test'}]}
def world(seed=42,model='cashflow_v2'):
 c=fixture();return Economy.create('test',seed=seed,scenario='credit_crunch',calibration_id=c['calibration_id'],calibration=c,operating_model=model)

def test_capacity_is_consistent_with_selected_wages_and_prices_without_creating_cash():
 w=world()
 for b in w.state['entities'].values():
  if b['kind']=='business' and b['employees']:
   payroll=w.payroll(b);capacity=len(b['employees'])*b['units_per_worker']*b['price_cents']
   assert capacity*10000>=payroll*12500
   assert (capacity-len(b['employees'])*b['price_cents'])*10000<payroll*12500
 assert w.metrics()['public_support_disbursed_cents']==0
 assert w.audit()['balanced']

def test_only_received_wages_drive_income_spending_and_purchases_stay_within_budgets():
 w=world();w.step()
 events=w.state['events'];salaries={e['counterparty_id']:e['amount_cents'] for e in events if e['event_type']=='salary'}
 budgets={e['agent_id']:e['details'] for e in events if e['event_type']=='consumption_budget'}
 assert sum(b['received_wages_cents'] for b in budgets.values())==sum(salaries.values())
 for household,details in budgets.items():
  assert details['received_wages_cents']==salaries.get(household,0)
  spent=sum(e['amount_cents'] for e in events if e['event_type']=='purchase' and e['agent_id']==household)
  assert spent<=details['budget_cents']
  view=w.entity_view(household)
  assert view['consumption_budget_cents'] is None
  assert view['last_consumption_budget_cents']==details['budget_cents']
  assert view['last_received_wages_cents']==salaries.get(household,0)
 assert w.audit()['balanced']

def test_saved_behavior_parameters_are_used_and_do_not_mutate_balances():
 w=world();h=w.customer('household_1');before=deepcopy(w.state)
 amount=w.ledger.balance(h['deposit_account'])
 w.state['operating_assumptions']['income_spending_bps']=0
 w.state['operating_assumptions']['wealth_spending_bps']=0
 assert w.household_spending_budget(h,0)==0
 assert w.ledger.balance(h['deposit_account'])==amount
 assert w.state['ledger']==before['ledger']

def test_liquidity_management_converts_assets_without_equity_or_public_support():
 w=world();bank='bank_1';amount=w.ledger.balance(bank+':reserves')-1
 w.ledger.post('portfolio-shift',[(bank+':reserves',-amount),(bank+':risky_assets',amount)],{'type':'test_shift'})
 before=w.ledger.sheet(bank);w.manage_operating_liquidity();after=w.ledger.sheet(bank)
 assert after['assets']['reserves']>before['assets']['reserves']
 assert after['assets_cents']==before['assets_cents'] and after['equity_cents']==before['equity_cents']
 assert w.metrics()['public_support_disbursed_cents']==0
 journal=len(w.state['ledger']['journal']);w.manage_operating_liquidity()
 assert len(w.state['ledger']['journal'])==journal
 assert w.audit()['balanced']

def test_insolvent_bank_is_not_recapitalized_and_shock_can_still_cause_failures():
 w=world();w.shock('loss','bank_1',10000);assert w.bank_health('bank_1')['status']=='insolvent'
 sheet=deepcopy(w.ledger.sheet('bank_1'));w.manage_operating_liquidity()
 assert w.ledger.sheet('bank_1')==sheet
 w.step(12);assert w.metrics()['business_defaults']>0
 assert w.metrics()['employment_rate']<.95 and w.audit()['balanced']

@pytest.mark.parametrize('seed',[41,42,43,44,45])
def test_public_reference_no_shock_controls_do_not_structurally_collapse(seed):
 w=world(seed);sample=deepcopy(w.state['calibration']);w.step(60)
 assert w.metrics()['business_defaults']==0
 assert w.metrics()['employment_rate']>=.90  # Small stress layoffs are permitted; systemic collapse is not.
 assert w.state['calibration']==sample and w.audit()['balanced']

def test_legacy_missing_marker_replays_the_same_old_operating_rules():
 a=world(model='legacy_v1');a.state.pop('operating_model');b=Economy(a.state);b.state['operating_model']='legacy_v1'
 a.step(12);b.step(12);b.state.pop('operating_model');assert a.state==b.state
 assert a.view()['operating_model']=='legacy_v1'

@pytest.mark.parametrize('model',['legacy_v1','cashflow_v2'])
def test_reset_preserves_operating_version_and_original_anchor(tmp_path,model):
 store=Store(tmp_path/'reset.sqlite3');w=world(model=model);store.create(w)
 r=store.reset_world('test','reset');reset=store.get(r['simulation_id'])
 assert reset.state['operating_model']==model
 assert reset.state.get('operating_assumptions')==w.state.get('operating_assumptions')
 assert {k:v.get('units_per_worker') for k,v in reset.state['entities'].items()}=={k:v.get('units_per_worker') for k,v in w.state['entities'].items()}
 assert store.reset_world('test','reset')==r


def test_reset_uses_frozen_parameters_even_if_new_defaults_change(tmp_path,monkeypatch):
 import backend.operating as operating
 store=Store(tmp_path/'frozen.sqlite3');source=world()
 source.state['operating_assumptions']['income_spending_bps']=8000
 store.create(source)
 monkeypatch.setattr(operating,'CAPACITY_PAYROLL_BPS',20000)
 target=store.get(store.reset_world('test','new')['simulation_id'])
 assert target.state['operating_assumptions']==source.state['operating_assumptions']
 assert target.customer('business_1')['units_per_worker']==source.customer('business_1')['units_per_worker']
