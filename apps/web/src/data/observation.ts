import type {EconomyEvent} from './api';
export function observationEvidence(events:EconomyEvent[],start:number,end:number){
 const ordered=[...new Map(events.map(e=>[e.sequence,e])).values()].sort((a,b)=>a.sequence-b.sequence);
 const window=ordered.filter(e=>e.sequence>start&&e.sequence<=end);
 return {shock:ordered.filter(e=>e.sequence<=start&&e.event_type==='bank_asset_loss').at(-1),window,
  borrowers:new Set(window.filter(e=>e.event_type==='credit_rejected').map(e=>e.agent_id).filter(Boolean)),
  unpaidWorkers:new Set(window.filter(e=>e.event_type==='payment_rejected'&&e.details.purpose==='salary').map(e=>e.counterparty_id).filter(Boolean)),
  defaults:new Set(window.filter(e=>e.event_type==='business_default').map(e=>e.agent_id).filter(Boolean))};
}
