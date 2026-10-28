"""Matched, no-rescue tests of sourced opening conditions versus existing assumptions."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from backend.benchmarks import latest,digest
from backend.engine import Economy
from backend.forks import snapshot_hash


def evaluate(snapshot):
 rows=[]
 for mode in ['model_assumptions','public_opening_v1','public_working_capital_v2']:
  for scenario in ['standard','credit_crunch']:
   for seed in [41,42,43,44,45]:
    source=Economy.create('benchmark',seed=seed,scenario=scenario,**({'benchmark_id':snapshot['benchmark_id'],'benchmark':snapshot,'financial_model':'fixed_limits_v1' if mode=='public_opening_v1' else 'working_capital_v2'} if mode!='model_assumptions' else {}))
    source_hash=snapshot_hash(source.state)
    for loss in [0,1000,4000]:
     branch=Economy(source.state)
     if loss:branch.shock('benchmark-loss','bank_1',loss)
     for day in [1,6,12,30,60]:
      branch.step(day-branch.state['tick']);m=branch.metrics();audit=branch.audit()
      assert audit['balanced'] and snapshot_hash(source.state)==source_hash
      rows.append(dict(mode=mode,scenario=scenario,seed=seed,loss_bps=loss,day=day,
       financial_model=branch.state.get('financial_model','fixed_limits_v1'),employment_percent=m['employment_rate']*100,defaults=m['business_defaults'],stressed_banks=m['stressed_banks'],
       public_support_cents=m['public_support_disbursed_cents'],balanced=True,source_unchanged=True))
 return dict(evaluated_at=datetime.now(timezone.utc).isoformat(),benchmark_id=snapshot['benchmark_id'],benchmark_sha256=digest(snapshot),
   scope='Matched synthetic seed and shock, different opening mappings. Not evidence of real-world predictive accuracy. Retains all tested cases. Public mode changes joint bank/workforce assumptions; not single-parameter attribution.',
   public_snapshot=snapshot,rows=rows,acceptance=acceptance(rows))

def acceptance(rows):
 controls=[r for r in rows if r['mode']=='public_working_capital_v2' and r['loss_bps']==0]
 ends=[r for r in rows if r['mode']=='public_working_capital_v2' and r['day']==60 and r['scenario']=='standard']
 control={r['seed']:r for r in ends if r['loss_bps']==0}
 shocks=[r for r in ends if r['loss_bps']==4000]
 gates={'all_accounting_balanced':all(r['balanced'] and r['source_unchanged'] for r in rows),
        'no_control_defaults':all(r['defaults']==0 for r in controls),
        'control_employment_at_least_90_percent':all(r['employment_percent']>=90 for r in controls),
        'severe_shock_lowers_employment_in_each_standard_seed':len(shocks)==5 and all(r['employment_percent']<control[r['seed']]['employment_percent'] for r in shocks),
        'no_automatic_support':all(r['public_support_cents']==0 for r in rows)}
 return {'criteria_scope':'Demonstration regression gates; not empirical validation or fit to real crisis outcomes.', 'gates':gates,'passed':all(gates.values())}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='artifacts/public-benchmark-evaluation.json');args=p.parse_args()
 snapshot=latest()
 if not snapshot:raise SystemExit('Collect public benchmarks first')
 result=evaluate(snapshot);target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 controls=[r for r in result['rows'] if r['mode']=='public_working_capital_v2' and r['loss_bps']==0 and r['day']==60]
 print(json.dumps({'checkpoints':len(result['rows']),'acceptance':result['acceptance'],'public_controls_day60':controls},indent=2))
