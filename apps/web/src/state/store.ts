import {create} from 'zustand';
import type {Stage,Branch,Scenario} from '../data/types';
import {api,API_URL,postOnce} from '../data/api';
import {readyPublicInputs} from './publicInputs';
import type {World,Metrics,EconomyEvent,Network,Fork,Job,Report,Contract} from '../data/api';
type State = {
 stage:Stage; country:string; hoverCountry:string; tick:number; maxTick:number; branch:Branch;
 playing:boolean; speed:number; mode:'city'|'network'; selected:string|null; compare:boolean; crisis:boolean;
 crisisTick:number; scenario:Scenario|null; notice:string; world:World|null; history:Metrics[];
 events:EconomyEvent[]; network:Network|null; fork:Fork|null; job:Job|null; report:Report|null;
 contracts:Contract[]; busy:boolean; error:string; connection:string; activityAt:number;
 agentMode:'demo'|'live'; selectedScenario:string; selectedCalibration:string; playbackError:string;
 providerStatus:{live_configured:boolean;model:string|null;missing_variables:string[]}|null;
 set:(patch:Partial<State>)=>void; back:()=>void; reset:()=>Promise<void>; advance:()=>Promise<void>;
 createWorld:()=>Promise<void>; restore:()=>Promise<void>; refresh:()=>Promise<void>; pause:()=>Promise<void>;
 togglePlay:()=>Promise<void>; changeSpeed:(speed:number)=>Promise<void>; shock:(bank:string,loss:number)=>Promise<void>;
 compareFutures:(show?:boolean)=>Promise<void>; startJob:(kind:Job['kind'],actor?:string,options?:{require_crs?:boolean;crs_profile_id?:string;human_approval_threshold_cents?:number;allow_paid_research?:boolean})=>Promise<void>;
 cancelJob:()=>Promise<void>; settleReport:()=>Promise<void>;
};
let stream:EventSource|null=null, polling:ReturnType<typeof setInterval>|undefined;
let refreshTimer:ReturnType<typeof setTimeout>|undefined, refreshing=false, generation=0;
let eventTimer:ReturnType<typeof setTimeout>|undefined;
export function disconnect(){generation++;stream?.close();stream=null;clearInterval(polling);clearTimeout(refreshTimer);clearTimeout(eventTimer);}
function saveWorld(world:World){localStorage.setItem('economy-world',world.simulation_id);
 // Events can advance tick before the slower snapshot arrives; never step the same world backwards.
 const prev=useStore.getState(),same=prev.world?.simulation_id===world.simulation_id,tick=same?Math.max(prev.tick,world.simulation_tick):world.simulation_tick;
 useStore.setState({world,tick,maxTick:tick,playing:world.status==='running'});}
async function guard(operation:()=>Promise<void>){if(useStore.getState().busy)return;
 useStore.setState({busy:true,error:''});try{await operation();}catch(error){useStore.setState({error:error instanceof Error?error.message:'Backend request failed'});}finally{useStore.setState({busy:false});}}
