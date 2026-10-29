from pathlib import Path
import importlib.util
import json
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('source_indexer',ROOT/'scripts/architecture/generate_index.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_python_ast_routes_calls_stable_ids_and_unresolved_receivers():
    index=module.Index()
    source='''from os import getenv as setting
from fastapi import APIRouter
PREFIX = '/internal/v1'
router = APIRouter(prefix=PREFIX)
def helper(value: int) -> int: return value
@router.get('/makes')
async def endpoint(query: str = '') -> list[str]:
    helper(1)
    unknown.resolve(query)
    return []
'''
    path='finalbuild/backend/services/vehicle_catalog/example.py'
    index.filemap[path]={'id':module.stable('file',path)}
    index.python(path,source);index.resolve()
    call=next(c for c in index.calls if c['expression']=='helper')
    assert call['target'] and call['resolution']=='static_binding_resolved'
    assert next(c for c in index.calls if c['expression']=='unknown.resolve')['target'] is None
    assert index.contracts[0]['full_route']=='/internal/v1/makes'
    assert index.contracts[0]['resolution']=='literal_route_and_prefix_verified'
    assert next(s for s in index.symbols if s['name']=='endpoint')['async_function']
    second=module.Index();second.python(path,'\n\n'+source)
    assert {s['id'] for s in index.symbols}=={s['id'] for s in second.symbols}
    assert index.symbols[0]['start_line']+2==second.symbols[0]['start_line']

def test_tree_sitter_extracts_native_declarations_without_faking_call_resolution():
    for extension,source in [('.kt','class Vehicle { fun read(x: Int): Int { return scan(x) } }'),
                             ('.swift','class Vehicle { func read(x: Int) -> Int { return scan(x) } }'),
                             ('.cpp','int read(int x) { return scan(x); }'),
                             ('.js','function read(x) { return scan(x); }')]:
        index=module.Index();index.structural_safe('src/example'+extension,source)
        assert any(s['name']=='read' for s in index.symbols),index.errors
        assert any('scan' in c['expression'] and c['target'] is None for c in index.calls)

def test_preview_redaction_and_output_references():
    assert 'DO_NOT_PUBLISH' not in module.clean_preview("api_key = 'DO_NOT_PUBLISH'\nx = 1")
    files=json.loads((ROOT/'docs/architecture/data/files.json').read_text())
    symbols=json.loads((ROOT/'docs/architecture/data/symbols.json').read_text())
    known={f['id'] for f in files}|{s['id'] for s in symbols}
    assert len(known)==len(files)+len(symbols)
    for name in ['dependencies','call_graph']:
        for edge in json.loads((ROOT/'docs/architecture/data'/f'{name}.json').read_text()):
            assert edge['source'] in known
            assert edge['target'] is None or edge['target'] in known
    assert all(not Path(f['path']).is_absolute() and '..' not in Path(f['path']).parts for f in files)
