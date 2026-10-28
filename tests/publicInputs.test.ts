import {afterEach,beforeEach,expect,it,vi} from 'vitest';

const data={calibration_id:'public_fixture',collected_at:'2026-10-24T00:00:00Z',sources:[],price_cents:[425],daily_wage_cents:[15688]};
const job={job_id:'test-job',status:'queued',error:null,calibration_id:null,runs:{}};
const response=(value:unknown)=>({ok:true,json:async()=>value});
beforeEach(()=>{vi.resetModules();vi.useFakeTimers();});
afterEach(()=>{vi.clearAllTimers();vi.useRealTimers();vi.unstubAllGlobals();});

it('shares startup across mounts and immediately uses cached public data',async()=>{
 const fetch=vi.fn().mockResolvedValue(response({configured:true,data,job:null,state:'fresh'}));vi.stubGlobal('fetch',fetch);
 const inputs=await import('../apps/web/src/state/publicInputs');
 await Promise.all([inputs.initializePublicInputs(),inputs.initializePublicInputs()]);
 expect(await inputs.readyPublicInputs()).toEqual(data);expect(fetch).toHaveBeenCalledTimes(1);
 expect(String(fetch.mock.calls[0][0])).toContain('/calibrations/ensure');
});

it('waits for the first dataset before resolving world creation',async()=>{
 let deliver!:(value:unknown)=>void;const dataset=new Promise(resolve=>{deliver=resolve;});
 vi.stubGlobal('fetch',vi.fn(async(path:string)=>{
  if(path.endsWith('/ensure'))return response({configured:true,data:null,job,state:'refreshing'});
  if(path.includes('/collection/'))return response({...job,status:'completed',calibration_id:data.calibration_id});
  return {ok:true,json:()=>dataset};
 }));
 const inputs=await import('../apps/web/src/state/publicInputs');await inputs.initializePublicInputs();
 let resolved=false;const waiting=inputs.readyPublicInputs().then(result=>{resolved=true;return result;});
 await vi.advanceTimersByTimeAsync(2000);expect(resolved).toBe(false);
 deliver(data);expect(await waiting).toEqual(data);expect(inputs.usePublicInputs.getState().state).toBe('fresh');
});

it('keeps cached data available when its background refresh fails',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(path:string)=>response(path.endsWith('/ensure')?{configured:true,data,job,state:'refreshing'}:{...job,status:'failed',error:'Source unavailable'})));
 const inputs=await import('../apps/web/src/state/publicInputs');await inputs.initializePublicInputs();
 expect(await inputs.readyPublicInputs()).toEqual(data);await vi.advanceTimersByTimeAsync(2000);
 expect(inputs.usePublicInputs.getState().error).toBe('Source unavailable');
 expect(await inputs.readyPublicInputs()).toEqual(data);
});

it('reports a failed first collection without creating synthetic inputs',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(path:string)=>response(path.endsWith('/ensure')?{configured:true,data:null,job,state:'refreshing'}:{...job,status:'failed',error:'Source unavailable'})));
 const inputs=await import('../apps/web/src/state/publicInputs');await inputs.initializePublicInputs();
 const failed=expect(inputs.readyPublicInputs()).rejects.toThrow('Source unavailable');
 await vi.advanceTimersByTimeAsync(2000);await failed;expect(inputs.usePublicInputs.getState().data).toBeNull();
});
