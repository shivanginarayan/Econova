import fs from 'node:fs';import {build}from'esbuild';import{pathToFileURL}from'node:url';
await build({entryPoints:['apps/web/src/city/cityGeometry.ts'],outfile:'artifacts/island-geometry.mjs',bundle:true,format:'esm',platform:'node'});const g=await import(pathToFileURL(process.cwd()+'/artifacts/island-geometry.mjs').href);const l=JSON.parse(fs.readFileSync('apps/web/src/data/fixtures/sfCityLayout.json','utf8'));
const roads=l.paths.filter(p=>p.kind==='road'&&p.role!=='bridge');
const outside=l.buildings.flatMap(b=>g.buildingFootprint(b).filter(p=>!g.isDry(l,p)).map(p=>({id:b.id,p})));
const wetRoutes=l.paths.filter(p=>p.kind==='park'||p.kind==='footpath'||p.kind==='road'&&p.role!=='bridge').map(p=>({id:p.id,count:p.points.filter(q=>!g.isDry(l,q)).length,wet:p.points.filter(q=>!g.isDry(l,q)).slice(0,3)})).filter(x=>x.count);
const collisions=roads.flatMap(r=>l.buildings.filter(b=>r.points.some(p=>g.pointInPolygon(...p,g.buildingFootprint(b)))).map(b=>r.id+' crosses '+b.id));
const gaps=[];for(let i=0;i<l.buildings.length;i++)for(let j=0;j<i;j++){const d=g.polygonDistance(g.buildingFootprint(l.buildings[i]),g.buildingFootprint(l.buildings[j]));if(d<l.minimumBuildingGap-.01)gaps.push([l.buildings[i].id,l.buildings[j].id,d]);}
console.log(JSON.stringify({buildings:l.buildings.length,kinds:l.buildings.reduce((a,b)=>(a[b.kind]=(a[b.kind]??0)+1,a),{}),outside,wetRoutes,collisions,gaps,coastOutside:l.island.boundary.filter(p=>!g.inTable(p)),headlandOutside:l.island.headland.filter(p=>!g.inTable(p))},null,2));

if(outside.length||wetRoutes.length||collisions.length||gaps.length||l.island.boundary.some(p=>!g.inTable(p))||l.island.headland.some(p=>!g.inTable(p)))process.exitCode=1;
