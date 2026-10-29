"""Real Qt event loop and daemon HTTP delivery for each independent client."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from types import SimpleNamespace
import argparse
import time
import pytest
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from apps.desktop import product_app,business_workspace


@pytest.mark.parametrize('role',['USER','CUSTOMER','MARKET'])
def test_fixed_product_window_authenticates_or_surfaces_server_error_and_exits(monkeypatch,role):
    app=QApplication.instance() or QApplication([])
    old=(app.organizationName(),app.applicationName(),app.styleSheet())
    class Settings:
        def value(self,key,default,type=None):return default
        def setValue(self,*args):pass
    monkeypatch.setattr(QtCore,'QSettings',Settings)
    observed=[]
    class HTTP:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def request(self,method,url,**kwargs):
            observed.append((method,url,kwargs))
            if url.endswith('/auth/login'):
                if role=='MARKET':return SimpleNamespace(status_code=401,content=b'x',json=lambda:{'detail':'Invalid credentials'})
                data={'access_token':'t'*43}
            elif url.endswith('/me'):data={'modes':['USER','CUSTOMER','ADMIN'],'portals':['MARKET']}
            elif '/navigation?' in url:data={'pages':[{'label':'Owned records','path':'/api/v2/ecosystem/vehicles'}]}
            else:data={'kind':'fixture'}
            return SimpleNamespace(status_code=200,content=b'x',json=lambda:data)
    monkeypatch.setattr(business_workspace.requests,'Session',HTTP)
    original=business_workspace.BusinessWorkspace;windows=[]
    class Window(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);windows.append(self)
            self.email.setText('owner@example.invalid');self.password.setText('memory-only-password')
            deadline=time.monotonic()+4
            def ready():
                if 'fixture' in self.output.toPlainText() or 'HTTP 401' in self.output.toPlainText() or time.monotonic()>deadline:self.close()
                else:QtCore.QTimer.singleShot(5,ready)
            QtCore.QTimer.singleShot(0,self.login);QtCore.QTimer.singleShot(5,ready)
    monkeypatch.setattr(business_workspace,'BusinessWorkspace',Window)
    try:
        assert product_app.main(role,['--backend-url','http://example.invalid'])==0
        window=windows[0]
        assert window.password.text()=='' and window.token==''
        assert observed and all(call[2]['allow_redirects'] is False for call in observed)
        if role!='MARKET':assert any('/navigation?workspace='+role in call[1] for call in observed)
        else:assert len(observed)==1
    finally:
        for window in windows:window.deleteLater()
        app.processEvents();app.setOrganizationName(old[0]);app.setApplicationName(old[1]);app.setStyleSheet(old[2])


@pytest.mark.parametrize('url',['http://host:bad','http://[','http://user:secret@host','ftp://host','http://host/#fragment'])
def test_client_rejects_unsafe_or_malformed_backend_urls(url):
    with pytest.raises(argparse.ArgumentTypeError):product_app.endpoint(url)


def test_product_identity_check_never_starts_qt_or_backend(capsys):
    assert product_app.main('MARKET',['--check'])==0
    assert '"backend_embedded": false' in capsys.readouterr().out
    with pytest.raises(ValueError):product_app.main('ADMIN',['--check'])
