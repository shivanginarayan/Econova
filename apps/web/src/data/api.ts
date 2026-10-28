export type Metrics = {simulation_tick:number; employment_rate:number; employed_households:number;
 households:number; businesses:number; banks:number; household_cash_cents:number; business_defaults:number;
 stressed_banks:number; public_support_disbursed_cents:number; finished_goods_units:number;
 produced_units_this_tick:number; sold_units_this_tick:number; unmet_demand_units_this_tick:number};
export type Entity = {id:string; name:string; kind:string; status:string; bank_id?:string|null;
 opening_payroll_cents?:number|null;credit_limit_cents?:number|null; employer_id?:string|null; employees?:string[]|null; materials_units?:number|null; goods_units?:number|null;
 last_produced_units?:number|null; loan_due_tick?:number|null; capital_ratio?:number|null; liquidity_ratio?:number|null;
 lending_available?:boolean|null; balance_sheet:{assets:Record<string,number>; liabilities:Record<string,number>;
 assets_cents:number; liabilities_cents:number; equity_cents:number; balanced:boolean}};
export type SourceObservation={item?:string;value?:number;unit?:string;kind?:string;effective_date?:string;variant?:string;source_url?:string;observed_at?:string};
export type CalibrationSource={actor_id:string;run_id:string;dataset_id:string;source_url:string;category?:string;scope?:string;conversion?:string;accepted?:number;observations?:SourceObservation[]};
export type World = {financial_model?:string;financial_assumptions?:{opening_payroll_days:number;credit_payroll_days:number;loan_review_days:number}|null;public_benchmark?:import('../ui/PublicBenchmarks').Benchmark|null;benchmark_mapping?:Record<string,unknown>|null;simulation_id:string; simulation_tick:number; status:'paused'|'running';calibration?:{calibration_id:string;provider:string;sha256:string;collected_at:string;sources:CalibrationSource[];price_sample_count:number;wage_sample_count:number}|null;
 config:{seed:number; scenario:string}; entities:Entity[]; metrics:Metrics; latest_event_sequence:number; production_model:string;operating_model?:string;operating_assumptions?:Record<string,unknown>|null;settlement_model?:string};
export type EconomyEvent = {sequence:number; simulation_id:string; simulation_tick:number; event_type:string;
 agent_id:string|null; counterparty_id:string|null; amount_cents:number|null; transaction_id:string|null; details:Record<string,unknown>};
export type Exposure = {kind:string; borrower_id:string; lender_id:string; amount_cents:number; due_tick:number|null};
export type Network = {simulation_id:string; simulation_tick:number; exposures:Exposure[]};
export type Contract = {contract_id:string; buyer_id:string; supplier_id:string; status:string;
 quantity:number; total_cents:number; down_payment_cents:number; outstanding_cents:number; due_tick:number};
export type Trace = {sequence:number; tool:string; role?:string; actor_id?:string; status:string; arguments:Record<string,unknown>; result:unknown};
export type Offer = {offer_id:string; supplier_id:string; quantity:number; total_cents:number; down_payment_cents:number; due_in_ticks:number};
export type AgentActivity={sequence:number;at:number;actor:string;target:string|null;message:string;tool:string|null;trace_sequence:number|null};
export type Supervision={status:'running'|'passed'|'blocked'|'failed';checks:{name:string;passed:boolean}[];rationale:string;provider:string|null;model:string|null};
export type Report = {request?:{agent_review?:boolean};activity?:AgentActivity[];active_agent?:string|null;supervision?:Supervision|null;supplier_ids?:string[];run_id:string; simulation_id:string; status:string; source_tick:number; snapshot_sha256?:string; provider?:string; model?:string;
 risk_evidence?:{provider:string;score:number|null;risk_decision:string;cached:boolean}|null;approval_reasons?:string[];human_approval?:{decision:string;rationale:string}|null;
 providers?:Record<string,string>; models?:Record<string,string>; error?:string|null; business_id?:string; buyer_id?:string; trace:Trace[];
 offers?:Offer[]; selected_offer?:Offer|null; settlement?:unknown;
 recommendation?:{strategy:string; amount_cents:number; rationale:string; bank_id:string|null;fork_id?:string};
 decision?:{approved:boolean; amount_cents:number; rationale:string}; business_accepted?:boolean|null};
export type Job = {job_id:string; simulation_id:string; kind:'central_bank'|'credit'|'procurement'; actor_id:string|null;
 status:string; error:string|null; report_url:string|null; report_status:string|null};
export type Fork = {fork_id:string; source_event_sequence?:number; source_tick:number; end_tick:number; snapshot_sha256:string;
 recommended_strategy:string; recommendation_basis:string; request?:{budget_cents:number; ticks:number};
 branches:{strategy:string; simulation_id:string; metrics:Metrics; timeline:Metrics[]}[]};
export type ComparisonEvidence = Omit<Fork,'branches'> & {source_simulation_id:string;source_event_sequence:number;seed:number;engine_version:string;
 request:{bank_id:string;budget_cents:number;ticks:number};cost_definition:string;tied_strategies:string[];
 branches:(Omit<Fork['branches'][number],'metrics'>&{metrics:Metrics&{fiscal_transfer_cost_cents:number;public_loan_outstanding_cents:number};audit:{balanced:boolean};delta_vs_no_intervention:Record<string,number>})[]};
export const API_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
export async function api<T>(path:string, body?:unknown):Promise<T> {
 const response = await fetch(API_URL+path, body === undefined ? undefined : {
  method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
 if (!response.ok) { const error = await response.json().catch(()=>null);
  throw new Error(typeof error?.detail === 'string' ? error.detail : `Request failed (${response.status})`); }
 return response.json();
}
export const requestId = () => crypto.randomUUID();
const pendingRequests = new Map<string,string>();
// Preserve an uncertain request's key until its acknowledgement is received.
export async function postOnce<T>(path:string,payload:Record<string,unknown>,field:'request_id'|'transaction_id'):Promise<T>{
 const key=path+JSON.stringify(payload),id=pendingRequests.get(key)??requestId();
 pendingRequests.set(key,id);
 const result=await api<T>(path,{...payload,[field]:id});
 pendingRequests.delete(key);
 return result;
}
export const currency = (cents:number) => new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', maximumFractionDigits:2}).format(cents/100);
