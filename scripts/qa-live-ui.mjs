import {chromium,expect as baseExpect} from '@playwright/test';
import fs from 'node:fs';
const expect=baseExpect.configure({timeout:90000});
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({baseURL:'http://127.0.0.1:5173',viewport:{width:1512,height:982}});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('/');await page.getByRole('button',{name:'Start in the United States',exact:true}).click();
 await page.getByRole('button',{name:'San Francisco',exact:true}).click();await page.getByLabel('Starting scenario').selectOption('standard');
 await page.getByRole('button',{name:'Create and explore economy',exact:true}).click();await expect(page.getByLabel('Agent mode')).toHaveValue('live');
 await expect(page.getByText('Configured model:',{exact:false})).toContainText('NVIDIA-Nemotron-3-Nano');
 await page.getByRole('button',{name:'Test rescue policies',exact:true}).click();await expect(page.getByLabel('Agent job progress')).toContainText('completed');
 await expect(page.getByLabel('Agent job progress')).toContainText('nebius');
 const id=await page.evaluate(()=>localStorage.getItem('economy-world'));
 const jobs=await (await page.request.get(`/api/worlds/${id}/agent-jobs`)).json();
 const report=await (await page.request.get(jobs[0].report_url)).json();
 expect(report.provider).toBe('nebius');expect(report.request.mode).toBe('live');expect(report.status).toBe('completed');expect(report.trace.length).toBeGreaterThanOrEqual(3);
 expect(report.recommendation.rationale).not.toMatch(/\$\s*\d/);
 const position=await page.locator('.app').evaluate(e=>({left:e.scrollLeft,top:e.scrollTop}));expect(position).toEqual({left:0,top:0});
 fs.mkdirSync('artifacts',{recursive:true});await page.screenshot({path:'artifacts/live-nemotron-ui.png'});
 expect(errors).toEqual([]);console.log(JSON.stringify({live_ui_verified:true,model:report.model,provider:report.provider,tool_calls:report.trace.length,source_tick:report.source_tick}));
}finally{await context.close();await browser.close();}
