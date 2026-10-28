import {create} from 'zustand';
import {api,postOnce} from '../data/api';
import type {CalibrationSource} from '../data/api';

export type Collection={job_id:string;status:string;error:string|null;calibration_id:string|null;runs:Record<string,string>;price_count?:number;wage_count?:number;usage_total_usd?:number};
export type PublicData={calibration_id:string;collected_at:string;sources:CalibrationSource[];price_cents:number[];daily_wage_cents:number[]};
type Result={configured:boolean;data:PublicData|null;job:Collection|null;state:string};
type State={configured:boolean;data:PublicData|null;job:Collection|null;state:string;error:string;loading:boolean};
export const usePublicInputs=create<State>(()=>({configured:false,data:null,job:null,state:'loading',error:'',loading:true}));
let initialization:Promise<void>|null=null,poll:ReturnType<typeof setTimeout>|undefined;
const active=(job:Collection|null)=>job?.status==='queued'||job?.status==='running';
function schedule(){
 clearTimeout(poll);if(!active(usePublicInputs.getState().job))return;
 poll=setTimeout(()=>{void updateJob();},2000);
}
async function updateJob(){
 const current=usePublicInputs.getState().job;if(!current)return;
 try{
  const job=await api<Collection>(`/api/calibrations/collection/${current.job_id}`);
  if(usePublicInputs.getState().job?.job_id!==job.job_id)return;
  if(job.status==='completed'&&job.calibration_id){const data=await api<PublicData>(`/api/calibrations/${job.calibration_id}`);usePublicInputs.setState({job,data,state:'fresh',error:''});}
  else usePublicInputs.setState({job,state:active(job)?'refreshing':job.status,error:job.error??''});
 }catch(e){usePublicInputs.setState({error:String(e)});}
 schedule();
}
export function initializePublicInputs(){
 if(initialization)return initialization;
 initialization=(async()=>{try{const result=await api<Result>('/api/calibrations/ensure',{});usePublicInputs.setState({...result,error:result.job?.status==='failed'?result.job.error??'':'',loading:false});schedule();}catch(e){usePublicInputs.setState({error:String(e),loading:false,state:'unavailable'});}})();
 return initialization;
}
export async function refreshPublicInputs(){
 usePublicInputs.setState({loading:true,error:''});
 try{const job=await postOnce<Collection>('/api/calibrations/collect',{},'request_id');usePublicInputs.setState({job,state:active(job)?'refreshing':job.status,loading:false});if(job.status==='completed')await updateJob();else schedule();}
 catch(e){usePublicInputs.setState({error:String(e),loading:false});}
}
export async function readyPublicInputs():Promise<PublicData>{
 await initializePublicInputs();
 const initial=usePublicInputs.getState();if(initial.data)return initial.data;
 if(!active(initial.job))throw new Error(initial.error||'Public inputs are unavailable. Check the data status or choose an explicit seeded demo.');
 return new Promise((resolve,reject)=>{
  const timeout=setTimeout(()=>{unsubscribe();reject(new Error('Public data is still loading. Its progress is shown in the data panel.'));},180000);
  const unsubscribe=usePublicInputs.subscribe(state=>{if(state.data){clearTimeout(timeout);unsubscribe();resolve(state.data);}else if(!active(state.job)){clearTimeout(timeout);unsubscribe();reject(new Error(state.error||'Public input collection did not complete.'));}});
 });
}
