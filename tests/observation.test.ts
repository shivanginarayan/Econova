import {describe,it,expect} from 'vitest';
import {observationEvidence} from '../apps/web/src/data/observation';
import type {EconomyEvent} from '../apps/web/src/data/api';
const event=(sequence:number,event_type:string,fields:Partial<EconomyEvent>={}):EconomyEvent=>({sequence,event_type,simulation_id:'w',simulation_tick:1,agent_id:null,counterparty_id:null,amount_cents:null,transaction_id:null,details:{},...fields});
describe('observation evidence context',()=>{
 it('separates the preceding shock from consequences and excludes future events',()=>{
 const r=observationEvidence([event(1,'bank_asset_loss'),event(2,'credit_rejected',{agent_id:'old'}),event(3,'credit_rejected',{agent_id:'current'}),event(4,'bank_asset_loss'),event(5,'business_default',{agent_id:'future'})],2,3);
 expect(r.shock?.sequence).toBe(1);expect([...r.borrowers]).toEqual(['current']);expect(r.defaults.size).toBe(0);
 });
 it('counts distinct borrowers and workers, not repeated daily failures or consumer payments',()=>{
 const e=event(1,'credit_rejected',{agent_id:'b'});
 const r=observationEvidence([e,e,event(2,'credit_rejected',{agent_id:'b'}),event(3,'payment_rejected',{counterparty_id:'worker',details:{purpose:'salary'}}),event(4,'payment_rejected',{counterparty_id:'worker',details:{purpose:'salary'}}),event(5,'payment_rejected',{counterparty_id:'shop',details:{purpose:'purchase'}})],0,5);
 expect(r.window).toHaveLength(5);expect(r.borrowers.size).toBe(1);expect([...r.unpaidWorkers]).toEqual(['worker']);
 });
 it('does not infer refusals or defaults from bank stress and job losses alone',()=>{
 const r=observationEvidence([event(1,'bank_status_changed'),event(2,'job_lost')],0,2);
 expect(r.borrowers.size).toBe(0);expect(r.defaults.size).toBe(0);expect(r.shock).toBeUndefined();
 });
});
