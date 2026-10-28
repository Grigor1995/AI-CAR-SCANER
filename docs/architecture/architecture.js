(() => {
'use strict';
const data=window.ARCHITECTURE_DATA, NS='http://www.w3.org/2000/svg';
const $=id=>document.getElementById(id), scene=$('scene'), svg=$('diagram');
const visibleLayers=new Set(data.layers), collapsed=new Set();
let scale=.95, dx=16, dy=16, drag=null;
function el(name, attrs={}, text){const e=document.createElementNS(NS,name);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;return e;}
function transform(){scene.setAttribute('transform',`translate(${dx},${dy}) scale(${scale})`);svg.dataset.scale=String(scale);}
function details(title, fields){const panel=$('details');panel.replaceChildren();const heading=document.createElement('h2');heading.textContent=title;panel.append(heading);const dl=document.createElement('dl');for(const [key,value] of Object.entries(fields)){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=Array.isArray(value)?value.join(', '):value;dl.append(dt,dd);}panel.append(dl);const link=document.createElement('a');link.href='../SYSTEM_ARCHITECTURE.md';link.textContent='Architecture documentation';panel.append(link);}
function activate(e,action){e.addEventListener('click',action);e.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();action();}});}
for(const title of Object.keys(data.views)){const option=document.createElement('option');option.textContent=title;$('view').append(option);}
for(const layer of data.layers){const label=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.checked=true;box.dataset.layer=layer;box.addEventListener('change',()=>{box.checked?visibleLayers.add(layer):visibleLayers.delete(layer);render();});label.append(box,document.createTextNode(layer));$('layers').append(label);}
function render(){
 scene.replaceChildren();
 const ids=new Set(data.views[$('view').value]),query=$('search').value.trim().toLowerCase();
 const selected=data.nodes.filter(n=>ids.has(n.id)&&visibleLayers.has(n.layer)&&JSON.stringify(n).toLowerCase().includes(query));
 const layers=data.layers.filter(layer=>selected.some(n=>n.layer===layer));
 const positions=new Map(),groups=[];let y=0;
 const columns=svg.clientWidth<600?1:3;
 for(let i=0;i<layers.length;i+=columns){const row=layers.slice(i,i+columns);let height=0;row.forEach((layer,col)=>{const nodes=selected.filter(n=>n.layer===layer),h=collapsed.has(layer)?50:64+nodes.length*88;const group={layer,nodes,x:col*335,y,h};groups.push(group);height=Math.max(height,h);if(!collapsed.has(layer))nodes.forEach((n,j)=>positions.set(n.id,{x:group.x+14,y:y+49+j*88}));});y+=height+24;}
 for(const group of groups)scene.append(el('rect',{x:group.x,y:group.y,width:316,height:group.h,rx:10,class:'group-box'}));
 for(const edge of data.edges){if(!positions.has(edge.source)||!positions.has(edge.target))continue;const path=$('path').value;if(path!=='all'&&edge.path!=='both'&&edge.path!==path)continue;const a=positions.get(edge.source),b=positions.get(edge.target),x1=a.x+(b.x>=a.x?288:0),y1=a.y+35,x2=b.x+(b.x>=a.x?0:288),y2=b.y+35;const line=el('path',{d:`M${x1},${y1} C${x1+90},${y1} ${x2-90},${y2} ${x2},${y2}`,class:'edge '+edge.path,tabindex:0,'data-edge':edge.id,'aria-label':edge.source+' to '+edge.target+': '+edge.label});activate(line,()=>details('Relationship',{Direction:edge.source+' → '+edge.target,Communication:edge.label,Path:edge.path,Status:edge.label.includes('future')||edge.label.includes('proposal')?'PROPOSED':'Existing / foundation boundary'}));scene.append(line);}
 for(const group of groups){const title=el('g',{class:'toggle',tabindex:0,role:'button','data-group':group.layer,'aria-expanded':String(!collapsed.has(group.layer))});title.append(el('text',{x:group.x+13,y:group.y+28,class:'group-title'},(collapsed.has(group.layer)?'+ ':'− ')+group.layer));activate(title,()=>{collapsed.has(group.layer)?collapsed.delete(group.layer):collapsed.add(group.layer);render();});scene.append(title);if(collapsed.has(group.layer))continue;
 for(const node of group.nodes){const pos=positions.get(node.id),g=el('g',{class:'node '+(node.status==='PLANNED'?'planned':''),transform:`translate(${pos.x},${pos.y})`,tabindex:0,role:'button','data-node':node.id,'aria-label':node.title+' '+node.status});g.append(el('rect',{width:288,height:70,rx:8}),el('text',{x:10,y:23},node.title),el('text',{x:10,y:43,class:'sub'},node.technology.slice(0,43)),el('text',{x:10,y:59,class:'sub'},node.status));activate(g,()=>details(node.title,{Responsibility:node.responsibility,Technology:node.technology,'Input / output':node.io,Dependencies:node.dependencies,'Relevant API':node.api,'Data flow':data.edges.filter(e=>e.source===node.id||e.target===node.id).map(e=>`${e.source} → ${e.target}: ${e.label}`),'Security boundary':node.security,'Failure handling':node.failure,Status:node.status}));scene.append(g);}}
 $('count').textContent=`${positions.size} modules / ${layers.length} layers`;transform();
}
function zoom(factor,x=svg.clientWidth/2,y=svg.clientHeight/2){const next=Math.min(2.5,Math.max(.15,scale*factor));dx=x-(x-dx)*next/scale;dy=y-(y-dy)*next/scale;scale=next;transform();}
$('zoom-in').onclick=()=>zoom(1.2);$('zoom-out').onclick=()=>zoom(1/1.2);
function reset(){const columns=svg.clientWidth<600?1:3;scale=Math.min(1.1,Math.max(.2,(svg.clientWidth-32)/(columns*335)));dx=16;dy=16;transform();}
$('reset').onclick=reset;
window.addEventListener('resize',()=>{render();reset();});
svg.addEventListener('wheel',e=>{e.preventDefault();const box=svg.getBoundingClientRect();zoom(e.deltaY<0?1.12:1/1.12,e.clientX-box.left,e.clientY-box.top);},{passive:false});
svg.addEventListener('pointerdown',e=>{if(e.target.closest('.node,.toggle,.edge'))return;drag={x:e.clientX,y:e.clientY,dx,dy};svg.setPointerCapture(e.pointerId);});
svg.addEventListener('pointermove',e=>{if(drag){dx=drag.dx+e.clientX-drag.x;dy=drag.dy+e.clientY-drag.y;transform();}});
svg.addEventListener('pointerup',()=>{drag=null;});svg.addEventListener('pointercancel',()=>{drag=null;});
$('view').onchange=render;$('search').oninput=render;$('path').onchange=render;
$('theme').onclick=()=>{const light=document.documentElement.dataset.theme==='dark';document.documentElement.dataset.theme=light?'light':'dark';$('theme').setAttribute('aria-pressed',String(light));};
render();reset();
})();
