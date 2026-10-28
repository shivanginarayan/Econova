import {it,expect} from 'vitest';
import {getCityLayout,getSnapshot} from '../apps/web/src/data/fixtures';
import {readDistrictActivity} from '../apps/web/src/city/activity';
import {createMoverPool,updateMovers} from '../apps/web/src/city/movers';
it('spaces queues along connected approaches without clamping people on one endpoint',()=>{const l=getCityLayout(),s=getSnapshot(6,'baseline'),base=getSnapshot(0,'baseline'),pool=createMoverPool(l);updateMovers(pool,0,10,new Map(l.districts.map(d=>[d.name,readDistrictActivity(s,base,d.name)])),new Map(s.firms.map(f=>[f.id,f.open])),{x:0,y:0,width:1440,height:940});for(const a of pool.filter(m=>m.queueIndex>=0&&m.active))for(const b of pool.filter(m=>m.id<a.id&&m.targetId===a.targetId&&m.queueIndex>=0&&m.active))expect(Math.hypot(a.x-b.x,a.y-b.y),String(a.id)+' / '+b.id).toBeGreaterThan(4);});
