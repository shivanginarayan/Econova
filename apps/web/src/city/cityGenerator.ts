// Build-time composition. The UI reads sfCityLayout.json and never generates scenery.
import type {Building,CityLayout,ScenePath,Landmark,ScenePoint,Tree,Pier,OverviewLabel} from '../data/types';
import {cityTemplate} from '../data/cityTemplates';
import {SCENE_WIDTH,SCENE_HEIGHT,BRIDGE,TABLE,COAST,HEADLAND,LAGOON,PARK,PONDS,ALCATRAZ,ISLET,COIT_HILL,PALACE_SITE,ISLAND_CONTROL,PARK_DRIVE_Y,project,unproject,ref,refs,spline,lakeShore,pointInPolygon,pathLength,pointAlong,distanceToPath,polygonDistance,buildingFootprint,buildingCenter,boundsOf,offsetPath,inTable,rimArc,rimAngle,resample,polygonArea,intersects,type Point,type Bounds} from './cityGeometry';
import {buildingOutline} from './buildingArt';
export const MIN_BUILDING_GAP=5.5;
export {BRIDGE};
export const FERRY_CENTER=ref(1522,700);
export function hashLayout(layout:Omit<CityLayout,'layoutHash'>|CityLayout){const {layoutHash:_ignored,...content}=layout as CityLayout;let h=2166136261;for(const c of JSON.stringify(content)){h^=c.charCodeAt(0);h=Math.imul(h,16777619);}return 'sf-'+(h>>>0).toString(16).padStart(8,'0');}
const round=(p:Point):Point=>[Math.round(p[0]*100)/100,Math.round(p[1]*100)/100];
// A uniform bucket grid keeps the placement passes linear in the number of nearby objects.
class Buckets<T>{private cells=new Map<number,T[]>();constructor(private size:number){}
 private keys(b:Bounds){const out:number[]=[];for(let x=Math.floor(b.x/this.size);x<=Math.floor((b.x+b.width)/this.size);x++)for(let y=Math.floor(b.y/this.size);y<=Math.floor((b.y+b.height)/this.size);y++)out.push(x*10000+y);return out;}
 add(b:Bounds,item:T){for(const k of this.keys(b)){const list=this.cells.get(k);if(list)list.push(item);else this.cells.set(k,[item]);}}
 near(b:Bounds){const out=new Set<T>();for(const k of this.keys(b))for(const item of this.cells.get(k)??[])out.add(item);return [...out];}}
