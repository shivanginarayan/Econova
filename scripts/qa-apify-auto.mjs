// Uses saved real public data. No manual collection action and no model or payment calls.
import {chromium,expect} from '@playwright/test';
const api='http://127.0.0.1:8000';
const get=async path=>{const r=await fetch(api+path);if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();};
const response=await fetch(api+'/api/worlds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:'standard'})});
const initial=await response.json(),before=await get('/api/calibrations/collection/status');
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({viewport:{width:1512,height:982}}),page=await context.newPage();
let ensures=0,manual=0;const errors=[];
page.on('request',r=>{if(r.url().endsWith('/api/calibrations/ensure'))ensures++;if(r.url().endsWith('/api/calibrations/collect'))manual++;});
page.on('pageerror',e=>errors.push(e.message));
try{
 await page.addInitScript(id=>{if(!localStorage.getItem('economy-world'))localStorage.setItem('economy-world',id);},initial.simulation_id);
 await page.goto('http://127.0.0.1:5173');
 await expect(page.getByText('Public data loaded automatically.',{exact:true})).toBeVisible({timeout:20000});
 expect(ensures).toBe(1);expect(manual).toBe(0);
 const created=page.waitForResponse(r=>r.url().endsWith('/api/worlds')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Create World',exact:true}).click();const world=await (await created).json();
 expect(world.calibration.provider).toBe('apify');expect(world.calibration.price_sample_count).toBeGreaterThan(10);
 await expect.poll(()=>page.evaluate(()=>localStorage.getItem('economy-world'))).toBe(world.simulation_id);
 await page.reload();await expect(page.getByRole('button',{name:'Play',exact:true})).toBeVisible();
 await page.locator('.public-data-panel summary').first().click();
 await expect(page.getByText('Public data loaded automatically.',{exact:true})).toBeVisible({timeout:15000});
 expect(manual).toBe(0);expect(ensures).toBe(2);
 const after=await get('/api/calibrations/collection/status');expect(after.latest.job_id).toBe(before.latest.job_id);
 expect((await get(`/api/worlds/${world.simulation_id}`)).calibration.sha256).toBe(world.calibration.sha256);
 expect(errors).toEqual([]);
 console.log(JSON.stringify({automatic_on_open:true,no_collection_click:true,cached_data_ready:true,new_world_public_inputs:true,reload_no_new_crawl:true,frozen_world_preserved:true}));
}finally{await browser.close();}
