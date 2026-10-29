"""Bounded representative live-agent evaluation. No automatic financial action."""
import json,time,math,argparse
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from uuid import uuid4
import httpx
CASES=[('policy_control','standard','central_bank',0),('policy_absorbed_loss','standard','central_bank',1000),('policy_fragile_loss','credit_crunch','central_bank',4000),('credit_payroll_gap','standard','credit',0),('credit_no_gap','standard','credit',0),('supplier_budget_too_small','supply_crunch','procurement',0),('supplier_normal_budget','supply_crunch','procurement',0)]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default='artifacts/agent-reliability.json');p.add_argument('--benchmark-id');a=p.parse_args();results=[];pending=[]
 with httpx.Client(base_url='http://127.0.0.1:8000',timeout=40,trust_env=False) as c:
  def call(path,body=None):
   r=c.get(path) if body is None else c.post(path,json=body);r.raise_for_status();return r.json()
  status=call('/api/agents/status')
  if not status['live_configured']:raise SystemExit('Live provider not configured')
  samples=call('/api/calibrations');sample=max(samples,key=lambda x:x['collected_at']) if samples else None
  for name,scenario,kind,loss in CASES:
   try:
    w=call('/api/worlds',{'scenario':scenario,'seed':42,**({'calibration_id':sample['calibration_id']} if sample else {}),**({'benchmark_id':a.benchmark_id} if a.benchmark_id else {})});base='/api/worlds/'+w['simulation_id']
    if loss:call(base+'/shocks',{'transaction_id':uuid4().hex,'bank_id':'bank_1','loss_bps':loss})
    if name=='credit_payroll_gap':
     cash=next(e for e in w['entities'] if e['id']=='business_1')['balance_sheet']['assets']['deposit']
     call(base+'/payments',{'transaction_id':uuid4().hex,'payer_id':'business_1','receiver_id':'business_2','amount_cents':cash})
    request={'request_id':'reliability-'+uuid4().hex,'mode':'live','agent_review':True}
    if kind=='central_bank':endpoint=base+'/agent-jobs';request.update(ticks=6,max_experiments=1,budget_cap_cents=100000)
    elif kind=='credit':endpoint=base+'/businesses/business_1/credit-jobs';request['auto_settle']=False;request['max_amount_cents']=max(1,next(e for e in w['entities'] if e['id']=='business_1').get('credit_limit_cents') or 500000)
    else:endpoint=base+'/businesses/business_1/procurement-jobs';request.update(auto_settle=False,quantity=20,max_total_cents=1 if name=='supplier_budget_too_small' else 100000)
    before=call(base);started=time.monotonic();job=call(endpoint,request)
    pending.append({'case':name,'job':job,'source':before,'started':started});print(json.dumps({'case':name,'queued':job['job_id']}),flush=True)
   except httpx.HTTPError as e:results.append({'case':name,'workflow_status':'submission_failed','error':type(e).__name__})
  deadline=time.monotonic()+480
  while pending and time.monotonic()<deadline:
   for item in pending[:]:
    job=call('/api/agent-jobs/'+item['job']['job_id'])
    if job['status'] not in ('completed','failed','cancelled'):continue
    report=call(job['report_url']) if job['report_url'] else {};after=call('/api/worlds/'+job['simulation_id']);audit=call('/api/worlds/'+job['simulation_id']+'/audit')
    row={'case':item['case'],'job_id':job['job_id'],'run_id':report.get('run_id'),'workflow_status':job['status'],'report_status':report.get('status'),'review_status':(report.get('supervision') or {}).get('status'),'elapsed_seconds_including_queue':round(time.monotonic()-item['started'],2),'source_financial_model':item['source'].get('financial_model'),'activity_count':len(report.get('activity',[])),'actors':sorted({x['actor'] for x in report.get('activity',[])}),'tool_calls':len(report.get('trace',[])),'tool_statuses':dict(Counter(t['status'] for t in report.get('trace',[]))),'source_unchanged':after==item['source'],'audit_balanced':audit['balanced'],'error':report.get('error') or job['error']}
    results.append(row);pending.remove(item);print(json.dumps(row),flush=True)
   if pending:time.sleep(1)
  for item in pending:results.append({'case':item['case'],'job_id':item['job']['job_id'],'workflow_status':'timed_out_in_evaluator'})
 values=sorted(r['elapsed_seconds_including_queue'] for r in results if 'elapsed_seconds_including_queue' in r)
 payload={'checked_at':datetime.now(timezone.utc).isoformat(),'provider':status['provider'],'model':status['model'],'calibration_id':sample['calibration_id'] if sample else None,'benchmark_id':a.benchmark_id,'case_definitions':[dict(case=n,scenario=s,kind=k,loss_bps=l) for n,s,k,l in CASES],'scope':f'{len(CASES)} predefined cases, one workflow attempt each; at most three transport attempts on explicit transient provider HTTP failures, no retries of financial tools or automatic settlement; supplier multi-call batches and malformed JSON may be rejected before execution for correction within the existing six-turn bound. Queue-inclusive latency from one local two-worker service, not a performance SLA or statistical reliability estimate.','counts':dict(Counter(r['workflow_status'] for r in results)),'review_counts':dict(Counter(r.get('review_status') or 'none' for r in results)),'latency_p50_seconds':values[math.ceil(len(values)*.5)-1] if values else None,'latency_p95_seconds':values[math.ceil(len(values)*.95)-1] if values else None,'results':results}
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in payload.items() if k!='results'}))
 return 0 if len(results)==len(CASES) and all(r.get('source_unchanged') and r.get('audit_balanced') and r['workflow_status']=='completed' for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