type Line={id:string;points:Point[];width:number;role?:string};
function lineCrossing(a:Point,b:Point,c:Point,d:Point){const r=[b[0]-a[0],b[1]-a[1]],s=[d[0]-c[0],d[1]-c[1]],den=r[0]*s[1]-r[1]*s[0];if(Math.abs(den)<1e-9)return null;const t=((c[0]-a[0])*s[1]-(c[1]-a[1])*s[0])/den,u=((c[0]-a[0])*r[1]-(c[1]-a[1])*r[0])/den;return t>=-1e-9&&t<=1+1e-9&&u>=-1e-9&&u<=1+1e-9?{t,u,p:[a[0]+r[0]*t,a[1]+r[1]*t] as Point}:null;}
function cumulative(p:Point[]){const c=[0];for(let i=1;i<p.length;i++)c.push(c[i-1]+Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]));return c;}
function slice(p:Point[],c:number[],s0:number,s1:number){const at=(s:number):Point=>{let i=1;while(i<c.length-1&&c[i]<s)i++;const t=(s-c[i-1])/((c[i]-c[i-1])||1);return [p[i-1][0]+(p[i][0]-p[i-1][0])*t,p[i-1][1]+(p[i][1]-p[i-1][1])*t];};const out:Point[]=[at(s0)];for(let i=0;i<p.length;i++)if(c[i]>s0+.01&&c[i]<s1-.01)out.push(p[i]);out.push(at(s1));return out;}
// Splits every polyline wherever another road crosses or meets it, so the graph has real junctions.
function buildNetwork(lines:Line[]){
 const cum=lines.map(l=>cumulative(l.points)),cuts=lines.map((l,i)=>[{s:0,p:l.points[0]},{s:cum[i].at(-1)!,p:l.points.at(-1)!}]);
 const boxes=lines.map(l=>boundsOf(l.points,1));
 for(let i=0;i<lines.length;i++)for(let j=i+1;j<lines.length;j++){if(!intersects(boxes[i],boxes[j]))continue;const a=lines[i].points,b=lines[j].points;
  for(let m=1;m<a.length;m++)for(let n=1;n<b.length;n++){const hit=lineCrossing(a[m-1],a[m],b[n-1],b[n]);if(!hit)continue;cuts[i].push({s:cum[i][m-1]+hit.t*(cum[i][m]-cum[i][m-1]),p:hit.p});cuts[j].push({s:cum[j][n-1]+hit.u*(cum[j][n]-cum[j][n-1]),p:hit.p});}}
 for(let i=0;i<lines.length;i++)for(const end of [lines[i].points[0],lines[i].points.at(-1)!])for(let j=0;j<lines.length;j++){if(i===j)continue;const b=lines[j].points;for(let n=1;n<b.length;n++){const dx=b[n][0]-b[n-1][0],dy=b[n][1]-b[n-1][1],len=Math.hypot(dx,dy)||1,t=Math.max(0,Math.min(1,((end[0]-b[n-1][0])*dx+(end[1]-b[n-1][1])*dy)/(len*len)));if(Math.hypot(b[n-1][0]+dx*t-end[0],b[n-1][1]+dy*t-end[1])<.8){cuts[j].push({s:cum[j][n-1]+t*len,p:end});break;}}}
 const points:Point[]=[],parent:number[]=[];const nodeAt=(p:Point)=>{let k=points.findIndex(q=>Math.hypot(q[0]-p[0],q[1]-p[1])<.05);if(k<0){k=points.length;points.push(round(p));parent.push(k);}return k;};
 const root=(k:number):number=>parent[k]===k?k:(parent[k]=root(parent[k]));
 // Junctions closer than 1.5px along any road collapse into one node, so near-coincident crossings share a junction.
 const sorted=lines.map((_,i)=>cuts[i].sort((a,b)=>a.s-b.s).map(c=>({...c,node:nodeAt(c.p)})));
 for(const list of sorted)for(let k=1;k<list.length;k++)if(list[k].s-list[k-1].s<1.5){const a=root(list[k-1].node),b=root(list[k].node);if(a!==b)parent[Math.max(a,b)]=Math.min(a,b);}
 const ids=new Map<number,string>(),nodes:{id:string;point:ScenePoint}[]=[];const nodeId=(k:number)=>{const r=root(k);let id=ids.get(r);if(!id){id='n'+nodes.length;ids.set(r,id);nodes.push({id,point:points[r]});}return {id,point:points[r]};};
 const edges:Array<{line:Line;from:string;to:string;points:Point[]}>=[];
 for(const [i,line]of lines.entries()){const list=sorted[i].map(c=>({...c,root:root(c.node)}));const kept=list.filter((c,k)=>k===0||c.root!==list[k-1].root);
  for(let k=1;k<kept.length;k++){const a=kept[k-1],b=kept[k],from=nodeId(a.root),to=nodeId(b.root),pts=resample(slice(line.points,cum[i],a.s,b.s),5).map(round);pts[0]=from.point;pts[pts.length-1]=to.point;edges.push({line,from:from.id,to:to.id,points:pts});}}
 return {nodes,edges};
}
export function generateCityLayout(layoutSeed=4242,actors:{id:string;district:string}[]=[]):CityLayout{
 let seed=layoutSeed>>>0;const random=()=>{seed+=0x6D2B79F5;let t=seed;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;};
 const pick=<T,>(list:T[])=>list[Math.floor(random()*list.length)];
 const sites:Array<[string,Point]>=[['Financial District',[1255,600]],['SoMa',[1215,742]],['Mission District',[930,700]],['Chinatown',[1030,548]],['Hayes Valley',[800,585]],['Marina',[650,500]],['Richmond',[560,600]],['Sunset',[1010,812]],['Castro',[700,655]]];
 const districts=sites.map(([name,p])=>{const g=unproject(...ref(...p));return {name,x:Math.round(g[0]*1000)/1000,y:Math.round(g[1]*1000)/1000};});
 const districtAt=(p:Point)=>districts.reduce((a,b)=>{const x=project(a.x,a.y),y=project(b.x,b.y);return Math.hypot(p[0]-x[0],p[1]-x[1])<=Math.hypot(p[0]-y[0],p[1]-y[1])?a:b;}).name;
 const ponds=PONDS.map(l=>lakeShore(l.x,l.y,l.rx,l.ry,l.rotation));const holes=[LAGOON,...ponds];
 // A 1px land mask (scanline filled) makes dry() a lookup; margins use bucketed shoreline samples.
 const mask=new Uint8Array(SCENE_WIDTH*SCENE_HEIGHT);
 const fill=(poly:Point[],value:number)=>{for(let y=0;y<SCENE_HEIGHT;y++){const yc=y+.5,xs:number[]=[];for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>yc)!==(b[1]>yc))xs.push(a[0]+(yc-a[1])*(b[0]-a[0])/(b[1]-a[1]));}xs.sort((a,b)=>a-b);for(let k=0;k+1<xs.length;k+=2)for(let x=Math.max(0,Math.ceil(xs[k]-.5));x<=Math.min(SCENE_WIDTH-1,Math.floor(xs[k+1]-.5));x++)mask[y*SCENE_WIDTH+x]=value;}};
 fill(COAST,1);fill(HEADLAND,1);for(const h of holes)fill(h,0);
 const shoreSamples=new Buckets<Point>(12);for(const poly of [COAST,HEADLAND,...holes])for(const p of resample([...poly,poly[0]],1.5))shoreSamples.add({x:p[0],y:p[1],width:0,height:0},p);
 const shoreDistance=(p:Point,limit:number)=>{let d=limit;for(const q of shoreSamples.near({x:p[0]-limit,y:p[1]-limit,width:2*limit,height:2*limit}))d=Math.min(d,Math.hypot(q[0]-p[0],q[1]-p[1]));return d;};
 const dry=(p:Point,margin=2)=>{const x=Math.floor(p[0]),y=Math.floor(p[1]);if(x<0||y<0||x>=SCENE_WIDTH||y>=SCENE_HEIGHT||!inTable(p,4)||!mask[y*SCENE_WIDTH+x])return false;return shoreDistance(p,Math.max(2,margin))>=Math.max(2,margin);};

 // ---- Road network: bridge, arterial, ring roads around the city, the grid, the boulevard and the park drive ----
 const B=BRIDGE.south,N=BRIDGE.north,toward=(a:Point,b:Point,d:number):Point=>{const l=Math.hypot(b[0]-a[0],b[1]-a[1]);return [a[0]+(b[0]-a[0])/l*d,a[1]+(b[1]-a[1])/l*d];};
 let W=B;for(let d=0;inTable(toward(B,N,-d),17);d+=.5)W=toward(B,N,-d);
 const parkAt=(x:number)=>project(x,PARK_DRIVE_Y);let xs=-16;while(!inTable(parkAt(xs),17))xs+=.02;const PN=parkAt(xs),H=parkAt(19.0);
 let wa=rimAngle(W);const pa=rimAngle(PN);while(wa-pa>Math.PI)wa-=Math.PI*2;while(pa-wa>Math.PI)wa+=Math.PI*2;const coastal=rimArc(pa,wa,17,.02);coastal[0]=PN;coastal[coastal.length-1]=W;
 const fTarget=ref(1392,694),E1=ref(1398,512);
 const embarcadero=spline([E1,...refs([[1414,540],[1431,574],[1446,606],[1445,632],[1418,660],[1387,690],[1359,721],[1333,749],[1298,768],[1262,781],[1228,798],[1194,813],[1156,829],[1120,843],[1090,851]]),H],false,12);
 // The boulevard runs from the bridge landing south-east to the Ferry Building plaza, cutting the grid like Market Street.
 let F:Point=fTarget;for(let i=1;i<embarcadero.length;i++){const hit=lineCrossing(B,toward(B,fTarget,900),embarcadero[i-1],embarcadero[i]);if(hit){F=hit.p;break;}}
 // The bay-shore road leaves the boulevard once it clears the bridge landing, then hugs the north coast.
 const S1:Point=[ref(842,0)[0],B[1]+(F[1]-B[1])*(ref(842,0)[0]-B[0])/(F[0]-B[0])];
 const bayShore=spline([S1,...refs([[880,500],[930,502],[980,503],[1020,500],[1060,497],[1104,492],[1150,483],[1196,467],[1244,458],[1300,470],[1350,484],[1382,498]]),E1],false,12);
 const X1=lineCrossing(B,W,PN,H)?.p??B;
 // The bridge deck continues into the headland as a short drive that circles the summit.
 const headlandDrive=():Line[]=>{const [cx,cy]=ref(1056,299),loop=lakeShore(cx,cy,22,6.5,-.1);let k=0;for(let i=0;i<64;i++)if(Math.hypot(loop[i][0]-N[0],loop[i][1]-N[1])<Math.hypot(loop[k][0]-N[0],loop[k][1]-N[1]))k=i;const ring2=[...loop.slice(k,64),...loop.slice(0,k)];return [{id:'headland-spur',points:[N,ring2[0]],width:4.5,role:'drive'},{id:'headland-summit-north',points:ring2.slice(0,33),width:4.5,role:'drive'},{id:'headland-summit-south',points:[...ring2.slice(32),ring2[0]],width:4.5,role:'drive'}];};
 const lines:Line[]=[
  {id:'bridge-deck',points:[B,N],width:9,role:'bridge'},
  {id:'presidio-arterial',points:[B,W],width:10,role:'arterial'},
  {id:'park-drive',points:[PN,H],width:9,role:'park-drive'},
  {id:'great-highway',points:coastal,width:7,role:'coastal'},
  {id:'bay-shore',points:bayShore,width:8.5,role:'shore'},
  {id:'embarcadero',points:embarcadero,width:8.5,role:'shore'},
  {id:'market-boulevard',points:[B,S1,F],width:11,role:'boulevard'},
  ...headlandDrive(),
 ];
 // Ring polygon: arterial, park drive, Embarcadero and the bay shore, closed along the boulevard.
 const ring:Point[]=[B,X1,H,...[...embarcadero].reverse(),...[...bayShore].reverse()];
 // Street pitch of 2.4 grid units gives the demo's 2 x 2 blocks of pastel cubes.
 const gridX=Array.from({length:15},(_,k)=>Math.round((1-2.4*4+2.4*k)*100)/100),gridY=Array.from({length:9},(_,k)=>Math.round((PARK_DRIVE_Y-2.4*(9-k))*100)/100);
 const clipLine=(at:(t:number)=>Point,id:string)=>{const a=at(-30),b=at(50),hits:number[]=[];for(let i=0;i<ring.length;i++){const hit=lineCrossing(a,b,ring[i],ring[(i+1)%ring.length]);if(hit)hits.push(hit.t);}hits.sort((x,y)=>x-y);const out:Line[]=[];for(let k=0;k+1<hits.length;k++){const p=[a[0]+(b[0]-a[0])*hits[k],a[1]+(b[1]-a[1])*hits[k]] as Point,q=[a[0]+(b[0]-a[0])*hits[k+1],a[1]+(b[1]-a[1])*hits[k+1]] as Point,mid:Point=[(p[0]+q[0])/2,(p[1]+q[1])/2];if(Math.hypot(q[0]-p[0],q[1]-p[1])>34&&pointInPolygon(...mid,ring))out.push({id:id+'-'+out.length,points:[p,q],width:8});}return out;};
 for(const x of gridX)lines.push(...clipLine(t=>project(x,t),'street-x'+String(x).replace('.','_').replace('-','m')));
 for(const y of gridY)lines.push(...clipLine(t=>project(t,y),'street-y'+String(y).replace('.','_').replace('-','m')));
 const network=buildNetwork(lines);
 const roads:ScenePath[]=network.edges.map((e,i)=>({id:e.line.id+'~'+i,kind:'road',from:e.from,to:e.to,points:e.points,controlPoints:e.line.role==='bridge'?[e.points[0],e.points.at(-1)!]:[e.points[0],e.points[Math.floor(e.points.length/2)],e.points.at(-1)!],width:e.line.width,district:districtAt(e.points[Math.floor(e.points.length/2)]),...(e.line.role?{role:e.line.role}:{})}));
 const paths:ScenePath[]=[...roads];
 for(const road of roads.filter(r=>r.role!=='bridge'&&r.role!=='drive'))for(const side of [-1,1])paths.push({id:road.id+'-walk-'+side,kind:'footpath',district:road.district,points:offsetPath(road.points,(road.width/2+3.2)*side).map(round),width:2.6,from:road.from,to:road.to});
 const roadSamples=new Buckets<{p:Point;r:number}>(18);for(const road of roads.filter(r=>r.role!=='bridge'))for(const p of resample(road.points,2.5))roadSamples.add({x:p[0],y:p[1],width:0,height:0},{p,r:road.width/2});
 const roadClearance=(p:Point,pad:number)=>roadSamples.near({x:p[0]-pad-7,y:p[1]-pad-7,width:2*pad+14,height:2*pad+14}).every(s=>Math.hypot(s.p[0]-p[0],s.p[1]-p[1])>=s.r+pad);

 // ---- Park and promenade paths ----
 // Park paths are trimmed to dry ground so no walker ever leaves the tabletop or enters a pond.
 const parkPath=(id:string,control:Array<[number,number]>,closed=false,district='Richmond',width=4.2)=>{let pts=spline(refs(control),closed,12).map(round);if(!closed){while(pts.length&&!dry(pts[0],6))pts.shift();while(pts.length&&!dry(pts.at(-1)!,6))pts.pop();}if(pts.length<4||!pts.every(p=>dry(p,4)))throw new Error('Park path leaves dry land: '+id);paths.push({id,kind:'park',district,controlPoints:refs(control).map(round),points:pts,width,closed});};
 parkPath('park-main-drive',[[296,690],[320,708],[400,704],[468,722],[540,748],[616,772],[690,800],[770,812],[850,834],[930,860],[1004,884]],false,'Sunset');
 // Each pond has a shoreline loop a few paces from the water.
 for(const [i,l]of PONDS.entries())paths.push({id:'park-pond-loop-'+i,kind:'park',district:i===2?'Sunset':'Richmond',points:lakeShore(l.x,l.y,l.rx+9,l.ry+6.5,l.rotation).map(round),controlPoints:[[l.x-l.rx-9,l.y],[l.x,l.y-l.ry-6.5],[l.x+l.rx+9,l.y]],width:4,closed:true});
 parkPath('park-north-link',[[470,598],[486,628],[470,664],[470,722]],false);
 parkPath('park-centre-link',[[652,664],[640,704],[624,742],[616,772]],false);
 parkPath('park-windmill-walk',[[420,742],[480,770],[540,804],[568,842],[586,884]],false,'Sunset');
 parkPath('park-south-walk',[[690,800],[728,778],[786,770],[840,790],[872,826],[930,860]],false,'Sunset');
 parkPath('park-west-walk',[[322,744],[360,766],[396,782],[420,742]],false);
 parkPath('presidio-loop',[[290,520],[330,502],[380,520],[420,552],[392,580],[338,584],[300,560]],true);
 parkPath('marina-green-walk',[[480,500],[540,494],[600,484],[650,478]],false,'Marina');
 paths.push({id:'palace-shore-walk',kind:'park',district:'Marina',points:offsetPath(LAGOON,-6).map(round),controlPoints:refs([[400,420],[562,446],[668,434]]),width:3.8,closed:true});
 {const [cx,cy]=ref(1130,420);paths.push({id:'coit-hill-walk',kind:'park',district:'Chinatown',points:lakeShore(cx,cy+1,30,13,.04).map(round),controlPoints:[[cx-30,cy],[cx,cy-13],[cx+30,cy]],width:3.4,closed:true});}
 const parkPaths=paths.filter(p=>p.kind==='park');
 const parkSamples=new Buckets<{p:Point;r:number}>(16);for(const path of parkPaths)for(const p of resample(path.points,2))parkSamples.add({x:p[0],y:p[1],width:0,height:0},{p,r:path.width/2});
 const pathClearance=(p:Point,pad:number)=>parkSamples.near({x:p[0]-pad-5,y:p[1]-pad-5,width:2*pad+10,height:2*pad+10}).every(s=>Math.hypot(s.p[0]-p[0],s.p[1]-p[1])>=s.r+pad);

 // ---- Buildings ----
 const buildings:Building[]=[];const buildingIndex=new Buckets<Building>(40);
 const create=(id:string,name:string,kind:string,p:Point,w:number,d:number,h:number,district:string,rotation=0,color='#d8d4c8'):Building=>{const q=unproject(...p);return {id,name,kind,x:Math.round((q[0]-w/2)*1e4)/1e4,y:Math.round((q[1]-d/2)*1e4)/1e4,w,d,h,district,rotation,color};};
 const downtown=refs([[1004,512],[1100,500],[1210,468],[1300,478],[1396,512],[1440,612],[1392,690],[1250,700],[1140,690],[1040,612]]);
 const coitReserve=boundsOf(refs([[1100,290],[1160,290],[1160,432],[1100,432]]));
 // Generic buildings in front of Coit hill stay low enough that the wooded mound still reads as a hill.
 const hillBox=boundsOf(COIT_HILL),coitBase=ref(1130,420),hillGuard={x:coitBase[0]-44,y:hillBox.y,width:88,height:hillBox.height*.66};
 const reserved=[COIT_HILL.map(p=>p),refs([[1330,690],[1420,660],[1440,700],[1420,780],[1330,780]]),spline(refs([[470,382],[660,382],[680,430],[620,470],[500,470],[460,430]]),true,6)];
 const footprintOk=(b:Building,gap=MIN_BUILDING_GAP)=>{const foot=buildingFootprint(b),edges=foot.flatMap((p,i)=>{const q=foot[(i+1)%4];return [p,[(p[0]*2+q[0])/3,(p[1]*2+q[1])/3] as Point,[(p[0]+q[0]*2)/3,(p[1]+q[1]*2)/3] as Point];});
  if(!edges.every(p=>pointInPolygon(...p,ring)&&dry(p,5)&&roadClearance(p,6.2)))return false;
  if(reserved.some(r=>edges.some(p=>pointInPolygon(...p,r))))return false;
  const box=boundsOf(foot,gap+1);return buildingIndex.near(box).every(o=>polygonDistance(foot,buildingFootprint(o))>=gap);};
 const add=(b:Building)=>{buildings.push(b);buildingIndex.add(boundsOf(buildingFootprint(b)),b);return b;};
 // Silhouettes stay readable: every tower keeps at least 38% of its outline clear of nearer towers.
 const towerKinds=['tower','pyramid','salesforce','coit','ferry'];
 const outlines=new Map<Building,Point[]>(),outlineOf=(b:Building)=>{let o=outlines.get(b);if(!o){o=buildingOutline(b);outlines.set(b,o);}return o;};
 const visibleShare=(own:Point[],depth:number,front:Array<{outline:Point[];depth:number}>)=>{const box=boundsOf(own),nearer=front.filter(t=>t.depth>depth).map(t=>t.outline);let total=0,clear=0;for(let x=box.x;x<box.x+box.width;x+=2.5)for(let y=box.y;y<box.y+box.height;y+=2.5){if(!pointInPolygon(x,y,own))continue;total++;if(!nearer.some(f=>pointInPolygon(x,y,f)))clear++;}return total?clear/total:1;};
 const readable=(b:Building)=>{const own=buildingOutline(b),box=boundsOf(own);if(intersects(box,coitReserve)||intersects(box,hillGuard))return false;if(b.kind!=='tower')return true;const group=[...buildings.filter(t=>towerKinds.includes(t.kind)&&intersects(boundsOf(outlineOf(t)),box)).map(t=>({outline:outlineOf(t),depth:buildingCenter(t)[1]})),{outline:own,depth:buildingCenter(b)[1]}];return group.every(t=>visibleShare(t.outline,t.depth,group)>=.38);};
 // Landmark buildings. Heights follow the demo: Pyramid tip is the highest point on screen, Salesforce is the
 // second-tallest structure, one generic tower is tallest, and Coit stands well below both on its hill.
 const coit=add(create('coit','Coit Tower','coit',ref(1130,420),.48,.48,64,'Chinatown'));
 const pyramid=add(create('pyramid','Transamerica Pyramid','pyramid',project(11.42,5.43),.8,.8,186,'Financial District'));
 const salesforce=add(create('salesforce','Salesforce Tower','salesforce',project(12.28,4.52),.7,.7,196,'Financial District'));
 const ferry=add(create('ferry','Ferry Building','ferry',FERRY_CENTER,4.9,1.25,24,'Financial District',-1.0207,'#efe6d2'));
 void coit;void pyramid;void salesforce;void ferry;
 const actorList=actors.length?actors:Array.from({length:240},(_,i)=>({id:i===14?'cafe-14':i<4?'bank-'+(i+1):'firm-'+i,district:cityTemplate.districts[i%9]}));let actorIndex=0;
 const specialIds=new Set(['cafe-14','bank-1','bank-2','bank-3','bank-4']);
 const nextActor=()=>{while(actorIndex<actorList.length&&(specialIds.has(actorList[actorIndex].id)||buildings.some(b=>b.id===actorList[actorIndex].id)))actorIndex++;return actorList[actorIndex++];};
 const placeNear=(b:Building,tries=420)=>{const c=buildingCenter(b);for(let i=0;i<tries;i++){const a=i*2.39996323,r=i?2+Math.sqrt(i)*3.2:0,q=unproject(c[0]+Math.cos(a)*r,c[1]+Math.sin(a)*r);const t={...b,x:Math.round((q[0]-b.w/2)*1e4)/1e4,y:Math.round((q[1]-b.d/2)*1e4)/1e4};if(footprintOk(t))return add(t);}throw new Error('No dry, spaced site for '+b.id);};
 // The single tallest tower stands south-east of the Pyramid, so the Pyramid tip still crowns the skyline.
 {const actor=nextActor();add(create(actor.id,'Downtown tower '+actor.id.replace('firm-',''),'tower',project(16.6,5.05),.78,.76,208,'Financial District',0,'#c4d4dd'));}
 const specials=[create('cafe-14','Café 14','shop',ref(904,676),.56,.5,19,'Mission District',0,'#efcfb4'),create('bank-1','Bank 1','bank',ref(1306,640),.66,.62,36,'Financial District',0,'#e6e1d3'),create('bank-2','Bank 2','bank',ref(1150,736),.64,.6,34,'SoMa',0,'#e2ddd0'),create('bank-3','Bank 3','bank',ref(980,640),.62,.6,32,'Mission District',0,'#e8e2d4'),create('bank-4','Bank 4','bank',ref(1000,560),.62,.6,33,'Chinatown',0,'#e4dfd2')];
 for(const b of specials){const placed=placeNear(b);if(placed.kind==='shop'){placed.awning='#c97f62';placed.kit=1;}}
 const pastel=['#ebc9c4','#f1ddb6','#bed2de','#c9d7c2','#f4e9d2','#dcdad2','#efd0b6','#d5cde0'],towerColors=['#cfd6d9','#b2cbe0','#efd6a4','#e9bfbb','#c3dbc6','#e6d3bd','#bcd0e3','#f0cdb8'];
 const awnings=['#c97f62','#7fa79a','#d0b264','#86a9bd','#c48c94'];
 const mainStreet=roads.filter(r=>r.id.startsWith('street-y'+String(gridY.at(-2)).replace('.','_'))||r.role==='boulevard');
 // Lots are a regular 2 x 2 subdivision of every grid block; roads, coast and reserves reject whole lots.
 const lots:Array<{p:Point;cx:number;cy:number;bx:number;by:number}>=[];
 for(let i=0;i+1<gridX.length;i++)for(let j=0;j+1<=gridY.length;j++){const y0=gridY[j],y1=j+1<gridY.length?gridY[j+1]:PARK_DRIVE_Y,x0=gridX[i],x1=gridX[i+1];
  for(const u of [.27,.73])for(const v of [.27,.73]){const cx=x0+(x1-x0)*u,cy=y0+(y1-y0)*v;lots.push({p:project(cx,cy),cx,cy,bx:(x0+x1)/2,by:(y0+y1)/2});}}
 for(const lot of lots.sort((a,b)=>a.p[1]-b.p[1]||a.p[0]-b.p[0])){
  const inDowntown=pointInPolygon(...lot.p,downtown),nearDowntown=!inDowntown&&downtown.some(q=>Math.hypot(q[0]-lot.p[0],q[1]-lot.p[1])<64);
  const onMain=mainStreet.some(r=>distanceToPath(lot.p,r.points)<34);
  const attempts=inDowntown?[[.64,.62],[.58,.56],[.52,.5]]:[[.62,.58],[.55,.52],[.46,.44],[.4,.38]];
  // Edge lots that clip a road or the coast retry slightly toward the block centre before giving up.
  for(const [k,[sw,sd]]of [...attempts.map(a=>[0,a] as const),...attempts.map(a=>[.32,a] as const)]){const w=Math.round(sw*(.9+random()*.2)*100)/100,d=Math.round(sd*(.9+random()*.2)*100)/100,jx=(random()-.5)*.14,jy=(random()-.5)*.14;
   const probe=create('probe','','probe',project(lot.cx+(lot.bx-lot.cx)*k+jx,lot.cy+(lot.by-lot.cy)*k+jy),w,d,20,districtAt(lot.p),0,pick(pastel));
   if(!footprintOk(probe))continue;
   if(inDowntown){probe.kind='probe';probe.h=Math.round(78+random()*96);probe.color=pick(towerColors);
    probe.kind='tower';while(probe.h>=60&&!readable(probe))probe.h-=14;if(probe.h<60){probe.kind='office';probe.h=Math.round(44+random()*16);}if(buildings.filter(b=>b.kind==='tower').length>=18&&probe.kind==='tower'){probe.kind='office';probe.h=Math.round(46+random()*22);}}
   else if(nearDowntown){probe.kind='office';probe.h=Math.round(32+random()*18);probe.color=pick([...towerColors,...pastel]);}
   else if(onMain&&random()<.72){probe.kind='shop';probe.h=Math.round(19+random()*7);probe.awning=pick(awnings);probe.kit=Math.floor(random()*5);}
   else {probe.kind='house';const small=w<.5;probe.roof=small||random()<.35?'hip':'flat';probe.h=Math.round(small?14+random()*6:22+random()*13);probe.kit=Math.floor(random()*5);}
   probe.district=districtAt(buildingCenter(probe));
   if(probe.kind==='house'){probe.id='home-'+buildings.filter(b=>b.kind==='house').length;probe.name=probe.roof==='hip'?'Pastel house':'Pastel apartment block';}
   else {const actor=nextActor();if(!actor)break;probe.id=actor.id;probe.name=probe.kind==='tower'?'Downtown tower '+actor.id.replace('firm-',''):probe.kind==='office'?'Office building '+actor.id.replace('firm-',''):'Neighbourhood shop '+actor.id.replace('firm-','');}
   if(!readable(probe))continue;
   add(probe);break;}
 }
 // Walkers reach each shop using its own clear apron, attached to the nearest continuous sidewalk.
 const sidewalks=paths.filter(p=>p.kind==='footpath');
 for(const b of buildings.filter(b=>b.kind==='shop')){const foot=buildingFootprint(b),door:Point=[(foot[2][0]+foot[3][0])/2,(foot[2][1]+foot[3][1])/2];let chosen=sidewalks[0],index=0,best=Infinity;for(const path of sidewalks)for(const [i,q]of path.points.entries()){const d=Math.hypot(q[0]-door[0],q[1]-door[1]);if(d<best){best=d;chosen=path;index=i;}}const route:Point[]=[door,chosen.points[index]];let distance=best;const direction=index<chosen.points.length/2?1:-1;for(let i=index+direction;i>=0&&i<chosen.points.length&&distance<58;i+=direction){const q=chosen.points[i],prev=route.at(-1)!;distance+=Math.hypot(q[0]-prev[0],q[1]-prev[1]);route.push(q);}paths.push({id:'approach-'+b.id,kind:'footpath',district:b.district,points:route.map(round),width:2.4});}

 // ---- Trees ----
 const trees:Tree[]=[];const treeIndex=new Buckets<Tree>(16);
 const windmill={x:ref(604,866)[0],y:ref(604,866)[1],scale:1};
 const flowerBeds=[ref(352,724),ref(398,752),ref(488,806),ref(838,812)].map(([x,y],i)=>({x:Math.round(x),y:Math.round(y),rx:[12,10,9,10][i],ry:[5,4.2,4,4.3][i]}));
 const clearings=[{x:windmill.x,y:windmill.y,r:24},...flowerBeds.map(f=>({x:f.x,y:f.y,r:f.rx+6})),{x:PALACE_SITE.center[0],y:PALACE_SITE.center[1],r:62}];
 const treeFits=(p:Point,size:number)=>{if(!dry(p,size*.8+2))return false;if(clearings.some(c=>Math.hypot((p[0]-c.x)*.6,p[1]-c.y)<c.r*.6))return false;
  const box={x:p[0]-size*3,y:p[1]-size*3,width:size*6,height:size*6};
  if(buildingIndex.near({x:p[0]-60,y:p[1]-60,width:120,height:120}).some(b=>{const f=buildingFootprint(b);return pointInPolygon(...p,f)||distanceToPath(p,[...f,f[0]])<size*.9+1.5;}))return false;
  if(!roadClearance(p,size*.55+1.2))return false;if(!pathClearance(p,size*.6+.8))return false;
  return treeIndex.near(box).every(t=>Math.hypot(t.x-p[0],(t.y-p[1])*1.4)>(t.size+size)*.82);};
 const plant=(p:Point,size:number,kind=0,shade=Math.floor(random()*4))=>{if(!treeFits(p,size))return false;const t:Tree={x:Math.round(p[0]*100)/100,y:Math.round(p[1]*100)/100,size:Math.round(size*100)/100,shade,kind};trees.push(t);treeIndex.add({x:t.x-.5,y:t.y-.5,width:1,height:1},t);return true;};
 // Street trees line both sidewalks at a regular pitch, as in the demo's boulevards.
 for(const road of roads.filter(r=>r.role!=='bridge'&&r.role!=='drive')){const length=pathLength(road.points);for(let d=7;d<length-7;d+=11.5)for(const side of [-1,1]){const q=pointAlong(road.points,d/length,length),off=road.width/2+6.4,p:Point=[q.x-Math.sin(q.angle)*off*side,q.y+Math.cos(q.angle)*off*side];plant(p,3.1+random()*.7,0);}}
 // Garden trees fill the gaps inside blocks.
 for(let i=0;i<5200;i++){const p:Point=[200+random()*1150,380+random()*420];if(!pointInPolygon(...p,ring))continue;plant(p,3+random()*.9,random()<.12?1:0);}
 // Parks: dense, varied canopy with meadows left open by a smooth clearing field.
 const meadow=(p:Point)=>Math.sin(p[0]*.034+1.3)*Math.cos(p[1]*.052-.4)+Math.sin((p[0]-p[1])*.021+2.1)*.8;
 const greens=[PARK,spline(refs([[276,476],[340,470],[400,460],[452,470],[470,520],[440,560],[360,592],[262,612],[240,560]]),true,8),spline(refs([[420,382],[700,402],[720,460],[560,500],[420,500],[396,440]]),true,8),COIT_HILL,HEADLAND];
 // Coit hill wears a dense, dark wooded crown, as in the demo.
 {const box=boundsOf(COIT_HILL);for(let i=0;i<2600;i++){const p:Point=[box.x+random()*box.width,box.y+random()*box.height];if(pointInPolygon(...p,COIT_HILL))plant(p,3.4+random()*1.5,random()<.2?1:0,random()<.6?2:0);}}
 for(let i=0;i<26000;i++){const g=i%5===0?1:i%9===0?2:i%13===0?3:i%17===0?4:0;const box=boundsOf(greens[g]);const p:Point=[box.x+random()*box.width,box.y+random()*box.height];if(!pointInPolygon(...p,greens[g])||pointInPolygon(...p,ring))continue;if(g===0&&meadow(p)>1.15)continue;plant(p,g>=3?3.4+random()*1.2:3.8+random()*2.6,random()<.14?1:0);}
 // ---- Water, piers, boats ----
 const alcatraz=ALCATRAZ.map(round);
 const pier=(x:number,y:number,length:number,dx:number,dy:number,width:number,slips:number):Pier=>{const l=Math.hypot(dx,dy);const p=ref(x,y);return {x:Math.round(p[0]*100)/100,y:Math.round(p[1]*100)/100,length,width,normal:[Math.round(dx/l*1e4)/1e4,Math.round(dy/l*1e4)/1e4],slips};};
 const piers:Pier[]=[pier(1424,513,132,1,-.17,7.2,0),pier(1450,556,154,1,-.17,6.8,1),pier(1470,594,154,1,-.17,6.8,-1),pier(1290,784,88,1,.2,5,1),pier(1232,812,98,1,.2,5.4,0),pier(1150,846,110,1,.2,5.8,-1)];
 const boats:CityLayout['boats']=[...refs([[1392,802],[1430,816],[1500,800],[1330,862],[1196,890],[1540,790],[1600,500],[1300,420],[880,410],[760,360]]).map(([x,y],i)=>({x:Math.round(x),y:Math.round(y),angle:[.05,-.1,.1,0,.08,-.05,.06,0,-.1,.04][i],sail:true}))];
 for(const p of piers){if(!p.slips)continue;const t=[-p.normal[1],p.normal[0]];for(let d=22;d<p.length-8;d+=11){const off=p.slips*(p.width/2+6);boats.push({x:Math.round((p.x+p.normal[0]*d+t[0]*off)*100)/100,y:Math.round((p.y+p.normal[1]*d+t[1]*off)*100)/100,angle:Math.round(Math.atan2(t[1],t[0])*100)/100,sail:false});}}
 const harbour=spline(refs([[1104,884],[1180,846],[1262,808],[1340,780],[1420,786],[1470,806],[1420,850],[1300,890],[1170,912]]),true,10).map(round);
 const bay=rimArc(-Math.PI,Math.PI,1,.04).map(round);
 // ---- Landmarks and overview labels ----
 const lm=(id:string,name:string,kind:Landmark['kind'],district:string,p:Point,footprint:Point[],bounds:Bounds,labelOffset:ScenePoint):Landmark=>({id,name,kind,district,x:Math.round(p[0]*100)/100,y:Math.round(p[1]*100)/100,footprint:footprint.map(round),bounds,labelOffset});
 const deckMid:Point=[(B[0]+N[0])/2,(B[1]+N[1])/2];
 const palaceFoot=lakeShore(PALACE_SITE.center[0],PALACE_SITE.center[1],PALACE_SITE.rx,PALACE_SITE.ry);
 const landmarkBuildings=buildings.filter(b=>['coit','pyramid','salesforce','ferry'].includes(b.kind));
 const landmarks:Landmark[]=[
  lm('golden-gate-bridge','Golden Gate Bridge','bridge','Marina',deckMid,[[B[0],B[1]-6],[N[0],N[1]-6],[N[0],N[1]+8],[B[0],B[1]+8]],boundsOf([B,N,[B[0],N[1]-BRIDGE.height-30]],12),[0,-120]),
  lm('palace-of-fine-arts','Palace of Fine Arts','palace','Marina',PALACE_SITE.center,palaceFoot,boundsOf([[PALACE_SITE.center[0]-66,PALACE_SITE.center[1]-118],[PALACE_SITE.center[0]+66,PALACE_SITE.center[1]+30]]),[0,-120]),
  lm('alcatraz','Alcatraz','alcatraz','Marina',ref(1262,346),alcatraz,boundsOf(alcatraz,34),[0,-46]),
  lm('golden-gate-park','Golden Gate Park','park','Richmond',ref(560,760),PARK,boundsOf(PARK),[0,0]),
  ...landmarkBuildings.map(b=>{const p=buildingCenter(b),o=boundsOf(buildingOutline(b),8);return lm(b.id,b.name,b.kind as Landmark['kind'],b.district,p,buildingFootprint(b),o,[0,-(b.h+24)]);})];
 const label=(id:string,text:string,at:Point,anchor:Point,angle:number,priority:number,district:string,landmarkId:string|null):OverviewLabel=>({id,text,at:round(at),anchor:round(anchor),angle,priority,district,landmarkId});
 const labels=[label('marina','MARINA',ref(428,362),ref(452,396),-.32,90,'Marina','palace-of-fine-arts'),label('alcatraz','ALCATRAZ',ref(1318,300),ref(1286,334),.16,80,'Marina','alcatraz'),label('coit','COIT TOWER',ref(1074,450),ref(1124,418),0,85,'Chinatown','coit'),label('financial-district','FINANCIAL DISTRICT',ref(1234,559),ref(1165,468),0,70,'Financial District','pyramid'),label('golden-gate-park','GOLDEN GATE PARK',ref(560,760),ref(560,760),0,75,'Richmond','golden-gate-park')];
 const cityGround=ring.map(round);
 const layout:CityLayout={layoutSeed,simulationSeed:42,layoutHash:'',version:4,diorama:{...TABLE},island:{controlPoints:ISLAND_CONTROL.map(round),boundary:COAST.map(round),headland:HEADLAND.map(round),alcatraz,park:PARK.map(round),islet:ISLET.map(round),coitHill:COIT_HILL.map(round),cityGround,greens:greens.slice(1,3).map(g=>g.map(round))},districts,buildings,roads:roads.map(r=>r.id),roadNetwork:{nodes:network.nodes,edges:roads},water:{name:'San Francisco Bay',lakes:PONDS,bodies:[{id:'marina-lagoon',kind:'lagoon',shore:LAGOON.map(round),enclosed:true},{id:'open-bay',kind:'bay',shore:bay,enclosed:false},{id:'south-harbour',kind:'harbour',shore:harbour,enclosed:false},...ponds.map((shore,i)=>({id:'park-pond-'+i,kind:'pond' as const,shore:shore.map(round),enclosed:true}))]},parks:[{x:0,y:0,w:0,d:0,name:'Golden Gate Park',district:'Richmond',boundary:PARK.map(round)}],landmarks,paths,trees,boats,piers,decor:{windmill,flowerBeds,area:Math.round(polygonArea(PARK))},labels,minimumBuildingGap:MIN_BUILDING_GAP};
 layout.layoutHash=hashLayout(layout);return layout;
}
