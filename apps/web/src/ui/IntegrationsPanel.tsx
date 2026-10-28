import {useEffect,useState} from 'react';
import {api,postOnce} from '../data/api';
import {useStore} from '../state/store';
import ControlRoom from './ControlRoom';

type Status={fetch:{configured:boolean};crs:{configured:boolean};spacetime:{configured:boolean;database:string|null}};
type Observation={tool:string;source?:string;source_url?:string;population_estimate?:number;reference_period?:string;total_institutions?:number;scope?:string;error?:string;institutions?:{name:string;fdic_certificate:number}[]};
type Context={provider:string;status:string;interpretation:string;observations:Observation[]};
type Screen={report_id:string;entity_id:string;profile_id:string;provider:string;decision:string;explanation:string;source_tick:number};
type Sync={enabled:boolean;last_sequence:number;source_sequence:number;error:string|null};

// Fraud screening, SpacetimeDB and Fetch research are hidden, not removed; set true to restore them.
const SPONSOR_TOOLS=true;
export default function IntegrationsPanel(){
 const s=useStore(),id=s.world?.simulation_id;
 const [status,setStatus]=useState<Status|null>(null),[context,setContext]=useState<Context|null>(null);
 const [profiles,setProfiles]=useState<string[]>([]),[profile,setProfile]=useState('demo_identity_mismatch');
 const [receiver,setReceiver]=useState('business_2'),[payer,setPayer]=useState('business_1');
 const [screen,setScreen]=useState<Screen|null>(null),[sync,setSync]=useState<Sync|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const [services,setServices]=useState<{services:string[];reports:unknown}|null>(null);
 const customers=s.world?.entities.filter(e=>['business','household'].includes(e.kind))??[];
 useEffect(()=>{let current=true;setContext(null);setScreen(null);setSync(null);setNotice('');setError('');if(!id)return;
  void Promise.all([api<Status>('/api/integrations/status'),api<{profiles:{profile_id:string}[]}>('/api/fraud/profiles'),api<{reports:Context[]}>(`/api/worlds/${id}/data-context`),api<Screen[]>(`/api/worlds/${id}/fraud/screens`)]).then(([a,b,c,d])=>{
   if(current){setStatus(a);setProfiles(b.profiles.map(p=>p.profile_id));setContext(c.reports[0]??null);setScreen(d[0]??null);}
   if(!SPONSOR_TOOLS&&!c.reports[0])return api<Context>(`/api/worlds/${id}/data-context/sources`,{}).then(r=>{if(current)setContext(r);});
  }).catch(e=>{if(current)setError(String(e));});
  return()=>{current=false;};
 },[id]);
 useEffect(()=>{if(!id)return;let current=true;const refresh=()=>void api<Sync>(`/api/worlds/${id}/spacetime`).then(value=>{if(current)setSync(value);}).catch(()=>{});
  refresh();const timer=setInterval(refresh,3000);return()=>{current=false;clearInterval(timer);};
 },[id]);
 const run=async(operation:()=>Promise<void>)=>{if(busy||!id)return;setBusy(true);setError('');setNotice('');try{await operation();}catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}};
 if(!id)return null;
 const base=`/api/worlds/${id}`;
 const canPay=screen?.provider==='crs'&&screen.decision==='clear'&&screen.entity_id===receiver&&screen.source_tick===s.tick;
 return <details className="sponsor-integrations"><summary>{SPONSOR_TOOLS?'Data, fraud & shared events':'Data sources'}</summary>
  {SPONSOR_TOOLS?<><p className="muted">This world uses seeded synthetic households, businesses and banks. City statistics below are sourced reference data.</p>
  <div className="button-row"><button disabled={busy} onClick={()=>void run(async()=>setContext(await api<Context>(base+'/data-context/sources',{})))}>Load Census + FDIC data</button>
  <button disabled={busy||!status?.fetch.configured} onClick={()=>void run(async()=>setContext(await api<Context>(base+'/data-context/research',{})))}>Research with Fetch ASI:One</button></div></>
  :<><p className="muted">City statistics below are sourced reference data from FDIC BankFind and US Census Bureau county population estimates, Vintage 2024 (2024-07-01).</p><p className="data-loaded">Loaded from Census + FDIC data 2024</p></>}
  {context&&<div className="sponsor-context"><small>{context.provider} · {context.status}</small>{context.observations.map(o=><div key={o.tool}>
   <strong>{o.population_estimate!==undefined?`${o.population_estimate.toLocaleString()} residents (${o.reference_period})`:o.total_institutions!==undefined?`${o.total_institutions} headquartered institutions`:o.tool}</strong>
   {o.error?<p role="alert">{o.error}</p>:<><p>{o.scope}</p><a href={o.source_url} target="_blank" rel="noreferrer">{o.source}</a>{o.institutions?.map(b=><small key={b.fdic_certificate}>{b.name} · FDIC {b.fdic_certificate}</small>)}</>}
  </div>)}{SPONSOR_TOOLS&&<p>{context.interpretation}</p>}</div>}
  {SPONSOR_TOOLS&&<><h3>Identity fraud screening</h3><p className="muted">Screen a receiver before a $1 test payment. Live screening uses only the private sponsor test profiles. Demo screens cannot authorize payments.</p>
  <label>Receiver<select aria-label="Fraud receiver" value={receiver} onChange={e=>{setReceiver(e.target.value);setScreen(null);}}>{customers.map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label>
  <label>Test identity<select aria-label="Fraud profile" value={profile} onChange={e=>{setProfile(e.target.value);setScreen(null);}}><option value="demo_identity_mismatch">Local demo: identity mismatch</option><option value="demo_clear">Local demo: needs live verification</option>{profiles.map(p=><option key={p} value={p}>CRS sandbox: {p}</option>)}</select></label>
  <button disabled={busy||(profiles.includes(profile)&&!status?.crs.configured)} onClick={()=>void run(async()=>setScreen(await api<Screen>(base+'/fraud/screens',{entity_id:receiver,profile_id:profile,mode:profiles.includes(profile)?'live':'demo'})))}>Screen identity</button>
  {screen&&<p role="status"><b>{screen.decision.toUpperCase()} · {screen.provider}</b><br/>{screen.explanation}</p>}
  <label>Payer<select aria-label="Screened payment payer" value={payer} onChange={e=>setPayer(e.target.value)}>{customers.map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label>
  <button disabled={busy||!canPay||payer===receiver||s.playing} onClick={()=>void run(async()=>{await postOnce(base+'/fraud/payments',{fraud_report_id:screen!.report_id,payer_id:payer,receiver_id:receiver,amount_cents:100},'transaction_id');setNotice('Screened $1 payment settled.');await s.refresh();})}>Confirm screened $1 payment</button>
  <h3>Economic service agents</h3><p>Ten typed Fetch service roles use saved-state tools. The existing live Nemotron workflows remain separate; these service audits move no money.</p>
  <button disabled={busy} onClick={()=>void run(async()=>setServices(await api(base+'/economic-services')))}>Inspect economic services</button>
  {services&&<><p>{services.services.join(' · ')}</p><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify(services.reports,null,2)}</pre></>}
  <ControlRoom/>
  <h3>SpacetimeDB shared feed</h3><p className="muted">Mirrors committed financial events into a shared database.</p>
  <button disabled={busy||!status?.spacetime.configured} onClick={()=>void run(async()=>setSync(await api<Sync>(base+'/spacetime/enable',{})))}>Enable shared event feed</button>
  <p>{sync?.enabled?`${sync.last_sequence} / ${sync.source_sequence} events delivered`:'Feed not enabled'}{status?.spacetime.database?` · ${status.spacetime.database}`:''}</p>
  {sync?.error&&<p role="alert">{sync.error}</p>}{notice&&<p role="status">{notice}</p>}{error&&<p role="alert" className="request-error">{error}</p>}
  <p className="muted">Fetch chat commands: <code>data {id}</code> or <code>stress {id}</code>. Agentverse registration is a separate setup step.</p></>}
  {!SPONSOR_TOOLS&&error&&<p role="alert" className="request-error">{error}</p>}
 </details>;
}
