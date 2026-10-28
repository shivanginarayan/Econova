import type {Building} from '../data/types';
import {buildingPoint,buildingFootprint,buildingCenter,boundsOf,type Point,type Bounds} from './cityGeometry';
import {face,oval,stroke,tint,arch} from './modelArt';
const bProject=buildingPoint;
export const landmarkKinds=['coit','pyramid','salesforce','ferry'];
const up=(p:Point,h:number):Point=>[p[0],p[1]-h];
function hull(points:Point[]):Point[]{const ps=[...points].sort((a,b)=>a[0]-b[0]||a[1]-b[1]),cross=(a:Point,b:Point,p:Point)=>(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]),l:Point[]=[],u:Point[]=[];for(const p of ps){while(l.length>1&&cross(l.at(-2)!,l.at(-1)!,p)<=0)l.pop();l.push(p);}for(const p of [...ps].reverse()){while(u.length>1&&cross(u.at(-2)!,u.at(-1)!,p)<=0)u.pop();u.push(p);}return [...l.slice(0,-1),...u.slice(0,-1)];}
// Warm north-west light: top faces brightest, south-west faces mid, south-east faces darkest.
const faceShade=(a:Point,b:Point)=>{const dx=b[0]-a[0],dy=b[1]-a[1],n=Math.hypot(dx,dy)||1;return .84-.26*(dy/n);};
const visibleSides=(foot:Point[])=>foot.map((p,i)=>[p,foot[(i+1)%foot.length]] as [Point,Point]).filter(([a,b])=>b[0]<a[0]-.01);
function sides(c:CanvasRenderingContext2D,foot:Point[],h:number,color:string,base=0){
 for(const [a,b]of visibleSides(foot)){const k=faceShade(a,b),g=c.createLinearGradient(0,a[1]-base-h,0,a[1]-base);g.addColorStop(0,tint(color,k+.05));g.addColorStop(1,tint(color,k-.05));face(c,[up(a,base),up(b,base),up(b,base+h),up(a,base+h)],g);}
}
function roofTop(c:CanvasRenderingContext2D,foot:Point[],h:number,color:string,edge='rgba(255,250,232,.55)'){const top=foot.map(p=>up(p,h)),g=c.createLinearGradient(top[3][0],top[0][1],top[1][0],top[2][1]);g.addColorStop(0,tint(color,1.1));g.addColorStop(1,tint(color,1.01));face(c,top,g,edge);return top;}
// Small window dots on each visible face; lit at night by the canvas overlay using the same positions.
export function windowDots(b:Building,lod:number):Point[]{
 if(['coit','ferry','pyramid','salesforce'].includes(b.kind))return [];const foot=buildingFootprint(b),out:Point[]=[];const tall=b.kind==='tower'||b.kind==='office',rowGap=tall?7:6.5,colGap=tall?6:7;
 for(const [a,bb]of visibleSides(foot)){const len=Math.hypot(bb[0]-a[0],bb[1]-a[1]),cols=Math.max(1,Math.floor(len/colGap)-1);for(let y=5;y<b.h-4;y+=rowGap)for(let i=1;i<=cols;i++){const t=i/(cols+1);out.push([a[0]+(bb[0]-a[0])*t,a[1]+(bb[1]-a[1])*t-y]);}if(!lod&&out.length>8)break;}
 return out;
}
export function ferryGeometry(b:Building){
 const L=(u:number,v:number,h=0)=>bProject(b,b.x+b.w*u,b.y+b.d*v,h),hall=[L(0,0),L(1,0),L(1,1),L(0,1)];
 // The clock tower stands at the west end of the hall, not in the middle.
 const tu=.085,tv=.62,s=.62/b.w,sv=.62/b.d,tower=[L(tu-s/2,tv-sv/2),L(tu+s/2,tv-sv/2),L(tu+s/2,tv+sv/2),L(tu-s/2,tv+sv/2)];
 const length=Math.hypot(hall[1][0]-hall[0][0],hall[1][1]-hall[0][1]),towerWidth=Math.hypot(tower[1][0]-tower[0][0],tower[1][1]-tower[0][1]);
 return {center:buildingCenter(b),hall,tower,towerBase:L(tu,tv),towerHeight:118,clockFaces:1,length,towerWidth,westEnd:L(.02,.5),eastEnd:L(.98,.5)};
}
export function buildingOutline(b:Building):Point[]{
 const f=buildingFootprint(b),h=b.h+(b.elevation??0),tops=f.map(p=>up(p,h));
 if(b.kind==='pyramid')return hull([...f,up(buildingCenter(b),h)]);
 if(b.kind==='coit'){const p=buildingCenter(b);return [[p[0]-12,p[1]+5],[p[0]+12,p[1]+5],[p[0]+8,p[1]-h-8],[p[0]-8,p[1]-h-8]];}
 if(b.kind==='salesforce')return hull([...f,...tops.map(p=>up(p,-8)),up(buildingCenter(b),h+4)]);
 if(b.kind==='ferry'){const g=ferryGeometry(b);return hull([...g.hall,...g.hall.map(p=>up(p,b.h+11)),...g.tower.map(p=>up(p,g.towerHeight)),up(g.towerBase,g.towerHeight+22)]);}
 if(b.kind==='house'&&b.roof==='hip')return hull([...f,...tops,up(buildingCenter(b),h+Math.min(b.w,b.d)*13)]);
 return hull([...f,...tops]);
}
export function buildingBounds(b:Building):Bounds{const p=buildingOutline(b),xs=p.map(p=>p[0]),ys=p.map(p=>p[1]);return {x:Math.min(...xs)-3,y:Math.min(...ys)-3,width:Math.max(...xs)-Math.min(...xs)+6,height:Math.max(...ys)-Math.min(...ys)+6};}
function hipRoof(c:CanvasRenderingContext2D,b:Building,color:string){
 const e=b.h+(b.elevation??0),rise=Math.min(b.w,b.d)*13,long=b.w>=b.d,inset=Math.min(b.w,b.d)/2;
 const r0=long?bProject(b,b.x+inset,b.y+b.d/2,e+rise):bProject(b,b.x+b.w/2,b.y+inset,e+rise),r1=long?bProject(b,b.x+b.w-inset,b.y+b.d/2,e+rise):bProject(b,b.x+b.w/2,b.y+b.d-inset,e+rise);
 const t=buildingFootprint(b).map(p=>up(p,e));const planes:Array<[Point[],number]>=long?[[[t[0],t[1],r1,r0],1.0],[[t[1],t[2],r1],.78],[[t[2],t[3],r0,r1],.92],[[t[3],t[0],r0],1.1]]:[[[t[0],t[1],r0],1.0],[[t[1],t[2],r1,r0],.78],[[t[2],t[3],r1],.92],[[t[3],t[0],r0,r1],1.1]];
 for(const [p,k]of planes.sort((a,b)=>Math.min(...a[0].map(q=>q[1]))-Math.min(...b[0].map(q=>q[1]))))face(c,p,tint(color,k));stroke(c,[r0,r1],tint(color,1.22),.6);
}
export function prism(c:CanvasRenderingContext2D,b:Building,lod:0|1|2=0){
 if(b.kind==='coit'){drawCoit(c,b);return;}if(b.kind==='salesforce'){drawSalesforce(c,b,lod);return;}if(b.kind==='pyramid'){drawPyramid(c,b,lod);return;}if(b.kind==='ferry'){drawFerryHall(c,b,lod);drawFerryClock(c,b,lod);return;}
 const foot=buildingFootprint(b),e=b.elevation??0,h=b.h;sides(c,foot,h,b.color,e);
 const roofColor=b.kind==='house'&&b.roof==='hip'?['#b98f84','#9aa6a6','#c3a881','#a8b39f','#8e9494'][b.kit??0]:b.color;
 if(b.kind==='house'&&b.roof==='hip')hipRoof(c,b,roofColor);else{const top=roofTop(c,foot,h+e,roofColor);if(b.kind!=='tower'&&lod>0&&(b.kit??0)%2===0){const m=top.map(p=>[p[0]*.72+(top[0][0]+top[2][0])/2*.28,p[1]*.72+(top[0][1]+top[2][1])/2*.28] as Point);face(c,m,tint(roofColor,.93));}}
 const sideFaces=visibleSides(foot);
 if(b.kind==='tower'||b.kind==='office'){
  // Curtain-wall rhythm: vertical mullions and floor bands, finer when zoomed.
  for(const [a,z]of sideFaces){const len=Math.hypot(z[0]-a[0],z[1]-a[1]),cols=Math.max(2,Math.round(len/(lod?4:7)));for(let i=1;i<cols;i++){const t=i/cols,x=a[0]+(z[0]-a[0])*t,y=a[1]+(z[1]-a[1])*t;stroke(c,[[x,y-e-2],[x,y-e-h+2]],'rgba(255,255,255,.16)',lod?.45:.35);}
   for(let y=lod?6:12;y<h-3;y+=lod?6:12)stroke(c,[up(a,e+y),up(z,e+y)],'rgba(70,86,96,.14)',.5);}
  if(lod>0)for(const p of windowDots(b,lod))face(c,[[p[0]-.7,p[1]-1.4],[p[0]+.7,p[1]-1.1],[p[0]+.7,p[1]+.5],[p[0]-.7,p[1]+.2]],'rgba(84,110,124,.45)');
  stroke(c,roofEdge(foot,h+e),'rgba(255,255,255,.5)',.7);return;
 }
 if(lod>0)for(const p of windowDots(b,lod))face(c,[[p[0]-.65,p[1]-1.3],[p[0]+.65,p[1]-1],[p[0]+.65,p[1]+.5],[p[0]-.65,p[1]+.2]],'#7d9093');
 if(b.kind==='house'&&lod>0){const door=bProject(b,b.x+b.w*.62,b.y+b.d,e);face(c,[[door[0]-1.5,door[1]-6],[door[0]+1.5,door[1]-5.3],[door[0]+1.5,door[1]],[door[0]-1.5,door[1]-.7]],'#86766a');}
 if(b.kind==='shop'){
  const start=bProject(b,b.x+.02,b.y+b.d,e+10),end=bProject(b,b.x+b.w-.02,b.y+b.d,e+10),tip=bProject(b,b.x+b.w-.02,b.y+b.d+.16,e+6.5),left=bProject(b,b.x+.02,b.y+b.d+.16,e+6.5);
  const door=shopFront(b);face(c,[[door[0]-4,door[1]-8],[door[0]+4,door[1]-6],[door[0]+4,door[1]],[door[0]-4,door[1]-2]],'#5d7066');
  face(c,[start,end,tip,left],tint(b.awning??'#cfa78b',1.02));stroke(c,[left,tip],'#f3e5c8',1.1);
  if(lod>0)for(let i=0;i<=6;i++){const t=i/6;stroke(c,[[start[0]+(end[0]-start[0])*t,start[1]+(end[1]-start[1])*t],[left[0]+(tip[0]-left[0])*t,left[1]+(tip[1]-left[1])*t]],'rgba(255,244,222,.75)',.8);}
 }
 if(b.kind==='bank'){const a=bProject(b,b.x+.05,b.y+b.d,e),z=bProject(b,b.x+b.w-.05,b.y+b.d,e);for(let i=0;i<=4;i++){const t=i/4,x=a[0]+(z[0]-a[0])*t,y=a[1]+(z[1]-a[1])*t;stroke(c,[[x,y-1],[x,y-h+8]],'#f5f0e2',lod?1.4:1);}const pa=up(a,h-6),pz=up(z,h-6),mid:Point=[(pa[0]+pz[0])/2,(pa[1]+pz[1])/2-6];face(c,[pa,pz,mid],'#f2ecdc');stroke(c,[pa,mid,pz],'#c8bfa8',.6);}
}
function roofEdge(foot:Point[],h:number){const t=foot.map(p=>up(p,h));return [t[3],t[2],t[1]];}
export function shopFront(b:Building){return bProject(b,b.x+b.w*.5,b.y+b.d,b.elevation??0);}
function drawPyramid(c:CanvasRenderingContext2D,b:Building,lod:number){
 const f=buildingFootprint(b),apex=up(buildingCenter(b),b.h),spireBase=up(buildingCenter(b),b.h*.88);
 // A low podium, then two visible tapering faces and the slim spire.
 sides(c,f,6,'#e7e2d4');const t=f.map(p=>up(p,6)),inset=t.map(p=>[p[0]+(spireBase[0]-p[0])*.06,p[1]+(spireBase[1]-p[1])*.06+1] as Point);
 face(c,[inset[2],inset[3],spireBase],'#f6f3ea');face(c,[inset[1],inset[2],spireBase],'#d3d7d0');
 const bands=lod?24:12;for(let i=1;i<bands;i++){const k=i/bands;for(const [a,z]of [[inset[2],inset[3]],[inset[1],inset[2]]] as Array<[Point,Point]>)stroke(c,[[a[0]+(spireBase[0]-a[0])*k,a[1]+(spireBase[1]-a[1])*k],[z[0]+(spireBase[0]-z[0])*k,z[1]+(spireBase[1]-z[1])*k]],'rgba(128,136,132,.16)',.45);}
 // The two "wings" that make the Transamerica silhouette.
 const wl=[inset[3][0]+(spireBase[0]-inset[3][0])*.58,inset[3][1]+(spireBase[1]-inset[3][1])*.58] as Point,wr=[inset[1][0]+(spireBase[0]-inset[1][0])*.58,inset[1][1]+(spireBase[1]-inset[1][1])*.58] as Point;
 face(c,[[wl[0]-3,wl[1]+6],[wl[0]+1,wl[1]+7],[wl[0]+1,wl[1]-14],[wl[0]-2,wl[1]-11]],'#efebe0');face(c,[[wr[0]+3,wr[1]+6],[wr[0]-1,wr[1]+7],[wr[0]-1,wr[1]-14],[wr[0]+2,wr[1]-11]],'#cbd0c8');
 stroke(c,[inset[2],spireBase],'rgba(255,255,255,.7)',.7);face(c,[[spireBase[0]-2.2,spireBase[1]+2],[spireBase[0]+2.2,spireBase[1]+2],apex],'#f2efe6');
}
function drawSalesforce(c:CanvasRenderingContext2D,b:Building,lod:number){
 // Blue-grey glass, rounded crown, vertical and horizontal lines and a bright highlight stripe.
 const f=buildingFootprint(b),p=buildingCenter(b),x=p[0],y=p[1],h=b.h,r=(f[1][0]-f[3][0])/2*.86,cap=r*.95;
 const body=c.createLinearGradient(x-r,0,x+r,0);body.addColorStop(0,'#a9c8d8');body.addColorStop(.3,'#d4e8ef');body.addColorStop(.62,'#86a9bc');body.addColorStop(1,'#5f8296');
 const shape=()=>{c.beginPath();c.moveTo(x-r,y);c.lineTo(x-r,y-h+cap);c.bezierCurveTo(x-r,y-h-cap*.35,x+r,y-h-cap*.35,x+r,y-h+cap);c.lineTo(x+r,y);c.bezierCurveTo(x+r,y+r*.5,x-r,y+r*.5,x-r,y);c.closePath();};
 shape();c.fillStyle=body;c.fill();const shade=c.createLinearGradient(0,y-h,0,y);shade.addColorStop(0,'rgba(236,246,250,.32)');shade.addColorStop(1,'rgba(40,74,96,.22)');c.fillStyle=shade;c.fill();
 c.save();shape();c.clip();for(let i=-r+3;i<r;i+=lod?2.6:4)stroke(c,[[x+i,y-h-cap],[x+i,y+r]],'rgba(232,244,248,.24)',.5);for(let yy=y-h+cap+4;yy<y;yy+=lod?4:7)stroke(c,[[x-r,yy],[x+r,yy+1]],'rgba(70,104,124,.16)',.45);c.fillStyle='rgba(255,255,246,.3)';c.fillRect(x-r*.62,y-h+cap,r*.28,h-cap-4);c.restore();
 c.beginPath();c.moveTo(x-r*.94,y-h+cap*.9);c.bezierCurveTo(x-r*.9,y-h-cap*.22,x+r*.9,y-h-cap*.22,x+r*.94,y-h+cap*.9);c.strokeStyle='#eef7f8';c.lineWidth=1.2;c.stroke();
}
function drawCoit(c:CanvasRenderingContext2D,b:Building){
 // Slender fluted white column with an observation deck and cap, standing alone on its hill.
 const [x,y]=buildingCenter(b),h=b.h,r=6.4;oval(c,x,y+1,r+5,(r+5)*.46,'#c9c6b0');oval(c,x,y-1.5,r+3.4,(r+3.4)*.46,'#efe7cf');c.fillStyle='#e6dfca';c.fillRect(x-r-2.4,y-6,2*r+4.8,4.5);
 const g=c.createLinearGradient(x-r,0,x+r,0);g.addColorStop(0,'#fffaea');g.addColorStop(.42,'#efe8d3');g.addColorStop(1,'#aeb8a8');c.fillStyle=g;c.fillRect(x-r,y-h,r*2,h-4);oval(c,x,y-4,r,r*.42,'#d5d2c0');
 for(let i=-3;i<=3;i++)stroke(c,[[x+i*1.75,y-h+10],[x+i*1.75,y-6]],'rgba(120,128,112,.2)',.45);
 for(let i=-2;i<=2;i++){c.fillStyle='#6f8175';c.fillRect(x+i*2.3-.5,y-h+2.5,1,5.5);}
 oval(c,x,y-h,r+1.5,(r+1.5)*.42,'#f4eddb');oval(c,x,y-h-1.6,r+.4,(r+.4)*.42,'#e3dcc7');c.fillStyle='#f7efdc';c.fillRect(x-r*.62,y-h-6.5,r*1.24,5);oval(c,x,y-h-6.5,r*.62,r*.27,'#fdf6e4');
}
export function drawFerryHall(c:CanvasRenderingContext2D,b:Building,lod:number){
 const g=ferryGeometry(b),f=g.hall,h=b.h,ridge=11;
 const mid=(a:Point,z:Point):Point=>[(a[0]+z[0])/2,(a[1]+z[1])/2];const rw=up(mid(f[0],f[3]),h+ridge),re=up(mid(f[1],f[2]),h+ridge);
 // Long low hall: pale facade with arched windows, dark grey pitched roof, gable on the visible end.
 sides(c,f,h,'#efe6d2');
 face(c,[up(f[0],h),up(f[1],h),re,rw],'#7d8784');face(c,[up(f[3],h),up(f[2],h),re,rw],'#68716f');
 stroke(c,[up(f[3],h),up(f[2],h)],'#f7eedb',1.2);stroke(c,[rw,re],'#929c98',.8);
 for(const [a,z]of visibleSides(f)){const len=Math.hypot(z[0]-a[0],z[1]-a[1]);if(len<40){face(c,[up(a,h),up(z,h),a[0]<z[0]?re:rw],'#e9dfc9');continue;}arcadeFace(c,z,a,h,Math.round(len/9),lod);}
 stroke(c,[f[3],f[2]],'rgba(70,80,72,.35)',.8);
}
function arcadeFace(c:CanvasRenderingContext2D,a:Point,z:Point,h:number,count:number,lod:number){
 const width=Math.hypot(z[0]-a[0],z[1]-a[1]);c.save();c.transform((z[0]-a[0])/width,(z[1]-a[1])/width,0,1,a[0],a[1]-h);
 for(let i=0;i<count;i++){const x=(i+.5)*width/count;arch(c,x,h-2,width/count*.46,h*.5,'#f6edd8','#77847d',lod?1:.7);if(lod>0)arch(c,x,h*.4,width/count*.3,h*.22,'#f6edd8','#8a968f',.6);}
 stroke(c,[[0,h*.45],[width,h*.45]],'rgba(170,158,130,.5)',.6);c.restore();
}
export function drawFerryClock(c:CanvasRenderingContext2D,b:Building,lod:number){
 const g=ferryGeometry(b),f=g.tower,H=g.towerHeight;
 // Stepped white tower: three diminishing stages, a pyramid cap, and a single gold clock face on the front.
 const stage=(s:number,base:number,h:number)=>{const c0=g.towerBase,q=f.map(p=>[c0[0]+(p[0]-c0[0])*s,c0[1]+(p[1]-c0[1])*s] as Point);sides(c,q,h,'#f4eddb',base);roofTop(c,q,base+h,'#f7f1e2','rgba(205,195,170,.7)');return q;};
 stage(1,0,H*.7);const s2=stage(.82,H*.7,H*.13);stage(.66,H*.83,H*.08);
 const top=f.map(p=>[g.towerBase[0]+(p[0]-g.towerBase[0])*.66,g.towerBase[1]+(p[1]-g.towerBase[1])*.66] as Point).map(p=>up(p,H*.91)),apex=up(g.towerBase,H+20);
 for(const [a,z]of visibleSides(top.map(p=>up(p,-H*.91))))face(c,[up(a,H*.91),up(z,H*.91),apex],tint('#f1e9d6',faceShade(a,z)+.06));
 const [a,z]=visibleSides(f).sort((p,q)=>Math.max(q[0][1],q[1][1])-Math.max(p[0][1],p[1][1]))[0];const cx=(a[0]+z[0])/2,cy=(a[1]+z[1])/2-H*.6;
 if(lod>0)for(const [p,q]of visibleSides(f))for(let y=12;y<H*.62;y+=9){const m:Point=[(p[0]+q[0])/2,(p[1]+q[1])/2];face(c,[[m[0]-1,m[1]-y-3],[m[0]+1,m[1]-y-2.5],[m[0]+1,m[1]-y+1],[m[0]-1,m[1]-y+.5]],'#8b978f');}
 oval(c,cx,cy,5.6,6,'#b8963d');oval(c,cx,cy,4.4,4.8,'#2f3b38');stroke(c,[[cx,cy-3.4],[cx,cy],[cx+2.4,cy+.8]],'#f2d98c',.8);
 void s2;
}
export {boundsOf};
