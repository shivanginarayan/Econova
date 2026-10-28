"""Trace no-shock controls without changing the economic rules."""
import argparse,json
from pathlib import Path
from backend.benchmarks import latest,load
from backend.engine import Economy


def diagnose(snapshot):
    reports=[]
    for seed in [41,42,43,44,45]:
        world=Economy.create('diagnostic',seed=seed,benchmark_id=snapshot['benchmark_id'],benchmark=snapshot)
        opening=[]
        for business in world.state['entities'].values():
            if business['kind']!='business':continue
            cash=world.ledger.balance(business['deposit_account']);payroll=world.payroll(business)
            opening.append(dict(id=business['id'],workers=len(business['employees']),daily_payroll_cents=payroll,
                opening_cash_cents=cash,payroll_days=cash/payroll if payroll else None))
        world.step(60)
        failures=[e for e in world.state['events'] if e['event_type'] in
            ['credit_rejected','payment_rejected','business_default','job_lost','production_limited']]
        reports.append(dict(seed=seed,opening=opening,employment_day60=world.metrics()['employment_rate']*100,
            first_failures=failures[:12],audit=world.audit()))
    return dict(benchmark_id=snapshot['benchmark_id'],scope='Synthetic no-additional-shock diagnostics, standard scenario; first12 recorded stress events per seed. Not a causal decomposition.',cases=reports)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--benchmark-id');parser.add_argument('--output',default='artifacts/public-benchmark-diagnostics.json');args=parser.parse_args()
    snapshot=load(args.benchmark_id) if args.benchmark_id else latest()
    if not snapshot:raise SystemExit('Collect public benchmarks first')
    result=diagnose(snapshot);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(result['cases']),'all_balanced':all(r['audit']['balanced'] for r in result['cases'])}))
