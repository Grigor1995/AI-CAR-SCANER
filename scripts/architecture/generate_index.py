#!/usr/bin/env python3
"""Offline source index. Parses syntax without importing/executing application code.

Only direct lexical/import bindings are statically resolved. Dynamic receivers,
overloads and native cross-language calls remain explicitly unresolved/inferred.
"""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = {'.py':'python','.kt':'kotlin','.swift':'swift','.js':'javascript',
             '.ts':'typescript','.cpp':'cpp','.cc':'cpp','.h':'cpp','.hpp':'cpp'}
SERVICE_RULES = [
 ('vehicle-catalog', 'Vehicle catalog', 'standalone_optional', ['finalbuild/backend/services/vehicle_catalog/', 'finalbuild/backend/vehicle/catalog_registry.py']),
 ('identity', 'Identity and authorization', 'embedded', ['finalbuild/backend/ecosystem/security.py','finalbuild/backend/ecosystem/models.py']),
 ('diagnostics', 'Diagnostics and OBD', 'embedded', ['finalbuild/backend/diagnostic/', 'finalbuild/backend/vehicle/']),
 ('telemetry', 'Telemetry', 'embedded', ['finalbuild/backend/telemetry/', 'finalbuild/backend/api/telemetry_routes.py']),
 ('ai', 'AI decision support', 'embedded', ['finalbuild/backend/ai/']),
 ('configuration', 'Configuration', 'embedded', ['finalbuild/backend/configuration/', 'finalbuild/backend/ecosystem/config_api.py']),
 ('gateway', 'Backend composition / shared business SQL', 'embedded_shared_database', ['finalbuild/backend/api/', 'finalbuild/backend/ecosystem/', 'finalbuild/backend/main.py','finalbuild/backend/server.py']),
 ('user-client', 'USER native clients', 'native_presentation', ['finalbuild/apps/user/']),
 ('customer-client', 'CUSTOMER native clients', 'native_presentation', ['finalbuild/apps/customer/']),
 ('market-client', 'MARKET native clients', 'native_presentation', ['finalbuild/apps/market/']),
 ('native-clients', 'Shared native presentation / bridges', 'native_presentation', ['finalbuild/apps/desktop/', 'finalbuild/apps/mobile-android/', 'finalbuild/apps/mobile-ios/']),
 ('monitoring', 'Monitoring extraction', 'planned', []),
 ('notifications', 'Notification delivery extraction', 'planned', []),
 ('customer', 'Customer workflow extraction', 'planned', []),
 ('marketplace', 'Marketplace extraction', 'planned', []),
 ('admin', 'Administration extraction', 'planned', []),
 ('updates', 'Signed update service', 'planned', []),
 ('purchase', 'Purchase / checkout', 'disabled_future', []),
 ('UNASSIGNED', 'Unassigned / tooling / shared infrastructure', 'unassigned', []),
]
EXCLUDE = {'docs/architecture/source-index.js', 'docs/architecture/architecture-data.js',
           'docs/architecture/business-data.js','docs/architecture/performance-data.js'}

def stable(kind, *parts):
    return kind + ':' + hashlib.sha256('|'.join(parts).encode()).hexdigest()[:20]

def owner(path):
    return next((sid for sid, _, _, prefixes in SERVICE_RULES if any(path.startswith(p) for p in prefixes)), 'UNASSIGNED')

def candidates(root):
    result = subprocess.run(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=root,capture_output=True,check=True).stdout
    for name in sorted(set(result.decode().strip('\x00').split('\x00'))):
        path = root/name
        if name in EXCLUDE or not path.is_file() or path.is_symlink() or path.suffix not in LANGUAGES:
            continue
        if any(part in {'node_modules','build','dist','.venv','generated_images'} for part in path.parts): continue
        # Local ignored JSON/ENV, asset binaries and credentials are never indexed.
        if path.stat().st_size > 2_000_000: continue
        yield name, path

def text(node, source):
    return source[node.start_byte:node.end_byte].decode('utf-8',errors='replace')

