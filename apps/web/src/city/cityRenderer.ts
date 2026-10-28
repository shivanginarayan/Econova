import {prism,buildingBounds,buildingOutline,landmarkKinds,drawFerryHall,drawFerryClock,ferryGeometry} from './buildingArt';
export {prism,buildingBounds,buildingOutline} from './buildingArt';
import {foliage,face,stroke,oval,shadowHull,TREE_COLORS,tintHex} from './modelArt';
import {renderAlcatraz} from './palaceArt';
import {drawBridge,drawPalace,drawWaterfront,bridgeSection} from './landmarkArt';
export {drawPalace} from './landmarkArt';
import type {Building,CityLayout,Landmark,Tree} from '../data/types';
import type {VisualMover} from './movers';
import {project,intersects,pointInPolygon,buildingCenter,buildingFootprint,treeOccludes,boundsOf,offsetPath,PALACE_SITE,BRIDGE,HEADLAND_RISE,FERRY_APRON,HARBOUR_SURF,SCENE_WIDTH,SCENE_HEIGHT,type Bounds,type Point} from './cityGeometry';
export {project} from './cityGeometry';
export type DetailLevel=0|1|2;
export const polygon=face;
export function shade(hex:string,n:number){const v=parseInt(hex.slice(1),16);return `rgb(${Math.min(255,(v>>16)*n)},${Math.min(255,((v>>8)&255)*n)},${Math.min(255,(v&255)*n)})`;}
const PALETTE={water:['#74afd2','#5893b9','#4682a8'],lagoon:['#7cb6e3','#5f9dd6'],pond:['#7ab4dc','#5d9bc9'],land:'#a7cf80',park:'#8fbf62',green:'#9dca72',hill:'#88b85c',city:'#dcdccd',lot:'#ece8dc',shore:'#ebe4c9',sidewalk:'#eeeadf',asphalt:'#8e9897',arterial:'#d98b68',path:'#f8f4e7',pathEdge:'#d9d3bd'};
function windmill(c:CanvasRenderingContext2D,l:CityLayout,lod:number){
 const {x,y}=l.decor.windmill;oval(c,x,y+2,15,6,'#9fc477');
 face(c,[[x-7,y],[x+7,y],[x+4.5,y-30],[x-4.5,y-30]],'#f3ede0');face(c,[[x+1,y],[x+7,y],[x+4.5,y-30],[x+1,y-30]],'#d5d2c6');face(c,[[x-5.5,y-29],[x+5.5,y-29],[x,y-38]],'#9a5c47');
 if(lod>0)for(const yy of [8,17])face(c,[[x-1.5,y-yy],[x+1.5,y-yy],[x+1.5,y-yy-4],[x-1.5,y-yy-4]],'#7d8a86');
 c.save();c.translate(x,y-31);c.rotate(.42);for(let i=0;i<4;i++){c.rotate(Math.PI/2);face(c,[[-1,0],[1.6,0],[3.4,-27],[-3,-27]],'#fbf7ec');face(c,[[-3,-27],[3.4,-27],[3.6,-30],[-3.1,-30]],'#d34a36');for(let j=5;j<26;j+=3.4)stroke(c,[[-2.6,-j],[3,-j]],'#b8b4a5',.45);}c.restore();oval(c,x,y-31,2.2,2.2,'#7b5a46');
}
function flowerBed(c:CanvasRenderingContext2D,f:{x:number;y:number;rx:number;ry:number},lod:number){
 oval(c,f.x,f.y,f.rx+2,f.ry+1.2,'#e6dfc8');oval(c,f.x,f.y,f.rx,f.ry,'#6d9a49');
 for(let i=0;i<(lod?30:16);i++){const a=i*2.39996,r=Math.sqrt((i+.5)/(lod?30:16));oval(c,f.x+Math.cos(a)*f.rx*r*.86,f.y+Math.sin(a)*f.ry*r*.86,lod?1.1:1.4,lod?.75:.9,['#d6503a','#ef9a3e','#f3c954','#5f8f3c'][i%4]);}
}
type Solid={depth:number;bounds:Bounds;draw:(c:CanvasRenderingContext2D,lod:DetailLevel)=>void};
function treeBounds(t:Tree):Bounds{return {x:t.x-t.size*1.8,y:t.y-t.size*3.6,width:t.size*3.6,height:t.size*4};}
export function sceneSolids(l:CityLayout):Solid[]{
 const solids:Solid[]=[];
 for(const t of l.trees){const rise=pointInPolygon(t.x,t.y,l.island.headland)?HEADLAND_RISE:0,b=treeBounds(t);solids.push({depth:t.y,bounds:{...b,y:b.y-rise},draw:(c,lod)=>foliage(c,t.x,t.y-rise,t.size,TREE_COLORS[t.shade],t.kind,lod)});}
 for(const b of l.buildings){if(b.kind==='ferry'){solids.push({depth:buildingCenter(b)[1],bounds:buildingBounds(b),draw:(c,lod)=>drawFerryHall(c,b,lod)});solids.push({depth:1e4,bounds:buildingBounds(b),draw:(c,lod)=>drawFerryClock(c,b,lod)});}else solids.push({depth:buildingCenter(b)[1],bounds:buildingBounds(b),draw:(c,lod)=>prism(c,b,lod)});}
 const palace=l.landmarks.find(a=>a.kind==='palace')!,bridge=l.landmarks.find(a=>a.kind==='bridge')!,alcatraz=l.landmarks.find(a=>a.kind==='alcatraz')!;
 solids.push({depth:PALACE_SITE.center[1]+PALACE_SITE.ry,bounds:palace.bounds,draw:(c,lod)=>drawPalace(c,lod)});
 solids.push({depth:BRIDGE.north[1]-20,bounds:bridge.bounds,draw:(c,lod)=>drawBridge(c,lod)});
 solids.push({depth:alcatraz.y,bounds:alcatraz.bounds,draw:(c,lod)=>renderAlcatraz(c,lod,l)});
 const w=l.decor.windmill;solids.push({depth:w.y,bounds:{x:w.x-36,y:w.y-66,width:72,height:72},draw:(c,lod)=>windmill(c,l,lod)});
 return solids.sort((a,b)=>a.depth-b.depth);
}
function ground(c:CanvasRenderingContext2D,l:CityLayout,lod:DetailLevel,bounds:Bounds){
 const {center:[x,y],radius:r,tilt,thickness}=l.diorama;
 // Thick grey-green tabletop: soft shadow to the south-east, a light upper band and a darker lower side.
 c.save();c.shadowColor='rgba(0,0,0,.55)';c.shadowBlur=26;c.shadowOffsetX=16;c.shadowOffsetY=14;oval(c,x,y+thickness,r,r*tilt,'#3d4c4b');c.restore();
 const side=c.createLinearGradient(0,y,0,y+r*tilt+thickness);side.addColorStop(0,'#7e9694');side.addColorStop(.86,'#6c8483');side.addColorStop(.87,'#506362');side.addColorStop(1,'#3f504f');
 c.beginPath();c.ellipse(x,y,r,r*tilt,0,0,Math.PI);c.ellipse(x,y+thickness,r,r*tilt,0,Math.PI,0,true);c.closePath();c.fillStyle=side;c.fill();
 c.beginPath();c.ellipse(x,y+thickness*.56,r,r*tilt,0,Math.PI*.02,Math.PI*.98);c.strokeStyle='rgba(40,54,53,.45)';c.lineWidth=1.2;c.stroke();
 c.save();c.beginPath();c.ellipse(x,y,r,r*tilt,0,0,Math.PI*2);c.clip();
 const water=c.createLinearGradient(0,y-r*tilt,0,y+r*tilt);water.addColorStop(0,PALETTE.water[0]);water.addColorStop(.55,PALETTE.water[1]);water.addColorStop(1,PALETTE.water[2]);c.fillStyle=water;c.fillRect(x-r,y-r*tilt,r*2,r*tilt*2);
 for(let yy=Math.floor((y-r*tilt)/3)*3;yy<y+r*tilt;yy+=3)if(yy>bounds.y-2&&yy<bounds.y+bounds.height+2)stroke(c,[[Math.max(bounds.x,x-r),yy],[Math.min(bounds.x+bounds.width,x+r),yy]],'rgba(232,246,250,.05)',.5);
 for(let i=0;i<420;i++){const wx=x-r+((i*137.508)%1)*r*2,wy=y-r*tilt+((i*.618034)%1)*r*tilt*2;if(wx<bounds.x-10||wx>bounds.x+bounds.width+10||wy<bounds.y-4||wy>bounds.y+bounds.height+4)continue;stroke(c,[[wx,wy],[wx+4+(i%3)*2,wy]],'rgba(240,250,252,.22)',.6);}
 // Shallow water halo and a pale beach where land meets water.
 for(const p of [l.island.boundary,l.island.headland,l.island.alcatraz])stroke(c,[...p,p[0]],'rgba(196,232,240,.45)',9);
 for(const p of [l.island.boundary,l.island.headland]){face(c,p,PALETTE.land);stroke(c,[...p,p[0]],PALETTE.shore,3.2);}
 face(c,l.island.islet,'#e8e1c8');stroke(c,[...l.island.islet,l.island.islet[0]],'#f4eedb',1.2);
 // The headland rises as a faceted green hill.
 const lifted=l.island.headland.map(p=>[p[0],p[1]-HEADLAND_RISE] as Point),hb=boundsOf(lifted);face(c,l.island.headland,'#5f7a48');face(c,l.island.headland.map(p=>[p[0],p[1]-HEADLAND_RISE*.5] as Point),'#6e8a53');
 const hg=c.createLinearGradient(hb.x,hb.y,hb.x+hb.width*.35,hb.y+hb.height);hg.addColorStop(0,'#b2cb8b');hg.addColorStop(1,'#86a466');face(c,lifted,hg);
 for(let i=0;i<10;i++){const fx=hb.x+24+i*hb.width/10.5,fy=hb.y+hb.height*.42+(i%3)*2;face(c,[[fx,fy-5],[fx+15,fy-2],[fx+9,fy+7],[fx-6,fy+4]],i%2?'rgba(64,92,52,.2)':'rgba(255,255,230,.13)');}
 c.save();c.beginPath();l.island.boundary.forEach((p,i)=>i?c.lineTo(...p):c.moveTo(...p));c.closePath();c.clip();face(c,l.island.park,PALETTE.park);c.restore();
 for(const g of l.island.greens)face(c,g,PALETTE.green);
 const hill=l.island.coitHill,hillBox=boundsOf(hill),hillGrad=c.createRadialGradient(hillBox.x+hillBox.width*.55,hillBox.y+hillBox.height*.3,4,hillBox.x+hillBox.width/2,hillBox.y+hillBox.height/2,hillBox.width*.6);hillGrad.addColorStop(0,'#a2c978');hillGrad.addColorStop(1,'#78a752');face(c,hill.map(p=>[p[0]+1,p[1]+3] as Point),'rgba(60,90,50,.3)');face(c,hill,hillGrad);
 face(c,l.island.cityGround,PALETTE.city);
 for(const b of l.water.bodies.filter(b=>b.kind==='lagoon'||b.kind==='pond')){const bb=boundsOf(b.shore),g=c.createLinearGradient(0,bb.y,0,bb.y+bb.height),colors=b.kind==='lagoon'?PALETTE.lagoon:PALETTE.pond;g.addColorStop(0,colors[0]);g.addColorStop(1,colors[1]);stroke(c,[...b.shore,b.shore[0]],'#e9e3cc',4);face(c,b.shore,g);stroke(c,[...b.shore,b.shore[0]],'rgba(255,255,255,.35)',.8);
  if(b.kind==='lagoon'&&lod>0)for(let i=0;i<14;i++){const p=b.shore[(i*23)%b.shore.length],q=[p[0]+(bb.x+bb.width/2-p[0])*.08,p[1]+(bb.y+bb.height/2-p[1])*.18];oval(c,q[0],q[1],1.6,.8,'#7fae62');}}
 for(const b of l.buildings)if(intersects(buildingBounds(b),bounds)&&!['ferry','coit'].includes(b.kind)){const f=buildingFootprint(b),m=buildingCenter(b);face(c,f.map(p=>[m[0]+(p[0]-m[0])*1.22,m[1]+(p[1]-m[1])*1.22] as Point),PALETTE.lot);}
 // The Ferry Building stands on a pale paved apron; white surf breaks along the south-east harbour.
 face(c,FERRY_APRON,'#e7e1cd');stroke(c,[...FERRY_APRON,FERRY_APRON[0]],'#d2cab2',1);
 for(const [k,o]of [[0,-3],[1,-6.5]] as const){c.setLineDash(k?[3,7]:[6,5]);stroke(c,offsetPath(HARBOUR_SURF,o),'rgba(255,255,255,'+(k?.45:.7)+')',k?.8:1.3);}c.setLineDash([]);
 c.restore();
}
function roads(c:CanvasRenderingContext2D,l:CityLayout,lod:DetailLevel,bounds:Bounds){
 const visible=l.paths.filter(p=>p.kind==='road'&&p.role!=='bridge'&&intersects(boundsOf(p.points,12),bounds));
 const lift=(p:typeof visible[number])=>p.role==='drive'?p.points.map(q=>[q[0],q[1]-HEADLAND_RISE] as Point):p.points;
 for(const p of visible)if(p.role==='drive'){stroke(c,lift(p),'#efe7cf',p.width+1.6);stroke(c,lift(p),'#cfc6a8',p.width);}
 for(const p of visible.filter(p=>p.role!=='drive'))stroke(c,p.points,PALETTE.sidewalk,p.width+6.4);
 for(const p of visible.filter(p=>p.role!=='drive'))stroke(c,p.points,'#c9c6b8',p.width+1.2);
 for(const p of visible.filter(p=>p.role!=='drive'))stroke(c,p.points,p.role==='arterial'?PALETTE.arterial:PALETTE.asphalt,p.width);
 for(const p of visible){if(p.role==='drive'||p.points.length<5)continue;const inner=p.points.slice(2,-2);c.setLineDash(lod?[2.4,2.6]:[3,4]);stroke(c,inner,p.role==='arterial'?'rgba(255,236,214,.9)':'rgba(255,255,250,.85)',lod?.55:.6);c.setLineDash([]);}
 if(lod>0)for(const n of l.roadNetwork.nodes){if(n.point[0]<bounds.x-10||n.point[0]>bounds.x+bounds.width+10||n.point[1]<bounds.y-10||n.point[1]>bounds.y+bounds.height+10)continue;for(const e of l.roadNetwork.edges.filter(e=>e.role!=='bridge'&&e.role!=='drive'&&(e.from===n.id||e.to===n.id))){const pts=e.from===n.id?e.points:[...e.points].reverse();if(pts.length<4)continue;const a=pts[2],b=pts[3],dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy)||1,nx=-dy/len,ny=dx/len;for(let k=-2;k<=2;k++){const ox=nx*k*e.width*.2,oy=ny*k*e.width*.2;stroke(c,[[a[0]+ox,a[1]+oy],[a[0]+ox+dx/len*2.4,a[1]+oy+dy/len*2.4]],'rgba(255,255,255,.75)',.75);}}}
 for(const p of l.paths.filter(p=>p.kind==='park'&&intersects(boundsOf(p.points,8),bounds))){stroke(c,p.points,PALETTE.pathEdge,p.width+1.4);stroke(c,p.points,PALETTE.path,p.width);}
 for(const f of l.decor.flowerBeds)flowerBed(c,f,lod);
}
function shadows(c:CanvasRenderingContext2D,l:CityLayout,bounds:Bounds,solids:Solid[]){
 // Shadows are unioned on their own layer, then laid down once at low opacity, so they never stack into a dark mass.
 const layer=document.createElement('canvas'),scale=c.getTransform().a;layer.width=Math.ceil(bounds.width*scale);layer.height=Math.ceil(bounds.height*scale);const s=layer.getContext('2d')!;s.scale(scale,scale);s.translate(-bounds.x,-bounds.y);s.fillStyle='#24361f';
 for(const b of l.buildings){if(!intersects({x:buildingBounds(b).x,y:buildingBounds(b).y,width:buildingBounds(b).width+b.h,height:buildingBounds(b).height+b.h*.4},bounds))continue;const f=b.kind==='ferry'?ferryGeometry(b).hall:buildingFootprint(b);s.beginPath();shadowHull(f,b.kind==='ferry'?b.h+6:b.h*(b.kind==='pyramid'?.55:b.kind==='coit'?.7:1)).forEach((p,i)=>i?s.lineTo(...p):s.moveTo(...p));s.closePath();s.fill();if(b.kind==='ferry'){const g=ferryGeometry(b);s.beginPath();shadowHull(g.tower,g.towerHeight).forEach((p,i)=>i?s.lineTo(...p):s.moveTo(...p));s.closePath();s.fill();}}
 for(const t of l.trees){if(t.x<bounds.x-20||t.x>bounds.x+bounds.width+10||t.y<bounds.y-24||t.y>bounds.y+bounds.height+10)continue;const rise=pointInPolygon(t.x,t.y,l.island.headland)?HEADLAND_RISE:0;s.beginPath();s.ellipse(t.x+t.size*1.1,t.y-rise+t.size*.35,t.size*1.35,t.size*.55,.32,0,Math.PI*2);s.fill();}
 const [px,py]=PALACE_SITE.center;s.beginPath();s.ellipse(px+22,py+8,PALACE_SITE.rx*.9,PALACE_SITE.ry*.9,0,0,Math.PI*2);s.fill();
 const w=l.decor.windmill;s.beginPath();s.ellipse(w.x+12,w.y+4,13,4,0,0,Math.PI*2);s.fill();
 s.beginPath();for(let i=0;i<=40;i++){const p=bridgeSection(i/40,1).deck;i?s.lineTo(p[0]+16,p[1]+22):s.moveTo(p[0]+16,p[1]+22);}for(let i=40;i>=0;i--){const p=bridgeSection(i/40,-1).deck;s.lineTo(p[0]+16,p[1]+22);}s.closePath();s.fill();
 c.save();c.globalAlpha=.21;c.drawImage(layer,bounds.x,bounds.y,bounds.width,bounds.height);c.restore();layer.width=0;void solids;
}
export function renderStatic(c:CanvasRenderingContext2D,l:CityLayout,lod:DetailLevel=0,bounds:Bounds={x:0,y:0,width:SCENE_WIDTH,height:SCENE_HEIGHT},solids=sceneSolids(l)){
 c.clearRect(bounds.x,bounds.y,bounds.width,bounds.height);ground(c,l,lod,bounds);
 const {center:[x,y],radius:r,tilt}=l.diorama;c.save();c.beginPath();c.ellipse(x,y,r,r*tilt,0,0,Math.PI*2);c.clip();
 roads(c,l,lod,bounds);drawWaterfront(c,l,lod,bounds);shadows(c,l,bounds,solids);c.restore();
 for(const s of solids)if(intersects(s.bounds,bounds))s.draw(c,lod);
}
export type SceneTile={canvas:HTMLCanvasElement;bounds:Bounds};
type Occluder={depth:number;test:(x:number,y:number)=>boolean;bounds:Bounds};
export class StaticSceneCache{
 readonly layers:SceneTile[][]=[[],[],[]];readonly renderCount:number;private occluders=new Map<number,Occluder[]>();
 constructor(l:CityLayout){let count=0;const solids=sceneSolids(l);for(const lod of [0,1,2] as const){const density=[1.25,2.25,3][lod];for(let y=0;y<SCENE_HEIGHT;y+=360)for(let x=0;x<SCENE_WIDTH;x+=360){const bounds={x,y,width:Math.min(360,SCENE_WIDTH-x),height:Math.min(360,SCENE_HEIGHT-y)},canvas=document.createElement('canvas');canvas.width=Math.ceil((bounds.width+4)*density);canvas.height=Math.ceil((bounds.height+4)*density);const c=canvas.getContext('2d')!;c.scale(density,density);c.translate(2-x,2-y);renderStatic(c,l,lod,{x:x-2,y:y-2,width:bounds.width+4,height:bounds.height+4},solids);this.layers[lod].push({canvas,bounds});count++;}}
  this.renderCount=count;
  // Occlusion index: a walker or car whose foot point lies behind a canopy or a building outline is hidden by it.
  const add=(o:Occluder)=>{for(let gx=Math.floor(o.bounds.x/24);gx<=Math.floor((o.bounds.x+o.bounds.width)/24);gx++)for(let gy=Math.floor(o.bounds.y/24);gy<=Math.floor((o.bounds.y+o.bounds.height)/24);gy++){const k=gx*1000+gy,list=this.occluders.get(k);if(list)list.push(o);else this.occluders.set(k,[o]);}};
  for(const t of l.trees)add({depth:t.y,bounds:treeBounds(t),test:(x,y)=>treeOccludes(t,x,y)});
  for(const b of l.buildings){const outline=buildingOutline(b);add({depth:b.kind==='ferry'?buildingCenter(b)[1]+8:buildingCenter(b)[1],bounds:boundsOf(outline),test:(x,y)=>pointInPolygon(x,y,outline)});}
 }
 occluded(x:number,y:number){for(const o of this.occluders.get(Math.floor(x/24)*1000+Math.floor(y/24))??[])if(o.depth>y+1&&o.test(x,y))return true;return false;}
 draw(c:CanvasRenderingContext2D,lod:DetailLevel,v:Bounds){let n=0;for(const t of this.layers[lod])if(intersects(t.bounds,v)){const b=t.bounds;c.drawImage(t.canvas,b.x-2,b.y-2,b.width+4,b.height+4);n++;}return n;}
 drawDepth(c:CanvasRenderingContext2D,_lod:DetailLevel,_v:Bounds,pool:VisualMover[],draw:(m:VisualMover)=>void){const items=pool.filter(m=>m.visible&&!this.occluded(m.x,m.y)).sort((a,b)=>a.y-b.y);for(const m of items)draw(m);return items.length;}
 dispose(){for(const list of this.layers)for(const t of list){t.canvas.width=0;t.canvas.height=0;}}
}
export function pointOccluded(l:CityLayout,x:number,y:number){return l.trees.some(t=>treeOccludes(t,x,y))||l.buildings.some(b=>buildingCenter(b)[1]>y+1&&pointInPolygon(x,y,buildingOutline(b)));}
export function landmarkAt(l:CityLayout,x:number,y:number):Landmark|undefined{
 for(const a of l.landmarks.filter(a=>landmarkKinds.includes(a.kind))){const b=l.buildings.find(b=>b.id===a.id);if(b&&pointInPolygon(x,y,buildingOutline(b)))return a;}
 const palace=l.landmarks.find(a=>a.kind==='palace')!,[px,py]=PALACE_SITE.center;if(pointInPolygon(x,y,palace.footprint)||Math.abs(x-px)<44&&y>py-104&&y<py+8)return palace;
 const island=l.landmarks.find(a=>a.kind==='alcatraz')!;if(pointInPolygon(x,y,island.footprint)||intersects({x,y,width:0,height:0},{x:island.bounds.x+16,y:island.bounds.y+4,width:island.bounds.width-32,height:island.bounds.height-24}))return island;
 const bridge=l.landmarks.find(a=>a.kind==='bridge')!;if(intersects({x,y,width:0,height:0},bridge.bounds)){for(let i=0;i<=120;i++){const p=bridgeSection(i/120,0);if(Math.hypot(x-p.deck[0],y-p.deck[1])<8||Math.hypot(x-p.cable[0],y-p.cable[1])<5)return bridge;}for(const t of BRIDGE.towers){const p=bridgeSection(t,0).deck;if(Math.abs(x-p[0])<9&&y<p[1]+10&&y>p[1]-BRIDGE.height-8)return bridge;}}
 const park=l.landmarks.find(a=>a.kind==='park')!;if(pointInPolygon(x,y,park.footprint))return park;
 return undefined;
}
export function buildingAt(l:CityLayout,b:Building){return project(b.x+b.w/2,b.y+b.d/2);}
export {tintHex};
