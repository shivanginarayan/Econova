import {useEffect,useState} from 'react';
import {Play,Pause,Plus,RotateCcw,GitFork,GitBranch,ArrowLeft,ArrowRight,ArrowUpRight,ArrowDownRight,ChevronRight,Building2,Landmark,Users,MapPin,Globe2,Sparkles,AlertTriangle,Check,X,Network as NetworkIcon} from 'lucide-react';
import {useStore} from '../state/store';
import {api,currency} from '../data/api';
import type {Metrics,Entity,Report,Exposure,Fork,ComparisonEvidence,EconomyEvent} from '../data/api';
import {comparisonReport,downloadComparison} from '../data/comparisonReport';
import PublicDataPanel from './PublicDataPanel';
import ShockStory from './ShockStory';
import IntegrationsPanel from './IntegrationsPanel';
import {useCityView} from '../state/cityView';
import {districtEntityIds,MOCK_PREFIX,mockProfile} from '../data/liveCity';
import {WorldDataOptions,CreditSafeguards} from './TrackControls';

export const strategyName:Record<string,string> = {no_intervention:'No intervention',bank_lending:'Emergency bank lending',household_cash:'Direct household support'};
const activeJob = (status?:string) => status === 'queued' || status === 'running';

export function TopControls(){const s=useStore();return <div className="top-controls">
 <div className="control-group"><button disabled={s.busy} onClick={s.createWorld}><Plus size={14}/>Create World</button>
 <button disabled={s.busy} onClick={s.togglePlay}>{s.playing?<Pause size={14}/>:<Play size={14}/>} {s.playing?'Pause':'Play'}</button>
 <select aria-label="Playback speed" disabled={s.busy} value={s.speed} onChange={e=>void s.changeSpeed(+e.target.value)}>{[1,2,4].map(n=><option key={n} value={n}>{n}×</option>)}</select>
 <button disabled={s.busy} title="Preserve history and reset into a new world" aria-label="Reset world" onClick={s.reset}><RotateCcw size={14}/></button></div>
 <div className="control-group"><span className="month-label">DAY <b>{String(s.tick).padStart(2,'0')}</b></span>
 <div className="segmented view-toggle"><button className={s.mode==='city'?'active':''} onClick={()=>s.set({mode:'city',compare:false})}><Building2 size={12}/>City</button><button className={s.mode==='network'?'active':''} onClick={()=>s.set({mode:'network',compare:false})}><NetworkIcon size={12}/>Network</button></div>
 <button disabled={s.busy} className="fork-button" onClick={()=>void s.compareFutures()}><GitFork size={14}/>Fork Reality</button></div></div>;}

const unemployment=(m:Metrics)=>(1-m.employment_rate)*100;
export function KpiStrip(){const s=useStore(),m=s.world?.metrics;if(!m)return null;
 const rows=[['Unemployment',`${unemployment(m).toFixed(1)}%`],['Household Cash',currency(m.household_cash_cents)],
 ['Business Defaults',m.business_defaults],['Bank Stress',`${m.stressed_banks} / ${m.banks} banks`],['Public Intervention Cost',currency(m.public_support_disbursed_cents)]];
 return <div className="kpi-strip">{rows.map(([label,value])=><div className="kpi" key={label}><span>{label}</span><strong>{value}</strong><small>Backend state · Day {s.tick}</small></div>)}</div>;}

// Original bottom bar: play/pause, speed, a day slider over the horizon, and the scenario picker slot.
// Dragging forward steps the backend to that day; the simulation cannot rewind, so earlier days are not selectable.
export function Timeline(){const s=useStore(),horizon=Math.max(30,Math.ceil(s.tick/30)*30),pct=Math.min(1,s.tick/horizon);
 const stepTo=(day:number)=>{if(!s.world||s.busy||day<=s.tick)return;void (async()=>{try{await s.pause();await api(`/api/worlds/${s.world!.simulation_id}/step`,{ticks:day-s.tick});await s.refresh();}catch(e){s.set({error:e instanceof Error?e.message:'Step failed'});}})();};
 return <div className="timeline"><button disabled={s.busy} aria-label={s.playing?'Pause timeline':'Play timeline'} onClick={s.togglePlay}>{s.playing?<Pause size={16}/>:<Play size={16}/>}</button>
 <select aria-label="Timeline speed" disabled={s.busy} value={s.speed} onChange={e=>void s.changeSpeed(+e.target.value)}>{[1,2,4].map(n=><option key={n} value={n}>{n}×</option>)}</select>
 <div className="timeline-track" style={{'--pct':pct} as React.CSSProperties}><div className="timeline-day"><span className={pct<.08?'at-start':pct>.92?'at-end':''}>DAY {s.tick}</span></div><input aria-label="Simulation day" type="range" min="0" max={horizon} value={s.tick} disabled={!s.world||s.busy} onChange={e=>stepTo(+e.target.value)}/><div className="timeline-ticks"><span>0</span><span>{horizon} DAY HORIZON</span><span>{horizon}</span></div></div>
 <div className="branch-picker"><GitBranch size={13}/><select aria-label="Simulation scenario" value="current" onChange={e=>{if(e.target.value==='fork')void s.compareFutures();}}><option value="current">{scenarioLabel[s.world?.config.scenario??'']??'Live world'}</option><option value="fork">Fork Reality · compare futures</option></select></div></div>;}
