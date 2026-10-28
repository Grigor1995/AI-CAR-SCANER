"""Regenerate each architecture view as Mermaid from the local interactive data."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT/'docs/architecture'


def main():
    data = json.loads((DIRECTORY/'architecture-data.js').read_text(encoding='utf-8').partition('=')[2].strip().removesuffix(';'))
    for title, ids in data['views'].items():
        selected = set(ids)
        lines = ['flowchart LR']
        for node in data['nodes']:
            if node['id'] not in selected: continue
            label = json.dumps(node['title']+' — '+node['status'], ensure_ascii=False)
            lines.append(f'  {node["id"]}[{label}]')
        for edge in data['edges']:
            if edge['source'] in selected and edge['target'] in selected:
                label = json.dumps(edge['label'], ensure_ascii=False)
                lines.append(f'  {edge["source"]} -->|{label}| {edge["target"]}')
        lines.append('  classDef planned stroke-dasharray: 5 5;')
        planned = [node['id'] for node in data['nodes'] if node['id'] in selected and node['status']=='PLANNED']
        if planned: lines.append('  class '+','.join(planned)+' planned;')
        content = '\n'.join(lines)+'\n'
        filename = re.sub('[^a-z0-9]+', '-', title.lower()).strip('-')+'.mmd'
        (DIRECTORY/filename).write_text(content,encoding='utf-8')
        if title=='High-Level Architecture': (DIRECTORY/'architecture.mmd').write_text(content,encoding='utf-8')
    print(f'Exported {len(data["views"])} Mermaid architecture views')


if __name__ == '__main__':
    main()
