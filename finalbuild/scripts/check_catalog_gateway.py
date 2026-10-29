"""Two real processes + temporary SQL: remote catalog failure never disables identity."""
from pathlib import Path
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
P='/api/v2/ecosystem'

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]

def http(base,path,method='GET',data=None,token=None):
    headers={'Content-Type':'application/json','X-Correlation-ID':'qa-remote-catalog'}
    if token:headers['Authorization']='Bearer '+token
    req=Request(base+path,method=method,headers=headers,data=json.dumps(data).encode() if data is not None else None)
    try:response=urlopen(req,timeout=5)
    except HTTPError as error:response=error
    with response:
        payload=response.read()
        return response.status,json.loads(payload) if payload else None,response.headers

def stop(process):
    if process is not None and process.poll() is None:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)

def ready(process,base):
    deadline=time.monotonic()+30
    while time.monotonic()<deadline:
        if process.poll() is not None:raise RuntimeError('Isolated service exited before readiness')
        try:
            if http(base,'/health')[0]==200:return
        except OSError:pass
        time.sleep(.05)
    raise RuntimeError('Isolated service startup timeout')

def main():
    checks={};backend=None;catalog=None
    with tempfile.TemporaryDirectory(prefix='ai-car-catalog-smoke-') as directory:
        folder=Path(directory);token=secrets.token_urlsafe(48)
        backend_port,catalog_port=free_port(),free_port()
        base=f'http://127.0.0.1:{backend_port}';catalog_base=f'http://127.0.0.1:{catalog_port}'
        env={**os.environ,'DATABASE_URL':'sqlite:///'+(folder/'business.sqlite').as_posix(),
             'AI_CAR_ECOSYSTEM_ENABLED':'1','AI_CAR_CATALOG_MODE':'remote','AI_CAR_CATALOG_URL':catalog_base,
             'AI_CAR_VEHICLE_SERVICE_TOKEN':token,'AI_CAR_CONFIG_ENV':'testing','AI_CAR_BACKEND_PORT':str(backend_port),
             'AI_CAR_DISABLE_LLM_AUTOSTART':'1','PYTHONUTF8':'1'}
        env.pop('AI_CAR_ENV_CONFIG',None)
        command=[sys.executable,'-m','backend.main','--migrate','--port',str(backend_port)]
        with (folder/'processes.log').open('w',encoding='utf-8') as log:
            try:
                catalog=subprocess.Popen([sys.executable,'-m','backend.services.vehicle_catalog','--port',str(catalog_port)],
                    cwd=ROOT/'finalbuild',env=env,stdout=log,stderr=subprocess.STDOUT)
                ready(catalog,catalog_base)
                backend=subprocess.Popen(command,cwd=ROOT/'finalbuild',env=env,stdout=log,stderr=subprocess.STDOUT)
                ready(backend,base)
                checks['independent_services_started']=True
                checks['catalog_authentication']=http(catalog_base,'/ready')[0]==401
                checks['catalog_readiness']=http(catalog_base,'/ready',token=token)[0]==200
                checks['gateway_requires_account']=http(base,P+'/catalog/makes')[0]==401
                account={'email':'catalog-smoke@example.invalid','full_name':'Catalog smoke','password':'local-smoke-passphrase-123'}
                assert http(base,P+'/accounts','POST',account)[0]==201
                code,login,_=http(base,P+'/auth/login','POST',{'email':account['email'],'password':account['password']})
                assert code==200;bearer=login['access_token']
                for operation,query in [('stats',''),('makes','?q=BMW'),('models','?make=BMW&year=2013'),
                                        ('fitments','?make=BMW&model=3%20Series&year=2013'),
                                        ('profile','?make=BMW&model=3%20Series&year=2013')]:
                    status,payload,headers=http(base,P+'/catalog/'+operation+query,token=bearer)
                    checks['gateway_remote_'+operation]=status==200 and bool(payload)
                    assert headers['X-Correlation-ID']=='qa-remote-catalog'
                stop(catalog)
                checks['catalog_failure_is_503']=http(base,P+'/catalog/stats',token=bearer)[0]==503
                checks['identity_survives_catalog_failure']=http(base,P+'/me',token=bearer)[0]==200
                stop(backend);env['AI_CAR_CATALOG_MODE']='embedded'
                backend=subprocess.Popen(command,cwd=ROOT/'finalbuild',env=env,stdout=log,stderr=subprocess.STDOUT)
                ready(backend,base)
                checks['rollback_embedded_preserves_account']=http(base,P+'/me',token=bearer)[0]==200
                checks['rollback_embedded_restores_catalog']=http(base,P+'/catalog/makes?q=BMW',token=bearer)[1]==['BMW']
                assert all(checks.values()),'Catalog gateway smoke check failed'
            finally:stop(backend);stop(catalog)
    evidence={'result':'PASS','checks':checks,'execution':'Two independent Python processes; real HTTP + temporary Alembic SQLite; no hardware/providers'}
    (ROOT/'docs/evidence/catalog-gateway-smoke.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('PASS: '+', '.join(checks))

if __name__=='__main__':main()
