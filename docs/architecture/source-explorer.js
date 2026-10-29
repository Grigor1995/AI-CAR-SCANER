(() => {
'use strict';
const index=window.SOURCE_INDEX,api=window.Architecture,$=id=>document.getElementById(id);
if(!index||!api)return;
const files=new Map(index.files.map(f=>[f.id,f])),symbols=new Map(index.symbols.map(s=>[s.id,s]));
const history=[];let cursor=-1;
function element(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function button(text,action){const b=element('button',text);b.onclick=action;return b;}
function ref(id){return files.get(id)||symbols.get(id);}
function link(id,label){return button(label||ref(id)?.qualified_name||ref(id)?.path||id,()=>open(id));}
for(const s of [{id:'all',title:'All services'},...index.services]){const o=element('option',s.title);o.value=s.id;$('source-service').append(o);}
function results(){
 const service=$('source-service').value,query=$('source-query').value.trim().toLowerCase(),kind=$('source-kind').value;
 const rows=[...index.files.map(f=>({...f,kind:'file'})),...index.symbols].filter(r=>(service==='all'||r.service_id===service)&&(kind==='all'||r.kind===kind)&&((r.path+' '+(r.qualified_name||'')+' '+(r.signature||'')).toLowerCase().includes(query)));
 const panel=$('source-results');panel.replaceChildren();
 for(const row of rows.slice(0,100)){const b=link(row.id,(row.kind==='file'?row.path:row.qualified_name+' — '+row.path+':'+row.start_line));b.setAttribute('role','listitem');panel.append(b);}
 $('source-summary').textContent=`${rows.length} matches, first ${Math.min(100,rows.length)} shown. ${index.summary.files} files, ${index.summary.symbols} symbols. Calls: ${index.summary.statically_resolved_calls}/${index.summary.calls} static bindings resolved; others unresolved. ${index.summary.import_scc.length} import SCCs (includes deferred imports).`;
}
function graph(focus){
 // Expand only the selected file/symbol and at most 60 adjacent nodes.
 const source=ref(focus);if(!source)return;
 const mode=$('view').value;
 if(!mode.startsWith('Source:'))return;
 const isFile=files.has(focus),edgePool=isFile?index.dependencies:index.call_graph;
 const related=edgePool.filter(e=>e.source===focus||e.target===focus).slice(0,60);
 const ids=new Set([focus]);for(const e of related){ids.add(e.source);if(e.target)ids.add(e.target);}
 if(isFile&&!related.length)for(const s of index.symbols.filter(s=>s.file_id===focus).slice(0,40))ids.add(s.id);
 const nodes=[];
 for(const id of ids){const row=ref(id);if(!row)continue;const nodeId='idx-'+id;nodes.push(nodeId);if(!window.ARCHITECTURE_DATA.nodes.some(n=>n.id===nodeId))window.ARCHITECTURE_DATA.nodes.push({id:nodeId,title:(row.name||row.path.split('/').pop()).slice(0,37),layer:'Indexed services',status:'INDEXED',technology:row.language+' · '+(row.kind||'file'),responsibility:row.path+':'+(row.start_line||1),io:row.signature||'File source',dependencies:'Static only',api:'Inspect source contracts',security:'Read-only',failure:'Unresolved calls are not fabricated'});}
 for(const e of related){if(!e.target)continue;const id='idx-edge-'+e.id;if(!window.ARCHITECTURE_DATA.edges.some(x=>x.id===id))window.ARCHITECTURE_DATA.edges.push({id,source:'idx-'+e.source,target:'idx-'+e.target,path:e.resolution.startsWith('inferred')?'online':'offline',label:e.resolution+'; '+(e.expression||e.kind)});}
 window.ARCHITECTURE_DATA.views[mode]=nodes;api.render();api.fit();
}
function show(id){
 const row=ref(id);if(!row)return;
 const file=files.get(row.file_id)||row;
 const panel=$('source-detail');panel.replaceChildren();
 const crumbs=element('nav');crumbs.append(button(row.service_id,()=>{$('source-service').value=row.service_id;results();}),link(file.id,file.path));if(symbols.has(id))crumbs.append(element('span',' → '+row.qualified_name));panel.append(crumbs);
 panel.append(element('h3',row.signature||row.path),element('p',`Service: ${row.service_id} · ${row.language} · lines ${row.start_line||1}–${row.end_line||row.lines}. ${row.resolution||'Indexed file'}`));
 panel.append(button('Copy relative path',async()=>{try{await navigator.clipboard.writeText(row.path+':'+(row.start_line||1));}catch{panel.append(element('p',row.path+':'+(row.start_line||1)));}}));
 panel.append(button('Focus bounded graph',()=>graph(id)));
 const children=index.symbols.filter(s=>s.file_id===file.id&&(!row.qualified_name||s.qualified_name.startsWith(row.qualified_name+'.'))).slice(0,100);
 const tree=element('details');tree.open=true;tree.append(element('summary','File symbols / class members (first 100)'));for(const child of children)tree.append(link(child.id,child.kind+' '+child.qualified_name+':'+child.start_line));panel.append(tree);
 const relation=element('details');relation.open=true;relation.append(element('summary','Callers / callees / file dependencies'));
 const edges=[...index.call_graph,...index.dependencies].filter(e=>e.source===id||e.target===id).slice(0,100);
 for(const e of edges){const other=e.source===id?e.target:e.source;const line=element('div',`${e.source===id?'→':'←'} ${e.expression||e.module||e.kind} · ${e.resolution} · ${e.path}:${e.line} `);if(other&&ref(other))line.append(link(other));relation.append(line);}panel.append(relation);
 const contracts=index.service_contracts.filter(c=>c.file_id===file.id);if(contracts.length)panel.append(element('p','API decorators: '+contracts.map(c=>c.method+' '+c.route+' ['+c.resolution+']').join(' | ')));
 const pre=element('pre');pre.setAttribute('aria-label','Read-only source preview');const symbolPreview=Boolean(row.preview_start_line),lines=(symbolPreview?row.preview:file.preview).split('\n'),start=symbolPreview?0:Math.max(0,(row.start_line||1)-4),end=Math.min(lines.length,symbolPreview?70:row.end_line?row.end_line+3:120,start+220),offset=symbolPreview?row.preview_start_line-1:0;
 pre.textContent=lines.slice(start,end).map((text,n)=>`${n+start+offset+1}  ${text}`).join('\n');panel.append(pre);
 if(file.preview_truncated)panel.append(element('p','Preview capped at 30,000 characters. Open the repository path locally for the complete file.'));
 if(modeIs('data ownership'))panel.append(element('p',index.services.find(s=>s.id===row.service_id)?.data_ownership));
 $('source-back').disabled=cursor<=0;$('source-forward').disabled=cursor>=history.length-1;
}
function modeIs(name){return $('view').value.includes(name);}
function open(id){history.splice(cursor+1);history.push(id);cursor=history.length-1;show(id);}
$('source-back').onclick=()=>{if(cursor>0)show(history[--cursor]);};$('source-forward').onclick=()=>{if(cursor<history.length-1)show(history[++cursor]);};
$('source-service').onchange=results;$('source-query').oninput=results;$('source-kind').onchange=results;
window.addEventListener('architecture-node',event=>{const id=event.detail;if(id.startsWith('idx-'))open(id.slice(4));else if(id.startsWith('svc-')){$('source-service').value=id.slice(4);results();const service=index.services.find(s=>s.id===id.slice(4));const p=$('source-detail');p.replaceChildren(element('h3',service.title),element('p',`${service.deployment}; runtime ${service.runtime_status}; data: ${service.data_ownership}`));for(const file of service.files.slice(0,80))p.append(link(file,files.get(file).path));}});
$('fit-layout').onclick=api.fit;$('auto-layout').onclick=api.autoLayout;
$('export-layout').onclick=()=>{const blob=new Blob([JSON.stringify(api.exportLayout(),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=element('a');a.href=url;a.download='architecture-layout.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('import-layout').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>2000000)throw new Error('Layout too large');api.importLayout(JSON.parse(await file.text()));$('source-summary').textContent='Layout imported';}catch(error){$('source-summary').textContent='Layout rejected: '+error.message;}};
$('view').addEventListener('change',()=>{if(modeIs('shared C++')){$('source-query').value='.cpp';results();}else if(modeIs('future purchase')){$('source-detail').replaceChildren(element('h3','Future purchase — DISABLED'),element('p','No checkout, payments or subscriptions are active. No payment credentials or UI purchase actions exist. See docs/microservices/FUTURE_PURCHASE_ARCHITECTURE.md.'));}else if(modeIs('before / after')){$('source-detail').replaceChildren(element('h3','Incremental migration'),element('p','Before: catalog routes directly call the shared backend catalog. After: a catalog port selects embedded or independently authenticated HTTP service. Identity, diagnostic state and business SQL remain in the backend; no independent database ownership is claimed.'));}});
const config=element('details');config.append(element('summary','Read-only configuration policy / parser limitations'),element('pre',JSON.stringify({configuration:index.configuration,schema:'config/global_config.schema.json',reloadable:['catalog timeout','catalog retries'],purchase:false,native_core:'experimental only; not a deployed service',limitations:index.summary.limitations},null,2)));$('source-browser').append(config);
results();
})();