function Crisis(){const s=useStore(),banks=s.world?.entities.filter(e=>e.kind==='bank')??[];
 const [bank,setBank]=useState('bank_1'),[loss,setLoss]=useState(40),[open,setOpen]=useState(false);
 const struck=s.world?.entities.find(e=>e.kind==='bank'&&e.status!=='active');
 return <section className="crisis-section"><button className="crisis-heading" onClick={()=>setOpen(!open)}><AlertTriangle size={16}/><span>{s.crisis?'Crisis active':'Trigger Crisis'}<small>{s.crisis?`${struck?.name??'Bank'} → lending → businesses → households`:'Introduce a shock. Watch the consequences.'}</small></span><span>{open?'−':'+'}</span></button>
 {open&&<div className="crisis-form fade-in"><label>Institution<select aria-label="Shock bank" value={bank} onChange={e=>setBank(e.target.value)}>{banks.map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label>
 <label>Asset category<select aria-label="Asset category" value="risky_assets" onChange={()=>{}}><option value="risky_assets">Risky assets</option></select></label><label>Asset loss <b>{loss}%</b><input aria-label="Asset loss" type="range" min="5" max="100" step="5" value={loss} onChange={e=>setLoss(+e.target.value)}/></label>
 <button disabled={s.busy} className="crisis-trigger" onClick={()=>{void s.shock(bank,loss);setOpen(false);}}>Apply bank shock <ArrowRight size={14}/></button><p className="muted">Pauses before settlement. Advance days to observe actual consequences.</p></div>}</section>;}
export function AgentProgress(){const s=useStore(),report=s.report,job=s.job;const [applied,setApplied]=useState('');
 const [reason,setReason]=useState(''),[deciding,setDeciding]=useState(false),[approvalError,setApprovalError]=useState('');
 useEffect(()=>setApplied(''),[report?.run_id]);
 if(!job)return null;
 const canApply=report&&(job.kind==='central_bank'?report.status==='completed':job.kind==='credit'?report.status==='approved'&&report.business_accepted:report.status==='ready');
 if(MINIMAL){const title=job.kind==='central_bank'?'Policy assistant':job.kind==='credit'?'Payroll credit':'Supplier contract';
  const outcome=report?.supervision?.status==='running'?'Supervisor reviewing':report?.supervision?.status==='blocked'||report?.supervision?.status==='failed'?'Held by supervisor':report?.status==='needs_human_approval'?'Needs your review':report?(report.error?'Failed':report.status.replaceAll('_',' ')):job.status;
  const result=report?.recommendation?`${strategyName[report.recommendation.strategy]??report.recommendation.strategy} · ${currency(report.recommendation.amount_cents)}`
   :report?.decision?`${report.status==='needs_human_approval'?'Proposed':report.decision.approved?'Approved':'Declined'} credit · ${currency(report.decision.amount_cents)}`
   :report?.selected_offer?`Selected offer · ${currency(report.selected_offer.total_cents)}`:'';
  const dismiss=()=>s.set({job:null,report:null});
  const source=report?.provider??[...new Set(Object.values(report?.providers??{}))].join(', '),model=report?.model??[...new Set(Object.values(report?.models??{}))].join(', ');
  const why=report?.recommendation?.rationale??report?.decision?.rationale??'';
  return <section className="result-card fade-in" aria-label="Agent job progress"><p className="result-status">{title} · {outcome.charAt(0).toUpperCase()+outcome.slice(1)}</p>
  {result&&<p className="result-value">{result}</p>}
  {SHOW_AGENT_SOURCE&&(source||model)&&<small className="result-source">via {source||s.agentMode}{model?` · ${model}`:''}</small>}
  {(job.error||report?.error)&&<p role="alert" className="request-error">{job.error||report?.error}</p>}
  {why&&<div className="agent-explanation"><b>Agent explanation</b><p>{why}</p></div>}
  {report?.risk_evidence&&<p>CRS sandbox score: {report.risk_evidence.score??'unavailable'} · Risk: {report.risk_evidence.risk_decision}</p>}
  {report?.selected_offer&&<p>Supplier terms: {currency(report.selected_offer.down_payment_cents)} upfront · full invoice {currency(report.selected_offer.total_cents)} · remainder due in {report.selected_offer.due_in_ticks} days.</p>}
  {report&&(why||report.trace.length>0)&&<details className="result-why"><summary>Why · {report.trace.length} tool steps</summary>{why&&<p>{why}</p>}
   {report.risk_evidence&&<p>CRS sandbox score: {report.risk_evidence.score??'unavailable'} · {report.risk_evidence.risk_decision}</p>}
   {report.trace.map(t=><div className="live-trace" key={t.sequence}><b>{t.sequence}. {t.role??'central bank'} · {t.tool} · {t.status}</b><pre>{JSON.stringify(t.result,null,2)}</pre></div>)}</details>}
  {report?.status==='needs_human_approval'&&<><h3>Human approval required</h3>{report.approval_reasons?.map(reason=><p key={reason}>{reason}</p>)}<p>Approval records your decision. Settlement separately issues the loan.</p><input aria-label="Credit approval rationale" placeholder="Review rationale" value={reason} maxLength={2000} onChange={e=>setReason(e.target.value)}/>
   <div className="button-row">{(['approve','decline'] as const).map(decision=><button key={decision} className={decision==='approve'?'primary small':'quiet'} disabled={deciding||!reason.trim()||!!(report?.request?.agent_review&&report.supervision?.status!=='passed')} onClick={async()=>{setDeciding(true);setApprovalError('');try{await api(`/api/credit-runs/${report.run_id}/approval`,{decision,rationale:reason.trim()});await s.refresh();}catch(e){setApprovalError(String(e));}finally{setDeciding(false);}}}>{decision==='approve'?'Approve':'Decline'}</button>)}</div>{approvalError&&<p role="alert">{approvalError}</p>}</>}
  {job.status==='queued'&&<button className="quiet" onClick={s.cancelJob}>Cancel</button>}
  {applied===report?.run_id?<p className="success-line"><Check size={15}/> {job.kind==='central_bank'?'Policy accepted':'Settled'}</p>
   :canApply&&(job.kind==='central_bank'?<div className="button-row"><button className="primary small" disabled={s.busy||!!(report?.request?.agent_review&&report.supervision?.status!=='passed')} onClick={async()=>{await s.settleReport();if(!useStore.getState().error)setApplied(report!.run_id);}}>Apply recommendation <Check size={14}/></button><button className="quiet" disabled={s.busy||!!(report?.request?.agent_review&&report.supervision?.status!=='passed')} onClick={dismiss}>Dismiss recommendation</button></div>
   :<button className="primary small" disabled={s.busy||!!(report?.request?.agent_review&&report.supervision?.status!=='passed')} onClick={async()=>{await s.settleReport();if(!useStore.getState().error)setApplied(report!.run_id);}}>Confirm settlement</button>)}
  </section>;}
 const source=report?.provider??[...new Set(Object.values(report?.providers??{}))].join(', ');
 return <section className="agent-section" aria-label="Agent job progress"><div className="section-heading"><span>{job.kind.replaceAll('_',' ')} · {job.status}</span><span className="badge">{source||s.agentMode}</span></div>
 <small>Report: {report?.status??'waiting for worker'} · observation day {report?.source_tick??'pending'}</small>
 <p className="muted">{report?.model??[...new Set(Object.values(report?.models??{}))].join(', ')}</p>
 {job.status==='queued'&&<button className="text-action" onClick={s.cancelJob}>Cancel queued job</button>}
 {(job.error||report?.error)&&<p role="alert" className="request-error">{job.error||report?.error}</p>}
 {report?.recommendation&&<div className="proposal"><h3>{strategyName[report.recommendation.strategy]}</h3><p>{report.recommendation.rationale}</p><b>{currency(report.recommendation.amount_cents)} gross support</b></div>}
 {report?.decision&&<p>{report.decision.rationale} · {currency(report.decision.amount_cents)}</p>}
 {report?.risk_evidence&&<p>CRS sandbox score: {report.risk_evidence.score??'unavailable'} · Risk: {report.risk_evidence.risk_decision} · {report.risk_evidence.cached?'cached evidence':'live pull'}</p>}
 {report?.status==='needs_human_approval'&&<div className="sponsor-integrations" role="status"><h3>Human approval required</h3>{report.approval_reasons?.map(r=><p key={r}>{r}</p>)}
 <label>Review rationale<input aria-label="Credit approval rationale" value={reason} maxLength={2000} onChange={e=>setReason(e.target.value)}/></label>
 {(['approve','decline'] as const).map(decision=><button key={decision} disabled={deciding||!reason.trim()||!!(report?.request?.agent_review&&report.supervision?.status!=='passed')} onClick={async()=>{setDeciding(true);setApprovalError('');try{await api(`/api/credit-runs/${report.run_id}/approval`,{decision,rationale:reason.trim()});await s.refresh();}catch(e){setApprovalError(String(e));}finally{setDeciding(false);}}}>{decision==='approve'?'Approve reviewed offer':'Decline reviewed offer'}</button>)}<p>Approval records your decision. Settlement remains a separate confirmation.</p>{approvalError&&<p role="alert">{approvalError}</p>}</div>}
 {report?.human_approval&&<p>Human decision: {report.human_approval.decision} · {report.human_approval.rationale}</p>}
 {report?.offers?.map(offer=><div className="detail-row" key={offer.offer_id}><span>{offer.supplier_id}{offer.offer_id===report.selected_offer?.offer_id?' · SELECTED':''}<small>{offer.quantity} units · due in {offer.due_in_ticks} days</small></span><strong>{currency(offer.total_cents)}<small>{currency(offer.down_payment_cents)} upfront</small></strong></div>)}
 {canApply&&applied!==report!.run_id&&<button className="primary small" disabled={s.busy||!!(report?.request?.agent_review&&report.supervision?.status!=='passed')} onClick={async()=>{await s.settleReport();if(!useStore.getState().error)setApplied(report!.run_id);}}>{job.kind==='central_bank'?'Apply recommendation':job.kind==='credit'?'Settle accepted credit':'Confirm contract and down payment'}</button>}
 {applied===report?.run_id&&<p className="success-line">Settlement confirmed</p>}
 <details className="agent-observations" open={activeJob(job.status)}><summary>Public tool trace ({report?.trace.length??0})</summary>{report?.trace.map(t=><div className="live-trace" key={t.sequence}><b>{t.sequence}. {t.role??'central bank'} · {t.tool} · {t.status}</b>{t.tool==='buy_market_forecast'&&t.status==='accepted'&&typeof (t.result as {transaction_hash?:unknown})?.transaction_hash==='string'&&/^0x[0-9a-fA-F]{64}$/.test((t.result as {transaction_hash:string}).transaction_hash)&&<a target="_blank" rel="noreferrer" href={'https://sepolia.basescan.org/tx/'+(t.result as {transaction_hash:string}).transaction_hash}>View Base Sepolia payment receipt</a>}<pre>{JSON.stringify(t.result,null,2)}</pre></div>)}</details>
 </section>;}

const NEGATIVE=/default|loss|lost|rejected|writeoff|status_changed/,POSITIVE=/issued|repayment|settled|cleared|refinanced|paid|created|produced/;
const MACRO=/world_created|bank_|interbank|public_intervention|agent_|tick_completed/;
function eventText(type:string){const t=type.replaceAll('_',' ');return t.charAt(0).toUpperCase()+t.slice(1);}
// Original ripple-effect feed: macro/micro filter, direction arrows and a link to the actor, fed by live backend events.
function EventFeed(){const s=useStore(),{districtFilter,setDistrict}=useCityView(),ids=districtFilter?districtEntityIds(districtFilter):null;
 const events=[...s.events].reverse().filter(e=>!ids||ids.has(e.agent_id??'')||ids.has(e.counterparty_id??'')).slice(0,25);
 return <section className="feed"><div className="section-heading"><span>THE RIPPLE EFFECT</span><span className="live-label">{s.connection}</span></div>
 {districtFilter&&<div className="district-feed-filter"><span>Showing {districtFilter} · visual grouping</span><button onClick={()=>setDistrict(null)}>Show whole-city events ×</button></div>}
 <div className="feed-items">{districtFilter&&!events.length&&<p>No recorded events for this visual district.</p>}{events.map(e=><button className="feed-item" key={e.sequence} onClick={()=>s.set({selected:e.agent_id??e.counterparty_id})}>
 <span><span className="feed-meta">DAY {e.simulation_tick} · #{e.sequence}</span><span className="feed-text">{eventText(e.event_type)}{e.amount_cents!==null?` · ${currency(e.amount_cents)}`:''}</span>
 <small>{e.agent_id}{e.counterparty_id?` → ${e.counterparty_id}`:''}</small>{typeof e.details.reason==='string'&&<small>{e.details.reason}</small>}</span></button>)}</div></section>;}

function MockInspector({m}:{m:NonNullable<ReturnType<typeof mockProfile>>}){const s=useStore();const Icon=m.role==='Household'?Users:m.role==='Public landmark'?Landmark:Building2;
 return <div className="inspector fade-in"><div className="inspector-top"><button className="text-action" onClick={()=>s.set({selected:null})}><ArrowLeft size={14}/> Back to live events</button><button className="icon-button" aria-label="Close inspector" onClick={()=>s.set({selected:null})}><X size={16}/></button></div>
 <div className="actor-icon"><Icon size={25}/></div><p className="eyebrow">{m.role} · DAY {s.tick}</p><h2>{m.name}</h2><p className="muted">{m.district}</p><span className={'status-chip '+(s.crisis?'distress':'')}>{s.crisis?'▼ Feeling the credit squeeze':'● Operating · healthy city'}</span>
 <div className="balance-grid">{[['Cash',m.cash],['Assets',m.assets],['Debt',m.debt]].map(([k,v])=><div key={k}><span>{k}</span><strong>{currency(+v)}</strong></div>)}</div>
 {m.employees>0&&<p>{m.employees} people work here.</p>}<p className="representative-note">Illustrative figures. This building is scenery and isn't linked to a backend institution, so nothing here is on the simulated ledger.</p>
 <div className="section-heading"><span>LINKED INSTITUTIONS</span></div>{s.world?.entities.filter(e=>e.kind==='bank').slice(0,2).map(e=><button className="relationship" key={e.id} onClick={()=>s.set({selected:e.id})}>{e.name} →</button>)}</div>;}
function Inspector(){const s=useStore(),entity=s.world?.entities.find(e=>e.id===s.selected);
 const [transactions,setTransactions]=useState<{transaction_id:string;metadata:{type?:string;tick?:number}}[]>([]);
 useEffect(()=>{let current=true;setTransactions([]);if(!s.world||!entity)return;const id=s.world.simulation_id;
  void api<{transactions:{transaction_id:string;metadata:{type?:string;tick?:number};lines:{account_id:string}[]}[]}>(`/api/worlds/${id}/transactions?entity_id=${encodeURIComponent(entity.id)}&newest_first=true&limit=12`).then(page=>{
   if(current)setTransactions(page.transactions);
  }).catch(()=>{});return()=>{current=false;};},[s.world?.simulation_id,s.tick,entity?.id]);
 if(!entity){const m=s.selected?.startsWith(MOCK_PREFIX)?mockProfile(s.selected):null;if(m)return <MockInspector m={m}/>;}
 if(!entity)return <button className="text-action" onClick={()=>s.set({selected:null})}>Return to events</button>;
 const related=s.contracts.filter(c=>c.buyer_id===entity.id||c.supplier_id===entity.id);
 const sheet=entity.balance_sheet;
 return <div className="inspector"><button className="text-action" onClick={()=>s.set({selected:null})}><ArrowLeft size={14}/> Back to live events</button>
 <p className="eyebrow">{entity.kind} · DAY {s.tick}</p><h2>{entity.name}</h2><code>{entity.id}</code><p className="status-chip">{entity.status}</p>
 <div className="balance-grid">{[['Cash',sheet.assets.deposit??sheet.assets.reserves??0],['Assets',sheet.assets_cents],['Debt',sheet.liabilities_cents]].map(([name,value])=><div key={name}><span>{name}</span><strong>{currency(+value)}</strong></div>)}</div>
 <p>Equity {currency(sheet.equity_cents)} · Ledger {sheet.balanced?'balanced':'unbalanced'}</p>
 {entity.kind==='bank'&&<p>Capital {((entity.capital_ratio??0)*100).toFixed(1)}% · Liquidity {((entity.liquidity_ratio??0)*100).toFixed(1)}% · Lending {entity.lending_available?'available':'constrained'}</p>}
 {entity.kind==='business'&&<><div className="detail-row"><span>Raw materials / finished goods</span><b>{entity.materials_units??'untracked'} / {entity.goods_units??'untracked'}</b></div><p>{entity.employees?.length??0} employees · Produced {entity.last_produced_units??'untracked'} goods today</p>
 <div className="button-row"><button className="primary small" disabled={s.busy||activeJob(s.job?.status)||entity.status!=='active'} onClick={()=>void s.startJob('credit',entity.id)}>Review payroll credit</button>
 <button className="quiet" disabled={s.busy||activeJob(s.job?.status)||entity.status!=='active'} onClick={()=>void s.startJob('procurement',entity.id)}>Negotiate supplies</button></div><CreditSafeguards key={entity.id} businessId={entity.id}/><p className="muted">Supplies: 20 units · maximum full invoice $1,000. Preview first, then confirm settlement.</p></>}
 <div className="section-heading"><span>CONNECTED INSTITUTIONS</span></div>{[entity.bank_id,entity.employer_id,...(entity.employees??[])].filter(Boolean).map(id=><button className="relationship" key={id} onClick={()=>s.set({selected:id!})}>{s.world?.entities.find(e=>e.id===id)?.name??id} →</button>)}
 <div className="section-heading"><span>SUPPLIER OBLIGATIONS</span></div>{related.length?related.map(c=><div className="detail-row" key={c.contract_id}><span>{c.status}<small>{c.buyer_id} → {c.supplier_id} · due day {c.due_tick}</small></span><b>{currency(c.outstanding_cents)}</b></div>):<p className="muted">No supplier contracts.</p>}
 {(s.report?.business_id===entity.id||s.report?.buyer_id===entity.id)&&<AgentProgress/>}
 <div className="section-heading"><span>RECENT LEDGER ENTRIES</span></div>{transactions.map(t=><div className="detail-row" key={t.transaction_id}><span>{t.metadata.type}<small>Day {t.metadata.tick} · {t.transaction_id}</small></span></div>)}
 </div>;}

const scenarioLabel:Record<string,string>={credit_crunch:'Credit crunch',standard:'Standard economy',supply_crunch:'Supply crunch'};
const scenarioQuestion:Record<string,string>={credit_crunch:'What happens when a bank takes heavy losses and credit tightens across the simulated economy?',standard:'How does a healthy, well-capitalized simulated economy evolve day by day?',supply_crunch:'What happens when supplier shortages squeeze inventories across the simulated economy?'};
const scenarioChoices:Array<[string,string]>=[['credit_crunch','Banks take a credit hit'],['standard','A healthy, well-capitalized city'],['supply_crunch','Suppliers run short']];
// Minimal side panel: sections gated by !MINIMAL are hidden, not removed; flip to false to restore them.
const MINIMAL=true,SHOW_SOURCE_LINE=false,SHOW_AGENT_SOURCE=true;
function CityHeading(){return <><div className="city-heading">{!MINIMAL&&<MapPin size={24} strokeWidth={1.6}/>}<div><h1>Simulated economy</h1><p>Synthetic banks, businesses and households{!MINIMAL&&<> <span>·</span> Model population</>}</p></div></div>{!MINIMAL&&<div className="city-profile"><span>Coastal economy</span><span>Technology & services</span></div>}</>;}
// Original policy assistant card; the button starts the backend central-bank agent job.
function PolicyAssistant({paid,setPaid}:{paid:boolean;setPaid:(v:boolean)=>void}){const s=useStore();const running=activeJob(s.job?.status);
 if(MINIMAL)return <>{running?<div className="thinking"><span className="pulse-dot"/>Testing rescue policies against the live economy…{s.job?.status==='queued'&&<button aria-label="Cancel proposal" onClick={s.cancelJob}><X size={14}/></button>}</div>
  :<button className="panel-action" disabled={s.busy} onClick={()=>void s.startJob('central_bank',undefined,paid?{allow_paid_research:true}:{})}><Sparkles size={15}/> Test a rescue policy</button>}
  <button className="panel-action" disabled={s.busy||!s.world} onClick={()=>void s.compareFutures()}><GitBranch size={15}/> Fork Reality</button>
  <AgentProgress/></>;
 return <section className="agent-section"><div className="section-heading"><span><Sparkles size={14}/> POLICY ASSISTANT</span><span className="badge">{s.agentMode==='live'?'Nemotron':'Demo agent'}</span></div>
 {running?<div className="thinking"><span className="pulse-dot"/>Testing rescue policies against the live economy…{s.job?.status==='queued'&&<button aria-label="Cancel proposal" onClick={s.cancelJob}><X size={14}/></button>}</div>:<><p className="muted">{s.crisis?'A credit shock is rippling through the city. Explore a way forward.':'Let the city run, introduce a shock, then explore a policy response.'}</p>
 <button className="text-action" disabled={s.busy} onClick={()=>void s.startJob('central_bank',undefined,paid?{allow_paid_research:true}:{})}><Sparkles size={14}/> Test a rescue policy <span>↗</span></button></>}
 <AgentProgress/>
 <details className="demo-state"><summary>Provider state preview</summary><select aria-label="Agent mode" disabled={running} value={s.agentMode} onChange={e=>s.set({agentMode:e.target.value as 'demo'|'live'})}><option value="demo">Deterministic demo · no AI inference</option><option value="live" disabled={!s.providerStatus?.live_configured}>Live Nemotron via Nebius</option></select>
 <p className="muted">{s.providerStatus?.live_configured?`Configured model: ${s.providerStatus.model}`:'Live mode needs backend NEBIUS_API_KEY and NEBIUS_MODEL.'} Tests two budgets over 12 days, maximum gross support $10,000.</p>
 <label className="muted"><input aria-label="Allow paid testnet research" type="checkbox" checked={paid} disabled={s.agentMode!=='live'||running} onChange={e=>setPaid(e.target.checked)}/> Allow one paid research purchase, up to 0.01 Base Sepolia test USDC.</label>
 {s.world?.calibration&&<p className="muted">Apify inputs: {s.world.calibration.calibration_id} · {s.world.calibration.collected_at}</p>}</details></section>;}
// Data provenance and agent settings, collapsed by default to keep the panel uncluttered.
function SourcesPanel({paid,setPaid}:{paid:boolean;setPaid:(v:boolean)=>void}){const s=useStore(),running=activeJob(s.job?.status),c=s.world?.calibration;
 // Only switch jobs to live once Nebius is configured, so the rescue policy keeps working without keys.
 useEffect(()=>{if(s.providerStatus?.live_configured&&s.agentMode!=='live')s.set({agentMode:'live'});},[s.providerStatus?.live_configured]);
 return <details className="panel-sources"><summary>Sources & agents</summary>
 {c&&<p className="muted">Prices and wages calibrated from {c.provider} ({c.calibration_id}, {c.collected_at.slice(0,10)}).</p>}
 <label>Policy agent<select aria-label="Agent mode" disabled={running} value={s.agentMode} onChange={e=>s.set({agentMode:e.target.value as 'demo'|'live'})}><option value="demo">Deterministic demo</option><option value="live" disabled={!s.providerStatus?.live_configured}>Live Nemotron via Nebius</option></select></label>
 <p className="muted">{s.providerStatus?.live_configured?`Configured model: ${s.providerStatus.model}.`:'Live mode needs backend NEBIUS_API_KEY and NEBIUS_MODEL.'} Credit and supplier agents run from a business's inspector.</p>
 {!MINIMAL&&<label className="muted"><input aria-label="Allow paid testnet research" type="checkbox" checked={paid} disabled={s.agentMode!=='live'||running} onChange={e=>setPaid(e.target.checked)}/> Allow one paid research purchase (≤0.01 test USDC)</label>}
 <PublicDataPanel/><ShockStory/><IntegrationsPanel key={s.world?.simulation_id}/><details className="institution-list"><summary>Inspect institutions ({s.world?.entities.length})</summary>{s.world?.entities.map(e=><button className="relationship" key={e.id} onClick={()=>s.set({selected:e.id})}>{e.name}<small>{e.kind} · {e.status}</small></button>)}</details></details>;}
export default function LivePanel(){const s=useStore(),city=s.stage==='CITY';const [paid,setPaid]=useState(false),[follow,setFollow]=useState(''),[followNotice,setFollowNotice]=useState('');useEffect(()=>setPaid(false),[s.world?.simulation_id]);
 const scenario=s.world?.config.scenario??s.selectedScenario;
 return <aside className="side-panel"><div className="panel-scroll">{city&&s.selected?<Inspector/>:<>
 <div className="panel-topline"><span className="eyebrow">{city?'RUNNING SCENARIO':'YOUR NEXT WHAT IF'}</span>{city?<span className="badge">LIVE BACKEND</span>:<button className="icon-button" aria-label="Close scenario panel" onClick={()=>s.set({stage:'COUNTRY'})}><X size={16}/></button>}</div><CityHeading/>
 {city?<><div className="pinned-prompt"><span className="eyebrow">THE QUESTION</span><p>{scenarioQuestion[scenario]??'How does this economy respond?'}</p></div>
 <div className="scenario-chips"><span>{scenarioLabel[scenario]??scenario}</span>{!MINIMAL&&<><span>Seed {s.world?.config.seed}</span><span>Day {s.tick}</span></>}</div>
 {SHOW_SOURCE_LINE&&<p className="data-source">{s.world?.calibration?`Synthetic ledger calibrated with ${s.world.calibration.provider} data · ${s.world.calibration.collected_at.slice(0,10)}`:'Synthetic households, firms & banks · double-entry ledger'} · Agent: {s.agentMode==='live'?'Nemotron via Nebius':'deterministic demo'}</p>}
 {MINIMAL?<><div className="panel-actions"><Crisis/><PolicyAssistant paid={paid} setPaid={setPaid}/></div><SourcesPanel paid={paid} setPaid={setPaid}/></>:<>
 <form className="followup" onSubmit={e=>{e.preventDefault();if(!follow.trim())return;setFollowNotice('Free-text follow-ups are not supported by the backend yet. Use Trigger Crisis, Test a rescue policy or Fork Reality to change this world.');setFollow('');}}><input aria-label="Follow-up question" placeholder="Ask a follow-up question…" value={follow} onChange={e=>setFollow(e.target.value)}/><button aria-label="Submit follow-up"><ArrowUpRight size={16}/></button></form>{followNotice&&<p className="muted">{followNotice}</p>}
 <PolicyAssistant paid={paid} setPaid={setPaid}/><Crisis/>
 <IntegrationsPanel key={s.world?.simulation_id}/><details className="institution-list"><summary>Inspect institutions ({s.world?.entities.length})</summary>{s.world?.entities.map(e=><button className="relationship" key={e.id} onClick={()=>s.set({selected:e.id})}>{e.name}<small>{e.kind} · {e.status}</small></button>)}</details></>}<EventFeed/></>
 :<><p className="panel-intro">One city. Thousands of connected decisions.<br/>Change something. See what follows.</p>
 <div className="pinned-prompt"><span className="eyebrow">THE QUESTION</span><p>{scenarioQuestion[s.selectedScenario]}</p></div>
 <div className="examples"><div className="section-heading"><span>A FEW PLACES TO START</span></div>{scenarioChoices.map(([id,label])=><button key={id} className={s.selectedScenario===id?'active':''} aria-pressed={s.selectedScenario===id} onClick={()=>s.set({selectedScenario:id})}><span>{label}</span>{s.selectedScenario===id?<Check size={14}/>:<ArrowUpRight size={14}/>}</button>)}</div>
 <WorldDataOptions/><PublicDataPanel/><button disabled={s.busy} className="primary" onClick={s.createWorld}>{s.busy?'Creating world…':'Create and explore economy'} <ArrowRight size={18}/></button>
 {!MINIMAL&&<p className="muted">Seed 42 · 40 households · 8 businesses · 5 banks. Supported experiments: bank asset losses and supplier shortages.</p>}
 <div className="connections"><Globe2 size={18}/><p>Follow the connections.<span>Households, businesses, banks and government. One shared economy.</span></p></div></>}
 </>}</div><div className="panel-footer"><span className="tiny-dot"/> {s.busy?'Working…':'Stylized simulation — not a forecast of a real city.'}</div></aside>;}
// Original exposure network: banks on an inner ring, firms outside, public institutions at the centre.
export function NetworkView(){const s=useStore(),[edge,setEdge]=useState<number|null>(null);
 const entities=s.world?.entities.filter(e=>e.kind!=='household')??[],banks=entities.filter(e=>e.kind==='bank'),firms=entities.filter(e=>e.kind==='business'),publics=entities.filter(e=>e.kind!=='bank'&&e.kind!=='business');
 const ring=(list:typeof entities,rx:number,ry:number,offset:number)=>list.map((e,i)=>({...e,x:450+Math.cos(offset+i/list.length*Math.PI*2)*rx,y:330+Math.sin(offset+i/list.length*Math.PI*2)*ry}));
 const nodes=[...ring(publics,publics.length>1?70:0,publics.length>1?50:0,0),...ring(banks,175,130,-Math.PI/2),...ring(firms,360,255,-Math.PI/2+.4)];
 // Live exposures first, then standing relationships from backend entities (a firm's bank account, supplier contracts,
 // central-bank reserve accounts), so the network stays readable after loans mature. Relationship lines carry no amount.
 const has=(x:string)=>nodes.some(n=>n.id===x),pair=new Set<string>(),edges:Exposure[]=[];const push=(e:Exposure)=>{const k=[e.borrower_id,e.lender_id].sort().join('|');if(!has(e.borrower_id)||!has(e.lender_id)||pair.has(k))return;pair.add(k);edges.push(e);};
 for(const e of s.network?.exposures??[])push(e);
 for(const c of s.contracts)if(c.status!=='settled')push({kind:'supplier_contract',borrower_id:c.buyer_id,lender_id:c.supplier_id,amount_cents:c.outstanding_cents,due_tick:c.due_tick});
 for(const f of firms)if(f.bank_id)push({kind:'bank_account',borrower_id:f.id,lender_id:f.bank_id,amount_cents:f.balance_sheet.assets.deposit??0,due_tick:null});
 const cb=publics.find(e=>e.kind==='central_bank');if(cb)for(const b of banks)push({kind:'reserve_account',borrower_id:b.id,lender_id:cb.id,amount_cents:b.balance_sheet.assets.reserves??0,due_tick:null});
 const selectedEdge=edge===null?undefined:edges[edge];
 const stressed=(id:string)=>nodes.find(n=>n.id===id&&n.kind==='bank'&&n.status!=='active');
 const counterparties=s.selected?edges.filter(e=>e.borrower_id===s.selected||e.lender_id===s.selected).map(e=>e.borrower_id===s.selected?e.lender_id:e.borrower_id):[];
 const nameOf=(id:string)=>nodes.find(n=>n.id===id)?.name??id;
 return <div className="network-view"><div className="network-heading"><p className="eyebrow">FOLLOW THE EXPOSURE</p><h2>The city is connected.</h2><p>Click an institution or a connection to follow its obligations.</p></div>
 <svg viewBox="0 0 900 660" aria-label="Financial network of banks and businesses">{edges.map((e,i)=>{const a=nodes.find(n=>n.id===e.borrower_id)!,b=nodes.find(n=>n.id===e.lender_id)!;const connected=!s.selected||e.borrower_id===s.selected||e.lender_id===s.selected;const loan=/loan|credit/.test(e.kind);
  return <g key={i} opacity={connected?1:.25} onClick={()=>setEdge(i)} className="network-edge"><line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="transparent" strokeWidth="20"/><line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={edge===i?'#ffe08a':stressed(e.lender_id)?'#ef4444':'#6d858d'} strokeWidth={loan?2.5:1.5} strokeDasharray={loan?'':'4 5'}/></g>;})}
 {nodes.map(n=>{const bank=n.kind==='bank',chosen=s.selected===n.id,hurt=n.status!=='active';return <g key={n.id} transform={`translate(${n.x},${n.y})`} className="network-node" role="button" aria-label={`Inspect ${n.name}`} tabIndex={0} opacity={!s.selected||chosen||counterparties.includes(n.id)?1:.35} onClick={()=>{s.set({selected:chosen?null:n.id});setEdge(null);}} onKeyDown={e=>{if(e.key==='Enter')s.set({selected:n.id});}}>
  <circle r={bank?32:22} fill={chosen?'#f0ce6c':'#1a2733'} stroke={hurt?'#ef4444':bank?'#a2b9b8':'#748d98'} strokeWidth="1.5"/><text textAnchor="middle" y="5" fill={chosen?'#111827':'#e0e9e5'} fontSize="18">{bank?'▥':n.kind==='business'?'▤':'◈'}</text><text textAnchor="middle" y={bank?54:43} fill="#e7ebea" fontSize="12">{n.name}</text>{hurt&&<text textAnchor="middle" y={bank?72:60} fill="#ef4444" fontSize="10">{bank?'▼ CREDIT CONTRACTING':'▼ '+n.status.toUpperCase()}</text>}</g>;})}</svg>
 {selectedEdge&&<div className="edge-detail"><span>{nameOf(selectedEdge.borrower_id)} → {nameOf(selectedEdge.lender_id)}</span><b>{currency(selectedEdge.amount_cents)}</b><small>{selectedEdge.kind.replaceAll('_',' ')}{selectedEdge.due_tick!==null?` · due day ${selectedEdge.due_tick}`:selectedEdge.kind.endsWith('account')?' · standing relationship (balance shown)':''}</small><button onClick={()=>setEdge(null)}>Dismiss</button></div>}
 <div className="network-legend"><span>◉ Bank</span><span>○ Business</span><span>— Loan</span><span>┄ Account / obligation</span></div></div>;}
// Identical branch values are drawn exactly on top of each other, so style, markers and opacity keep every series visible.
const BRANCH_STYLE=[{color:'#e8ecef',dash:undefined,marker:'circle'},{color:'#e6bd6c',dash:'6 4',marker:'square'},{color:'#5fd4bd',dash:undefined,marker:'triangle'}];
function Marker({kind,x,y,color,opacity=1}:{kind:string;x:number;y:number;color:string;opacity?:number}){
 // Nested sizes (ring, square, triangle) keep all three markers visible when values coincide.
 return kind==='circle'?<circle cx={x} cy={y} r="5.6" fill="none" stroke={color} strokeWidth="1.6" opacity={opacity}/>:kind==='square'?<rect x={x-3.2} y={y-3.2} width="6.4" height="6.4" fill={color} opacity={opacity}/>
  :<path d={`M${x} ${y-2.8}L${x+2.6} ${y+1.9}L${x-2.6} ${y+1.9}Z`} fill={color} stroke="#0b141b" strokeWidth=".5" opacity={opacity}/>;}
type ForkMetric={key:string;title:string;get:(t:Metrics)=>number;format:(n:number)=>string;max:number;ticks:number[]};
const integerTicks=(n:number)=>{const step=Math.max(1,Math.ceil(n/4)),t:number[]=[];for(let v=0;v<=n;v+=step)t.push(v);if(t[t.length-1]!==n)t.push(n);return t;};
const CW=360,CH=190,CL=48,CR=344,CT=14,CB=150;
function ForkChart({metric,fork,index,setIndex,focus}:{metric:ForkMetric;fork:Fork;index:number;setIndex:(i:number)=>void;focus:string|null}){
 const [hover,setHover]=useState(false),n=fork.branches[0].timeline.length;
 const x=(j:number)=>CL+j/Math.max(1,n-1)*(CR-CL),y=(v:number)=>CB-Math.min(1,v/metric.max)*(CB-CT);
 const at=fork.branches.map(b=>metric.get(b.timeline[index])),identical=at.every(v=>v===at[0]);
 const move=(e:React.MouseEvent<SVGSVGElement>)=>{const r=e.currentTarget.getBoundingClientRect(),px=(e.clientX-r.left)/r.width*CW;setIndex(Math.max(0,Math.min(n-1,Math.round((px-CL)/(CR-CL)*(n-1)))));setHover(true);};
 return <div className="comparison-chart"><div className="chart-head"><span>{metric.title}</span>{identical&&<em className="identical-note">Branches identical on this day</em>}</div>
 <div className="chart-finals">{fork.branches.map((b,i)=><span key={b.strategy} style={{color:BRANCH_STYLE[i].color}}><svg width="14" height="14" viewBox="-7 -7 14 14"><Marker kind={BRANCH_STYLE[i].marker} x={0} y={0} color={BRANCH_STYLE[i].color}/></svg>{metric.format(metric.get(b.timeline[n-1]))}</span>)}<small>final · day {fork.end_tick}</small></div>
 <div className="chart-plot"><svg viewBox={`0 0 ${CW} ${CH}`} role="img" aria-label={`${metric.title} comparison`} onMouseMove={move} onMouseLeave={()=>setHover(false)}>
  {metric.ticks.map(t=><g key={t}><line x1={CL} x2={CR} y1={y(t)} y2={y(t)} stroke="#ffffff1c"/><text x={CL-6} y={y(t)+3} textAnchor="end" fill="#8fa3ad" fontSize="9">{metric.format(t)}</text></g>)}
  <line x1={CL} x2={CL} y1={CT} y2={CB} stroke="#ffffff40"/><line x1={CL} x2={CR} y1={CB} y2={CB} stroke="#ffffff40"/>
  {fork.branches.map((b,i)=><polyline key={b.strategy} points={b.timeline.map((t,j)=>`${x(j)},${y(metric.get(t))}`).join(' ')} fill="none" stroke={BRANCH_STYLE[i].color} strokeWidth="2.4" strokeDasharray={BRANCH_STYLE[i].dash} opacity={focus&&focus!==b.strategy?.1:.7}/>)}
  {fork.branches.map((b,i)=><g key={b.strategy}>{b.timeline.map((t,j)=><Marker key={j} kind={BRANCH_STYLE[i].marker} x={x(j)} y={y(metric.get(t))} color={BRANCH_STYLE[i].color} opacity={focus&&focus!==b.strategy?.12:.85}/>)}</g>)}
  <line x1={x(index)} x2={x(index)} y1={CT} y2={CB} stroke="#ffffff80"/>
  <text x={CL} y={CH-22} fill="#aab9c9" fontSize="9">Day {fork.source_tick}</text><text x={CR} y={CH-22} textAnchor="end" fill="#aab9c9" fontSize="9">Day {fork.end_tick}</text></svg>
  {hover&&<div className="chart-tooltip" style={{left:`${x(index)/CW*100}%`}} role="tooltip"><b>Day {fork.source_tick+index}</b>{fork.branches.map((b,i)=><span key={b.strategy}><i style={{background:BRANCH_STYLE[i].color}}/>{strategyName[b.strategy]}<strong>{metric.format(at[i])}</strong></span>)}{identical&&<small>All three branches have the same value.</small>}</div>}</div></div>;}
export function BranchCompare(){const s=useStore(),fork=s.fork,[index,setIndex]=useState(0),[focus,setFocus]=useState<string|null>(null),[exporting,setExporting]=useState(false),[exportError,setExportError]=useState('');useEffect(()=>{setIndex(0);setFocus(null);},[fork?.fork_id]);if(!fork)return null;
 const exportReport=async()=>{if(!s.world)return;setExporting(true);setExportError('');try{
  const [saved,events]=await Promise.all([api<ComparisonEvidence>(`/api/forks/${fork.fork_id}`),api<{events:EconomyEvent[]}>(`/api/worlds/${s.world.simulation_id}/events?limit=1000`)]);
  downloadComparison(comparisonReport(saved,s.world,events.events,s.report),saved.fork_id);
 }catch(error){setExportError(error instanceof Error?error.message:'Comparison export failed');}finally{setExporting(false);}};
 const first=fork.branches[0].timeline[0],budget=Math.max(fork.request?.budget_cents??0,...fork.branches.flatMap(b=>b.timeline.map(t=>t.public_support_disbursed_cents)),1);
 const metrics:ForkMetric[]=[
  {key:'unemployment',title:'Unemployment',get:unemployment,format:n=>Math.round(n*10)/10+'%',max:100,ticks:[0,25,50,75,100]},
  {key:'business_defaults',title:'Business defaults',get:t=>t.business_defaults,format:n=>String(Math.round(n)),max:first.businesses,ticks:integerTicks(first.businesses)},
  {key:'stressed_banks',title:'Stressed banks',get:t=>t.stressed_banks,format:n=>String(Math.round(n)),max:first.banks,ticks:integerTicks(first.banks)},
  {key:'public_support_disbursed_cents',title:'Gross public support',get:t=>t.public_support_disbursed_cents,format:n=>currency(n).replace(/\.00$/,''),max:budget,ticks:[0,.25,.5,.75,1].map(f=>Math.round(budget*f))}];
 const last=fork.branches[0].timeline.length-1;
 return <div className="compare-view"><button className="dark-quiet" disabled={exporting} onClick={()=>void exportReport()}>{exporting?'Preparing report…':'Download comparison report'}</button>{exportError&&<p role="alert">{exportError}</p>}<div className="compare-header"><div><p className="eyebrow">FORK REALITY</p><h2>One world. Three futures.</h2></div><button className="dark-quiet" onClick={()=>s.set({compare:false})}><ArrowLeft size={14}/>Back to city</button></div>
 <div className="snapshot-proof">Same source day {fork.source_tick}<code title={fork.snapshot_sha256}>{fork.snapshot_sha256.slice(0,16)}…</code></div>
 <div className="comparison-legend">{fork.branches.map((b,i)=><button key={b.strategy} aria-pressed={focus===b.strategy} className={focus&&focus!==b.strategy?'dimmed':''} onClick={()=>setFocus(focus===b.strategy?null:b.strategy)}><svg width="26" height="10" viewBox="0 0 26 10"><line x1="0" x2="26" y1="5" y2="5" stroke={BRANCH_STYLE[i].color} strokeWidth="2" strokeDasharray={BRANCH_STYLE[i].dash}/><Marker kind={BRANCH_STYLE[i].marker} x={13} y={5} color={BRANCH_STYLE[i].color}/></svg>{strategyName[b.strategy]}</button>)}<small>Click a branch to isolate it</small></div>
 <div className="chart-grid">{metrics.map(m=><ForkChart key={m.key} metric={m} fork={fork} index={index} setIndex={setIndex} focus={focus}/>)}</div>
 <div className="final-table-wrap"><table className="final-table"><caption>Final values · day {fork.end_tick}</caption><thead><tr><th>Branch</th>{metrics.map(m=><th key={m.key}>{m.title}</th>)}</tr></thead>
 <tbody>{fork.branches.map((b,i)=><tr key={b.strategy}><td><svg width="14" height="14" viewBox="-7 -7 14 14"><Marker kind={BRANCH_STYLE[i].marker} x={0} y={0} color={BRANCH_STYLE[i].color}/></svg><span style={{color:BRANCH_STYLE[i].color}}>{strategyName[b.strategy]}</span></td>{metrics.map(m=><td key={m.key}>{m.format(m.get(b.timeline[last]))}</td>)}</tr>)}</tbody></table></div>
 <p className="compare-footnote">Calculated branches · source unchanged · agent recommendation shown separately in the inspector.</p></div>;}
