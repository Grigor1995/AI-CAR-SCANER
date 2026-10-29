import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from services.vehicle_catalog.app import app
from services.vehicle_catalog import port
from configuration import ConfigManager

TOKEN = 'test-internal-credential-' + 'x'*32

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('AI_CAR_VEHICLE_SERVICE_TOKEN', TOKEN)
    return TestClient(app)

def test_health_authorization_validation_and_correlation(client):
    assert client.get('/health').json()['status'] == 'alive'
    assert client.get('/ready').status_code == 401
    headers={'Authorization': 'Bearer '+TOKEN, 'X-Correlation-ID': 'qa-catalog-1'}
    response=client.get('/internal/v1/catalog/makes?query=BMW', headers=headers)
    assert response.json() == ['BMW']
    assert response.headers['X-Correlation-ID'] == 'qa-catalog-1'
    assert client.get('/internal/v1/catalog/models?make=BMW&limit=0', headers=headers).status_code==422
    assert client.get('/ready', headers=headers).json()=={'status':'ready'}

def test_missing_service_secret_fails_closed(client, monkeypatch):
    monkeypatch.delenv('AI_CAR_VEHICLE_SERVICE_TOKEN')
    assert client.get('/ready').status_code==503

def test_real_http_adapter_equivalence_and_partial_failure(tmp_path, monkeypatch):
    # A real independent uvicorn process, not an ASGI transport substitute.
    import os, socket, subprocess, time
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); number=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-m','backend.services.vehicle_catalog','--port',str(number)],
                             env={**os.environ,'AI_CAR_VEHICLE_SERVICE_TOKEN':TOKEN},
                             stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                             cwd=str(__import__('pathlib').Path(__file__).resolve().parents[2]))
    folder=tmp_path/'config';folder.mkdir()
    folder.joinpath('global_config.json').write_text(json.dumps({'services':{'vehicle_catalog':{
        'mode':'remote','url':f'http://127.0.0.1:{number}','timeout_seconds':0.2,'retries':1}}}))
    m=ConfigManager(tmp_path,environ={})
    monkeypatch.setattr(port,'get_manager',lambda:m)
    monkeypatch.setenv('AI_CAR_VEHICLE_SERVICE_TOKEN',TOKEN)
    try:
        for _ in range(100):
            try:
                assert port.catalog('makes',query='BMW')==['BMW'];break
            except HTTPException: time.sleep(.05)
        else: pytest.fail('catalog service did not become ready')
        for op,args in [('stats',{}),('models',{'make':'BMW','year':2013}),
                        ('fitments',{'make':'BMW','model':'3 Series','year':2013}),
                        ('profile',{'make':'BMW','model':'3 Series','year':2013})]:
            assert port.catalog(op,**args)==port.embedded(op,args)
    finally:
        process.terminate();process.wait(timeout=10)
    started=time.monotonic()
    with pytest.raises(HTTPException) as exc: port.catalog('stats')
    assert exc.value.status_code==503 and time.monotonic()-started<2

def test_service_imports_no_database_in_fresh_process():
    import subprocess
    result=subprocess.run([sys.executable,'-c',"import services.vehicle_catalog.app,sys; assert not any(n.startswith(('sqlalchemy','ecosystem','diagnostic.session_persistence')) for n in sys.modules)"],capture_output=True,text=True,cwd=str(__import__('pathlib').Path(__file__).resolve().parents[2]/'backend'))
    assert result.returncode==0,result.stderr

@pytest.mark.parametrize('scenario', ['retry', 'invalid', 'redirect', 'timeout'])
def test_real_http_retry_timeout_redirect_and_invalid_contract(tmp_path, monkeypatch, scenario):
    import time
    class Handler(BaseHTTPRequestHandler):
        attempts=0
        def do_GET(self):
            type(self).attempts+=1
            assert self.headers['Authorization']=='Bearer '+TOKEN
            if scenario=='timeout':time.sleep(.3)
            status=503 if scenario=='retry' and self.attempts==1 else 302 if scenario=='redirect' else 200
            self.send_response(status)
            if scenario=='redirect':self.send_header('Location','http://127.0.0.1:9/credential-leak')
            self.end_headers()
            try:self.wfile.write(json.dumps([42] if scenario=='invalid' else ['BMW']).encode())
            except (BrokenPipeError, ConnectionResetError):pass
        def log_message(self,*_):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    folder=tmp_path/'config';folder.mkdir()
    folder.joinpath('global_config.json').write_text(json.dumps({'services':{'vehicle_catalog':{
        'mode':'remote','url':f'http://127.0.0.1:{server.server_port}','timeout_seconds':0.1,'retries':1}}}))
    manager=ConfigManager(tmp_path,environ={})
    monkeypatch.setattr(port,'get_manager',lambda:manager);monkeypatch.setenv('AI_CAR_VEHICLE_SERVICE_TOKEN',TOKEN)
    try:
        started=time.monotonic()
        if scenario=='retry':assert port.catalog('makes',query='BMW')==['BMW']
        else:
            with pytest.raises(HTTPException) as error:port.catalog('makes',query='BMW')
            assert error.value.status_code==503 and 'credential-leak' not in str(error.value)
        assert time.monotonic()-started<1
        assert Handler.attempts==(2 if scenario in {'retry','timeout'} else 1)
    finally:server.shutdown();server.server_close();thread.join(timeout=5)
