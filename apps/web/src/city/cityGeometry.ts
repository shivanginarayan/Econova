import type {Building,CityLayout} from '../data/types';
export type Point=[number,number];
export type Bounds={x:number;y:number;width:number;height:number};
export const SCENE_WIDTH=1440,SCENE_HEIGHT=940;
export const TABLE={center:[720,530] as Point,radius:650,tilt:.433,thickness:34};
// The home pose frames the tabletop, its base and the tallest landmarks with a thin starfield margin.
export const OVERVIEW={x:720,y:540,width:1345,height:668};
export const project=(x:number,y:number,height=0):Point=>[700+(x-y)*32,195+(x+y)*16-height];
export const unproject=(x:number,y:number):Point=>[(x-700)/64+(y-195)/32,(y-195)/32-(x-700)/64];
// The demo reference frame (2000x1000, rim centred at 972,600 with a 746px radius) maps linearly onto the scene.
// Coastlines and landmark sites are traced in that frame so the miniature keeps the demo's composition.
export const REF_SCALE=TABLE.radius/746;
export const ref=(x:number,y:number):Point=>[TABLE.center[0]+(x-972)*REF_SCALE,TABLE.center[1]+(y-600)*REF_SCALE];
export const refs=(p:Point[])=>p.map(q=>ref(q[0],q[1]));
export const intersects=(a:Bounds,b:Bounds)=>a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;
export function pointInPolygon(x:number,y:number,p:Point[]){let inside=false;for(let i=0,j=p.length-1;i<p.length;j=i++){const a=p[i],b=p[j];if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside;}return inside;}
export const inTable=(p:Point,margin=0)=>((p[0]-TABLE.center[0])/(TABLE.radius-margin))**2+((p[1]-TABLE.center[1])/(TABLE.radius*TABLE.tilt-margin))**2<1;
export const rimPoint=(angle:number,inset=0):Point=>[TABLE.center[0]+Math.cos(angle)*(TABLE.radius-inset),TABLE.center[1]+Math.sin(angle)*(TABLE.radius-inset)*TABLE.tilt];
export const rimAngle=(p:Point)=>Math.atan2((p[1]-TABLE.center[1])/TABLE.tilt,p[0]-TABLE.center[0]);
export function rimArc(from:number,to:number,inset:number,step=.015):Point[]{const n=Math.max(2,Math.ceil(Math.abs(to-from)/step));return Array.from({length:n+1},(_,i)=>rimPoint(from+(to-from)*i/n,inset));}
// Catmull-Rom splines are baked into the layout. Rendering and movers share these samples.
export function spline(control:Point[],closed=false,steps=14):Point[]{const p=closed?[control.at(-1)!,...control,control[0],control[1]]:[control[0],...control,control.at(-1)!];const out:Point[]=[];for(let i=1;i<p.length-2;i++){const a=p[i-1],b=p[i],c=p[i+1],d=p[i+2];for(let j=0;j<steps;j++){const t=j/steps,t2=t*t,t3=t2*t;out.push([.5*((2*b[0])+(-a[0]+c[0])*t+(2*a[0]-5*b[0]+4*c[0]-d[0])*t2+(-a[0]+3*b[0]-3*c[0]+d[0])*t3),.5*((2*b[1])+(-a[1]+c[1])*t+(2*a[1]-5*b[1]+4*c[1]-d[1])*t2+(-a[1]+3*b[1]-3*c[1]+d[1])*t3)]);}}out.push(closed?out[0]:control.at(-1)!);return out;}
export const smoothPath=(p:Point[])=>spline(p);
export function pathLength(p:Point[]){let n=0;for(let i=1;i<p.length;i++)n+=Math.hypot(p[i][0]-p[i-1][0],p[i][1]-p[i-1][1]);return n;}
export function pointAlong(p:Point[],progress:number,length=pathLength(p)){let n=Math.max(0,Math.min(1,progress))*length;for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i],d=Math.hypot(b[0]-a[0],b[1]-a[1]);if(n<=d||i===p.length-1){const t=d?Math.min(1,n/d):0;return {x:a[0]+(b[0]-a[0])*t,y:a[1]+(b[1]-a[1])*t,angle:Math.atan2(b[1]-a[1],b[0]-a[0])};}n-=d;}return {x:p[0][0],y:p[0][1],angle:0};}
export function resample(p:Point[],step:number):Point[]{const length=pathLength(p),n=Math.max(1,Math.ceil(length/step));return Array.from({length:n+1},(_,i)=>{const q=pointAlong(p,i/n,length);return [q.x,q.y] as Point;});}
export function segmentDistance(p:Point,a:Point,b:Point){const dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);}
export function distanceToPath(p:Point,path:Point[]){let d=Infinity;for(let i=1;i<path.length;i++)d=Math.min(d,segmentDistance(p,path[i-1],path[i]));return d;}
export function polygonDistance(a:Point[],b:Point[]){if(a.some(p=>pointInPolygon(...p,b))||b.some(p=>pointInPolygon(...p,a)))return 0;return Math.min(...a.map(p=>distanceToPath(p,[...b,b[0]])),...b.map(p=>distanceToPath(p,[...a,a[0]])));}
export function offsetPath(p:Point[],distance:number):Point[]{return p.map((q,i)=>{const a=p[Math.max(0,i-1)],b=p[Math.min(p.length-1,i+1)],dx=b[0]-a[0],dy=b[1]-a[1],n=Math.hypot(dx,dy)||1;return [q[0]-dy/n*distance,q[1]+dx/n*distance];});}
export function polygonArea(p:Point[]){let a=0;for(let i=0,j=p.length-1;i<p.length;j=i++)a+=(p[j][0]+p[i][0])*(p[j][1]-p[i][1]);return Math.abs(a/2);}
export function buildingPoint(b:Building,x:number,y:number,h=0):Point{const cx=b.x+b.w/2,cy=b.y+b.d/2,r=b.rotation??0,dx=x-cx,dy=y-cy;return project(cx+dx*Math.cos(r)-dy*Math.sin(r),cy+dx*Math.sin(r)+dy*Math.cos(r),h);}
export const buildingCenter=(b:Building)=>project(b.x+b.w/2,b.y+b.d/2);
export const buildingFootprint=(b:Building):Point[]=>[buildingPoint(b,b.x,b.y),buildingPoint(b,b.x+b.w,b.y),buildingPoint(b,b.x+b.w,b.y+b.d),buildingPoint(b,b.x,b.y+b.d)];
export function boundsOf(p:Point[],padding=0):Bounds{const x=p.map(p=>p[0]),y=p.map(p=>p[1]);return {x:Math.min(...x)-padding,y:Math.min(...y)-padding,width:Math.max(...x)-Math.min(...x)+padding*2,height:Math.max(...y)-Math.min(...y)+padding*2};}
export function lakeShore(x:number,y:number,rx:number,ry:number,rotation=0):Point[]{return Array.from({length:65},(_,i)=>{const a=(i%64)/64*Math.PI*2,r=.91+.045*Math.sin(a*3)+.035*Math.cos(a*5),u=Math.cos(a)*rx*r,v=Math.sin(a)*ry*r;return [x+u*Math.cos(rotation)-v*Math.sin(rotation),y+u*Math.sin(rotation)+v*Math.cos(rotation)];});}

