import {useEffect,useState} from 'react';
import {useStore,disconnect} from './state/store';
import {initializePublicInputs} from './state/publicInputs';
import InvestigationWorkspace from './ui/InvestigationWorkspace';
import './styles/integration.css';
import './styles/investigation.css';
export default function ConnectedApp(){
 const [ready,setReady]=useState(false);
 useEffect(()=>{
  let mounted=true;
  void initializePublicInputs();
  void useStore.getState().restore().catch(()=>{useStore.getState().set({error:'The saved investigation could not be restored. You can create a new economy.'});}).finally(()=>{if(mounted)setReady(true);});
  return()=>{mounted=false;disconnect();};
 },[]);
 if(!ready)return <div className="startup-screen"><a href="#" aria-label="Parallax">◈ <b>Parallax</b></a><div role="status" aria-live="polite"><span className="startup-indicator" aria-hidden="true"/><h1>Opening your workspace…</h1><p>Checking for a saved investigation.</p></div></div>;
 return <InvestigationWorkspace/>;
}
