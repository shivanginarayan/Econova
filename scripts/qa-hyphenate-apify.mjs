// Records actual UI actions and checks the authoritative API. Never substitutes demo inference.
// --live makes real Nebius calls; app initialization may start bounded Apify refresh work.
import {chromium, expect as baseExpect} from '@playwright/test';
import {mkdir, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';

if (!process.argv.includes('--live')) throw new Error('Use --live to authorize the live track demonstration.');
const expect = baseExpect.configure({timeout:30000});
const api = process.env.ECONOMY_API_URL ?? 'http://127.0.0.1:8000';
const ui = process.env.ECONOMY_UI_URL ?? 'http://127.0.0.1:5173';
const output = resolve('artifacts', `hyphenate-apify-${new Date().toISOString().replaceAll(/[:.]/g,'-')}`);
await mkdir(output, {recursive:true});
async function request(path, body) {
 const response = await fetch(api + path, body === undefined ? {} : {
  method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body),
 });
 if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
 return response.json();
}
const provider = await request('/api/agents/status');
expect(provider.live_configured).toBe(true);
const initial = await request('/api/worlds', {scenario:'standard'});
const evidence = {recorded_at:new Date().toISOString(), mode:'live', checks:[], worlds:{},
 scope:'Public menu prices and statutory wage floor; synthetic entities, balances and scenario setup.',
 scenario_setup:'A simulated supplier expense deliberately exhausts Business 1 deposits to create a payroll gap. This is not observed real-world distress.',
 errors:[]};
const browser = await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
const context = await browser.newContext({viewport:{width:1512,height:982},
 recordVideo:{dir:output,size:{width:1512,height:982}}});
