"""Capture native Qt demo pages using seeded data and mocked I/O.
Run after installing project runtime/dev dependencies.
"""
import os,sys,json,gc
from pathlib import Path
from unittest.mock import Mock,patch
os.environ['QT_QPA_PLATFORM']='offscreen'
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QCoreApplication,QEvent,QTimer
from PySide6.QtWidgets import QApplication,QWidget,QLabel,QVBoxLayout,QPlainTextEdit
from PySide6.QtGui import QFont
from apps.desktop import ui
from apps.desktop.models import Vehicle,Session
from apps.desktop.tests.test_ui_pom import FakeStore,MemorySettings
out=ROOT/'docs/demo/screenshots';out.mkdir(parents=True,exist_ok=True)
app=QApplication([])
raw=json.loads((ROOT/'docs/demo/demo-data.json').read_text());raw['session_id']='private-demo-session'
vehicle=Vehicle.from_json(raw['vehicle'])
api=Mock();api.list_sessions.return_value=[raw];api.acquisition_status.return_value={'state':'STOPPED'}
api.ai_provider_info.return_value={'available':False,'model':'local','reason':'Demo fixture: provider not connected'}
api.acquisition_records.return_value={'records':[]}
MemorySettings.values={'language':'en','dark_theme':True}
with patch.object(ui,'DiagnosticApiClient',lambda:api),patch.object(ui,'VehicleStore',lambda:FakeStore([vehicle])),patch.object(ui,'QSettings',MemorySettings),patch.object(ui.MainWindow,'refresh_all',lambda self:None):
 w=ui.MainWindow();w.active_vehicle=vehicle;w.session=Session(raw['session_id'],raw['state'],vehicle);w.session_json=raw;w.online=True;w.network={'ecus':[{'ecu_id':'ME9.7','state':'INFERRED'}]};w.decision={'candidates':raw.get('recommendations',[])}
 w.resize(1440,920);w.show();w.refresh_pages();w.pages[9].loaded([raw])
 for name,index in [('desktop-dashboard',0),('desktop-analysis',3),('desktop-tests',8),('desktop-reports',9)]:
  w.nav.setCurrentRow(index);app.processEvents()
  for label in w.findChildren(QLabel):assert raw['session_id'] not in label.text(),label.text()
  assert w.grab().save(str(out/f'{name}.png'))
 w.dark_theme=False;w._apply_theme();w.nav.setCurrentRow(0);w.refresh_pages();app.processEvents();w.grab().save(str(out/'desktop-dashboard-light.png'))
 w.close();w.deleteLater();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
# These are actual Qt log/source viewers, explicitly labelled in the deck.
for name,title,text in [
 ('source-privacy','SOURCE VIEW • apps/desktop/models.py',(ROOT/'apps/desktop/models.py').read_text().split('def user_report_data')[1]),
 ('test-evidence','QA OUTPUT VIEW • completed test run',(ROOT/'docs/demo/evidence/desktop-tests.txt').read_text()),
 ('backend-evidence','PROCESS OUTPUT VIEW • actual local backend startup',(ROOT/'docs/demo/evidence/backend-startup.txt').read_text())]:
 viewer=QWidget();viewer.resize(1360,760);viewer.setStyleSheet('background:#071827;color:#E9F4FA;');layout=QVBoxLayout(viewer);label=QLabel(title);label.setStyleSheet('font-size:20px;padding:18px;color:#27C4EE;');layout.addWidget(label)
 textedit=QPlainTextEdit();textedit.setReadOnly(True);textedit.setFont(QFont('DejaVu Sans Mono',13));textedit.setStyleSheet('border:1px solid #17445D;padding:20px;')
 if name=='source-privacy':text='def user_report_data'+text
 textedit.setPlainText(text);layout.addWidget(textedit);viewer.show();app.processEvents();viewer.grab().save(str(out/f'{name}.png'));viewer.close();viewer.deleteLater()
QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents();gc.collect()
print('Captured native Qt UI and evidence viewers:',len(list(out.glob('*.png'))))
