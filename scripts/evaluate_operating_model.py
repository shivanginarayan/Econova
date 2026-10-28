"""Reproducible legacy/current operating-model comparison; no model calls/crawls."""
import argparse,json
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
from backend.engine import Economy
from backend.calibration import load,checksum
from backend.forks import snapshot_hash

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--calibration-id',required=True);p.add_argument('--output',default='artifacts/operating-model-comparison.json');a=p.parse_args();sample=load(a.calibration_id);rows=[]
 for model in ['legacy_v1','cashflow_v2']:
  for mode in ['synthetic','public']:
   for scenario in ['standard','credit_crunch']:
    for seed in [41,42,43,44,45]:
     source=Economy.create('benchmark',seed=seed,scenario=scenario,operating_model=model,**({'calibration_id':a.calibration_id,'calibration':sample} if mode=='public' else {}));digest=snapshot_hash(source.state)
     for loss in [0,1000,4000]:
      branch=Economy(source.state)
      if loss:branch.shock('loss','bank_1',loss)
      for day in [6,12,30,60]:
       branch.step(day-branch.state['tick']);audit=branch.audit();assert audit['balanced'] and snapshot_hash(source.state)==digest
       m=branch.metrics();rows.append({'operating_model':model,'input_mode':mode,'scenario':scenario,'seed':seed,'loss_bps':loss,'day':day,'employment_percent':m['employment_rate']*100,'defaults':m['business_defaults'],'bank_stress':m['stressed_banks'],'balanced':True,'source_unchanged':True,'public_support_cents':m['public_support_disbursed_cents']})
 sensitivity=[]
 for income,wealth in [(8000,200),(9000,500),(10000,1000)]:
  w=Economy.create('sensitivity',scenario='credit_crunch',calibration_id=a.calibration_id,calibration=sample)
  w.state['operating_assumptions'].update(income_spending_bps=income,wealth_spending_bps=wealth)
  w.step(60);assert w.audit()['balanced'];sensitivity.append({'income_spending_bps':income,'wealth_spending_bps':wealth,'day':60,'employment_percent':w.metrics()['employment_rate']*100,'defaults':w.metrics()['business_defaults']})
 result={'evaluated_at':datetime.now(timezone.utc).isoformat(),'scope':'Fixed benchmark assumptions, not empirically calibrated or a forecast. Finite stocks may eventually require procurement. Retains all tested seeds and failures.','calibration_id':a.calibration_id,'calibration_sha256':checksum(sample),'seeds':[41,42,43,44,45],'horizons':[6,12,30,60],'assumptions':{'income_spending_bps':9000,'wealth_spending_bps':500,'capacity_payroll_bps':12500,'liquidity_target_bps':2000},'rows':rows,'sensitivity':sensitivity}
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 groups=defaultdict(list)
 for r in rows:
  if r['operating_model']=='cashflow_v2' and r['day']==60:groups[r['input_mode'],r['scenario'],r['loss_bps']].append(r['employment_percent'])
 print(json.dumps({'observations':len(rows),'all_balanced':True,'all_sources_unchanged':True,'new_model_day60':{str(k):[min(v),max(v)] for k,v in groups.items()},'sensitivity':sensitivity}),flush=True)
if __name__=='__main__':main()