const page = await context.newPage();
const recordingStarted = Date.now();
evidence.screens = [];
page.on('pageerror', error => evidence.errors.push(error.message));
let manualCollections = 0;
page.on('request', request => {if(request.url().endsWith('/api/calibrations/collect')) manualCollections++;});
const check = name => {evidence.checks.push(name); console.log('PASS',name);};
const click = name => page.getByRole('button',{name,exact:true}).click();
const screenshot = async name => {
 // Give a human viewer time to read the actual UI state in the backup video.
 await page.waitForTimeout(1500);
 evidence.screens.push({name,seconds_into_recording:(Date.now()-recordingStarted)/1000});
 return page.screenshot({path:resolve(output,name+'.png')});
};
const current = async () => request(`/api/worlds/${await page.evaluate(()=>localStorage.getItem('economy-world'))}`);
const transactions = id => request(`/api/worlds/${id}/transactions?limit=1000`);
async function finishedJob(submission) {
 expect(['queued','running','completed']).toContain(submission.status);
 await expect.poll(async()=> (await request(`/api/agent-jobs/${submission.job_id}`)).status,
  {timeout:300000,intervals:[1000,2000]}).not.toMatch(/^(queued|running)$/);
 const job = await request(`/api/agent-jobs/${submission.job_id}`);
 if(job.status !== 'completed') {
  evidence.failed_job = job;
  if(job.report_url) evidence.failed_report = await request(job.report_url);
 }
 expect(job.status).toBe('completed');
 return job;
}
async function launchJob(button, suffix) {
 const pending = page.waitForResponse(r=>r.url().endsWith(suffix)&&r.request().method()==='POST');
 await click(button);
 const response = await pending;
 expect(response.status()).toBe(202);
 return finishedJob(await response.json());
}
try {
 await page.addInitScript(({id,origin})=>{
  if(location.origin===origin&&!localStorage.getItem('economy-world'))localStorage.setItem('economy-world',id);
 },{id:initial.simulation_id,origin:new URL(ui).origin});
 await page.goto(ui);
 await expect(page.getByText('Public data loaded automatically.',{exact:true})).toBeVisible({timeout:180000});
 expect(manualCollections).toBe(0);
 const created = page.waitForResponse(r=>r.url().endsWith('/api/worlds')&&r.request().method()==='POST');
 await click('Create World');
 const world = await (await created).json(), id = world.simulation_id;
 evidence.worlds.credit = id;
 expect(world.calibration.provider).toBe('apify');
 const data = await request(`/api/calibrations/${world.calibration.calibration_id}`);
 expect(data.sources.every(s=>s.actor_id&&s.run_id&&s.dataset_id&&s.observations.length)).toBe(true);
 for (const entity of world.entities) {
  if(entity.kind==='business') expect(data.price_cents).toContain(entity.price_cents);
  if(entity.kind==='household') expect(data.daily_wage_cents).toContain(entity.wage_cents);
 }
 evidence.apify = {calibration_id:data.calibration_id,sha256:world.calibration.sha256,
  collected_at:data.collected_at,price_count:data.price_cents.length,wage_count:data.daily_wage_cents.length,
  sources:data.sources.map(({category,actor_id,run_id,dataset_id,source_url})=>({category,actor_id,run_id,dataset_id,source_url}))};
 await expect.poll(()=>page.evaluate(()=>localStorage.getItem('economy-world'))).toBe(id);
 await page.locator('.public-data-panel summary').first().click();
 await page.getByText('Public data loaded automatically.',{exact:true}).scrollIntoViewIfNeeded();
 await screenshot('01-apify-public-inputs');
 check('Apify loads without collection clicks; actual observations set new-world prices and wages');

 const business = world.entities.find(e=>e.id==='business_1');
 await request(`/api/worlds/${id}/payments`,{transaction_id:`track-setup-${id}`,
  payer_id:'business_1',receiver_id:'business_2',amount_cents:business.balance_sheet.assets.deposit});
 await page.reload();
 await page.getByLabel('Agent mode').selectOption('live');
 await page.locator('.institution-list summary').click();
 await page.locator('.institution-list button').filter({hasText:/^Business 1business/}).click();
 await page.getByText('Credit safeguards',{exact:true}).click();
 await page.getByLabel('Credit human approval threshold').fill('0.01');
 const before = await transactions(id);
 const job = await launchJob('Review with safeguards','/credit-jobs');
 const report = await request(job.report_url);
 expect(Object.values(report.providers).every(value=>value==='nebius')).toBe(true);
 expect(report.status).toBe('needs_human_approval');
 expect(report.settlement).toBeNull();
 expect((await transactions(id)).transactions).toEqual(before.transactions);
 await expect(page.getByRole('heading',{name:'Human approval required'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Settle accepted credit',exact:true})).toHaveCount(0);
 await page.getByRole('heading',{name:'Human approval required'}).scrollIntoViewIfNeeded();
 await screenshot('02-live-agent-human-gate');
 check('Live Nemotron credit review escalates above threshold and changes no money');
 await page.getByLabel('Credit approval rationale').fill('Reviewed the payroll gap and recorded bank capital/liquidity checks. Approve this bounded simulated loan.');
 await click('Approve reviewed offer');
 await expect(page.getByRole('button',{name:'Settle accepted credit',exact:true})).toBeVisible();
 expect((await transactions(id)).transactions).toEqual(before.transactions);
 await page.waitForTimeout(1500);
 check('Human approval records a decision without settling');
 await click('Settle accepted credit');
 await expect(page.getByText('Settlement confirmed',{exact:true})).toBeVisible();
 const settled = await request(`/api/credit-runs/${report.run_id}`);
 expect(settled.status).toBe('settled');
 const after = await transactions(id);
 expect(after.transactions.length).toBe(before.transactions.length+1);
 expect((await request(`/api/worlds/${id}/audit`)).balanced).toBe(true);
 // Retry the exact UI transaction key: no second posting is allowed.
 await request(`/api/credit-runs/${report.run_id}/settle`,{transaction_id:`ui-${report.run_id}`});
 expect((await transactions(id)).transactions).toEqual(after.transactions);
 evidence.credit = {run_id:report.run_id,providers:report.providers,models:report.models,
  amount_cents:report.decision.amount_cents,trace:report.trace,approval_reasons:report.approval_reasons,
  human_approval:settled.human_approval,settlement:settled.settlement};
 await page.getByText('Settlement confirmed',{exact:true}).scrollIntoViewIfNeeded();
 await screenshot('03-separate-balanced-settlement');
 await page.reload();
 await expect(page.getByLabel('Agent job progress')).toContainText('settled');
 expect((await current()).calibration.sha256).toBe(world.calibration.sha256);
 check('Separate settlement posts once, audit balances, and reload preserves approval and frozen inputs');

 const crisis = await request('/api/worlds',{scenario:'credit_crunch',calibration_id:data.calibration_id});
 evidence.worlds.crisis = crisis.simulation_id;
 // Stop the old world's SSE/polling before changing the saved selection.
 // Otherwise a late refresh can save the old world between evaluate and reload.
 await page.goto('about:blank');
 await page.addInitScript(({id,origin})=>{
  if(location.origin===origin)localStorage.setItem('economy-world',id);
 },{id:crisis.simulation_id,origin:new URL(ui).origin});
 await page.goto(ui);
 await expect.poll(async()=>(await current()).simulation_id).toBe(crisis.simulation_id);
 await page.getByLabel('Agent mode').selectOption('live');
 await page.getByRole('button',{name:'Trigger Crisis',exact:false}).click();
 await click('Apply bank shock');
 await expect.poll(async()=> (await request(`/api/worlds/${crisis.simulation_id}/events?limit=1000`)).events.some(e=>e.event_type==='bank_asset_loss')).toBe(true);
 const shocked = await current();
 const crisisBefore = await transactions(crisis.simulation_id);
 await click('Fork Reality');
 await expect(page.locator('.live-branch-result')).toHaveCount(3);
 await page.getByLabel('Compare day').fill('12');
 await screenshot('04-calculated-futures');
 await click('Back to city');
 const policyJob = await launchJob('Test rescue policies','/agent-jobs');
 const policy = await request(policyJob.report_url);
 expect(policy.provider).toBe('nebius');
 expect(policy.status).toBe('completed');
 expect(policy.trace.some(t=>t.tool==='compare_interventions'&&t.status==='accepted')).toBe(true);
 expect((await request(`/api/worlds/${crisis.simulation_id}/events?limit=1000`)).events.some(e=>e.event_type==='agent_recommendation_applied')).toBe(false);
 expect((await current()).simulation_tick).toBe(shocked.simulation_tick);
 expect((await transactions(crisis.simulation_id)).transactions).toEqual(crisisBefore.transactions);
 expect((await request(`/api/worlds/${crisis.simulation_id}/audit`)).balanced).toBe(true);
 const comparison = await request(`/api/forks/${policy.recommendation.fork_id}`);
 evidence.policy = {run_id:policy.run_id,provider:policy.provider,model:policy.model,
  recommendation:policy.recommendation,trace:policy.trace,branches:comparison.branches.map(b=>({strategy:b.strategy,delta_vs_no_intervention:b.delta_vs_no_intervention,final:b.timeline.at(-1)}))};
 await expect(page.getByLabel('Agent job progress')).toContainText('completed');
 await page.getByText('Public tool trace',{exact:false}).click();
 await screenshot('05-live-policy-evidence');
 check('Live Nemotron tests calculated futures and recommends without mutating or applying to the source');
 await page.setViewportSize({width:390,height:844});
 expect(await page.locator('body').evaluate(e=>e.scrollWidth<=innerWidth)).toBe(true);
 await screenshot('06-mobile');
 expect(evidence.errors).toEqual([]);
 check('Mobile layout fits; no browser runtime errors');
 evidence.status = 'passed';
} catch(error) {
 evidence.status = 'failed';
 evidence.failure = error.message;
 await screenshot('failure').catch(()=>{});
 throw error;
} finally {
 await context.close();
 await browser.close();
 evidence.video = await page.video().path();
 await writeFile(resolve(output,'evidence.json'),JSON.stringify(evidence,null,2));
 console.log('Evidence:',output);
}
