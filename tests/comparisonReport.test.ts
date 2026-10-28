import {describe,it,expect} from 'vitest';
import {comparisonReport} from '../apps/web/src/data/comparisonReport';
import type {ComparisonEvidence,Metrics,World,Report} from '../apps/web/src/data/api';

const metrics:Metrics={simulation_tick:12,employment_rate:0,employed_households:0,households:40,businesses:8,banks:5,
 household_cash_cents:100000,business_defaults:8,stressed_banks:5,public_support_disbursed_cents:0,
 finished_goods_units:20,produced_units_this_tick:0,sold_units_this_tick:0,unmet_demand_units_this_tick:0};
const world:World={simulation_id:'source',simulation_tick:0,status:'paused',config:{seed:42,scenario:'credit_crunch'},
 entities:[],metrics,latest_event_sequence:1,production_model:'finite_v1'};
const fork:ComparisonEvidence={fork_id:'fork1',source_simulation_id:'source',source_event_sequence:1,source_tick:0,end_tick:12,
 snapshot_sha256:'snapshot1',seed:42,engine_version:'test',request:{bank_id:'bank_1',budget_cents:1000000,ticks:12},
 recommended_strategy:'no_intervention',recommendation_basis:'Rule-based, not AI',tied_strategies:['no_intervention'],
 cost_definition:'Gross support disbursed, not net fiscal loss.',branches:['no_intervention','bank_lending','household_cash'].map(strategy=>({
  strategy,simulation_id:strategy,metrics:{...metrics,public_support_disbursed_cents:strategy==='no_intervention'?0:1000000,
   fiscal_transfer_cost_cents:strategy==='household_cash'?1000000:0,public_loan_outstanding_cents:strategy==='bank_lending'?1000000:0},
  timeline:[metrics],audit:{balanced:true},delta_vs_no_intervention:{employed_households:0,business_defaults:0}}))};

describe('shareable comparison evidence',()=>{
 it('reports a failed rescue honestly and converts cents once',()=>{
  const html=comparisonReport(fork,world,[]);
  expect(html).toContain('Neither tested intervention improves final employment or business defaults');
  expect(html).toContain('$10,000.00');expect(html).not.toContain('$1,000,000.00');
  expect(html).toContain('not measured customer savings');
  expect(html).toContain('Explicit seeded synthetic');expect(html).toContain('not net fiscal loss');
  expect(html).toContain('No AI recommendation is linked');
 });
 it('does not attach an AI recommendation from another comparison or snapshot',()=>{
  const report:Report={run_id:'agent1',simulation_id:'source',source_tick:0,status:'completed',trace:[],snapshot_sha256:'snapshot1',
   provider:'nebius',model:'Nemotron',recommendation:{fork_id:'another',strategy:'household_cash',amount_cents:1000000,bank_id:null,rationale:'MODEL_REASON'}};
  expect(comparisonReport(fork,world,[],report)).not.toContain('MODEL_REASON');
  report.recommendation!.fork_id='fork1';
  expect(comparisonReport(fork,world,[],report)).toContain('MODEL_REASON');
  report.snapshot_sha256='different';expect(comparisonReport(fork,world,[],report)).not.toContain('MODEL_REASON');
 });
 it('keeps public-input scope and safely escapes untrusted source text',()=>{
  const calibrated:World={...world,calibration:{calibration_id:'public1',provider:'apify',sha256:'frozen',collected_at:'2026-10-24',
   price_sample_count:29,wage_sample_count:1,sources:[{actor_id:'actor',run_id:'run',dataset_id:'dataset',source_url:'https://example.com',scope:'<script>alert("unsafe")</script>'}]}};
  const html=comparisonReport(fork,calibrated,[]);
  expect(html).toContain('&lt;script&gt;');expect(html).not.toContain('<script>');
  expect(html).toContain('wage floor is not average pay');expect(html).toContain('frozen');
  expect(html).not.toContain('Explicit seeded synthetic');
 });
 it('rejects a different source world',()=>{
  expect(()=>comparisonReport(fork,{...world,simulation_id:'other'},[])).toThrow('do not match');
 });
});
