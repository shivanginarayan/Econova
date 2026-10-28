// Live, bounded Apify collection through the UI. Creates fresh test worlds, never edits the user's world.
import {chromium,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
const api='http://127.0.0.1:8000',ui='http://127.0.0.1:5173';
const get=async path=>{const r=await fetch(api+path);if(!r.ok)throw new Error(`API ${r.status}`);return r.json();};
const post=async(path,body)=>{const r=await fetch(api+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw new Error(`API ${r.status}`);return r.json();};
const initial=await post('/api/worlds',{scenario:'standard'});
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1512,height:982}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.addInitScript(id=>{if(!localStorage.getItem('economy-world'))localStorage.setItem('economy-world',id);},initial.simulation_id);
 await page.goto(ui);const panel=page.locator('.public-data-panel');
 await expect(panel.getByText('This existing world has frozen seeded inputs.',{exact:false})).toBeVisible();
 await panel.getByText('Refresh options',{exact:true}).click();
 const submitted=page.waitForResponse(r=>r.url().endsWith('/api/calibrations/collect')&&r.request().method()==='POST');
 await panel.getByRole('button',{name:'Refresh public inputs now',exact:true}).click();
 const response=await submitted;expect(response.status()).toBe(202);const queued=await response.json();
 await expect.poll(async()=>(await get(`/api/calibrations/collection/${queued.job_id}`)).status,{timeout:180000,intervals:[2000]}).toBe('completed');
 const job=await get(`/api/calibrations/collection/${queued.job_id}`),data=await get(`/api/calibrations/${job.calibration_id}`);
 expect(data.price_cents.length).toBeGreaterThan(10);expect(data.daily_wage_cents).toHaveLength(1);
 expect(data.sources.every(s=>s.actor_id&&s.run_id&&s.dataset_id&&s.observations.length)).toBe(true);
 expect(data.sources.find(s=>s.category==='wages').observations[0].kind).toBe('statutory_wage_floor_not_average_pay');
 await expect(panel).toContainText('Collection: completed',{timeout:15000});
 const created=page.waitForResponse(r=>r.url().endsWith('/api/worlds')&&r.request().method()==='POST');
 await panel.getByRole('button',{name:'Create new world with public inputs',exact:true}).click();
 const world=await (await created).json();expect(world.calibration.calibration_id).toBe(job.calibration_id);
 for(const entity of world.entities){if(entity.kind==='business')expect(data.price_cents).toContain(entity.price_cents);if(entity.kind==='household')expect(data.daily_wage_cents).toContain(entity.wage_cents);}
 expect((await get(`/api/worlds/${initial.simulation_id}`)).entities).toEqual(initial.entities);
 await expect.poll(()=>page.evaluate(()=>localStorage.getItem('economy-world'))).toBe(world.simulation_id);
 await page.reload();await page.locator('.public-data-panel summary').first().click();
 await expect(page.locator('.public-data-panel')).toContainText('frozen public price and wage references');
 expect((await get(`/api/worlds/${world.simulation_id}`)).calibration.sha256).toBe(world.calibration.sha256);
 await page.getByRole('button',{name:'Step one day',exact:true}).click();
 await expect(page.locator('.month-label')).toContainText('01');
 expect((await get(`/api/worlds/${world.simulation_id}/audit`)).balanced).toBe(true);
 // The default Create World control also selects collected inputs, never silent synthetic substitution.
 const next=page.waitForResponse(r=>r.url().endsWith('/api/worlds')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Create World',exact:true}).click();expect((await (await next).json()).calibration.provider).toBe('apify');
 await page.locator('.public-data-panel summary').first().click();
 await page.setViewportSize({width:390,height:844});await page.locator('.public-data-panel').scrollIntoViewIfNeeded();
 await mkdir('artifacts',{recursive:true});await page.screenshot({path:'artifacts/apify-mobile.png'});
 expect(await page.locator('.app').evaluate(e=>e.scrollLeft)).toBe(0);expect(errors).toEqual([]);
 console.log(JSON.stringify({live_collection:true,price_count:job.price_count,wage_reference_count:job.wage_count,runs:job.runs,actual_inputs_used:true,source_world_unchanged:true,default_public_inputs:true,reload_frozen:true,step_balanced:true,mobile:true}));
}finally{await browser.close();}
