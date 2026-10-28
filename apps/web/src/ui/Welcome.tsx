import {ArrowRight,Search,ShieldCheck,Workflow} from 'lucide-react';
import {useStore} from '../state/store';
import {WorldDataOptions} from './TrackControls';
import PublicDataPanel from './PublicDataPanel';

const questions=[
 {title:'How does a bank loss spread?',text:'Choose a hypothetical investment loss and follow its effect on bank health, business lending and jobs.'},
 {title:'Why was a business refused a loan?',text:'Inspect the business’s finances and recorded credit decisions to understand what prevented lending.'},
 {title:'What if the shock were different?',text:'Compare separate versions of the same economy with different losses, using the same starting conditions.'},
 {title:'Which response helps?',text:'Compare no new intervention, lending to banks and support for households before deciding whether to apply a policy.'}
];
const roles=[
 {name:'Investigator',text:'Examines bank health, credit relationships and recorded outcomes to investigate the problem.',icon:Search},
 {name:'Policy planner',text:'Tests rescue options on separate copies of the economy and compares their results.',icon:Workflow},
 {name:'Supervisor',text:'Checks the recorded work and can hold a recommendation for review. You decide whether to apply support.',icon:ShieldCheck}
];
export default function Welcome(){const s=useStore();
 return <section className="welcome product-landing" aria-label="About Econova">
  <div className="product-intro">
   <span className="section-kicker">ECONOVA · BANK-CRISIS SIMULATOR</span>
   <h1>Understand a bank crisis.<br/><span>Explore ways to respond.</span></h1>
   <p className="product-lead">Econova is a simulated economy where financial AI agents investigate bank shocks, negotiate credit and compare rescue policies.</p>
   <p className="product-intro-detail">Start with connected banks, businesses and households. Introduce a bank loss, see how it affects lending and jobs, then explore what could change the outcome.</p>
   <button className="action-primary welcome-start" disabled={s.busy} onClick={()=>void s.createWorld()}>{s.busy?'Creating economy…':'Start investigation'}<ArrowRight size={19}/></button>
   <p className="welcome-start-note">Opens an interactive economy before you apply a shock. You choose what happens next.</p>
  </div>
  <section className="product-section" aria-labelledby="explore-heading">
   <span className="section-kicker">WHAT YOU CAN EXPLORE</span><h2 id="explore-heading">Follow the problem from the bank to the business.</h2>
   <div className="product-questions">{questions.map(item=><article key={item.title}><h3>{item.title}</h3><p>{item.text}</p></article>)}</div>
  </section>
  <section className="product-section product-how" aria-labelledby="how-heading">
   <div><span className="section-kicker">WHAT TO EXPECT</span><h2 id="how-heading">One investigation, step by step.</h2><p>Explore at your own pace. Charts show percentage changes, while individual businesses and recorded events explain the details.</p></div>
   <ol><li><b>Create your economy.</b><span>Begin with a synthetic network of 5 banks, 8 businesses and 40 households.</span></li><li><b>Apply a shock and follow consequences.</b><span>Choose a bank loss and advance the simulation to see calculated changes in credit, business survival and employment.</span></li><li><b>Ask agents to investigate.</b><span>Follow their tasks, tool results and handoffs as they inspect evidence and test responses.</span></li><li><b>Compare possible futures.</b><span>Explore alternative shocks or rescue policies side by side. Comparing a future does not apply it to your current economy.</span></li></ol>
  </section>
  <section className="product-section" aria-labelledby="roles-heading"><span className="section-kicker">AI WITH VISIBLE RESPONSIBILITIES</span><h2 id="roles-heading">See what each agent is working on.</h2><p className="product-section-lead">You set the shock. During a policy investigation, these three roles examine the response.</p><div className="product-roles">{roles.map(role=>{const Icon=role.icon;return <article key={role.name}><Icon size={24} aria-hidden="true"/><h3>{role.name}</h3><p>{role.text}</p></article>;})}</div></section>
  <section className="product-scope"><p>For finance learners and instructors exploring how financial problems spread, with inspectable evidence and controlled comparisons.</p><h2>A controlled experiment with a clear starting point.</h2><p>The banks, businesses, households and their finances are synthetic. This is a generic economy, not a model of a particular city. Optional public menu prices and minimum-wage references come from San Francisco and stay fixed within each experiment. Outcomes describe this simulation, rather than predict the real economy.</p></section>
  <details className="welcome-settings"><summary>Starting economy & data settings</summary><div className="welcome-settings-grid"><label>Starting scenario<select aria-label="Starting scenario" value={s.selectedScenario} onChange={e=>s.set({selectedScenario:e.target.value})}><option value="credit_crunch">Credit crunch — fragile banks</option><option value="standard">Standard — stronger banks</option><option value="supply_crunch">Supply crunch — material shortage</option></select></label><WorldDataOptions/></div><p>Public price/wage references load automatically and are frozen in each new economy.</p><PublicDataPanel/></details>
 </section>;
}
