/* Source-backed overlays, loaded before the existing renderer. No remote fetch. */
(() => {
'use strict';
const data=window.ARCHITECTURE_DATA,index=window.SOURCE_INDEX;
if(!data||!index)return;
const layer='Indexed services';data.layers.push(layer);
for(const s of index.services)data.nodes.push({id:'svc-'+s.id,title:s.title,layer,status:s.deployment.includes('planned')||s.deployment==='disabled_future'?'PLANNED':'INDEXED',technology:s.deployment,responsibility:`${s.files.length} indexed files; ${s.runtime_status}`,io:'Read-only source evidence',dependencies:'Select a file to inspect static dependencies',api:'Source-indexed contracts; prefix resolution shown separately',security:'No credentials or runtime authorization changed',failure:'Runtime health not probed'});
const services=index.services.map(s=>'svc-'+s.id), actual=index.services.filter(s=>s.files.length).map(s=>'svc-'+s.id);
const views={
 'Source: system':actual,
 'Source: microservices':services,
 'Source: service dependencies':actual,
 'Source: files':actual,
 'Source: classes and interfaces':actual,
 'Source: call graph':actual,
 'Source: API and events':services.filter(id=>['svc-gateway','svc-vehicle-catalog','svc-configuration','svc-notifications'].includes(id)),
 'Source: data ownership':actual,
 'Source: shared C++ core':['svc-UNASSIGNED','svc-diagnostics','svc-native-clients'],
 'Source: platforms':['svc-user-client','svc-customer-client','svc-market-client','svc-native-clients'],
 'Source: future purchase':['svc-marketplace','svc-purchase','svc-identity'],
 'Source: before / after':['svc-gateway','svc-vehicle-catalog','svc-configuration']
};
for(const [name,ids] of Object.entries(views)){data.views[name]=ids;data.descriptions[name]='Generated repository evidence. Embedded/shared SQL, independently deployable catalog and planned extractions are distinct. Browse exact files and symbols below. No live service health is asserted.';}
const fileById=new Map(index.files.map(f=>[f.id,f]));const seen=new Set();
for(const edge of index.dependencies){if(!edge.target||edge.resolution!=='static_import_resolved')continue;const a=fileById.get(edge.source)?.service_id,b=fileById.get(edge.target)?.service_id;if(!a||!b||a===b)continue;const id=a+'->'+b;if(seen.has(id))continue;seen.add(id);data.edges.push({id:'source-'+id,source:'svc-'+a,target:'svc-'+b,path:'offline',label:'Static code import (not a network request)'});}
})();
