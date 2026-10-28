import type {CityLayout} from '../data/types';
import {intersects,type Bounds,type Point} from './cityGeometry';
export type PlacedLabel={id:string;text:string;box:Bounds;anchor:Point;priority:number;angle?:number;center?:Point};
export function chooseLabels(candidates:PlacedLabel[],width:number,height:number,blocked:Bounds[]=[],limit=5){const result:PlacedLabel[]=[];for(const a of [...candidates].sort((a,b)=>b.priority-a.priority)){const b=a.box;if(b.x<12||b.y<12||b.x+b.width>width-12||b.y+b.height>height-12)continue;if([...blocked,...result.map(r=>r.box)].some(r=>intersects({x:b.x-6,y:b.y-6,width:b.width+12,height:b.height+12},r)))continue;result.push(a);if(result.length===limit)break;}return result;}
// Rotated pills are collision-tested by their axis-aligned bounding box.
export function labelBox(center:Point,width:number,height:number,angle=0):Bounds{const c=Math.abs(Math.cos(angle)),s=Math.abs(Math.sin(angle)),w=width*c+height*s,h=width*s+height*c;return {x:center[0]-w/2,y:center[1]-h/2,width:w,height:h};}
export function overviewCandidates(l:CityLayout,screen:(x:number,y:number)=>Point,measure:(text:string)=>number):PlacedLabel[]{return l.labels.map(a=>{const center=screen(...a.at),w=measure(a.text)+20;return {id:a.id,text:a.text,box:labelBox(center,w,20,a.angle),anchor:screen(...a.anchor),priority:a.priority,angle:a.angle,center};});}
export function overviewBlocked(width:number,height:number):Bounds[]{return [{x:8,y:8,width:335,height:66},{x:8,y:height-60,width:300,height:56},{x:width-145,y:height-94,width:140,height:90}];}
export function drawOverviewLabels(c:CanvasRenderingContext2D,l:CityLayout,screen:(x:number,y:number)=>Point,width:number,height:number){
 c.font='600 9.5px system-ui';const labels=chooseLabels(overviewCandidates(l,screen,t=>c.measureText(t).width+t.length*1.1),width,height,overviewBlocked(width,height));
 for(const a of labels){const center=a.center!,w=c.measureText(a.text).width+a.text.length*1.1+20,distance=Math.hypot(a.anchor[0]-center[0],a.anchor[1]-center[1]);
  // A short leader line ties a label to its landmark when they are separated; distant district labels stand alone.
  if(distance>18&&distance<130){c.strokeStyle='rgba(225,236,230,.45)';c.lineWidth=.8;c.beginPath();c.moveTo(...a.anchor);c.lineTo(...center);c.stroke();c.fillStyle='rgba(225,236,230,.8)';c.beginPath();c.arc(a.anchor[0],a.anchor[1],1.6,0,7);c.fill();}
  c.save();c.translate(...center);c.rotate(a.angle??0);c.fillStyle='rgba(10,19,25,.86)';c.beginPath();c.roundRect(-w/2,-10,w,20,10);c.fill();c.strokeStyle='rgba(255,255,255,.14)';c.lineWidth=.7;c.stroke();c.fillStyle='#eef2ea';c.textAlign='center';c.textBaseline='middle';c.letterSpacing='1.1px';c.fillText(a.text,0,.5);c.restore();}
 return labels;
}