async function connect(world:World){disconnect();
 useStore.setState({events:[],history:[],network:null,fork:null,job:null,report:null,contracts:[],selected:null,compare:false,error:'',crisis:false,selectedScenario:world.config.scenario});
 const currentGeneration=generation;saveWorld(world);await useStore.getState().refresh();const id=world.simulation_id;
 if(currentGeneration!==generation)return;
 const providerStatus=await api<NonNullable<State['providerStatus']>>('/api/agents/status');
 if(currentGeneration!==generation)return;
 useStore.setState({providerStatus,agentMode:providerStatus.live_configured?'live':'demo'});
 const after=useStore.getState().events.at(-1)?.sequence??0;
 stream=new EventSource(`${API_URL}/api/worlds/${id}/events/stream?after=${after}`);
 stream.onopen=()=>{if(useStore.getState().world?.simulation_id===id)useStore.setState({connection:'connected'});};
 stream.onerror=()=>{if(useStore.getState().world?.simulation_id===id)useStore.setState({connection:'reconnecting'});};
 const pending=new Map<number,EconomyEvent>();
 stream.addEventListener('economy_event',({data})=>{const event=JSON.parse(data) as EconomyEvent;
  if(useStore.getState().world?.simulation_id!==id)return;
  pending.set(event.sequence,event);
  if(pending.size===1)eventTimer=setTimeout(()=>{
   if(currentGeneration!==generation)return;
   const incoming=[...pending.values()];pending.clear();
   const latest=Math.max(...incoming.map(e=>e.simulation_tick));
   useStore.setState(s=>({tick:Math.max(s.tick,latest),maxTick:Math.max(s.maxTick,latest),events:[...s.events.filter(e=>!incoming.some(n=>n.sequence===e.sequence)),...incoming].sort((a,b)=>a.sequence-b.sequence).slice(-300),activityAt:Date.now(),crisis:s.crisis||incoming.some(e=>e.event_type==='bank_asset_loss')}));
   clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>{void useStore.getState().refresh();},100);
  },100);
 });// Events already trigger a refresh; this slower poll only catches state changes that emit no event.
 polling=setInterval(()=>{void useStore.getState().refresh();},5000);
}
export const useStore=create<State>((set,get)=>({
 stage:'GLOBE',country:'',hoverCountry:'',tick:0,maxTick:0,branch:'baseline',playing:false,speed:1,mode:'city',
 selected:null,compare:false,crisis:false,crisisTick:0,scenario:null,notice:'',world:null,history:[],events:[],network:null,
 fork:null,job:null,report:null,contracts:[],busy:false,error:'',connection:'not connected',activityAt:0,
 agentMode:'demo',selectedScenario:'credit_crunch',selectedCalibration:'latest',playbackError:'',providerStatus:null,set,
 back:()=>set({stage:get().stage==='PIN_SELECTED'?'COUNTRY':'GLOBE',selected:null,compare:false}),
 createWorld:()=>guard(async()=>{let calibration=get().selectedCalibration;if(calibration==='latest'){calibration=(await readyPublicInputs()).calibration_id;}if(get().world)await get().pause();const world=await api<World>('/api/worlds',{seed:42,scenario:get().selectedScenario,...(calibration?{calibration_id:calibration}:{})});await connect(world);set({stage:'CITY'});}),
 restore:async()=>{const requested=new URLSearchParams(location.search).get('room');const id=requested&&/^[A-Za-z0-9_-]{1,128}$/.test(requested)?requested:localStorage.getItem('economy-world');if(!id)return;
  try{await connect(await api<World>(`/api/worlds/${id}`));const jobs=await api<Job[]>(`/api/worlds/${id}/agent-jobs`);set({job:jobs[0]??null,stage:'CITY'});await get().refresh();}
  catch{set({error:'Saved world could not be loaded. Start the backend or create a new world.'});}},
 refresh:async()=>{const id=get().world?.simulation_id;if(!id||refreshing)return;refreshing=true;
  try{const base=`/api/worlds/${id}`;const [world,history,network,contracts,playback]=await Promise.all([
   api<World>(base),api<Metrics[]>(base+'/metrics'),api<Network>(base+'/network'),api<Contract[]>(base+'/contracts'),api<{error:string|null}>(base+'/playback')]);
   if(get().world?.simulation_id!==id)return;saveWorld(world);set({history,network,contracts,playbackError:playback.error??''});
   if(!get().events.length){const page=await api<{events:EconomyEvent[]}>(base+'/events?limit=1000');if(get().world?.simulation_id===id)set({events:page.events.slice(-300),crisis:page.events.some(e=>e.event_type==='bank_asset_loss')});}
   const jobId=get().job?.job_id;if(jobId){const job=await api<Job>(`/api/agent-jobs/${jobId}`);const report=job.report_url?await api<Report>(job.report_url):null;
    if(get().world?.simulation_id===id&&get().job?.job_id===jobId)set({job,report});}
  }catch(error){if(get().world?.simulation_id===id)set({error:error instanceof Error?error.message:'Refresh failed',connection:'disconnected'});}finally{refreshing=false;}},
 pause:async()=>{if(!get().world)return;await api(`/api/worlds/${get().world!.simulation_id}/pause`,{});set({playing:false});},
 togglePlay:()=>guard(async()=>{if(!get().world)return;if(get().playing)await get().pause();else await api(`/api/worlds/${get().world!.simulation_id}/play`,{interval_ms:1000/get().speed});await get().refresh();}),
 changeSpeed:speed=>guard(async()=>{if(get().playing&&get().world)await api(`/api/worlds/${get().world!.simulation_id}/play`,{interval_ms:1000/speed});set({speed});}),
 advance:()=>guard(async()=>{if(!get().world)return;await get().pause();await api(`/api/worlds/${get().world!.simulation_id}/step`,{ticks:1});await get().refresh();}),
 reset:()=>guard(async()=>{if(!get().world)return;const result=await postOnce<{simulation_id:string}>(`/api/worlds/${get().world!.simulation_id}/reset`,{},'request_id');await connect(await api<World>(`/api/worlds/${result.simulation_id}`));}),
 shock:(bank,loss)=>guard(async()=>{await get().pause();await postOnce(`/api/worlds/${get().world!.simulation_id}/shocks`,{bank_id:bank,asset_category:'risky_assets',loss_bps:Math.round(loss*100)},'transaction_id');set({crisis:true,crisisTick:get().tick});await get().refresh();}),
 compareFutures:(show=true)=>guard(async()=>{if(get().compare&&show){set({compare:false});return;}await get().pause();const fork=await postOnce<Fork>(`/api/worlds/${get().world!.simulation_id}/forks`,{bank_id:'bank_1',budget_cents:1000000,ticks:12},'request_id');set({fork,compare:show});await get().refresh();}),
 startJob:(kind,actor,options={})=>guard(async()=>{await get().pause();const base=`/api/worlds/${get().world!.simulation_id}`;
  const paths={central_bank:'/agent-jobs',credit:`/businesses/${actor}/credit-jobs`,procurement:`/businesses/${actor}/procurement-jobs`};
  const job=await postOnce<Job>(base+paths[kind],{mode:get().agentMode,agent_review:true,...options,...(kind==='central_bank'?{ticks:12,max_experiments:2,budget_cap_cents:1000000}:{auto_settle:false})},'request_id');set({job,report:null});await get().refresh();}),
 cancelJob:()=>guard(async()=>{if(get().job)set({job:await api<Job>(`/api/agent-jobs/${get().job!.job_id}/cancel`,{})});}),
 settleReport:()=>guard(async()=>{const report=get().report,job=get().job;if(!report||!job)return;await get().pause();
  const paths={central_bank:`agent-runs/${report.run_id}/apply`,credit:`credit-runs/${report.run_id}/settle`,procurement:`procurement-runs/${report.run_id}/settle`};
  await api(`/api/${paths[job.kind]}`,{transaction_id:`ui-${report.run_id}`});set({notice:'Settlement confirmed by the backend ledger.'});await get().refresh();})
}));
