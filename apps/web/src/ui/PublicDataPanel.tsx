import {useEffect} from 'react';
import {useStore} from '../state/store';
import {usePublicInputs,initializePublicInputs,refreshPublicInputs} from '../state/publicInputs';

export default function PublicDataPanel(){
 const s=useStore(),inputs=usePublicInputs(),{configured,job,error,loading:busy,data:latest}=inputs;
 const running=job?.status==='queued'||job?.status==='running';
 useEffect(()=>{void initializePublicInputs();},[]);
 const frozen=s.world?.calibration,sources=frozen?.sources??latest?.sources??[];
 return <details className="public-data-panel" open={!frozen}><summary>Real public inputs · Apify</summary>
 <p>{frozen?'This world uses frozen public price and wage references collected through Apify.':s.world?'This existing world has frozen seeded inputs. Public data loads automatically for new worlds.':'New worlds use the public inputs loaded automatically below.'}</p>
 <p role="status">{busy?'Loading public data?':running?(latest?'Saved public data is ready. Refreshing sources in the background?':'Collecting public data automatically for the first time?'):latest?'Public data loaded automatically.':'Public data is currently unavailable.'}</p>
 <details><summary>Refresh options</summary><button disabled={!configured||running||busy} onClick={()=>void refreshPublicInputs()}>Refresh public inputs now</button><small>Saved data loads on open. Sources refresh automatically when more than six hours old. Refreshing uses bounded Apify runs.</small></details>
 {!configured&&<p>Backend needs APIFY_TOKEN and a deployed APIFY_ACTOR_ID.</p>}
 {job&&<p role="status">Collection: {job.status}{job.status==='completed'?` · ${job.price_count} menu-price observations · ${job.wage_count} statutory wage reference · reported run usage $${(job.usage_total_usd??0).toFixed(4)}`:''}</p>}
 {job?.error&&<p role="alert">{job.error}</p>}{error&&<p role="alert">{error}</p>}
 {job&&job.status!=='completed'&&Object.entries(job.runs).map(([category,run])=><p key={run}><a href={`https://console.apify.com/actors/runs/${encodeURIComponent(run)}`} target="_blank" rel="noreferrer">Inspect {category} collection run</a></p>)}
 {latest&&<><p>Latest collection: {new Date(latest.collected_at).toLocaleString()}<br/>{latest.price_cents.length} listed menu prices · daily wage reference ${(latest.daily_wage_cents[0]/100).toFixed(2)} (assumed 8-hour day).</p>
 <button disabled={s.busy} onClick={async()=>{s.set({selectedCalibration:latest.calibration_id});await s.createWorld();}}>Create new world with public inputs</button></>}
 {frozen&&<p>Frozen collection: {new Date(frozen.collected_at).toLocaleString()} · {frozen.price_sample_count} menu-price observations · {frozen.wage_sample_count} wage reference<br/>Snapshot {frozen.sha256.slice(0,16)}</p>}
 <p><b>Scope:</b> One cafe's posted drink prices and the official general minimum wage. The wage is a legal floor, not average pay. Households, bank balance sheets, employment links and behavior remain simulated. This is not a citywide economic calibration.</p>
 {sources.map(source=><div className="public-source-card" key={source.run_id}><p><a href={source.source_url} target="_blank" rel="noreferrer">{source.category==='wages'?'SF official wage source':source.category==='prices'?'Cafe Seventy8 public menu':'Public source'}</a> · {source.accepted??source.observations?.length??0} observations<br/>{source.scope}<br/>{source.conversion}</p>
 <a href={`https://console.apify.com/actors/runs/${encodeURIComponent(source.run_id)}`} target="_blank" rel="noreferrer">Inspect Apify run</a>
 <details><summary>Collected values and dates</summary>{source.observations?.map((row,i)=><p key={i}>{row.item}: ${row.value?.toFixed(2)} {row.unit==='usd_hour'?'/ hour':'/ listed item'}{row.variant?` · ${row.variant}`:''}<br/>{row.effective_date?`Effective ${row.effective_date} · `:''}Collected {row.observed_at?new Date(row.observed_at).toLocaleString():'date unavailable'}</p>)}</details></div>)}
 </details>;
}
