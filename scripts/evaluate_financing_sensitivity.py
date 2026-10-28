"""Actual-menu demonstration checks and financing sensitivity; no inference or rescue."""
import json
from pathlib import Path
from datetime import datetime,timezone
from backend.benchmarks import latest,digest
from backend.calibration import load,checksum
from backend.apify_collection import latest_data
from backend.engine import Economy
from backend.forks import snapshot_hash
from scripts.run_backend import load_environment


def evaluate():
    load_environment();snapshot=latest();data,_=latest_data()
    if not data:raise ValueError('Actual saved menu inputs are required; no substitute')
    calibration=load(data['calibration_id']);rows=[];diagnostics=[]
    for seed in [41,42,43,44,45]:
        for label,rates in [('default',{}),('shorter_buffers',{'opening_payroll_days':3,'credit_payroll_days':10,'loan_review_days':10}),('longer_buffers',{'opening_payroll_days':10,'credit_payroll_days':40,'loan_review_days':40})]:
            source=Economy.create('demo',seed=seed,benchmark_id=snapshot['benchmark_id'],benchmark=snapshot,
                calibration_id=calibration['calibration_id'],calibration=calibration,financial_assumptions=rates)
            before=snapshot_hash(source.state)
            for loss in ([0,4000] if label=='default' else [0]):
                branch=Economy(source.state)
                if loss:branch.shock('loss','bank_1',loss)
                for day in [6,12,60]:
                    branch.step(day-branch.state['tick']);metrics=branch.metrics();assert branch.audit()['balanced'] and snapshot_hash(source.state)==before
                    rows.append(dict(seed=seed,variant=label,loss_bps=loss,day=day,employment_percent=metrics['employment_rate']*100,
                        defaults=metrics['business_defaults'],stressed_banks=metrics['stressed_banks'],balanced=True,source_unchanged=True,
                        public_support_cents=metrics['public_support_disbursed_cents']))
                if label=='default' and loss==0:
                    diagnostics.append(dict(seed=seed,events=[e for e in branch.state['events'] if e['event_type'] in ['job_lost','credit_rejected','payment_rejected','production_limited']][:8]))
    controls=[r for r in rows if r['loss_bps']==0]
    standard=[r for r in rows if r['variant']=='default' and r['day']==60]
    before={r['seed']:r for r in standard if r['loss_bps']==0}
    passed=all(r['employment_percent']>=90 and r['defaults']==0 and r['public_support_cents']==0 for r in controls) and all(r['employment_percent']<before[r['seed']]['employment_percent'] for r in standard if r['loss_bps']==4000)
    return dict(evaluated_at=datetime.now(timezone.utc).isoformat(),scope='Actual frozen menu-price sample; joint financing sensitivities, not empirical estimation.',benchmark_id=snapshot['benchmark_id'],benchmark_sha256=digest(snapshot),
        calibration_id=calibration['calibration_id'],calibration_sha256=checksum(calibration),rows=rows,control_diagnostics=diagnostics,passed=passed)

if __name__=='__main__':
    result=evaluate();Path('artifacts/reconciled-demo-sensitivity.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checkpoints':len(result['rows']),'passed':result['passed'],'day60':[r for r in result['rows'] if r['day']==60]},indent=2))
