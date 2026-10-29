"""Native account browser boundaries; backend permission tests use real SQL/HTTP separately."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from types import SimpleNamespace
import httpx
from PySide6.QtWidgets import QApplication,QWidget
from apps.desktop import business_workspace as module


def test_account_browser_auth_navigation_and_logout(monkeypatch):
    app=QApplication.instance() or QApplication([])
    host=QWidget();host.api=SimpleNamespace(base_url='http://127.0.0.1:8001')
    observed=[];real_client=httpx.Client
    def handler(request):
        observed.append(request)
        path=request.url.path
        if path.endswith('/auth/login'):return httpx.Response(200,json={'access_token':'t'*43})
        if path.endswith('/me'):return httpx.Response(200,json={'modes':['USER'],'portals':[]})
        if path.endswith('/navigation'):return httpx.Response(200,json={'pages':[{'label':'My vehicles','path':'/api/v2/ecosystem/vehicles'}]})
        if path.endswith('/auth/logout'):return httpx.Response(204)
        return httpx.Response(200,json=[])
    class Client:
        def __init__(self):self.client=real_client(transport=httpx.MockTransport(handler))
        def __enter__(self):return self
        def __exit__(self,*args):self.client.close()
        def request(self,*args,**kwargs):
            kwargs['follow_redirects']=kwargs.pop('allow_redirects')
            return self.client.request(*args,**kwargs)
    monkeypatch.setattr(module.requests,'Session',Client)
    def worker(fn,done,failed):
        try:done(fn())
        except Exception as error:failed(str(error))
    host.run_worker=worker
    window=module.BusinessWorkspace(host);window.email.setText('owner@example.invalid');window.password.setText('never persisted')
    window.login()
    assert window.token=='t'*43 and window.password.text()==''
    assert window.workspace.itemText(0)=='USER' and window.page.itemText(0)=='My vehicles'
    assert observed[0].headers.get('authorization') is None
    assert all(r.headers.get('authorization')=='Bearer '+'t'*43 for r in observed[1:])
    window.logout();assert window.token=='' and window.workspace.count()==0
    assert observed[-1].url.path.endswith('/auth/logout')
    window.close();host.close();app.processEvents()


def test_registration_and_failed_login_keep_password_out_of_output(monkeypatch):
    app=QApplication.instance() or QApplication([])
    host=QWidget();host.api=SimpleNamespace(base_url='http://127.0.0.1:8001')
    def worker(fn,done,failed):failed('HTTP 401: Invalid email or password.')
    host.run_worker=worker
    window=module.BusinessWorkspace(host);window.password.setText('secret passphrase')
    window.login();assert window.password.text()=='' and window.token==''
    assert 'secret passphrase' not in window.output.toPlainText()
    captured=[]
    window.request=lambda *args:captured.append(args)
    window.password.setText('long new password');window.full_name.setText('Owner');window.email.setText('owner@example.invalid');window.register()
    assert captured[0][1]=='POST' and captured[0][2]['full_name']=='Owner'
    assert window.password.text()==''
    window.close();host.close();app.processEvents()
