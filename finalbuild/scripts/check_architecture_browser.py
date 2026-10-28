"""Local browser QA; external links/providers are never opened."""
from pathlib import Path
import argparse,base64,json,shutil,socket,subprocess,tempfile,time,urllib.request
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from websockets.sync.client import connect


def main():
    root=Path(__file__).resolve().parents[2]
    parser=argparse.ArgumentParser(description='Validate the bundled architecture in real Chromium over localhost.')
    parser.add_argument('--browser',default=shutil.which('chromium') or shutil.which('google-chrome'),help='Chromium/Chrome executable')
    args=parser.parse_args()
    if not args.browser:parser.error('Install Chromium or pass --browser PATH')
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root/'docs')))
    Thread(target=server.serve_forever,daemon=True).start()
    with tempfile.TemporaryDirectory(prefix='architecture-browser-',ignore_cleanup_errors=True) as profile:
     process=subprocess.Popen([args.browser,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--disable-background-networking','--no-first-run','--no-default-browser-check','--remote-allow-origins=*','--remote-debugging-port='+str(port),'--user-data-dir='+profile,'--window-size=1600,1000',f'http://127.0.0.1:{server.server_port}/architecture/interactive_architecture.html'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
     try:
      for _ in range(100):
       try:
        tabs=json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json',timeout=1));tab=next(t for t in tabs if t['type']=='page' and t.get('url','').endswith('interactive_architecture.html'));break
       except (OSError,StopIteration):time.sleep(.1)
      else:raise RuntimeError('Chromium did not start')
      with connect(tab['webSocketDebuggerUrl'],open_timeout=5) as ws:
       index=0
       def call(method,params=None):
        nonlocal index
        index+=1;ws.send(json.dumps({'id':index,'method':method,'params':params or {}}))
        while True:
         response=json.loads(ws.recv())
         if response.get('id')==index:
          if 'error' in response:raise RuntimeError(response['error'])
          return response.get('result',{})
       def evaluate(script):
        result=call('Runtime.evaluate',{'expression':script,'returnByValue':True,'awaitPromise':True})
        if result.get('exceptionDetails'):raise RuntimeError(result['exceptionDetails'])
        return result.get('result',{}).get('value')
       for _ in range(60):
        if evaluate('Boolean(document.querySelector("[data-node]"))'):break
        time.sleep(.1)
       checks={}
       checks['initial_nodes']=evaluate('document.querySelectorAll("[data-node]").length')
       if checks['initial_nodes'] != 22:
        print(evaluate('JSON.stringify({url:location.href,ready:document.readyState,title:document.title,data:window.ARCHITECTURE_DATA&&window.ARCHITECTURE_DATA.nodes.length,views:document.getElementById("view")&&document.getElementById("view").options.length,text:document.body.innerText.slice(0,500)})'))
       assert checks['initial_nodes']==22
       checks['all_views']=evaluate('''(()=>{const s=document.getElementById('view'),r={};for(const option of s.options){s.value=option.value;s.dispatchEvent(new Event('change'));r[s.value]=document.querySelectorAll('[data-node]').length;}s.selectedIndex=0;s.dispatchEvent(new Event('change'));return r;})()''')
       assert len(checks['all_views'])==10 and all(checks['all_views'].values())
       checks['search']=evaluate('''(()=>{const s=document.getElementById('search');s.value='PostgreSQL';s.dispatchEvent(new Event('input'));const n=document.querySelectorAll('[data-node]').length;s.value='';s.dispatchEvent(new Event('input'));return n;})()''');assert checks['search']==1
       checks['layer_filter']=evaluate('''(()=>{const b=document.querySelector('[data-layer="Native UI"]');b.checked=false;b.dispatchEvent(new Event('change'));const n=document.querySelectorAll('[data-node]').length;b.checked=true;b.dispatchEvent(new Event('change'));return n;})()''');assert checks['layer_filter']==19
       checks['collapse']=evaluate('''(()=>{document.querySelector('[data-group="Native UI"]').dispatchEvent(new Event('click'));const n=document.querySelectorAll('[data-node]').length;document.querySelector('[data-group="Native UI"]').dispatchEvent(new Event('click'));return n;})()''');assert checks['collapse']==19
       evaluate('document.querySelector("[data-node=consent]").dispatchEvent(new Event("click"))');checks['component_details']=evaluate('document.getElementById("details").textContent');assert 'Security boundary' in checks['component_details']
       evaluate('document.querySelector("[data-edge]").dispatchEvent(new Event("click"))');checks['relationship_details']=evaluate('document.getElementById("details").textContent');assert 'Direction' in checks['relationship_details']
       checks['path_filter']=evaluate('''(()=>{const s=document.getElementById('path');s.value='offline';s.dispatchEvent(new Event('change'));const n=document.querySelectorAll('.edge.online').length;s.value='all';s.dispatchEvent(new Event('change'));return n;})()''');assert checks['path_filter']==0
       checks['zoom']=evaluate('''(()=>{const b=Number(document.getElementById('diagram').dataset.scale);document.getElementById('zoom-in').click();return Number(document.getElementById('diagram').dataset.scale)>b;})()''');assert checks['zoom']
       evaluate('document.getElementById("theme").click()');checks['theme']=evaluate('document.documentElement.dataset.theme');assert checks['theme']=='light'
       evaluate('document.getElementById("theme").click()')
       box=evaluate('''(()=>{const svg=document.getElementById('diagram'),r=svg.getBoundingClientRect();for(let y=r.top+8;y<r.bottom-8;y+=16){for(let x=r.left+8;x<r.right-8;x+=16){const target=document.elementFromPoint(x,y);if(target&&svg.contains(target)&&!target.closest('.node,.toggle,.edge'))return {x,y};}}throw new Error('No diagram background available for drag');})()''')
       before=evaluate('document.getElementById("scene").getAttribute("transform")')
       call('Input.dispatchMouseEvent',dict(type='mousePressed',button='left',buttons=1,clickCount=1,x=box['x'],y=box['y']))
       time.sleep(.1)
       call('Input.dispatchMouseEvent',dict(type='mouseMoved',buttons=1,x=box['x']+50,y=box['y']+40))
       time.sleep(.15)
       call('Input.dispatchMouseEvent',dict(type='mouseReleased',button='left',buttons=0,clickCount=1,x=box['x']+50,y=box['y']+40))
       checks['pan']=evaluate('document.getElementById("scene").getAttribute("transform")')!=before;assert checks['pan']
       before=evaluate('document.getElementById("diagram").dataset.scale')
       call('Input.dispatchMouseEvent',dict(type='mouseWheel',x=box['x'],y=box['y'],deltaX=0,deltaY=-120));time.sleep(.15)
       checks['wheel_zoom']=evaluate('document.getElementById("diagram").dataset.scale')!=before;assert checks['wheel_zoom']
       evaluate('document.getElementById("reset").click();document.querySelector("[data-node=identity]").dispatchEvent(new Event("click"))')
       shot=call('Page.captureScreenshot',{'format':'png'})
       (root/'docs/evidence/interactive-architecture.png').write_bytes(base64.b64decode(shot['data']))
       call('Emulation.setDeviceMetricsOverride',{'width':420,'height':900,'deviceScaleFactor':1,'mobile':False});time.sleep(.2)
       checks['responsive']=evaluate('document.documentElement.scrollWidth <= 420');assert checks['responsive']
       (root/'docs/evidence/architecture-browser-checks.json').write_text(json.dumps({'browser':'Chromium headless; bundled assets over localhost (file URLs blocked by host browser policy)','checks':checks,'result':'PASS'},indent=2)+'\n')
       try:call('Browser.close')
       except Exception:pass
       print('PASS: 10 views, 22 nodes, search, layer filter, collapse, details, relationships, zoom, real pointer pan, wheel, theme')
     finally:
      if process.poll() is None:
       try:process.wait(timeout=5)
       except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10)
      server.shutdown();server.server_close()


if __name__ == "__main__":
    main()
