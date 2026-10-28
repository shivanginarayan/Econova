import {currency} from './api';
import type {ComparisonEvidence,World,Report,EconomyEvent} from './api';

const escape = (value:unknown) => String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const names:Record<string,string> = {no_intervention:'No intervention',bank_lending:'Emergency bank lending',household_cash:'Direct household support'};
const name = (strategy:string) => escape(names[strategy]??strategy);

export function comparisonReport(fork:ComparisonEvidence,world:World,events:EconomyEvent[],report?:Report|null){
 if(fork.source_simulation_id!==world.simulation_id)throw new Error('Comparison and source world do not match');
 const baseline=fork.branches.find(b=>b.strategy==='no_intervention');
 if(!baseline)throw new Error('Comparison is missing its no-intervention baseline');
 const calibration=world.calibration;
 const linked=report?.status==='completed'&&report?.snapshot_sha256===fork.snapshot_sha256&&report?.recommendation?.fork_id===fork.fork_id;
 const captured=events.filter(e=>e.sequence<=fork.source_event_sequence);
 const shockRows=captured.filter(e=>['bank_asset_loss','sourced_debt_stress_applied'].includes(e.event_type));
 const rows=fork.branches.map(branch=>{
  const m=branch.metrics,d=branch.delta_vs_no_intervention;
  return `<tr><th scope="row">${name(branch.strategy)}</th><td>${m.employed_households} / ${m.households}</td><td>${m.business_defaults}</td><td>${m.stressed_banks}</td><td>${escape(currency(m.public_support_disbursed_cents))}</td><td>${d.employed_households>0?'+':''}${d.employed_households}</td><td>${-d.business_defaults}</td><td>${branch.audit.balanced?'Balanced':'FAILED'}</td></tr>`;
 }).join('');
 const fundingRows=fork.branches.map(b=>`<tr><th scope="row">${name(b.strategy)}</th><td>${typeof b.metrics.fiscal_transfer_cost_cents==='number'?escape(currency(b.metrics.fiscal_transfer_cost_cents)):'Not recorded'}</td><td>${typeof b.metrics.public_loan_outstanding_cents==='number'?escape(currency(b.metrics.public_loan_outstanding_cents)):'Not recorded'}</td></tr>`).join('');
 const improved=fork.branches.some(b=>b.metrics.employed_households>baseline.metrics.employed_households||b.metrics.business_defaults<baseline.metrics.business_defaults);
 const sourceRows=calibration?.sources.map(source=>`<li><b>${escape(source.category??'Public observation')}</b>: ${escape(source.source_url)}<br>Actor ${escape(source.actor_id)} · run ${escape(source.run_id)} · dataset ${escape(source.dataset_id)}<br>${escape(source.scope)} ${escape(source.conversion)}</li>`).join('');
 return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Economy God Mode comparison report</title>
<style>body{font:16px/1.6 system-ui,sans-serif;color:#172b3a;max-width:1150px;margin:40px auto;padding:0 24px}h1,h2{line-height:1.2}h1{font-size:32px}h2{margin-top:32px;font-size:22px}.intro{font-size:18px}.note{padding:16px;background:#f2f5f6;border-left:4px solid #607b86}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:12px 10px;border-bottom:1px solid #d7dfe3;text-align:left}thead{background:#e8eff1}code,pre{font:13px/1.5 ui-monospace,monospace;overflow-wrap:anywhere;white-space:pre-wrap}li{margin-bottom:12px}footer{margin-top:35px;color:#526675}@media print{body{margin:0;max-width:none;font-size:11pt}.table-wrap{overflow:visible}tr,li{break-inside:avoid}}</style></head><body>
<h1>Economic stress-test comparison</h1><p class="intro">Three calculated futures from one saved snapshot. Prepared for a risk analyst reviewing a hypothetical financial shock.</p>
<p class="note">This is a synthetic experiment, not a calibrated forecast or financial advice. Results apply to this seed, assumptions and time horizon. Exporting this report changes no balances.</p>
<h2>Experiment</h2><p>World <code>${escape(fork.source_simulation_id)}</code><br>Comparison <code>${escape(fork.fork_id)}</code><br>Starting scenario ${escape(world.config.scenario)} · seed ${fork.seed} · engine ${escape(fork.engine_version)}<br>Day ${fork.source_tick} to day ${fork.end_tick} · target bank ${escape(fork.request.bank_id)} · support budget per intervention ${escape(currency(fork.request.budget_cents))}<br>Source snapshot <code>${escape(fork.snapshot_sha256)}</code></p>
<h2>Final outcomes</h2><div class="table-wrap"><table aria-label="Final outcomes"><thead><tr><th>Strategy</th><th>Employed households</th><th>Business defaults</th><th>Stressed banks</th><th>Gross support</th><th>Additional jobs vs baseline</th><th>Defaults avoided vs baseline</th><th>Ledger audit</th></tr></thead><tbody>${rows}</tbody></table></div>
<p>${improved?'At least one intervention improves final employment or business defaults relative to this baseline.':'Neither tested intervention improves final employment or business defaults relative to this baseline.'} Negative defaults avoided means additional defaults. These are calculated simulation differences, not measured customer savings.</p>
<p>${escape(fork.cost_definition)}</p><div class="table-wrap"><table aria-label="Funding breakdown"><thead><tr><th>Strategy</th><th>Fiscal transfers</th><th>Outstanding public loans</th></tr></thead><tbody>${fundingRows}</tbody></table></div><h2>Ranking and agent decision</h2><p>Rule-based ranking: <b>${name(fork.recommended_strategy)}</b>. ${escape(fork.recommendation_basis)}</p>
${linked?`<p>Separate agent report <code>${escape(report?.run_id)}</code> · ${escape(report?.provider??Object.values(report?.providers??{}).join(', '))} · ${escape(report?.model??Object.values(report?.models??{}).join(', '))}<br>Recommendation: ${name(report!.recommendation!.strategy)} · ${escape(currency(report!.recommendation!.amount_cents))}<br>${escape(report!.recommendation!.rationale)}</p>`:'<p>No AI recommendation is linked to this exact comparison in this export. The rule-based ranking is not an AI decision.</p>'}
<h2>Inputs and assumptions</h2>${calibration?`<p>Frozen public observations: ${escape(calibration.calibration_id)} · collected ${escape(calibration.collected_at)}<br>${calibration.price_sample_count} menu-price options · ${calibration.wage_sample_count} statutory wage reference<br>Dataset checksum <code>${escape(calibration.sha256)}</code></p><ul>${sourceRows}</ul><p>One cafe and the official general minimum wage are limited references. The wage floor is not average pay; the daily conversion assumes eight hours of work. Public observations do not calibrate the entire economy.</p>`:'<p>Explicit seeded synthetic price and wage inputs. No collected public prices or wages are claimed for this world.</p>'}
<p>Households, businesses, bank balance sheets, employment links, consumption budgets, lending constraints and production rules are simulated. Loan interest, taxes and rent are not modeled. Forks use matched random streams and leave the source unchanged.</p>
<h2>Recorded shock context</h2>${shockRows.length?shockRows.map(e=>`<p>Day ${e.simulation_tick} · ${escape(e.event_type)} · ${escape(e.agent_id)} · ${e.amount_cents===null?'':escape(currency(e.amount_cents))}</p><pre>${escape(JSON.stringify(e.details,null,2))}</pre>`).join(''):'<p>No shock event was found in the retrieved source-event window. Do not infer that the snapshot has no prior shocks.</p>'}
${fork.source_event_sequence>Math.max(0,...captured.map(e=>e.sequence))?'<p>The retrieved event window is incomplete; consult the saved source history for full shock provenance.</p>':''}
<footer>Decision support prototype. Human approval and financial settlement are separate. This report does not authorize intervention or establish that a policy is optimal.</footer></body></html>`;
}

export function downloadComparison(html:string,forkId:string){
 const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));
 const link=document.createElement('a');link.href=url;link.download=`economy-comparison-${forkId.replace(/[^a-zA-Z0-9_-]/g,'')}.html`;
 document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
