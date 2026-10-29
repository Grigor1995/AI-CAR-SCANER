"""Validate bundled performance dashboard using local Chromium and real input."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
from threading import Thread
import time
import urllib.request
from websockets.sync.client import connect


def main():
    root=Path(__file__).resolve().parents[2]
    browser=shutil.which('chromium') or shutil.which('google-chrome')
    if not browser:raise RuntimeError('Chromium/Chrome required')
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root/'docs')))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        with tempfile.TemporaryDirectory(prefix='performance-browser-') as folder:
            proc=subprocess.Popen([browser,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--disable-background-networking','--remote-allow-origins=*',f'--remote-debugging-port={port}',f'--user-data-dir={folder}','--window-size=1500,1000',f'http://127.0.0.1:{server.server_port}/architecture/performance_architecture_dashboard.html'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                for _ in range(100):
                    try:
                        tabs=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json',timeout=2));break
                    except OSError:time.sleep(.1)
                else:raise RuntimeError('Browser startup timeout')
                with connect(next(t for t in tabs if t.get('type')=='page')['webSocketDebuggerUrl']) as ws:
                    index=0
                    def call(method,params=None):
                        nonlocal index
                        index+=1;ws.send(json.dumps({'id':index,'method':method,'params':params or {}}))
                        while True:
                            response=json.loads(ws.recv())
                            if response.get('id')==index:
                                if 'error' in response:raise RuntimeError(response['error'])
                                return response.get('result',{})
                    def js(code):
                        result=call('Runtime.evaluate',{'expression':code,'returnByValue':True})
                        if result.get('exceptionDetails'):raise RuntimeError(result['exceptionDetails'])
                        return result.get('result',{}).get('value')
                    for _ in range(100):
                        if js('document.querySelectorAll("[data-node]").length===13'):break
                        time.sleep(.1)
                    checks={'initial_nodes':js('document.querySelectorAll("[data-node]").length')};assert checks['initial_nodes']==13
                    checks['search']=js("document.querySelector('#search').value='Telemetry summary';document.querySelector('#search').dispatchEvent(new Event('input'));document.querySelectorAll('[data-node]').length");assert checks['search']==1
                    js("document.querySelector('#reset').click();document.querySelector('#language').value='C++';document.querySelector('#language').dispatchEvent(new Event('change'))")
                    checks['language']=js("document.querySelectorAll('[data-node]').length");assert checks['language']==1
                    js("document.querySelector('#reset').click();document.querySelector('#status').value='OPTIMIZE';document.querySelector('#status').dispatchEvent(new Event('change'))")
                    checks['decision']=js("document.querySelectorAll('[data-node]').length");assert checks['decision']==1
                    js("document.querySelector('#reset').click();document.querySelector('[data-node=telemetry]').dispatchEvent(new Event('click'))")
                    checks['details_and_dependencies']=js("document.querySelector('#details').textContent.includes('service.py') && document.querySelectorAll('.edge.highlight').length>0");assert checks['details_and_dependencies']
                    js("document.querySelector('#zoom-in').click()")
                    checks['zoom']=js("Number(document.querySelector('#diagram').dataset.scale)>1");assert checks['zoom']
                    js("document.querySelector('#reset').click()")
                    box=js("(()=>{const r=document.querySelector('#diagram').getBoundingClientRect();return {x:r.left+r.width*.9,y:r.top+r.height*.8}})()")
                    before=js("document.querySelector('#scene').getAttribute('transform')")
                    call('Input.dispatchMouseEvent',dict(type='mousePressed',button='left',buttons=1,clickCount=1,**box))
                    call('Input.dispatchMouseEvent',dict(type='mouseMoved',buttons=1,x=box['x']+20,y=box['y']+20))
                    call('Input.dispatchMouseEvent',dict(type='mouseReleased',button='left',buttons=0,clickCount=1,x=box['x']+20,y=box['y']+20))
                    checks['pan']=js("document.querySelector('#scene').getAttribute('transform')")!=before;assert checks['pan']
                    call('Input.dispatchMouseEvent',dict(type='mouseWheel',deltaX=0,deltaY=-100,**box));time.sleep(.1)
                    checks['wheel']=js("Number(document.querySelector('#diagram').dataset.scale)>1");assert checks['wheel']
                    js("document.querySelector('[data-view=performance]').click()")
                    checks['baseline_rows']=js("document.querySelectorAll('#metrics tbody tr').length");assert checks['baseline_rows']==9
                    js("document.querySelector('[data-view=comparison]').click()")
                    checks['comparison_rows']=js("document.querySelectorAll('#comparison-data tbody tr').length");assert checks['comparison_rows']==3
                    js("document.querySelector('#native-data summary').click()")
                    checks['expandable']=js("document.querySelector('#native-data details').open");assert checks['expandable']
                    call('Emulation.setDeviceMetricsOverride',{'width':420,'height':900,'deviceScaleFactor':1,'mobile':False})
                    checks['responsive']=js('document.documentElement.scrollWidth<=window.innerWidth');assert checks['responsive']
                    out=root/'docs/performance/evidence/dashboard-browser.json';out.write_text(json.dumps({'status':'PASS','checks':checks,'scope':'Chromium local HTTP, not Windows/iOS rendering'},indent=2)+'\n',encoding='utf-8')
                    print(json.dumps(checks))
            finally:
                proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
    finally:server.shutdown();server.server_close()

if __name__=='__main__':main()
