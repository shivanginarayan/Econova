import {afterEach,describe,expect,it,vi} from 'vitest';
import {api,currency,postOnce} from '../apps/web/src/data/api';
import {getLiveLayout,liveCityState,bindEntities,liveSnapshot,districtEntityIds} from '../apps/web/src/data/liveCity';
import {getCityLayout} from '../apps/web/src/data/fixtures';
import {useStore} from '../apps/web/src/state/store';
import examples from '../docs/examples.json';
import type {World} from '../apps/web/src/data/api';

afterEach(()=>vi.unstubAllGlobals());
describe('backend integration contract',()=>{
 it('converts integer cents exactly once for display',()=>{
  expect(currency(12345)).toBe('$123.45');expect(currency(0)).toBe('$0.00');
 });
 it('maps the decorative city onto real backend IDs without inventing institutions',()=>{
  const world=structuredClone(examples.world_after_one_tick) as unknown as World;
  useStore.setState({world});const layout=getLiveLayout();
  const mapped=layout.buildings.filter(b=>!b.id.startsWith('scenery-'));
  expect(new Set(mapped.map(b=>b.id)).size).toBe(world.entities.length);
  expect(mapped.map(b=>b.id).sort()).toEqual(world.entities.map(e=>e.id).sort());
  const business=world.entities.find(e=>e.kind==='business')!;business.status='defaulted';
  useStore.setState({world});expect(liveCityState().firms.find(e=>e.id===business.id)?.open).toBe(false);
 });
 it('reports backend rejections instead of substituting fixture outcomes',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:409,json:async()=>({detail:'Source world changed'})}));
  await expect(api('/api/test',{})).rejects.toThrow('Source world changed');
 });
 it('binds featured banks and shops once without changing decorative layout IDs',()=>{
  const world=structuredClone(examples.world_after_one_tick) as unknown as World;
  useStore.setState({world});const layout=getCityLayout(),ids=layout.buildings.map(b=>b.id),bound=bindEntities(layout.buildings);
  expect(bound.get('bank-1')?.id).toBe('bank_1');expect(bound.get('cafe-14')?.id).toBe('business_1');
  expect(districtEntityIds('Mission District').has('business_1')).toBe(true);
  expect(districtEntityIds('Mission District').has('bank_1')).toBe(false);
  expect(new Set([...bound.values()].map(e=>e.id)).size).toBe(world.entities.length);
  expect(layout.buildings.map(b=>b.id)).toEqual(ids);
 });
 it('reflects replacement backend objects and constrained active banks in live overlays',()=>{
  const world=structuredClone(examples.world_after_one_tick) as unknown as World;
  useStore.setState({world});const layout=getCityLayout(),before=bindEntities(layout.buildings);
  const replacement=structuredClone(world),business=replacement.entities.find(e=>e.id==='business_1')!,bank=replacement.entities.find(e=>e.id==='bank_1')!;
  business.status='defaulted';bank.status='active';bank.lending_available=false;
  useStore.setState({world:replacement,tick:12});const bound=bindEntities(layout.buildings),snapshot=liveSnapshot(layout,1,bound);
  expect(before.get('cafe-14')?.status).toBe('active');expect(bound.get('cafe-14')?.status).toBe('defaulted');
  expect(snapshot.firms.find(f=>f.id==='cafe-14')?.open).toBe(false);
  expect(snapshot.districts[layout.buildings.find(b=>b.id==='cafe-14')!.district].firmOpenRate).toBeLessThan(100);
  expect(liveCityState().stressedBanks.has('bank_1')).toBe(true);expect(snapshot.tick).toBe(12);
 });
 it('reuses the original request ID after an uncertain network response',async()=>{
  const fetch=vi.fn().mockRejectedValueOnce(new Error('connection lost')).mockResolvedValue({ok:true,json:async()=>({status:'settled'})});
  vi.stubGlobal('fetch',fetch);
  await expect(postOnce('/api/retry-test',{amount_cents:100},'transaction_id')).rejects.toThrow('connection lost');
  await postOnce('/api/retry-test',{amount_cents:100},'transaction_id');
  const first=JSON.parse(fetch.mock.calls[0][1].body),second=JSON.parse(fetch.mock.calls[1][1].body);
  expect(second.transaction_id).toBe(first.transaction_id);
  await postOnce('/api/retry-test',{amount_cents:100},'transaction_id');
  expect(JSON.parse(fetch.mock.calls[2][1].body).transaction_id).not.toBe(first.transaction_id);
 });
});
