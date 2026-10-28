import {useEffect,useState} from 'react';
import {DbConnection} from '../data/spacetime';
import type {Participant,Proposal,EconomyEvent} from '../data/spacetime/types';
import {api} from '../data/api';
import {useStore} from '../state/store';

export default function ControlRoom(){
 const world=useStore(s=>s.world),refresh=useStore(s=>s.refresh),id=world?.simulation_id;
 const [enabled,setEnabled]=useState(new URLSearchParams(location.search).has('room'));
 const [conn,setConn]=useState<DbConnection|null>(null),[identity,setIdentity]=useState('');
 const [people,setPeople]=useState<Participant[]>([]),[proposals,setProposals]=useState<Proposal[]>([]),[events,setEvents]=useState<EconomyEvent[]>([]);
 const [status,setStatus]=useState('Disconnected'),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [name,setName]=useState('Analyst'),[bank,setBank]=useState('bank_1'),[loss,setLoss]=useState(40);
 useEffect(()=>{
  if(!enabled||!id)return;
  let stopped=false,connection:DbConnection|undefined;
  setError('');setStatus('Connecting');setPeople([]);setProposals([]);setEvents([]);setConn(null);
  void api<{uri:string;database:string}>(`/api/worlds/${id}/control-room`,{}).then(config=>{
   if(stopped)return;
   const key=`economy-room:${config.uri}:${config.database}`;
   const update=()=>{
    if(stopped||!connection)return;
    setPeople([...connection.db.participant.iter()]);setProposals([...connection.db.proposal.iter()]);
    setEvents([...connection.db.economyEvent.iter()].sort((a,b)=>a.sequence-b.sequence).slice(-10));
   };
   connection=DbConnection.builder().withUri(config.uri).withDatabaseName(config.database)
    .withToken(sessionStorage.getItem(key)??undefined).withAutomaticReconnect()
    .onConnect((c,who,token)=>{
     if(stopped){c.disconnect();return;}
     sessionStorage.setItem(key,token);setIdentity(who.toHexString());setConn(c);
     c.db.participant.onInsert(update);c.db.participant.onUpdate(update);c.db.participant.onDelete(update);
     c.db.proposal.onInsert(update);c.db.proposal.onUpdate(update);
     c.db.economyEvent.onInsert(update);
     c.subscriptionBuilder().onApplied(()=>{setStatus('Live via SpacetimeDB');update();})
      .onError(()=>setError('Room subscription failed'))
      .subscribe(['participant','proposal','economy_event','control_room'].map(table=>`SELECT * FROM ${table} WHERE simulation_id = '${id}'`));
    }).onAutomaticReconnect((c,who,token)=>{if(!stopped){sessionStorage.setItem(key,token);setIdentity(who.toHexString());setConn(c);setStatus('Live via SpacetimeDB');}})
    .onConnectError(()=>{if(!stopped)setError('SpacetimeDB connection failed');})
    .onDisconnect(()=>{if(!stopped){setStatus('Disconnected');setConn(null);}}).build();
  }).catch(e=>{if(!stopped)setError(String(e));});
  return()=>{stopped=true;connection?.disconnect();};
 },[enabled,id]);
 const run=async(fn:()=>Promise<unknown>)=>{if(busy)return;setBusy(true);setError('');try{await fn();}catch(e){setError(e instanceof Error?e.message:String(e));}finally{setBusy(false);}};
 if(!id)return null;
 const joined=people.some(p=>p.identity.toHexString()===identity);
 return <section className="control-room" aria-label="Shared economy control room">
  <h3>Shared economy control room</h3>
  <p>Propose a hypothetical bank loss for another participant to review. Approval moves no money; execution is separate. Browser identities are not verified human roles.</p>
  {!enabled?<button onClick={()=>setEnabled(true)}>Open shared control room</button>:<>
   <p role="status">{status} · {people.length} participants</p>
   <label>Share room<input aria-label="Share room" readOnly value={`${location.origin}${location.pathname}?room=${encodeURIComponent(id)}`} onFocus={e=>e.target.select()}/></label>
   <label>Your name<input aria-label="Room participant name" maxLength={40} value={name} onChange={e=>setName(e.target.value)}/></label>
   <button disabled={!conn||busy} onClick={()=>void run(()=>conn!.reducers.joinRoom({simulationId:id,name}))}>{joined?'Update participant name':'Join room'}</button>
   <p data-testid="room-participants">{people.map(p=>p.name).join(', ')||'No participants yet'}</p>
   <label>Proposed bank<select aria-label="Room bank" value={bank} onChange={e=>setBank(e.target.value)}>{world?.entities.filter(e=>e.kind==='bank').map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label>
   <label>Hypothetical asset loss (%)<input aria-label="Room loss percent" type="number" min={0.01} max={100} step={0.01} value={loss} onChange={e=>setLoss(Number(e.target.value))}/></label>
   <button disabled={!conn||!joined||busy||loss<=0||loss>100} onClick={()=>void run(()=>conn!.reducers.proposeShock({id:crypto.randomUUID(),simulationId:id,bankId:bank,lossBps:Math.round(loss*100)}))}>Propose bank shock</button>
   <button disabled={!conn||busy} onClick={()=>void run(()=>api(`/api/worlds/${id}/control-room`,{}))}>Refresh proposal snapshot</button>
   <p>Pause before proposing. If financial state changes, refresh the snapshot and create a new proposal.</p>
   <div data-testid="room-proposals">{proposals.map(p=><article key={p.id} data-proposal-id={p.id}>
    <b>{p.bankId} · {p.lossBps/100}% hypothetical loss · {p.status}</b><p>Day {p.tick} · snapshot {p.snapshot.slice(0,12)}</p>
    {p.status==='pending'&&<><button disabled={!joined||p.author.toHexString()===identity||busy} onClick={()=>void run(()=>conn!.reducers.reviewProposal({id:p.id,approve:true}))}>Approve proposal</button>
    <button disabled={!joined||p.author.toHexString()===identity||busy} onClick={()=>void run(()=>conn!.reducers.reviewProposal({id:p.id,approve:false}))}>Reject proposal</button></>}
    {p.status==='approved'&&<button disabled={!joined||busy} onClick={()=>void run(async()=>{await api(`/api/worlds/${id}/control-room/${p.id}/execute`,{});await refresh();})}>Execute approved shock</button>}
    {p.transactionId&&<p>Receipt: {p.transactionId}</p>}
   </article>)}</div>
   <h4>Live shared financial events</h4><ul data-testid="room-events">{events.map(e=><li key={e.key}>#{e.sequence} · day {e.tick} · {e.eventType} · {e.actorId}</li>)}</ul>
  </>}{error&&<p role="alert">{error}</p>}
 </section>;
}
