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
        assert window.parent() is None
        assert window.windowType()==QtCore.Qt.WindowType.Window
        assert not window.windowIcon().isNull() and not app.windowIcon().isNull()
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


@pytest.mark.parametrize('role',['USER','CUSTOMER','MARKET'])
def test_windows_taskbar_identity_matches_installer_shortcut(monkeypatch,role):
    import ctypes
    from pathlib import Path
    from unittest.mock import Mock
    setter=Mock(return_value=0)
    monkeypatch.setattr(product_app.sys,'platform','win32')
    monkeypatch.setattr(ctypes,'windll',SimpleNamespace(shell32=SimpleNamespace(SetCurrentProcessExplicitAppUserModelID=setter)),raising=False)
    product_app.configure_windows_identity(role)
    setter.assert_called_once_with('com.aicarscaner.'+role.lower())
    installer=(Path(product_app.__file__).resolve().parents[2]/'installer/windows/AI-Car-Scanner.iss').read_text(encoding='utf-8')
    shortcuts=[line for line in installer.splitlines() if line.startswith('Name:') and '--app '+role.lower()+' ' in line]
    assert len(shortcuts)==2
    assert all('AppUserModelID: "'+product_app.APP_IDS[role]+'"' in line for line in shortcuts)


def test_windows_identity_failure_keeps_gui_startup_available(monkeypatch,capsys):
    import ctypes
    from unittest.mock import Mock
    monkeypatch.setattr(product_app.sys,'platform','win32')
    setter=Mock(return_value=-1)
    monkeypatch.setattr(ctypes,'windll',SimpleNamespace(shell32=SimpleNamespace(SetCurrentProcessExplicitAppUserModelID=setter)),raising=False)
    product_app.configure_windows_identity('USER')
    assert 'taskbar identity unavailable' in capsys.readouterr().err
