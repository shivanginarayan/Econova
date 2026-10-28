import {schema,table,t,SenderError} from 'spacetimedb/server';

const publisher=table({name:'publisher'},{identity:t.identity().primaryKey()});
const economy_event=table({name:'economy_event',public:true},{
 key:t.string().primaryKey(),simulation_id:t.string(),sequence:t.u32(),tick:t.u32(),
 event_type:t.string(),actor_id:t.string(),counterparty_id:t.string(),amount_cents:t.f64(),
});
const control_room=table({name:'control_room',public:true},{simulation_id:t.string().primaryKey(),snapshot:t.string(),tick:t.u32(),banks:t.string()});
const participant=table({name:'participant',public:true},{key:t.string().primaryKey(),simulation_id:t.string(),identity:t.identity(),name:t.string()});
const proposal=table({name:'proposal',public:true},{id:t.string().primaryKey(),simulation_id:t.string(),snapshot:t.string(),tick:t.u32(),bank_id:t.string(),loss_bps:t.u32(),author:t.identity(),approver:t.string(),status:t.string(),transaction_id:t.string()});
const db=schema({publisher,economy_event,control_room,participant,proposal});
export default db;
export const init=db.init(ctx=>{ctx.db.publisher.insert({identity:ctx.sender});});
export const publish_context=db.reducer({simulation_id:t.string(),snapshot:t.string(),tick:t.u32(),banks:t.string()},(ctx,row)=>{
 if(!ctx.db.publisher.identity.find(ctx.sender))throw new SenderError('Publisher required');
 if(!/^[-\w]{1,128}$/.test(row.simulation_id)||!/^\w{64}$/.test(row.snapshot))throw new SenderError('Invalid context');
 const banks=JSON.parse(row.banks);if(!Array.isArray(banks)||banks.length>10||!banks.every(b=>/^bank_\d+$/.test(b)))throw new SenderError('Invalid banks');
 if(ctx.db.control_room.simulation_id.find(row.simulation_id))ctx.db.control_room.simulation_id.update(row);else ctx.db.control_room.insert(row);
});
export const join_room=db.reducer({simulation_id:t.string(),name:t.string()},(ctx,{simulation_id,name})=>{
 if(!ctx.db.control_room.simulation_id.find(simulation_id))throw new SenderError('Open the room first');
 if(!name.trim()||name.length>40)throw new SenderError('Choose a name up to 40 characters');
 const row={key:`${simulation_id}:${ctx.sender.toHexString()}`,simulation_id,identity:ctx.sender,name:name.trim()};
 if(ctx.db.participant.key.find(row.key))ctx.db.participant.key.update(row);else ctx.db.participant.insert(row);
});
export const disconnected=db.clientDisconnected(ctx=>{
 for(const p of ctx.db.participant.iter())if(p.identity.toHexString()===ctx.sender.toHexString())ctx.db.participant.key.delete(p.key);
});
export const propose_shock=db.reducer({id:t.string(),simulation_id:t.string(),bank_id:t.string(),loss_bps:t.u32()},(ctx,args)=>{
 const room=ctx.db.control_room.simulation_id.find(args.simulation_id);
 if(!room||!ctx.db.participant.key.find(`${args.simulation_id}:${ctx.sender.toHexString()}`))throw new SenderError('Join the room first');
 if(!/^[a-zA-Z0-9_-]{1,64}$/.test(args.id)||!JSON.parse(room.banks).includes(args.bank_id)||args.loss_bps<1||args.loss_bps>10000)throw new SenderError('Invalid shock');
 const previous=ctx.db.proposal.id.find(args.id);
 if(previous){if(previous.author.toHexString()===ctx.sender.toHexString()&&previous.simulation_id===args.simulation_id&&previous.bank_id===args.bank_id&&previous.loss_bps===args.loss_bps)return;throw new SenderError('Conflicting proposal ID');}
 ctx.db.proposal.insert({...args,snapshot:room.snapshot,tick:room.tick,author:ctx.sender,approver:'',status:'pending',transaction_id:''});
});
export const review_proposal=db.reducer({id:t.string(),approve:t.bool()},(ctx,{id,approve})=>{
 const p=ctx.db.proposal.id.find(id);if(!p)throw new SenderError('Unknown proposal');
 if(!ctx.db.participant.key.find(`${p.simulation_id}:${ctx.sender.toHexString()}`))throw new SenderError('Join the room first');
 if(p.author.toHexString()===ctx.sender.toHexString())throw new SenderError('A different participant must review');
 if(p.status!=='pending')throw new SenderError('Proposal already reviewed');
 ctx.db.proposal.id.update({...p,approver:ctx.sender.toHexString(),status:approve?'approved':'rejected'});
});
export const complete_proposal=db.reducer({id:t.string(),transaction_id:t.string()},(ctx,{id,transaction_id})=>{
 if(!ctx.db.publisher.identity.find(ctx.sender))throw new SenderError('Publisher required');
 const p=ctx.db.proposal.id.find(id);if(!p||!['approved','executed'].includes(p.status)||transaction_id!==`room_${id}`)throw new SenderError('Invalid execution receipt');
 ctx.db.proposal.id.update({...p,status:'executed',transaction_id});
});
export const ingest_events=db.reducer({batch:t.string()},(ctx,{batch})=>{
 if(!ctx.db.publisher.identity.find(ctx.sender))throw new SenderError('Only the publishing identity may mirror events');
 if(batch.length>100000)throw new SenderError('Batch too large');
 const rows=JSON.parse(batch);
 if(!Array.isArray(rows)||rows.length>100)throw new SenderError('Expected at most 100 events');
 for(const row of rows){
  if(typeof row.simulation_id!=='string'||!/^[-\w]{1,128}$/.test(row.simulation_id)||
    !Number.isSafeInteger(row.sequence)||row.sequence<1||row.sequence>4294967295||
    !Number.isSafeInteger(row.tick)||row.tick<0||row.tick>4294967295||
    row.key!==`${row.simulation_id}:${row.sequence}`||!Number.isSafeInteger(row.amount_cents)||
    !['event_type','actor_id','counterparty_id'].every(k=>typeof row[k]==='string'&&row[k].length<=128))throw new SenderError('Invalid event');
  const previous=ctx.db.economy_event.key.find(row.key);
  if(previous){
   if(['simulation_id','sequence','tick','event_type','actor_id','counterparty_id','amount_cents'].some(k=>previous[k as keyof typeof previous]!==row[k]))throw new SenderError('Conflicting replay');
  }else ctx.db.economy_event.insert(row);
 }
});
