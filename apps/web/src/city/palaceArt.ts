import type {CityLayout} from '../data/types';
import {PALACE_SITE,boundsOf,type Point} from './cityGeometry';
import {face,oval,stroke,material,block,arch,foliage} from './modelArt';
type LOD=0|1|2;
// Thick terracotta columns with capitals and bases, not thin sticks.
function column(c:CanvasRenderingContext2D,x:number,y:number,h:number,w:number,lod:LOD){
 block(c,x,y,w*.62,w*.62,2.2,'#e3d4b8');const g=c.createLinearGradient(x-w/2,0,x+w/2,0);g.addColorStop(0,'#e9b9a0');g.addColorStop(.4,'#cf917a');g.addColorStop(1,'#a9634f');c.fillStyle=g;c.fillRect(x-w/2,y-h,w,h-3);block(c,x,y-h+1.5,w*.74,w*.74,2.4,'#efd9b6');
 if(lod>0){for(let i=-1;i<=1;i++)stroke(c,[[x+i*w*.24,y-h+3],[x+i*w*.24,y-4]],'rgba(108,61,44,.25)',.4);for(const side of [-1,1]){c.beginPath();c.arc(x+side*w*.52,y-h+2.4,w*.17,0,Math.PI*1.7);c.strokeStyle='#b39673';c.lineWidth=.5;c.stroke();}}
}
export function renderPalace(c:CanvasRenderingContext2D,lod:LOD){
 const [x,y]=PALACE_SITE.center,rx=36,ry=15.5,h=50;
 // Stepped circular platform jutting into the lagoon.
 for(const [dy,r,fill]of [[4,1.06,'#c3b192'],[2,1.04,'#ebdcbd'],[0,1,'#d2c09f'],[-2,.97,'#f3e5c8']] as const)oval(c,x,y+dy,PALACE_SITE.rx*r,PALACE_SITE.ry*r+2,fill);
 for(const [dx,dy]of [[-50,4],[-38,13],[42,12],[52,3]])foliage(c,x+dx,y+dy,3.4,'#5c8c3d',dx%2?1:0,lod);
 const ring=Array.from({length:10},(_,i)=>{const a=Math.PI/10+i*Math.PI/5;return [x+Math.cos(a)*rx,y+Math.sin(a)*ry-4] as Point;});
 const back=ring.filter(p=>p[1]<y-4),front=ring.filter(p=>p[1]>=y-4);
 for(const p of back)column(c,p[0],p[1],h,6.4,lod);
 // Drum: open arches between the columns, dark inside.
 for(let i=0;i<10;i++){const a=ring[i],b=ring[(i+1)%10];if((a[1]+b[1])/2<y-4)continue;face(c,[a,b,[b[0],b[1]-h],[a[0],a[1]-h]],material(c,a[0],a[1]-h,b[0]-a[0],h,'#dcc0a1',a[0]<x?1.08:.92,a[0]<x?.95:.8));const w=Math.hypot(b[0]-a[0],b[1]-a[1]);c.save();c.transform((b[0]-a[0])/w,(b[1]-a[1])/w,0,1,a[0],a[1]-h);arch(c,w/2,h,w*.62,h-8,'#f2e3c6','#5b6457',lod?2.2:1.7);if(lod>0)for(let j=0;j<7;j++){const t=Math.PI+j/6*Math.PI,r=w*.31;stroke(c,[[w/2+Math.cos(t)*(r+1),8+r+Math.sin(t)*(r+1)],[w/2+Math.cos(t)*(r+3),8+r+Math.sin(t)*(r+3)]],'#ae9574',.5);}c.restore();}
 for(const p of front)column(c,p[0],p[1],h,7.2,lod);
 // Continuous entablature ring with a relief band, then the shallow dome with its rim and finial.
 for(const [dy,r,fill]of [[-h-3,1.17,'#c4ab89'],[-h-6,1.19,'#efddbc'],[-h-11,1.14,'#d9c09c'],[-h-14,1.17,'#f4e4c7']] as const)oval(c,x,y+dy,rx*r,rx*r*.44,fill);
 for(let i=0;i<9;i++){const a=i/8*Math.PI,px=x+Math.cos(a)*rx*1.12,py=y-h-9+Math.sin(a)*rx*.46;stroke(c,[[px-1.6,py],[px+1.6,py]],'#b99d77',lod?.9:.6);}
 const dy=y-h-18,dome=c.createRadialGradient(x-12,dy-14,2,x+8,dy+6,44);dome.addColorStop(0,'#fff7e4');dome.addColorStop(.55,'#efe3c9');dome.addColorStop(1,'#c4b396');
 c.beginPath();c.moveTo(x-34,dy);c.bezierCurveTo(x-33,dy-30,x+33,dy-30,x+34,dy);c.bezierCurveTo(x+26,dy+13,x-26,dy+13,x-34,dy);c.fillStyle=dome;c.fill();
 c.beginPath();c.ellipse(x,dy+1,35,13,0,0,Math.PI);c.strokeStyle='#a99a80';c.lineWidth=1;c.stroke();c.beginPath();c.ellipse(x,dy,36,13,0,0,Math.PI);c.strokeStyle='#f8eacf';c.lineWidth=1.5;c.stroke();
 oval(c,x,dy-22,3,1.4,'#e2d5b8');c.fillStyle='#efe3c9';c.fillRect(x-1,dy-27,2,5);oval(c,x,dy-27,1.6,1.6,'#f6ecd6');
 // Curved colonnade wings on the platform's front, each with a continuous moulded beam.
 for(const [start,end]of [[Math.PI*.6,Math.PI*.9],[Math.PI*.1,Math.PI*.4]]){const feet=Array.from({length:5},(_,i)=>{const a=start+(end-start)*i/4;return [x+Math.cos(a)*(PALACE_SITE.rx-5),y+2+Math.sin(a)*(PALACE_SITE.ry-1)] as Point;}).sort((a,b)=>a[1]-b[1]);
  stroke(c,feet.slice().sort((a,b)=>a[0]-b[0]),'#ddcaa8',6);for(const p of feet)column(c,p[0],p[1],24,4.6,lod);const row=feet.slice().sort((a,b)=>a[0]-b[0]);for(let i=1;i<row.length;i++){const a=row[i-1],b=row[i];face(c,[[a[0],a[1]-27],[b[0],b[1]-27],[b[0],b[1]-22],[a[0],a[1]-22]],'#c3a482');stroke(c,[[a[0],a[1]-28],[b[0],b[1]-28]],'#f0dfbe',2.4);}}
}
export function renderAlcatraz(c:CanvasRenderingContext2D,lod:LOD,layout:CityLayout){
 const shore=layout.island.alcatraz,b=boundsOf(shore),cx=b.x+b.width/2,cy=b.y+b.height/2,k=b.width/160;
 face(c,shore.map(p=>[p[0],p[1]+4.5]),'#7d8a7b');face(c,shore,'#d9d3bb');face(c,shore.map(p=>[cx+(p[0]-cx)*.9,cy+(p[1]-cy)*.78-1.5]),'#8daa72');
 for(let i=1;i<shore.length;i+=4){const p=shore[i];if(p[1]<cy)continue;face(c,[[p[0]-3,p[1]],[p[0],p[1]-3],[p[0]+4,p[1]+2],[p[0]-1,p[1]+3]],i%2?'#bfc3ad':'#efe6cf');}
 // Dock on the west tip, terraced lawn to the east.
 face(c,[[b.x-6,cy+3],[b.x+12,cy-1],[b.x+14,cy+2],[b.x-4,cy+6]],'#e4d9be');stroke(c,[[b.x-4,cy+6],[b.x+14,cy+2]],'#9aa699',1);
 oval(c,cx-14*k,cy+2,26*k,6,'#9fc07a');stroke(c,[[cx-50*k,cy+8],[cx,cy+11],[cx+50*k,cy+7]],'#ece2c9',2);
 // The cellhouse: a row of low pale blocks with flat roofs, small windows and a dark base.
 // The prison sits on the east of the island and the lighthouse on the west, so downtown towers never hide either.
 for(const [dx,dy,w,d,h]of [[14,-2,20,9,8],[32,-6,32,12,11],[58,-1,16,8,7]])block(c,cx+dx*k,cy+dy,w*k,d*k*.9,h,'#ece3cb');
 c.fillStyle='rgba(80,92,84,.55)';c.fillRect(cx+6*k,cy+5.5,66*k,1.2);
 for(let i=0;i<(lod?14:8);i++){c.fillStyle='#6f8077';c.fillRect(cx+30*k+i*(lod?2:3.2)*k,cy+1-i*.06,.8,1.7);}
 // Lighthouse: taller than the prison, white, with a lit lantern.
 const lx=cx-54*k,ly=cy-4;c.fillStyle=material(c,lx-2,ly-26,5,26,'#f7efda',1.1,.8);c.fillRect(lx-2.2,ly-26,4.4,26);oval(c,lx,ly-26,3.2,1.4,'#ece8d2');c.fillStyle='#f3d27a';c.fillRect(lx-1.8,ly-31,3.6,4.4);oval(c,lx,ly-31.5,3,1.3,'#5f706a');
 for(const [tx,ty,r]of [[cx-66*k,cy+4,3],[cx-30*k,cy+7,3.4],[cx-4*k,cy+5,3],[cx+70*k,cy+3,3.4]])foliage(c,tx,ty,r,'#4f7e34',0,lod);
}
