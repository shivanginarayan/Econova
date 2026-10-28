import type {Point} from './cityGeometry';
export type Paint=string|CanvasGradient;
export function face(c:CanvasRenderingContext2D,p:Point[],fill:Paint,edge?:string){c.beginPath();p.forEach((v,i)=>i?c.lineTo(...v):c.moveTo(...v));c.closePath();c.fillStyle=fill;c.fill();if(edge){c.strokeStyle=edge;c.lineWidth=.55;c.stroke();}}
export function oval(c:CanvasRenderingContext2D,x:number,y:number,rx:number,ry:number,fill:Paint,rotation=0){c.beginPath();c.ellipse(x,y,Math.max(.01,rx),Math.max(.01,ry),rotation,0,Math.PI*2);c.fillStyle=fill;c.fill();}
export function stroke(c:CanvasRenderingContext2D,p:Point[],color:string,w=1){c.beginPath();p.forEach((v,i)=>i?c.lineTo(...v):c.moveTo(...v));c.strokeStyle=color;c.lineWidth=w;c.lineJoin='round';c.lineCap='round';c.stroke();}
export function tint(hex:string,n:number){const v=parseInt(hex.slice(1),16);return `rgb(${Math.min(255,Math.round((v>>16)*n))},${Math.min(255,Math.round(((v>>8)&255)*n))},${Math.min(255,Math.round((v&255)*n))})`;}
export function material(c:CanvasRenderingContext2D,x:number,y:number,w:number,h:number,color:string,bright=1,dark=.87){const g=c.createLinearGradient(x,y,x+w,y+h);g.addColorStop(0,tint(color,bright));g.addColorStop(1,tint(color,dark));return g;}
// Shadows fall south-east, away from the warm north-west light.
export const LIGHT={x:.55,y:.3};
export function shadowHull(foot:Point[],height:number):Point[]{
 const all=[...foot,...foot.map(p=>[p[0]+height*LIGHT.x,p[1]+height*LIGHT.y] as Point)].sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const cross=(a:Point,b:Point,p:Point)=>(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);
 const lower:Point[]=[],upper:Point[]=[];for(const p of all){while(lower.length>1&&cross(lower.at(-2)!,lower.at(-1)!,p)<=0)lower.pop();lower.push(p);}for(const p of [...all].reverse()){while(upper.length>1&&cross(upper.at(-2)!,upper.at(-1)!,p)<=0)upper.pop();upper.push(p);}return [...lower.slice(0,-1),...upper.slice(0,-1)];
}
export function castShadow(c:CanvasRenderingContext2D,foot:Point[],height:number,opacity=.2){face(c,shadowHull(foot,height),`rgba(44,58,39,${opacity})`);}
// Small architectural solids in screen coordinates, sharing the main model's 2:1 projection.
export function block(c:CanvasRenderingContext2D,x:number,y:number,w:number,d:number,h:number,color='#ded6c3'){
 const p:Point=[x,y],a:Point=[x+w,y+w*.5],z:Point=[x+w-d,y+(w+d)*.5],v:Point=[x-d,y+d*.5];
 face(c,[v,z,[z[0],z[1]-h],[v[0],v[1]-h]],material(c,v[0],v[1]-h,w,h,color,.96,.84));face(c,[a,z,[z[0],z[1]-h],[a[0],a[1]-h]],material(c,a[0],a[1]-h,-d,h,color,.8,.68));face(c,[[x,y-h],[a[0],a[1]-h],[z[0],z[1]-h],[v[0],v[1]-h]],material(c,x-d,y-h,w+d,15,color,1.1,1),'rgba(255,248,220,.38)');return {p,a,z,v};
}
export function arch(c:CanvasRenderingContext2D,x:number,bottom:number,w:number,h:number,trim='#e5d2b4',dark='#646a60',thickness=1.8){c.beginPath();c.moveTo(x-w/2,bottom);c.lineTo(x-w/2,bottom-h+w/2);c.arc(x,bottom-h+w/2,w/2,Math.PI,Math.PI*2);c.lineTo(x+w/2,bottom);c.closePath();c.fillStyle=dark;c.fill();c.strokeStyle=trim;c.lineWidth=thickness;c.stroke();}
export function arcade(c:CanvasRenderingContext2D,a:Point,b:Point,h:number,count:number,lod:number,trim='#eee1c5',dark='#738078'){
 const width=Math.hypot(b[0]-a[0],b[1]-a[1]);c.save();c.transform((b[0]-a[0])/width,(b[1]-a[1])/width,0,1,a[0],a[1]-h);
 for(let i=0;i<count;i++){const x=(i+.5)*width/count;arch(c,x,h-3,width/count*.47,h*.55,trim,dark,lod?1.2:.8);}
 stroke(c,[[0,2],[width,2]],trim,1.4);c.restore();
}
export const TREE_COLORS=['#40702a','#4f8131','#365f25','#5c8b36'];
// Round, saturated canopies with a sunlit north-west highlight and a trunk dot, as in the demo.
export function foliage(c:CanvasRenderingContext2D,x:number,y:number,size:number,color='#56813f',kind=0,lod=0){
 stroke(c,[[x,y],[x,y-size*.9]],'#7b5f40',Math.max(.8,size*.3));
 if(kind===1){const cy=y-size*1.9,g=c.createRadialGradient(x-size*.3,cy-size*.8,size*.15,x,cy,size*1.7);g.addColorStop(0,tintHex(color,1.35));g.addColorStop(.55,color);g.addColorStop(1,tintHex(color,.68));oval(c,x,cy,size*.62,size*1.45,g);return;}
 const cy=y-size*1.5,g=c.createRadialGradient(x-size*.38,cy-size*.42,size*.12,x+size*.12,cy+size*.18,size*1.18);g.addColorStop(0,tintHex(color,1.34));g.addColorStop(.5,color);g.addColorStop(1,tintHex(color,.62));
 c.beginPath();c.arc(x,cy,size,0,Math.PI*2);if(size>4.2){c.moveTo(x+size*1.05,cy+size*.25);c.arc(x+size*.5,cy+size*.25,size*.6,0,Math.PI*2);}c.fillStyle=g;c.fill();
 if(lod>0){c.fillStyle='rgba(255,255,220,.18)';c.beginPath();c.arc(x-size*.35,cy-size*.38,size*.34,0,Math.PI*2);c.fill();}
}
export function tintHex(hex:string,n:number){const v=parseInt(hex.slice(1),16);return '#'+[v>>16,(v>>8)&255,v&255].map(a=>Math.min(255,Math.round(a*n)).toString(16).padStart(2,'0')).join('');}
