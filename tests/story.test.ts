import {describe,it,expect} from 'vitest';
import {checkpointEvents,lastCreditRejection,rejectionSource,salesSince} from '../apps/web/src/data/story';
import type {EconomyEvent} from '../apps/web/src/data/api';
const event=(sequence:number,event_type:string,fields:Partial<EconomyEvent>={}):EconomyEvent=>({sequence,event_type,simulation_id:'w',simulation_tick:1,agent_id:null,counterparty_id:null,amount_cents:null,transaction_id:null,details:{},...fields});
describe('recorded economy story',()=>{
 it('does not turn a comparison or recommendation into applied rescue',()=>{
 expect(checkpointEvents('rescue',[event(1,'agent_recommendation_applied'),event(2,'tick_completed')])).toEqual([]);
 expect(checkpointEvents('rescue',[event(3,'intervention_settled')])).toHaveLength(1);
 });
 it('includes actual credit decisions and excludes rejected consumer payments',()=>{
 const events=[event(1,'credit_rejected'),event(2,'loan_issued'),event(3,'payment_rejected',{details:{purpose:'purchase'}})];
 expect(checkpointEvents('credit',events).map(e=>e.sequence)).toEqual([1,2]);expect(checkpointEvents('business',events)).toEqual([]);
 });
 it('sums only recorded sales to the selected business',()=>{
 expect(salesSince([event(1,'purchase',{counterparty_id:'b',amount_cents:450}),event(2,'purchase',{counterparty_id:'other',amount_cents:900}),event(3,'payment_rejected',{counterparty_id:'b',amount_cents:500})],'b')).toBe(450);
 });
 it('does not mistake a stressed bank for a rejected business loan',()=>{
 expect(lastCreditRejection([event(1,'bank_status_changed',{agent_id:'bank_1'})],'b')).toBeUndefined();
 });
 it('uses the latest recorded rejection for that borrower',()=>{
 expect(lastCreditRejection([event(1,'credit_rejected',{agent_id:'b'}),event(2,'credit_rejected',{agent_id:'other'}),event(3,'credit_rejected',{agent_id:'b'})],'b')?.sequence).toBe(3);
 });
 it('distinguishes recorded bank constraints from borrower constraints',()=>{
 expect(rejectionSource('Bank capital or liquidity constraints prevent lending')).toBe('Bank constraint');
 expect(rejectionSource('Borrower credit limit exceeded')).toBe('Borrower constraint');
 expect(rejectionSource('Unspecified')).toBe('Recorded lending constraint');
 });
});
