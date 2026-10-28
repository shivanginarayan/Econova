"""Diagnose input/operating assumptions without changing or tuning the model."""
import argparse,json
from collections import Counter
from pathlib import Path
from backend.engine import Economy
from backend.calibration import load,checksum

def audit(calibration,seed=42,model="cashflow_v2"):
 w=Economy.create('operating_audit',seed=seed,scenario='credit_crunch',operating_model=model,**({'calibration_id':calibration['calibration_id'],'calibration':calibration} if calibration else {}))
 businesses=[]
 for b in w.state['entities'].values():
  if b['kind']!='business':continue
  payroll=w.payroll(b);capacity=len(b['employees'])*w.output_per_worker(b)*b['price_cents']
  businesses.append({'business_id':b['id'],'employees':len(b['employees']),'daily_payroll_cents':payroll,'price_cents':b['price_cents'],'maximum_daily_sales_cents':capacity,'maximum_sales_to_payroll':round(capacity/payroll,4) if payroll else None,'initial_cash_cents':w.ledger.balance(b['deposit_account'])})
 wages=sum(b['daily_payroll_cents'] for b in businesses)
 budgets=0
 for e in w.state['entities'].values():
  if e['kind']!='household':continue
  if not w.circular_flow():budgets+=e['consumption_budget_cents'];continue
  income=e['wage_cents'] if e['employer_id'] else 0
  cash=w.ledger.balance(e['deposit_account']);params=w.state['operating_assumptions']
  budgets+=min(cash+income,income*params['income_spending_bps']//10000+cash*params['wealth_spending_bps']//10000)
 checkpoints=[]
 for day in [6,12,30]:
  w.step(day-w.state['tick']);m=w.metrics()
  checkpoints.append({'day':day,'employment_percent':m['employment_rate']*100,'defaults':m['business_defaults'],'balanced':w.audit()['balanced'],'default_reasons':dict(Counter(e['details'].get('reason','') for e in w.state['events'] if e['event_type']=='business_default'))})
 return {'operating_model':model,'seed':seed,'input_mode':'frozen_public' if calibration else 'seeded_synthetic','initial_daily_payroll_cents':wages,'initial_household_spending_budgets_cents':budgets,'spending_budget_to_payroll':round(budgets/wages,4),'businesses':businesses,'checkpoints':checkpoints}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--calibration-id',required=True);p.add_argument('--operating-model',choices=['cashflow_v2','legacy_v1'],default='cashflow_v2');p.add_argument('--output',default='artifacts/operating-audit.json');a=p.parse_args();calibration=load(a.calibration_id)
 result={'scope':'Diagnostic of fixed current assumptions; no model revision, AI calls or collection. Capacity is an upper bound, not guaranteed sales. Spending budgets are initial caps, not actual spending.','calibration_id':a.calibration_id,'calibration_sha256':checksum(calibration),'runs':[audit(c,seed,a.operating_model) for c in [None,calibration] for seed in [41,42,43,44,45]]}
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 for row in result['runs']:
  if row['seed']==42:print(json.dumps(row))
if __name__=='__main__':main()
