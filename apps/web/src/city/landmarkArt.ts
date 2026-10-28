import type {CityLayout} from '../data/types';
import {BRIDGE,intersects,type Bounds,type Point} from './cityGeometry';
import {face,oval,stroke} from './modelArt';
import {renderPalace} from './palaceArt';
export {lakeShore as shoreline} from './cityGeometry';
// One continuous cable per side: rising from each land anchorage to the tower tops and sagging across the main span.
export function bridgeSection(t:number,side=-1){
 const u=Math.max(0,Math.min(1,t)),[t1,t2]=BRIDGE.towers,H=BRIDGE.height;
 const h=u<t1?H*(u/t1)**1.45:u>t2?H*((1-u)/(1-t2))**1.45:H-H*.78*4*((u-t1)/(t2-t1))*(1-(u-t1)/(t2-t1));
 const [ax,ay]=BRIDGE.south,[bx,by]=BRIDGE.north,x=ax+(bx-ax)*u+side*4.4,y=ay+(by-ay)*u+side*3.1;
 return {deck:[x,y] as Point,cable:[x,y-h] as Point,height:h};
}
const ORANGE='#d9562f',ORANGE_LIGHT='#f07a4f',ORANGE_DARK='#a8391f';
function tower(c:CanvasRenderingContext2D,t:number,side:number,lod:number){
 const p=bridgeSection(t,side),x=p.deck[0],y=p.deck[1],H=BRIDGE.height+5;
 oval(c,x,y+11,5,2.2,'#e9e4d2');face(c,[[x-2.4,y+10],[x+2.4,y+10.6],[x+2.4,y-H],[x-2.4,y-H-.6]],ORANGE);stroke(c,[[x-1.4,y-H+1],[x-1.4,y+9]],ORANGE_LIGHT,1.1);
 if(lod>0)for(let k=10;k<H;k+=7)stroke(c,[[x-2.2,y-k],[x+2.2,y-k+.3]],'rgba(120,40,20,.35)',.4);
}
export function drawBridge(c:CanvasRenderingContext2D,lod:0|1|2){
 const [t1,t2]=BRIDGE.towers,cable=(side:number)=>Array.from({length:241},(_,i)=>bridgeSection(i/240,side).cable);
 const hangers=(side:number,color:string)=>{for(let i=1;i<96;i++){const p=bridgeSection(i/96,side);if(p.height>1.5)stroke(c,[p.cable,p.deck],color,lod?.55:.42);}};
 // Far cable and suspenders, far tower legs, deck slab, near legs and portal bracing, then the near cable.
 hangers(-1,'rgba(236,190,160,.75)');stroke(c,cable(-1),'#e8c2a2',1.3);
 for(const t of [t1,t2])tower(c,t,-1,lod);
 const a0=bridgeSection(0,-1).deck,b0=bridgeSection(1,-1).deck,a1=bridgeSection(0,1).deck,b1=bridgeSection(1,1).deck;
 face(c,[a0,b0,b1,a1],ORANGE);face(c,[a1,b1,[b1[0],b1[1]+4.5],[a1[0],a1[1]+4.5]],ORANGE_DARK);stroke(c,[a0,b0],ORANGE_LIGHT,.9);
 const road=[bridgeSection(0,0).deck,bridgeSection(1,0).deck];stroke(c,road,'#b9502f',3.2);c.setLineDash([2.5,3.5]);stroke(c,road,'rgba(255,226,180,.65)',.5);c.setLineDash([]);
 // Approach truss over the Marina shoreline.
 for(let i=0;i<7;i++){const p=bridgeSection(.012+i*.012,1).deck;stroke(c,[[p[0],p[1]+4.5],[p[0]+2.6,p[1]+9]],ORANGE_DARK,.8);stroke(c,[[p[0]+2.6,p[1]+9],[p[0]+5,p[1]+3.6]],ORANGE_DARK,.8);}
 for(const t of [t1,t2]){tower(c,t,1,lod);const far=bridgeSection(t,-1).deck,near=bridgeSection(t,1).deck,H=BRIDGE.height+5;
  for(const k of [H,H*.72,H*.46,H*.2]){face(c,[[far[0]-2.4,far[1]-k],[near[0]+2.4,near[1]-k],[near[0]+2.4,near[1]-k+(k===H?4:2.6)],[far[0]-2.4,far[1]-k+(k===H?4:2.6)]],k===H?ORANGE_LIGHT:ORANGE);}}
 hangers(1,'rgba(255,214,186,.9)');stroke(c,cable(1),'#f6d4b4',1.5);
 for(const [i,t]of [.08,.17,.31,.44,.58,.69,.86,.93].entries()){const p=bridgeSection(t,i%2?-.45:.45).deck;c.save();c.translate(p[0],p[1]);c.rotate(Math.atan2(BRIDGE.north[1]-BRIDGE.south[1],BRIDGE.north[0]-BRIDGE.south[0]));c.fillStyle=['#f2cf5b','#e2553f','#7fbcc6','#f6f1e4'][i%4];c.fillRect(-2.4,-.9,4.8,1.8);c.restore();}
}
export const drawPalace=renderPalace;
export function pierGeometry(x:number,y:number,length:number,normal:Point=[1,0],width=5){const n=Math.hypot(...normal),out:Point=[normal[0]/n,normal[1]/n],t:Point=[-out[1],out[0]],p=(d:number,w:number):Point=>[x+out[0]*d+t[0]*w,y+out[1]*d+t[1]*w];return {normal:out,tangent:t,point:p,top:[p(-4,-width/2),p(length,-width/2),p(length,width/2),p(-4,width/2)]};}
export function drawWaterfront(c:CanvasRenderingContext2D,layout:CityLayout,lod:0|1|2,bounds:Bounds){
 for(const [index,pier]of layout.piers.entries()){const g=pierGeometry(pier.x,pier.y,pier.length,pier.normal,pier.width);const box={x:Math.min(...g.top.map(p=>p[0]))-14,y:Math.min(...g.top.map(p=>p[1]))-14,width:pier.length+30,height:60};if(!intersects(box,bounds))continue;
  const near=g.top[2][1]>g.top[1][1]?[g.top[3],g.top[2]]:[g.top[0],g.top[1]],far=g.top[2][1]>g.top[1][1]?[g.top[0],g.top[1]]:[g.top[3],g.top[2]];
  face(c,g.top.map(p=>[p[0]+3,p[1]+3.5] as Point),'rgba(40,82,110,.22)');
  // Short perpendicular slip fingers, on one side only, leave room for a row of moored boats.
  if(pier.slips)for(let d=16;d<pier.length-6;d+=11)face(c,[g.point(d-.7,pier.slips*pier.width/2),g.point(d+.7,pier.slips*pier.width/2),g.point(d+.7,pier.slips*(pier.width/2+11)),g.point(d-.7,pier.slips*(pier.width/2+11))],'#e2d9c2');
  face(c,[near[0],near[1],[near[1][0],near[1][1]+2.4],[near[0][0],near[0][1]+2.4]],'#93a39f');face(c,g.top,'#e8dfc8');stroke(c,far,'#f8f0dc',.6);
  if(lod>0)for(let d=6;d<pier.length;d+=6)stroke(c,[g.point(d,-pier.width/2+.6),g.point(d,pier.width/2-.6)],'rgba(150,138,110,.35)',.35);
  if(index===0){const e=g.point(pier.length-5,0);face(c,[[e[0]-1.6,e[1]],[e[0]+1.6,e[1]],[e[0]+1.2,e[1]-11],[e[0]-1.2,e[1]-11]],'#f4efe2');face(c,[[e[0]-1.8,e[1]-11],[e[0]+1.8,e[1]-11],[e[0],e[1]-14]],'#5c6b67');}
 }
 for(const boat of layout.boats){if(boat.x<bounds.x-12||boat.x>bounds.x+bounds.width+12||boat.y<bounds.y-18||boat.y>bounds.y+bounds.height+8)continue;c.save();c.translate(boat.x,boat.y);
  if(boat.sail){c.rotate(boat.angle);oval(c,3,1.6,7,1.4,'rgba(232,248,250,.32)');face(c,[[-4.5,0],[4.5,0],[3,2],[-3,2]],'#f7f4ea');face(c,[[-4.5,0],[4.5,0],[3,2],[-3,2]].map(p=>[p[0],p[1]+.8] as Point),'rgba(70,90,100,.25)');stroke(c,[[0,0],[0,-13]],'#c9d2cf',.5);face(c,[[.4,-13],[.4,-1],[6,-1]],'#fffdf6');face(c,[[-.4,-10],[-.4,-1],[-4,-1]],'#ecebe2');}
  else{c.rotate(boat.angle);face(c,[[-3.6,-1],[2.4,-1],[3.8,0],[2.4,1],[-3.6,1]],'#f8f5ec');face(c,[[-1.4,-.6],[.8,-.6],[.8,.6],[-1.4,.6]],'#c8d6d8');if(lod>0)stroke(c,[[0,0],[0,-5]],'#d2dad6',.4);}
  c.restore();}
}
