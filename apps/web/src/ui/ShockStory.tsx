import {useEffect,useState} from 'react';
import {api,currency} from '../data/api';
import {useStore} from '../state/store';

type Story = {report_id:string;title:string;status:string;baseline:{value_usd:string;observation_date:string;retrieved_at:string;source_url:string;stale:boolean};hypothetical_debt_usd:string;loss_bps:number;portfolio_cents:number;estimated_loss_cents:number;formula:string;transmission:string;limitations:string[];assumptions:{bank_id:string;debt_increase_percent:number;yield_increase_bps:number;modified_duration_years:number;portfolio_exposure_percent:number}};
const dollars=(value:string)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(Number(value));

export default function ShockStory(){
 const s=useStore(),id=s.world?.simulation_id;
 const [bank,setBank]=useState('bank_1'),[increase,setIncrease]=useState(25),[yieldBps,setYield]=useState(200),[duration,setDuration]=useState(5),[exposure,setExposure]=useState(50);
 const [story,setStory]=useState<Story|null>(null),[saved,setSaved]=useState<Story[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let current=true;if(id)void api<Story[]>(`/api/worlds/${id}/shock-stories`).then(rows=>{if(current)setSaved(rows);}).catch(()=>{if(current)setError('Story history could not be loaded.');});return()=>{current=false;};},[id]);
 if(!id)return null;
 const change=(setter:(n:number)=>void,value:string)=>{setter(Number(value));setStory(null);setError('');};
 const preview=async()=>{setBusy(true);setStory(null);setError('');try{await s.pause();const result=await api<Story>(`/api/worlds/${id}/shock-stories/preview`,{bank_id:bank,debt_increase_percent:increase,yield_increase_bps:yieldBps,modified_duration_years:duration,portfolio_exposure_percent:exposure});setStory(result);setSaved(rows=>[result,...rows]);}catch(e){setError(String(e));}finally{setBusy(false);}};
 const apply=async()=>{if(!story)return;setBusy(true);setError('');try{await s.pause();await api(`/api/worlds/${id}/shock-stories/apply`,{report_id:story.report_id});setStory({...story,status:'applied'});setSaved(rows=>rows.map(row=>row.report_id===story.report_id?{...row,status:'applied'}:row));await s.refresh();s.set({notice:'Debt stress applied. Use Fork Reality or Test rescue policies before advancing time.'});}catch(e){setError(String(e));}finally{setBusy(false);}};
 return <details className="shock-story-panel shock-story"><summary>Build a sourced crisis story</summary>
 <h3>What if US debt rises by 25%?</h3><p>Load real US Treasury debt data, choose a hypothetical increase, then test an explicit bank-loss assumption. No API key needed.</p>
 <p><b>The debt increase does not automatically cause a yield rise.</b> You choose that separately. War, spending policy or an oil crisis need their own transmission models; this experiment models debt-related bond repricing only.</p>
 <fieldset disabled={busy||s.busy}><label>Target bank<select aria-label="Story target bank" value={bank} onChange={e=>{setBank(e.target.value);setStory(null);}}>{s.world?.entities.filter(e=>e.kind==='bank').map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label>
 <label>Hypothetical debt increase (%)<input aria-label="Debt increase percent" type="number" min="0" max="100" step="1" value={increase} onChange={e=>change(setIncrease,e.target.value)}/></label>
 <h3>Separate stress assumptions</h3>
 <label>Assumed bond-yield increase (basis points)<input aria-label="Assumed yield increase" type="number" min="0" max="500" step="1" value={yieldBps} onChange={e=>change(setYield,e.target.value)}/></label><small>100 basis points = 1 percentage point. This is a user assumption, not a Treasury forecast.</small>
 <label>Assumed modified duration (years)<input aria-label="Assumed bond duration" type="number" min="1" max="10" step="1" value={duration} onChange={e=>change(setDuration,e.target.value)}/></label><small>Approximate sensitivity of bond prices to a change in yields.</small>
 <label>Assumed bond share of risky portfolio (%)<input aria-label="Assumed bond exposure" type="number" min="0" max="100" step="1" value={exposure} onChange={e=>change(setExposure,e.target.value)}/></label>
 <button onClick={()=>void preview()}>Load Treasury data and preview</button></fieldset>
 {busy&&<p role="status">Working…</p>}{error&&<p role="alert" className="request-error">{error}</p>}
 {story&&<div className="sponsor-context" aria-label="Debt shock preview"><h3>{story.title}</h3><p><b>Observed US debt:</b> {dollars(story.baseline.value_usd)}<br/>As of {story.baseline.observation_date} · <a href={story.baseline.source_url} target="_blank" rel="noreferrer">US Treasury source</a><br/>Retrieved {new Date(story.baseline.retrieved_at).toLocaleString()}</p>
 {story.baseline.stale&&<p role="status">The latest returned observation is more than seven days old. This is dated context, not a real-time figure.</p>}
 <p><b>Hypothetical debt:</b> {dollars(story.hypothetical_debt_usd)} (+{story.assumptions.debt_increase_percent}%). No future date is predicted.</p>
 <p><b>Assumed transmission:</b> {story.transmission}</p><p>{story.formula}</p>
 <p>Assumed yield rise {story.assumptions.yield_increase_bps} bps · duration {story.assumptions.modified_duration_years} years · exposure {story.assumptions.portfolio_exposure_percent}%.</p>
 <p><b>Calculated risky-portfolio loss:</b> {(story.loss_bps/100).toFixed(2)}% of {currency(story.portfolio_cents)} = {currency(story.estimated_loss_cents)} at {story.assumptions.bank_id}.</p>
 <details><summary>Model assumptions and limits</summary>{story.limitations.map(line=><p key={line}>{line}</p>)}</details>
 <p>Preview moves no money. Applying records a simulated investment loss; it does not increase the simulation government's debt or directly take money from customer deposits.</p>
 <button disabled={busy||s.busy||story.status==='applied'||story.estimated_loss_cents===0} onClick={()=>void apply()}>{story.status==='applied'?'Story shock applied':'Apply this story shock'}</button>
 {story.status==='applied'&&<p>Next: Fork Reality → compare futures → Test rescue policies → inspect the recommendation.</p>}</div>}
 {saved.length>0&&<details><summary>Saved story evidence ({saved.length})</summary>{saved.map(row=><div key={row.report_id}><p>{row.title} · {row.status} · baseline {row.baseline.observation_date}</p><button onClick={()=>{setStory(row);setError('');}}>View saved evidence</button></div>)}</details>}
 </details>;
}