// ---- Island and water, traced clockwise from the north-west rim in reference coordinates ----
const RIM_INSET=2.5;
const NW_RIM=rimAngle(ref(600,320)),SOUTH_RIM=rimAngle(ref(1052,921));
// Bay-side coast: Marina headland, bridge landing, north shore, Coit hill, downtown edge, east quay,
// the Ferry pier platform (doubled corners stay square), south-east harbour and the south rim.
const BAY_COAST:Point[]=[[626,338],[652,360],[678,386],[698,412],[712,438],[724,456],[750,464],[790,473],[840,481],[900,487],[960,489],[994,482],[1008,458],[1024,432],[1046,408],[1078,393],[1112,386],[1150,384],[1180,391],[1198,408],[1216,426],[1255,438],[1315,452],[1368,468],[1402,484],[1422,502],[1442,540],[1462,576],[1482,612],[1490,634],[1490,634],[1652,626],[1652,626],[1680,642],[1664,706],[1664,706],[1494,776],[1494,776],[1420,780],[1388,772],[1358,766],[1326,772],[1296,782],[1264,796],[1236,810],[1200,826],[1160,842],[1122,856],[1092,872],[1070,894]];
export const ISLAND_CONTROL:Point[]=[rimPoint(NW_RIM,RIM_INSET),...refs(BAY_COAST),rimPoint(SOUTH_RIM,RIM_INSET)];
export const COAST:Point[]=[...spline(ISLAND_CONTROL,false,10),...rimArc(SOUTH_RIM,NW_RIM+Math.PI*2,RIM_INSET).slice(1,-1)];
const HEAD_WEST=rimAngle(ref(985,277)),HEAD_EAST=rimAngle(ref(1285,306));
export const HEADLAND_CONTROL:Point[]=refs([[1280,311],[1268,309],[1228,310],[1185,309],[1142,311],[1114,318],[1098,334],[1074,330],[1044,312],[1014,296],[988,283]]);
// The Marin headland is modelled as a raised hill; everything standing on it is lifted by this much.
export const HEADLAND_RISE=12;
export const HEADLAND:Point[]=[...rimArc(HEAD_WEST,HEAD_EAST,RIM_INSET),...spline(HEADLAND_CONTROL,false,10).slice(1,-1)];
// The kidney lagoon wraps the Palace platform on three sides; the platform joins the Marina strip to the north.
export const LAGOON_CONTROL:Point[]=refs([[404,408],[420,396],[448,392],[478,394],[494,402],[496,414],[504,427],[522,437],[562,442],[602,438],[622,428],[630,414],[634,402],[652,404],[666,416],[668,434],[652,451],[622,464],[572,473],[504,473],[450,467],[416,454],[402,436],[400,420]]);
export const LAGOON=spline(LAGOON_CONTROL,true);
export const PALACE_SITE={center:ref(562,410),rx:58,ry:20};
// Golden Gate Bridge: Marina landing to the north headland, two portal towers, sagging main cables.
export const BRIDGE={south:ref(706,462),north:ref(1096,322),towers:[.245,.755],height:84};
export const ALCATRAZ_CONTROL:Point[]=refs([[1169,343],[1185,330],[1223,322],[1273,318],[1323,323],[1352,335],[1350,354],[1323,367],[1273,372],[1223,370],[1185,362]]);
export const ALCATRAZ=spline(ALCATRAZ_CONTROL,true,8);
// Paved pier apron under the Ferry Building and its plaza, and the surf line along the south-east harbour.
export const FERRY_APRON=spline(refs([[1478,634],[1652,628],[1676,644],[1662,702],[1494,770],[1408,772],[1384,742],[1424,700],[1460,664]]),true,6);
export const HARBOUR_SURF=spline(refs([[1392,766],[1350,764],[1312,776],[1276,794],[1240,812],[1200,830],[1158,846],[1118,862],[1088,880]]),false,8);
export const ISLET=lakeShore(...ref(927,459),25,10,-.08);
export const COIT_HILL=spline(refs([[1012,474],[1012,452],[1026,428],[1048,406],[1080,394],[1114,388],[1150,386],[1178,393],[1195,410],[1204,430],[1186,448],[1150,462],[1100,474],[1050,482]]),true,8);
// Two ponds in Golden Gate Park and one in the park meadow beside the arterial, as in the demo.
export const PONDS=[{x:ref(351,661)[0],y:ref(351,661)[1],rx:46,ry:19,rotation:.05},{x:ref(568,670)[0],y:ref(568,670)[1],rx:39,ry:21,rotation:.12},{x:ref(713,848)[0],y:ref(713,848)[1],rx:50,ry:17,rotation:.06}];
export const WATER_HOLES=[LAGOON,...PONDS.map(l=>lakeShore(l.x,l.y,l.rx,l.ry,l.rotation))];
// Golden Gate Park lies south-west of the park drive (grid line y=15.85) out to the rim.
export const PARK_DRIVE_Y=15.85;
export const PARK=((): Point[]=>{const edge:Point[]=[];for(let x=-14;x<=19.4;x+=.25){const p=project(x,PARK_DRIVE_Y+.42);if(inTable(p,14))edge.push(p);}const a=rimAngle(edge.at(-1)!),b=rimAngle(edge[0]);return [...edge,...rimArc(a,b<a?b+Math.PI*2:b,RIM_INSET+1).slice(1,-1)];})();
export function onLand(x:number,y:number){const p=project(x,y);return inTable(p,8)&&(pointInPolygon(...p,COAST)||pointInPolygon(...p,HEADLAND))&&!WATER_HOLES.some(h=>pointInPolygon(...p,h));}
export function isDry(layout:CityLayout,p:Point){return inTable(p,2)&&(pointInPolygon(...p,layout.island.boundary)||pointInPolygon(...p,layout.island.headland))&&!layout.water.bodies.filter(b=>b.kind==='lagoon'||b.kind==='pond').some(b=>pointInPolygon(...p,b.shore));}
export function treeOccludes(tree:{x:number;y:number;size:number},x:number,y:number){return tree.y>y+1&&((x-tree.x)/(tree.size*.94))**2+((y-(tree.y-tree.size*1.05))/(tree.size*1.35))**2<1;}
