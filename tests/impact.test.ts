import {describe,it,expect} from 'vitest';
import {captureBaseline,changeLabel,percentChange,percentage,signed,eventDescription,significant} from '../apps/web/src/data/impact';
import examples from '../docs/examples.json';
import type {World,EconomyEvent} from '../apps/web/src/data/api';
const event=(changes:Partial<EconomyEvent>):EconomyEvent=>({sequence:1,simulation_id:'test',simulation_tick:0,event_type:'test',agent_id:null,counterparty_id:null,amount_cents:null,transaction_id:null,details:{},...changes});
describe('honest impact presentation',()=>{
 it('distinguishes relative change from percentage points',()=>{expect(percentChange(80,100)).toBe(-20);expect(signed((.8-.9)*100,' pp')).toBe('-10.0 pp');});
 it('never invents a percentage from a zero or negative baseline',()=>{expect(percentChange(10,0)).toBeNull();expect(changeLabel(10,0)).toBe('New since baseline');expect(changeLabel(-5,-10)).toBe('Negative baseline');expect(changeLabel(0,0)).toBe('No change');});
 it('handles empty populations without infinite values',()=>{expect(percentage(0,0)).toBe(0);expect(percentage(2,5)).toBe(40);});
 it('captures independent per-world baselines',()=>{const world=structuredClone(examples.world_after_one_tick) as unknown as World;const base=captureBaseline(world);world.metrics.household_cash_cents=1;world.entities[0].balance_sheet.equity_cents=9;expect(base.metrics.household_cash_cents).not.toBe(1);expect(base.entities[world.entities[0].id].equity).not.toBe(9);expect(base.worldId).toBe(world.simulation_id);});
 it('describes the recorded investment loss without asserting a deposit loss',()=>{const loss=event({event_type:'bank_asset_loss',agent_id:'bank_1',details:{loss_bps:4000}});expect(eventDescription(loss,[])).toBe('bank_1 lost 40% of its risky investments.');});
 it('separates payroll failures from ordinary rejected payments',()=>{expect(significant(event({event_type:'payment_rejected',details:{purpose:'salary'}}))).toBe(true);expect(significant(event({event_type:'payment_rejected',details:{purpose:'purchase'}}))).toBe(false);});
});
