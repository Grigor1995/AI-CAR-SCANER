"""Three independent thin desktop clients; no local server or domain engine import."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from urllib.parse import urlsplit

ROLES=('USER','CUSTOMER','MARKET')


def endpoint(value):
    try:
        parsed=urlsplit(value)
        parsed.port
    except ValueError as error:
        raise argparse.ArgumentTypeError('Invalid backend URL') from error
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise argparse.ArgumentTypeError('Use a backend HTTP(S) URL without credentials/query/fragment')
    return value.rstrip('/')


def main(role,argv=None):
    if role not in ROLES:raise ValueError('Unknown application')
    parser=argparse.ArgumentParser(prog='AI-Car-'+role.title())
    parser.add_argument('--backend-url',type=endpoint)
    parser.add_argument('--check',action='store_true',help='Print this fixed application identity without opening UI')
    parser.add_argument('--smoke',action='store_true',help='Open and close the real Qt window without network operations')
    args=parser.parse_args(argv)
    if args.check:
        print(json.dumps({'application':role,'backend_embedded':False,'primary_mode':role!='MARKET'}));return 0
    from PySide6.QtCore import Signal,Slot,QSettings,QTimer
    from PySide6.QtGui import QIcon,QFont
    from PySide6.QtWidgets import QApplication,QWidget
    from .business_workspace import BusinessWorkspace
    app=QApplication.instance() or QApplication(sys.argv[:1])
    app.setOrganizationName('AI-Car-Scanner');app.setApplicationName('AI-Car-'+role.title());app.setFont(QFont('Segoe UI',10))
    settings=QSettings()
    base=args.backend_url or os.environ.get('AI_CAR_BACKEND_URL') or settings.value('backend_url',f"http://127.0.0.1:{os.environ.get('AI_CAR_BACKEND_PORT','8001')}",type=str)
    base=endpoint(base);settings.setValue('backend_url',base)
    # Presentation constants remain shared; importing this module does not start services.
    from .theme import APP_QSS
    app.setStyleSheet(APP_QSS)
    asset_root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[2]))
    app.setWindowIcon(QIcon(str(asset_root/'assets/AI-Car-Scanner-mobile.png')))
    class Host(QWidget):
        delivered=Signal(int,object,str)
        def __init__(self):
            super().__init__();self.api=SimpleNamespace(base_url=base);self.pending={};self.sequence=0;self.closing=False
            self.delivered.connect(self.deliver)
        def run_worker(self,fn,done,failed):
            if self.closing:return
            self.sequence+=1;ticket=self.sequence;self.pending[ticket]=(done,failed)
            def run():
                try:result,error=fn(),''
                except Exception as exc:result,error=None,str(exc)
                try:self.delivered.emit(ticket,result,error)
                except RuntimeError:pass  # Application was closed; daemon owns no Qt resource.
            threading.Thread(target=run,daemon=True).start()
        @Slot(int,object,str)
        def deliver(self,ticket,result,error):
            callbacks=self.pending.pop(ticket,None)
            if callbacks and not self.closing:
                (callbacks[1](error) if error else callbacks[0](result))
    host=Host();window=BusinessWorkspace(host,fixed_workspace=role)
    window.finished.connect(app.quit)
    def closing():host.closing=True;host.pending.clear()
    app.aboutToQuit.connect(closing);window.show()
    if args.smoke:QTimer.singleShot(100,window.close)
    return app.exec()
