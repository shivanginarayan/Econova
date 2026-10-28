import {chromium,expect} from '@playwright/test';
import {writeFile} from 'node:fs/promises';
const response=await fetch('http://127.0.0.1:8000/api/worlds',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seed:42})});
if(!response.ok)throw new Error('QA world creation failed');
const world=await response.json();
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
try{
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(id=>localStorage.setItem('economy-world',id),world.simulation_id);
 await page.goto('http://127.0.0.1:5173');
 await page.getByText('Data, fraud & shared events',{exact:true}).click();
 await page.getByRole('button',{name:'Inspect economic services',exact:true}).click();
 const panel=page.locator('.sponsor-integrations');
 await expect(panel).toContainText('auditor_inspector');
 await expect(panel.locator('pre').first()).toContainText('"is_balanced": true');
 await expect(panel.locator('pre').first()).toContainText('"total_households": 40');
 const after=await(await fetch(`http://127.0.0.1:8000/api/worlds/${world.simulation_id}`)).json();
 expect(after.latest_event_sequence).toBe(world.latest_event_sequence);expect(errors).toEqual([]);
 await writeFile('artifacts/economic-services-ui.json',JSON.stringify({passed:true,source_unchanged:true,errors},null,2));
 console.log('PASS Economic services UI shows real ledger/welfare reports with no financial mutation or page errors');
}finally{await browser.close();}
