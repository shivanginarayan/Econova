import type {EconomyEvent,Entity,Metrics,World} from './api';
export type ImpactBaseline={worldId:string;day:number;sequence:number;metrics:Metrics;entities:Record<string,{equity:number;cash:number;employees:number}>};
export function captureBaseline(world:World):ImpactBaseline{return {worldId:world.simulation_id,day:world.simulation_tick,sequence:world.latest_event_sequence,metrics:{...world.metrics},entities:Object.fromEntries(world.entities.map(e=>[e.id,{equity:e.balance_sheet.equity_cents,cash:e.balance_sheet.assets.deposit??0,employees:e.employees?.length??0}]))};}
export function percentage(value:number,total:number){return total>0?value/total*100:0;}
export function percentChange(value:number,baseline:number){return baseline>0?(value-baseline)/baseline*100:null;}
export function signed(value:number,suffix='%'){return `${value>0?'+':''}${Math.abs(value)<.05?'0.0':value.toFixed(1)}${suffix}`;}
export function changeLabel(value:number,baseline:number){const change=percentChange(value,baseline);return change===null?(value===baseline?'No change':baseline<0?'Negative baseline': 'New since baseline'):signed(change);}
export function stressed(bank:Entity){return bank.status!=='active'||bank.lending_available===false;}
const meaningfulEvents=new Set(['bank_asset_loss','bank_status_changed','credit_rejected','job_lost','business_default','production_limited','interbank_default','bank_lending','household_cash']);
export function significant(event:EconomyEvent){return meaningfulEvents.has(event.event_type)||(event.event_type==='payment_rejected'&&event.details.purpose==='salary');}
export function eventDescription(event:EconomyEvent,entities:Entity[]){
 const name=(id:string|null)=>entities.find(e=>e.id===id)?.name??id??'The economy';
 switch(event.event_type){
  case 'bank_asset_loss':return `${name(event.agent_id)} lost ${typeof event.details.loss_bps==='number'?(event.details.loss_bps/100).toFixed(0)+'% of its risky investments':'investment value'}.`;
  case 'bank_status_changed':return `${name(event.agent_id)} changed from ${String(event.details.previous_status).replaceAll('_',' ')} to ${String(event.details.status??'a different financial condition').replaceAll('_',' ')}.`;
  case 'credit_rejected':return `${name(event.agent_id)} could not obtain ${event.details.purpose==='refinancing'?'refinancing':'payroll credit'} from ${name(event.counterparty_id)}.`;
  case 'payment_rejected':return `${name(event.counterparty_id)} did not receive a wage payment from ${name(event.agent_id)}.`;
  case 'job_lost':return `${name(event.agent_id)} lost their job at ${name(event.counterparty_id)}${event.details.reason==='layoff'?' in a layoff':''}.`;
  case 'business_default':return `${name(event.agent_id)} defaulted. ${String(event.details.reason??'Financial obligations could not be met.')}`;
  case 'production_limited':return `${name(event.agent_id)} had insufficient inputs for full production.`;
  case 'interbank_default':return `${name(event.agent_id)} could not fully repay ${name(event.counterparty_id)}.`;
  default:return `${name(event.agent_id)}: ${event.event_type.replaceAll('_',' ')}.`;
 }
}
