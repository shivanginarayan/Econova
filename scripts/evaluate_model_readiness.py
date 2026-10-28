"""Matched synthetic stress experiments; never calls a model or collects new data."""
import argparse
import json
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from backend.engine import Economy
from backend.calibration import load,checksum
from backend.forks import snapshot_hash

def evaluate(calibration=None,seeds=(41,42,43,44,45)):
 rows=[]
 for model in ('full_deposit_protection_v1','scheduled_liquidity_v2'):
  for mode in ('seeded_synthetic','frozen_public') if calibration else ('seeded_synthetic',):
   for scenario in ('standard','credit_crunch'):
    for seed in seeds:
     source=Economy.create('model_evaluation',seed=seed,scenario=scenario,**({'calibration_id':calibration['calibration_id'],'calibration':calibration} if mode=='frozen_public' else {}))
     source.state['settlement_model']=model
     digest=snapshot_hash(source.state)
     for loss in (0,1000,4000,8000):
      branch=Economy(source.state)
      if loss:branch.shock('evaluation-shock','bank_1',loss)
      for day in (3,6,12):
       branch.step(day-branch.state['tick'])
       audit=branch.audit()
       assert audit['balanced'] and audit['interbank_counterparties_match']
       assert snapshot_hash(source.state)==digest
       metrics=branch.metrics()
       rows.append({'settlement_model':model,'input_mode':mode,'scenario':scenario,'seed':seed,'loss_bps':loss,'day':day,'employment_percent':metrics['employment_rate']*100,'defaults':metrics['business_defaults'],'stressed_banks':metrics['stressed_banks'],'source_unchanged':True,'audit_balanced':True,'default_reasons':dict(Counter(e['details'].get('reason','unspecified') for e in branch.state['events'] if e['event_type']=='business_default'))})
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--calibration-id');p.add_argument('--output',default='artifacts/model-readiness');a=p.parse_args()
 calibration=load(a.calibration_id) if a.calibration_id else None
 rows=evaluate(calibration)
 payload={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'Controlled model sensitivity tests, not real-world validation. All fixed seeds and zero-effect/adverse outcomes retained. No model calls, collections or existing-world mutations.','calibration':{'id':calibration['calibration_id'],'sha256':checksum(calibration),'collected_at':calibration['collected_at']} if calibration else None,'seeds':[41,42,43,44,45],'loss_bps':[0,1000,4000,8000],'horizons':[3,6,12],'observations':rows}
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True);(out/'results.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
 groups=defaultdict(list)
 for row in rows:
  if row['day']==6:groups[row['settlement_model'],row['input_mode'],row['scenario'],row['loss_bps']].append(row)
 lines=['# Model sensitivity evidence','',payload['scope'],'',f"Generated {payload['checked_at']}. {len(rows)} checkpoints across both settlement versions. Five seeds, four losses, three horizons. Frozen public sample: {payload['calibration']}.",'','## Six-day employment ranges across all five seeds','']
 for key,items in groups.items():
  values=[i['employment_percent'] for i in items]
  line=f"{key[0]} / {key[1]} / {key[2]} / {key[3]/100:.0f}% loss: {min(values):.1f}% to {max(values):.1f}% employed; {sum(i['defaults'] for i in items)} defaults across five separate economies."
  lines.append('- '+line)
 lines+=['','## Limits','','The 10% retained liquidity buffer, par-value conversion of risky assets for settlement, compact population and rapid default rules are explicit model assumptions. These tests establish repeatability and sensitivity, not empirical accuracy. Old snapshots keep v1. Values at day12 may deteriorate even with no new shock because household spending, payroll and inventory are simplified; inspect results.json rather than extrapolating a short stable window. All audit/source-isolation checks passed during generation.']
 (out/'summary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(json.dumps({'checkpoints':len(rows),'all_audits_balanced':True,'all_sources_unchanged':True,'output':str(out)}))
 for key,items in groups.items():
  if key[0]=='scheduled_liquidity_v2':print(json.dumps({'group':key,'employment_range':[min(x['employment_percent'] for x in items),max(x['employment_percent'] for x in items)]}))
if __name__=='__main__':main()
