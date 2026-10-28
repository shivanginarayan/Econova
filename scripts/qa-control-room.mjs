import {chromium,expect} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
const api='http://127.0.0.1:8000',ui='http://127.0.0.1:5173';
const post=async(path,body={})=>{const r=await fetch(api+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw new Error(`${path}: ${r.status} ${await r.text()}`);return r.json();};
const world=await post('/api/worlds',{seed:42,scenario:'credit_crunch'}),sid=world.simulation_id,base=`/api/worlds/${sid}`;
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-unsafe-swiftshader']});
const errors=[],checks=[];
const a=await browser.newContext({viewport:{width:1512,height:982}}),b=await browser.newContext({viewport:{width:1512,height:982}});
const alice=await a.newPage(),bob=await b.newPage();
for(const page of [alice,bob])page.on('pageerror',e=>errors.push(e.message));
try{
 for(const [page,name] of [[alice,'Alice'],[bob,'Bob']]){
  await page.goto(`${ui}/?room=${sid}`);
  await page.getByText('Data, fraud & shared events',{exact:true}).click();
  await expect(page.getByRole('region',{name:'Shared economy control room'})).toContainText('Live via SpacetimeDB',{timeout:60000});
  await page.getByLabel('Room participant name',{exact:true}).fill(name);
  await page.getByRole('button',{name:'Join room',exact:true}).click();
  await expect(page.getByTestId('room-participants')).toContainText(name);
 }
 await expect(alice.getByTestId('room-participants')).toContainText('Bob');
 await expect(bob.getByTestId('room-participants')).toContainText('Alice');checks.push('Real two-session presence and subscriptions');
 await alice.getByRole('button',{name:'Propose bank shock',exact:true}).click();
 const first=alice.locator('[data-proposal-id]').first();await expect(first).toContainText('pending');
 const pid=await first.getAttribute('data-proposal-id');
 await expect(first.getByRole('button',{name:'Approve proposal',exact:true})).toBeDisabled();
 const premature=await fetch(api+base+`/control-room/${pid}/execute`,{method:'POST'});expect(premature.status).toBe(409);
 await expect(bob.locator(`[data-proposal-id="${pid}"]`)).toContainText('pending');
 await bob.locator(`[data-proposal-id="${pid}"]`).getByRole('button',{name:'Approve proposal',exact:true}).click();
 await expect(first).toContainText('approved');
 const unchanged=await (await fetch(api+base)).json();expect(unchanged.latest_event_sequence).toBe(world.latest_event_sequence);checks.push('Second identity review; approval moves no money; pending execution rejected');
 await first.getByRole('button',{name:'Execute approved shock',exact:true}).click();
 await expect(first).toContainText('executed');
 await expect(bob.getByTestId('room-events')).toContainText('bank_asset_loss',{timeout:20000});
 const after=await (await fetch(api+base)).json();await post(base+`/control-room/${pid}/execute`);
 const replay=await (await fetch(api+base)).json();expect(replay.latest_event_sequence).toBe(after.latest_event_sequence);expect(replay.metrics).toEqual(after.metrics);
 const audit=await (await fetch(api+base+'/audit')).json();expect(audit.balanced).toBe(true);checks.push('Exactly-once execution, real event subscription and balanced ledger');
 await alice.getByRole('button',{name:'Refresh proposal snapshot',exact:true}).click();
 await alice.getByLabel('Room loss percent',{exact:true}).fill('10');
 await alice.getByRole('button',{name:'Propose bank shock',exact:true}).click();
 await expect(alice.locator('[data-proposal-id]')).toHaveCount(2);
 const stale=alice.locator('[data-proposal-id]').filter({hasText:'pending'});const staleId=await stale.getAttribute('data-proposal-id');
 await bob.locator(`[data-proposal-id="${staleId}"]`).getByRole('button',{name:'Approve proposal',exact:true}).click();
 await post(base+'/step',{ticks:1});
 const rejected=await fetch(api+base+`/control-room/${staleId}/execute`,{method:'POST'});expect(rejected.status).toBe(409);checks.push('Stale snapshot rejected after real financial state change');
 await bob.reload();await bob.getByText('Data, fraud & shared events',{exact:true}).click();
 await expect(bob.locator(`[data-proposal-id="${pid}"]`)).toContainText('executed',{timeout:30000});checks.push('Persistent proposals and receipts after reload');
 const authorization=await alice.evaluate(async sid=>{
  const {DbConnection}=await import('/src/data/spacetime/index.ts');
  const c=await new Promise((resolve,reject)=>DbConnection.builder().withUri('http://127.0.0.1:3000').withDatabaseName('economy-god-mode').onConnect(resolve).onConnectError((_,e)=>reject(e)).build());
  const rejected=async fn=>{try{await fn();return false;}catch{return true;}};
  try{
   await c.reducers.joinRoom({simulationId:sid,name:'Reducer authorization check'});
   const id=crypto.randomUUID();await c.reducers.proposeShock({id,simulationId:sid,bankId:'bank_1',lossBps:1000});
   return {
    selfApproval:await rejected(()=>c.reducers.reviewProposal({id,approve:true})),
    forgedReceipt:await rejected(()=>c.reducers.completeProposal({id,transactionId:'room_'+id})),
    forgedSnapshot:await rejected(()=>c.reducers.publishContext({simulationId:sid,snapshot:'0'.repeat(64),tick:0,banks:'[]'})),
    invalidBank:await rejected(()=>c.reducers.proposeShock({id:crypto.randomUUID(),simulationId:sid,bankId:'bank_999',lossBps:1000})),
   };
  }finally{c.disconnect();}
 },sid);
 expect(Object.values(authorization).every(Boolean)).toBe(true);checks.push('Server reducers reject self approval, forged receipts/context and invalid banks');
 await mkdir('artifacts/control-room',{recursive:true});await alice.locator('.control-room').screenshot({path:'artifacts/control-room/alice.png'});
 await bob.setViewportSize({width:390,height:844});await bob.locator('.control-room').screenshot({path:'artifacts/control-room/mobile.png'});
 expect(errors).toEqual([]);checks.push('No browser exceptions');
 await writeFile('artifacts/control-room/evidence.json',JSON.stringify({sid,checks,audit,errors},null,2));console.log(JSON.stringify({passed:true,checks},null,2));
}finally{await browser.close();}

