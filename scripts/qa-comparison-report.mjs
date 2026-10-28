// Checks the actual downloaded analyst report. No model calls, payments or manual crawls.
import {chromium,expect} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const api='http://127.0.0.1:8000',ui='http://127.0.0.1:5173';
async function request(path,body){const r=await fetch(api+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);return r.json();}
const calibrations=await request('/api/calibrations');
expect(calibrations.length).toBeGreaterThan(0);
calibrations.sort((a,b)=>b.collected_at.localeCompare(a.collected_at));
const output=resolve('artifacts/microsoft-technical-evidence');await mkdir(output,{recursive:true});
const checks=[];
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
try{
 for(const mode of ['public','seeded']){
  const world=await request('/api/worlds',{scenario:'credit_crunch',seed:42,...(mode==='public'?{calibration_id:calibrations[0].calibration_id}:{})});
  const base=`/api/worlds/${world.simulation_id}`;
  await request(base+'/shocks',{transaction_id:'export-scenario',bank_id:'bank_1',loss_bps:4000});
  const source=await request(base),context=await browser.newContext({viewport:{width:1512,height:982},acceptDownloads:true});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(({id,origin})=>{if(location.origin===origin)localStorage.setItem('economy-world',id);},{id:world.simulation_id,origin:new URL(ui).origin});
  await page.goto(ui);
  const pending=page.waitForResponse(r=>r.url().endsWith('/forks')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Fork Reality',exact:true}).click();
  const fork=await (await pending).json();
  await expect(page.locator('.live-branch-result')).toHaveCount(3);
  const downloadPromise=page.waitForEvent('download');
  await page.getByRole('button',{name:'Download comparison report',exact:true}).click();
  const download=await downloadPromise;
  const path=resolve(output,`${mode}-comparison.html`);await download.saveAs(path);
  expect(await request(base)).toEqual(source);
  const report=await context.newPage();await report.goto(pathToFileURL(path).href);
  await expect(report.getByRole('heading',{name:'Economic stress-test comparison'})).toBeVisible();
  await expect(report.getByRole('table',{name:'Final outcomes'}).locator('tbody tr')).toHaveCount(3);
  await expect(report.getByRole('table',{name:'Funding breakdown'}).locator('tbody tr')).toHaveCount(3);
  await expect(report.locator('body')).toContainText(fork.snapshot_sha256);
  await expect(report.locator('body')).toContainText('No AI recommendation is linked');
  await expect(report.locator('body')).toContainText('$10,000.00');
  await expect(report.locator('body')).toContainText(mode==='public'?'Frozen public observations':'Explicit seeded synthetic');
  if(mode==='public')await expect(report.locator('body')).toContainText('Neither tested intervention improves final employment');
  for(const [index,branch] of fork.branches.entries()){
   await expect(report.getByRole('table',{name:'Final outcomes'}).locator('tbody tr').nth(index)).toContainText(`${branch.metrics.employed_households} / ${branch.metrics.households}`);
   for(const field of ['fiscal_transfer_cost_cents','public_loan_outstanding_cents'])await expect(report.getByRole('table',{name:'Funding breakdown'}).locator('tbody tr').nth(index)).toContainText(new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(branch.metrics[field]/100));
  }
  await report.screenshot({path:resolve(output,`${mode}-report.png`),fullPage:true});
  await page.screenshot({path:resolve(output,`${mode}-export-control.png`)});
  await page.setViewportSize({width:390,height:844});
  expect(await page.locator('body').evaluate(e=>e.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:resolve(output,`${mode}-mobile.png`)});
  expect(errors).toEqual([]);
  checks.push({mode,world:world.simulation_id,fork_id:fork.fork_id,download:path,actual_outcomes:true,source_unchanged:true,mobile:true,no_browser_errors:true});
  await context.close();
 }
 await writeFile(resolve(output,'verification.json'),JSON.stringify({status:'passed',checks},null,2));
 console.log(JSON.stringify({status:'passed',checks},null,2));
}finally{await browser.close();}