def clean_preview(source):
    """Do not publish secret-like literal assignments; keep line numbering stable."""
    lines=source.splitlines()
    try:
        tree=ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node,(ast.Assign,ast.AnnAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                names=[n.id.lower() for target in targets for n in ast.walk(target) if isinstance(n,ast.Name)]
                if any(any(s in name for s in ('password','secret','api_key','credential','dummy_hash')) for name in names) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
                    for n in range(node.lineno-1,node.end_lineno): lines[n]='[redacted credential-like literal]'
    except SyntaxError: pass
    return '\n'.join(lines)

class Index:
    def __init__(self):
        self.files=[];self.symbols=[];self.dependencies=[];self.calls=[];self.contracts=[]
        self.trees={};self.sources={};self.modules={};self.filemap={};self.python_bindings={}
        self.symbol_lookup={};self.errors=[]

    def add_symbol(self, path, name, qualified, kind, start, end, signature, params, returns, async_, access, parser):
        sid=stable('symbol',path,qualified,kind,signature)
        # Legitimate overloads have signatures in IDs; identical duplicate definitions
        # receive deterministic ordinal suffixes rather than silently overwriting.
        ordinal=sum(1 for item in self.symbols if item['id'].split('~')[0]==sid)
        if ordinal: sid+='~'+str(ordinal)
        row=dict(id=sid,file_id=stable('file',path),path=path,service_id=owner(path),name=name,qualified_name=qualified,
                 kind=kind,start_line=start,end_line=end,signature=signature[:600],parameters=params,
                 returns=returns,async_function=async_,access=access,parser=parser,
                 resolution='syntax_verified',language=LANGUAGES[Path(path).suffix])
        self.symbols.append(row);self.symbol_lookup[(path,qualified)]=row
        return row

    def python(self,path,source):
        try: tree=ast.parse(source)
        except SyntaxError as exc:
            self.errors.append({'path':path,'line':exc.lineno,'error':'Python syntax error'});return
        self.trees[path]=tree
        constants={};prefixes={}
        def literal(node):
            if isinstance(node,ast.Constant):return node.value
            if isinstance(node,ast.Name):return constants.get(node.id)
            if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
                a,b=literal(node.left),literal(node.right)
                if isinstance(a,str) and isinstance(b,str):return a+b
            return None
        for stmt in tree.body:
            if isinstance(stmt,ast.Assign):
                for target in stmt.targets:
                    if not isinstance(target,ast.Name):continue
                    value=literal(stmt.value)
                    if value is not None:constants[target.id]=value
                    if isinstance(stmt.value,ast.Call) and ast.unparse(stmt.value.func).endswith('APIRouter'):
                        keyword=next((kw for kw in stmt.value.keywords if kw.arg=='prefix'),None)
                        prefixes[target.id]=literal(keyword.value) if keyword else ''
        scopes={}
        def visit(node,scope=''):
            for child in ast.iter_child_nodes(node):
                if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                    qualified=(scope+'.' if scope else '')+child.name
                    is_class=isinstance(child,ast.ClassDef)
                    args=[] if is_class else [ast.unparse(a) for a in child.args.posonlyargs+child.args.args+child.args.kwonlyargs]
                    if not is_class:
                        if child.args.vararg: args.append('*'+ast.unparse(child.args.vararg))
                        if child.args.kwarg: args.append('**'+ast.unparse(child.args.kwarg))
                    signature=('class ' if is_class else 'async def ' if isinstance(child,ast.AsyncFunctionDef) else 'def ')+child.name+'('+', '.join(args)+')'
                    row=self.add_symbol(path,child.name,qualified,'class' if is_class else 'method' if self.symbol_lookup.get((path,scope),{}).get('kind')=='class' else 'function',
                        child.lineno,child.end_lineno,signature,args,ast.unparse(child.returns) if not is_class and child.returns else None,
                        isinstance(child,ast.AsyncFunctionDef),'private' if child.name.startswith('_') else 'public','python_ast')
                    scopes[id(child)]=row['id']
                    for kind, refs in [('inheritance', child.bases if is_class else []),
                                       ('annotation', [arg.annotation for arg in child.args.posonlyargs+child.args.args+child.args.kwonlyargs if arg.annotation] + ([child.returns] if child.returns else []) if not is_class else [])]:
                        for number, ref in enumerate(refs):
                            self.dependencies.append(dict(id=stable('type',row['id'],kind,str(number)),source=row['id'],target=None,path=path,
                                line=ref.lineno,kind=kind,module=ast.unparse(ref),scope=scope,loading='type_reference',resolution='unresolved'))
                    if not is_class:
                        for dec in child.decorator_list:
                            if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr in {'get','post','patch','delete','put','websocket'} and dec.args and isinstance(dec.args[0],ast.Constant) and isinstance(dec.args[0].value,str):
                                self.contracts.append(dict(id=stable('route',row['id'],ast.unparse(dec)),file_id=row['file_id'],symbol_id=row['id'],
                                    path=path,line=dec.lineno,method=dec.func.attr.upper(),route=dec.args[0].value,
                                    router=ast.unparse(dec.func.value),prefix=prefixes.get(ast.unparse(dec.func.value)),
                                    full_route=(prefixes[ast.unparse(dec.func.value)]+dec.args[0].value) if isinstance(prefixes.get(ast.unparse(dec.func.value)),str) else None,
                                    resolution='literal_route_and_prefix_verified' if isinstance(prefixes.get(ast.unparse(dec.func.value)),str) else 'literal_route_verified_prefix_unresolved'))
                    visit(child,qualified)
                else: visit(child,scope)
        visit(tree)
        self.python_bindings[path]={}
        def traverse(node,scope='',caller=None):
            if id(node) in scopes:
                caller=scopes[id(node)]
                scope=next(s['qualified_name'] for s in self.symbols if s['id']==caller)
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                imports=[]
                if isinstance(node,ast.Import):
                    imports=[(a.name, None, a.asname or a.name.split('.')[0]) for a in node.names]
                else:
                    module=node.module or ''
                    if node.level:
                        base=path[:-3].split('/')[:-1]
                        base=base[:len(base)-node.level+1]
                        module='/'.join(base)+('/'+module.replace('.','/') if module else '')
                    imports=[(module,a.name,a.asname or a.name) for a in node.names]
                for module,member,alias in imports:
                    self.python_bindings[path][(scope,alias)]=(module,member)
                    self.dependencies.append(dict(id=stable('import',path,str(node.lineno),module,str(member)),source=stable('file',path),
                        target=None,path=path,line=node.lineno,kind='import',module=module,member=member,scope=scope,
                        loading='deferred' if caller else 'module',resolution='unresolved'))
            if isinstance(node,ast.Call):
                expr=ast.unparse(node.func)
                self.calls.append(dict(id=stable('call',path,str(node.lineno),str(node.col_offset),expr),source=caller or stable('file',path),
                    target=None,file_id=stable('file',path),path=path,line=node.lineno,expression=expr[:300],scope=scope,resolution='unresolved'))
            for child in ast.iter_child_nodes(node):traverse(child,scope,caller)
        traverse(tree)

    def structural(self,path,source):
        from tree_sitter_language_pack import get_parser
        language=LANGUAGES[Path(path).suffix]
        data=source.encode('utf-8');tree=get_parser(language).parse(data)
        if tree.root_node.has_error:self.errors.append(dict(path=path,error='Grammar recovery; structural results may be incomplete'))
        symbol_types={'class_declaration':'class','class_specifier':'class','struct_specifier':'struct',
                      'interface_declaration':'interface','object_declaration':'object','protocol_declaration':'interface',
                      'function_declaration':'function','function_definition':'function','method_definition':'method'}
        def descend(node,scope='',caller=None):
            if node.type in symbol_types:
                name=node.child_by_field_name('name')
                declarator=node.child_by_field_name('declarator')
                if name is None:
                    pool=declarator.named_children if declarator else node.named_children
                    name=next((n for n in pool if n.type in {'simple_identifier','type_identifier','identifier','field_identifier','scoped_identifier'}),None)
                if name:
                    value=text(name,data); qualified=(scope+'.' if scope else '')+value
                    body=node.child_by_field_name('body') or next((n for n in node.named_children if n.type in {'function_body','class_body','compound_statement','statement_block','field_declaration_list'}),None)
                    signature=data[node.start_byte:body.start_byte if body else min(node.end_byte,node.start_byte+600)].decode(errors='replace').strip()
                    params=node.child_by_field_name('parameters') or next((n for n in node.named_children if 'parameters' in n.type or n.type=='parameter_list'),None)
                    if params is None and declarator:params=declarator.child_by_field_name('parameters')
                    ret=node.child_by_field_name('return_type') or node.child_by_field_name('type')
                    if ret is None and symbol_types[node.type] in {'function','method'}:
                        ret=next((n for n in node.named_children if n.type in {'user_type','nullable_type','function_type'}),None)
                    parameter_nodes=list(params.named_children) if params else [n for n in node.named_children if n.type=='parameter']
                    modifiers=next((n for n in node.named_children if n.type=='modifiers'),None)
                    modifier_text=text(modifiers,data) if modifiers else ''
                    access=next((value for value in ('private','protected','internal','public','fileprivate','open') if value in modifier_text.split()),'syntax_unspecified')
                    row=self.add_symbol(path,value,qualified,symbol_types[node.type],node.start_point.row+1,node.end_point.row+1,
                        signature,[text(p,data) for p in parameter_nodes],text(ret,data) if ret else None,
                        any(n.type=='async' or text(n,data)=='async' for n in node.children) or 'suspend' in modifier_text.split(),
                        access,f'tree_sitter_{language}')
                    scope=qualified;caller=row['id']
            if node.type in {'call_expression','new_expression'}:
                function=node.child_by_field_name('function') or (node.named_children[0] if node.named_children else None)
                if function:
                    expr=text(function,data)
                    self.calls.append(dict(id=stable('call',path,str(node.start_byte),expr),source=caller or stable('file',path),target=None,
                        file_id=stable('file',path),path=path,line=node.start_point.row+1,expression=expr[:300],scope=scope,
                        resolution='unresolved',reason='Receiver/type/overload analysis not available'))
            if node.type in {'import_header','import_declaration','import_statement','preproc_include'}:
                self.dependencies.append(dict(id=stable('import',path,str(node.start_byte)),source=stable('file',path),target=None,path=path,
                    line=node.start_point.row+1,kind='import',module=text(node,data)[:400],scope=scope,resolution='unresolved',loading='syntax_only'))
            for child in node.named_children:descend(child,scope,caller)
        descend(tree.root_node)

    def structural_safe(self,path,source):
        # Native parser faults are isolated from the generator and reported honestly.
        try:
            result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--native-worker',path],
                                  input=source,capture_output=True,text=True,timeout=30)
            if result.returncode:raise ValueError('Parser worker failed')
            data=json.loads(result.stdout)
            self.symbols.extend(data['symbols']);self.calls.extend(data['calls'])
            self.dependencies.extend(data['dependencies']);self.errors.extend(data['errors'])
        except (ValueError,subprocess.TimeoutExpired):
            self.errors.append({'path':path,'error':'Native parser worker failed or timed out; file retained, symbols unresolved'})

    def resolve_module(self,module):
        module=module.replace('.','/').rstrip('/')
        return next((path for root in ('finalbuild/backend/','finalbuild/','') for path in (root+module+'.py',root+module+'/__init__.py') if path in self.filemap),None)

    def resolve(self):
        for edge in self.dependencies:
            if LANGUAGES[Path(edge['path']).suffix]!='python' or edge['kind']!='import':continue
            dest=self.resolve_module(edge['module'])
            member=edge.get('member')
            # "from package import module" may bind a submodule, not an attribute.
            if member and (sub:=self.resolve_module(edge['module']+'/'+member)):dest=sub
            if dest:
                edge['target']=stable('file',dest);edge['resolution']='static_import_resolved'
                if 'backend.vehicle' in edge['module']:
                    edge['resolution']='inferred_legacy_alias';edge['reason']='Runtime package __path__ alias; inspect backend/vehicle/__init__.py'
        for edge in self.calls:
            path=edge['path']
            if LANGUAGES[Path(path).suffix]!='python':continue
            expr=edge['expression'];parts=expr.split('.')
            if any(not part.isidentifier() for part in parts):continue
            scope=edge['scope'];target=None
            if len(parts)==1:
                scopes=scope.split('.')
                for length in range(len(scopes),-1,-1):
                    qualified='.'.join(scopes[:length]+parts)
                    target=self.symbol_lookup.get((path,qualified))
                    # Class namespaces are not lexical scopes for bare calls in methods.
                    parent=self.symbol_lookup.get((path,'.'.join(scopes[:length])))
                    if parent and parent['kind']=='class':target=None
                    if target:break
            bindings=self.python_bindings[path]
            bound=None
            chunks=scope.split('.')
            for length in range(len(chunks),-1,-1):
                bound=bindings.get(('.'.join(chunks[:length]),parts[0]))
                if bound:break
            if not target and bound:
                module,member=bound;dest=self.resolve_module(module)
                if member:
                    sub=self.resolve_module(module+'/'+member)
                    if sub:dest=sub;member=None
                qualified='.'.join(([member] if member else [])+parts[1:])
                target=self.symbol_lookup.get((dest,qualified))
            if target:
                edge['target']=target['id'];edge['resolution']='static_binding_resolved'
                edge['reason']='Lexical/import binding; runtime monkey-patching not modeled'

    def cycles(self):
        # Tarjan SCC over resolved module imports only, including deferred edges.
        graph=defaultdict(set)
        for e in self.dependencies:
            if e['target'] and e['resolution']=='static_import_resolved':graph[e['source']].add(e['target'])
        counter=0;stack=[];active=set();indices={};low={};groups=[]
        def visit(v):
            nonlocal counter
            indices[v]=low[v]=counter;counter+=1;stack.append(v);active.add(v)
            for w in sorted(graph[v]):
                if w not in indices:visit(w);low[v]=min(low[v],low[w])
                elif w in active:low[v]=min(low[v],indices[w])
            if low[v]==indices[v]:
                group=[]
                while True:
                    w=stack.pop();active.remove(w);group.append(w)
                    if w==v:break
                if len(group)>1:groups.append(sorted(group))
        for v in sorted(list(graph)):
            if v not in indices:visit(v)
        return groups

    def generate(self,root,output):
        for path,file in candidates(root):
            source=file.read_text(encoding='utf-8',errors='replace');self.sources[path]=source
            row=dict(id=stable('file',path),path=path,language=LANGUAGES[file.suffix],service_id=owner(path),
                     lines=len(source.splitlines()),sha256=hashlib.sha256(source.encode()).hexdigest(),
                     # Preview bounded; complete navigation still indexes every symbol.
                     preview=clean_preview(source)[:30000],preview_truncated=len(source)>30000)
            self.files.append(row);self.filemap[path]=row
        for path,source in self.sources.items():
            self.python(path,source) if LANGUAGES[Path(path).suffix]=='python' else self.structural_safe(path,source)
        self.resolve()
        preview_lines={path:clean_preview(source).splitlines() for path,source in self.sources.items()}
        for symbol in self.symbols:
            if symbol['path'] not in self.sources:continue
            lines=preview_lines[symbol['path']]
            start=max(0,symbol['start_line']-2)
            # Every symbol has its own bounded preview, even beyond a large file's
            # first preview chunk. No browser request can read an arbitrary path.
            symbol['preview_start_line']=start+1
            symbol['preview']='\n'.join(lines[start:min(symbol['end_line']+1,start+70)])[:6000]
        services=[dict(id=sid,title=title,deployment=status,files=[f['id'] for f in self.files if f['service_id']==sid],
                       data_ownership='immutable catalog JSON only' if sid=='vehicle-catalog' else 'shared SQL / embedded' if status.startswith('embedded') else 'none or not yet extracted',
                       runtime_status='NOT_PROBED',prefixes=prefixes) for sid,title,status,prefixes in SERVICE_RULES]
        cycles=self.cycles()
        summary=dict(schema_version=1,files=len(self.files),symbols=len(self.symbols),calls=len(self.calls),
                     statically_resolved_calls=sum(c['target'] is not None for c in self.calls),
                     parser_diagnostics=self.errors,import_scc=cycles,
                     limitations=['Static bindings are not runtime traces','Tree-sitter native/dynamic calls are unresolved',
                                  'Mixed business_api.py/service.py share SQL; no independent ownership claimed',
                                  'No compile_commands.json/Clang semantic index; C++ overloads unresolved'])
        config_path=root/'config/global_config.json'
        raw_config=json.loads(config_path.read_text()) if config_path.is_file() else {}
        public_config={key:raw_config[key] for key in ('schema_version','app','native','ui','marketplace') if key in raw_config}
        data=dict(configuration={'source':'config/global_config.json','kind':'checked_in_defaults_not_live_runtime','snapshot':public_config},services=services,files=self.files,symbols=self.symbols,dependencies=self.dependencies,
                  call_graph=self.calls,service_contracts=self.contracts,summary=summary)
        output.mkdir(parents=True,exist_ok=True)
        for name,value in data.items():
            (output/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
        bundle='window.SOURCE_INDEX='+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n'
        (output.parent/'source-index.js').write_text(bundle,encoding='utf-8')
        print(json.dumps({k:v for k,v in summary.items() if k not in {'parser_diagnostics','import_scc'}},indent=2))
        return data

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/architecture/data')
    args=parser.parse_args();Index().generate(args.root,args.output)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--native-worker':
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        except ImportError:pass
        worker=Index();worker.structural(sys.argv[2],sys.stdin.read())
        print(json.dumps({key:getattr(worker,key) for key in ('symbols','calls','dependencies','errors')}))
    else:main()
