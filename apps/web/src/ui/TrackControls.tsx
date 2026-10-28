import {useEffect,useState} from 'react';
import {api} from '../data/api';
import {useStore} from '../state/store';
import {usePublicInputs} from '../state/publicInputs';

export function WorldDataOptions(){
 const s=useStore(),[items,setItems]=useState<{calibration_id:string;collected_at:string}[]>([]);
 const latest=usePublicInputs(state=>state.data?.calibration_id);
 useEffect(()=>{let active=true;void api<typeof items>('/api/calibrations').then(v=>{if(active)setItems(v);}).catch(()=>{});return()=>{active=false;};},[latest]);
 return <label className="slider-label">Price and wage inputs<select aria-label="World calibration" value={s.selectedCalibration} onChange={e=>s.set({selectedCalibration:e.target.value})}>
 <option value="latest">Latest collected Apify inputs</option><option value="">Seeded synthetic inputs · explicit demo</option>{items.map(c=><option key={c.calibration_id} value={c.calibration_id}>Apify: {c.calibration_id} · {c.collected_at.slice(0,10)}</option>)}</select>
 <small>Public inputs load automatically and are frozen in each new world. Existing worlds keep their original inputs.</small></label>;
}

export function CreditSafeguards({businessId}:{businessId:string}){
 const s=useStore(),[profiles,setProfiles]=useState<string[]>([]),[profile,setProfile]=useState(''),[threshold,setThreshold]=useState(1000);
 useEffect(()=>{let active=true;void api<{profiles:string[]}>('/api/credit/profiles').then(v=>{if(active)setProfiles(v.profiles);}).catch(()=>{});return()=>{active=false;};},[]);
 const running=s.job?.status==='queued'||s.job?.status==='running';
 return <details className="sponsor-integrations"><summary>Credit safeguards</summary><p className="muted">Loans above this limit require an explicit human review before settlement.</p>
 <label>Review above USD<input aria-label="Credit human approval threshold" type="number" min="0.01" max="5000" step="0.01" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/></label>
 <label>Owner credit evidence<select aria-label="CRS underwriting profile" value={profile} onChange={e=>setProfile(e.target.value)}><option value="">Financial checks only</option>{profiles.map(p=><option key={p} value={p}>CRS sandbox: {p}</option>)}</select></label>
 <p className="muted">CRS flags and scores come from configured sponsor test profiles. Unknown results require review; blocked identities cannot be overridden.</p>
 <button disabled={s.busy||running||!Number.isFinite(threshold)||threshold<.01||threshold>5000} onClick={()=>void s.startJob('credit',businessId,{human_approval_threshold_cents:Math.round(threshold*100),...(profile?{require_crs:true,crs_profile_id:profile}:{})})}>Review with safeguards</button></details>;
}
