#!/usr/bin/env python3
"""AI-CAR-SCANER Desktop v1.0 local VISIBLE UI acceptance evidence.

Run from finalbuild: python scripts/real_ui_acceptance.py --exe dist-release/icon-preview/AICarScanner.exe
Modes: --mode source | exe | all. No CI, no network except an ephemeral loopback mock.
Sources use an in-memory API and vehicle store; the frozen EXE uses a mock HTTP
backend and its existing auto-close facility. Neither mode certifies live OBD/LLM.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import html
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from unittest.mock import patch


def project_root() -> Path:
    candidates = (Path.cwd(), Path(__file__).resolve().parent, Path(__file__).resolve().parent.parent)
    for candidate in candidates:
        if (candidate / 'apps' / 'desktop' / 'ui.py').is_file():
            return candidate.resolve()
    raise RuntimeError('Run from finalbuild/ or copy this script into finalbuild/scripts/.')


ROOT = project_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class Evidence:
    def __init__(self, report: Path):
        self.path = report
        self.images = report / 'screenshots'
        self.images.mkdir(parents=True, exist_ok=True)
        self.cases: list[dict] = []
        self.started = datetime.now().astimezone().isoformat(timespec='seconds')
        rev = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=False)
        self.source_commit = rev.stdout.strip() if rev.returncode == 0 else 'unknown'
        self.source_mode = 'visible-native-Qt-window / deterministic fake API'
        self.exe_mode = 'not requested'

    def record(self, name, fn, *, mode='source'):
        before = time.perf_counter()
        try:
            msg = fn()
            result = {'case': name, 'status': 'PASS', 'mode': mode, 'details': str(msg or ''),
                      'seconds': round(time.perf_counter()-before, 3)}
            print(f"[REAL-UI] PASS | {name} | {result['details']}", flush=True)
        except Exception as exc:
            result = {'case': name, 'status': 'FAIL', 'mode': mode,
                      'details': f'{type(exc).__name__}: {exc}',
                      'traceback': traceback.format_exc(),
                      'seconds': round(time.perf_counter()-before, 3)}
            print(f"[REAL-UI] FAIL | {name} | {result['details']}", flush=True)
        self.cases.append(result)
        return result['status'] == 'PASS'

    def shot(self, widget, filename: str, qapp):
        from PySide6.QtTest import QTest
        qapp.processEvents()
        QTest.qWait(100)
        pixmap = widget.grab()
        if pixmap.isNull() or pixmap.width() < 50 or pixmap.height() < 50:
            raise AssertionError(f'Empty screenshot: {filename}')
        target = self.images / filename
        if not pixmap.save(str(target), 'PNG') or target.stat().st_size < 1000:
            raise AssertionError(f'Screenshot was not saved: {target}')
        return target.relative_to(self.path).as_posix()

    def finish(self):
        failures = [case for case in self.cases if case['status'] == 'FAIL']
        automated_status = 'FAIL' if failures else 'PASS'
        result = {
            'project': 'AI-CAR-SCANER Desktop v1.0 RC — Real UI Acceptance',
            'timestamp': self.started,
            'source_commit': self.source_commit,
            'status': automated_status,
            'tests_total': len(self.cases),
            'passed': len(self.cases) - len(failures), 'failed': len(failures),
            'source_mode': self.source_mode,
            'exe_mode': self.exe_mode,
            'manual_release_acceptance': 'PENDING',
            'limitations': [
                'Visible source UI uses simulated in-memory backend responses and storage; it does not validate real FastAPI, OBD, or LLM.',
                'Visible frozen EXE smoke (when enabled) verifies native startup, screenshot, and clean exit against a loopback fake HTTP backend.',
                'A human must review screenshots, taskbar icon, clipping, locale quality, actual backend diagnostics, and the manual checklist.',
            ],
            'cases': self.cases,
        }
        (self.path/'results.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        rows = []
        gallery = []
        for case in self.cases:
            rows.append('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(
                html.escape(case['case']), case['status'], html.escape(case['mode']),
                html.escape(case['details'])))
        for file in sorted(self.images.glob('*.png')):
            gallery.append(f'<figure><a href="screenshots/{html.escape(file.name)}"><img loading="lazy" src="screenshots/{html.escape(file.name)}"></a><figcaption>{html.escape(file.name)}</figcaption></figure>')
        webpage = f'''<!doctype html><html lang="en"><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Desktop v1.0 Real UI Acceptance</title>
<style>body{{font:15px/1.5 system-ui,Segoe UI,sans-serif;background:#111827;color:#e5e7eb;max-width:1280px;margin:auto;padding:28px}}h1,h2{{color:#fff}}.kpi{{font-size:1.4em;color:{'#f87171' if failures else '#34d399'}}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #374151;text-align:left;padding:9px}}th{{background:#1f2937}}.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(370px,1fr));gap:16px}}figure{{margin:0;background:#1f2937;padding:12px;border-radius:8px}}img{{width:100%;height:auto;border:1px solid #334155}}figcaption{{word-wrap:break-word;color:#cbd5e1}}.warning{{color:#fbbf24}}code{{color:#a5b4fc}}</style>
<h1>AI-CAR-SCANER Desktop v1.0 — Real UI Acceptance</h1><p class="kpi">Automated: {automated_status} — {result['passed']}/{result['tests_total']} passed</p><p class="warning">Release gate: MANUAL ACCEPTANCE PENDING. Test automation uses safe simulated data.</p><p>Run: {html.escape(self.started)} · Git commit: <code>{html.escape(self.source_commit)}</code></p><h2>Executed checks</h2><table><tr><th>Case</th><th>Result</th><th>Mode</th><th>Details</th></tr>{''.join(rows)}</table><h2>Visible UI screenshots</h2><div class="gallery">{''.join(gallery)}</div><h2>Release checklist</h2><p>Review <code>MANUAL_CHECKLIST.md</code> before tagging v1.0.</p></html>'''
        (self.path/'report.html').write_text(webpage, encoding='utf-8')
        (self.path/'MANUAL_CHECKLIST.md').write_text(MANUAL_CHECKLIST, encoding='utf-8')
        print(f'[REAL-UI] AUTOMATED {automated_status}: {result["passed"]}/{result["tests_total"]}', flush=True)
        print(f'[REAL-UI] HTML report: {self.path / "report.html"}', flush=True)
        print(f'[REAL-UI] Manual release acceptance: PENDING', flush=True)
        return not failures


MANUAL_CHECKLIST = '''# AI-CAR-SCANER Desktop v1.0 — Manual Release Acceptance

Date: __________  Tester: __________  Windows version / display scaling: __________

## Packaged EXE — real Windows presentation (required)
- [ ] Open the EXE normally with a real display; no crash, missing Qt plugin, or frozen splash
- [ ] The taskbar/window icon is correct (not Python default), and the title appears correctly
- [ ] Dashboard, Vehicles, VCI / Devices, Diagnostic, Live Data, ECU Network, Tests all render without clipping
- [ ] EN / RU / HY text is readable and correctly translated (including placeholders/results)
- [ ] Dark/light theme and settings persist after closing and reopening the EXE
- [ ] 100% and 125% or 150% Windows DPI scaling is usable (if available)
- [ ] Resize/minimize/restore, focus, modal dialogs, and application exit work
- [ ] No UI freezes with the configured backend unavailable

## Real backend diagnostic workflow (required; *not* covered by fake UI run)
- [ ] Confirm backend health / offline indicator matches reality
- [ ] Add W211 2006 M272 Petrol+LPG vehicle; verify catalog choices and local persistence
- [ ] Create diagnostic session, enter LPG-only misfire <2000 RPM + P0302
- [ ] Analysis produces evidence-based hypotheses, useful missing information, and no unjustified confirmed coil failure
- [ ] Open recommended tests and record PASS, FAIL or INCOMPLETE; results persist on reload
- [ ] Re-analysis updates recommendations after the submitted test evidence
- [ ] Live Data simulation and ECU network work without a physical OBD adapter
- [ ] If LLM is unavailable, user sees meaningful deterministic analysis and clear provider status/error
- [ ] No uncaught exception on invalid DTC/empty symptom, offline API, bad network, or Cancel dialogs

## Already verified automated evidence (attach current local output)
- [ ] 310/310 Desktop pytest cases PASS, all-source >= 90%, production-core >= 90%
- [ ] Packaged EXE three-repeat offscreen stability 3/3 PASS
- [ ] Visible source UI report PASS and screenshots visually reviewed
- [ ] Visible packaged EXE smoke PASS and screenshot reviewed
- [ ] Build was generated from the intended Git main commit, with correct assets
- [ ] Release artifact SHA256, executable startup, and clean shutdown recorded

## Go / No-go
Decision: [ ] GO   [ ] NO-GO
Critical defects / evidence links: __________________________________________
Approved by: ____________________   Date: ____________________

Do not tag Desktop v1.0 until manual checks pass. The mocked visual UI test
never substitutes for real FastAPI/LLM/OBD integration evidence.
'''


class EphemeralSettings:
    values: dict = {'language': 'en', 'dark_theme': True}
    def __init__(self, *_args, **_kwargs):
        pass
    def value(self, key, default=None, type=None):
        val = self.values.get(key, default)
        return type(val) if type is not None and val is not None else val
    def setValue(self, key, value):
        self.values[key] = value


class EphemeralVehicles:
    def __init__(self, vehicle):
        self.items = [vehicle]
    def load(self):
        return list(self.items)
    def save(self, values):
        self.items = list(values)


class FakeBackend:
    def __init__(self):
        self.calls: list[dict] = []
        self.evidence: list[dict] = []
        self.results: list[dict] = []
        self.dtcs: list[str] = []

    def vehicle_catalog_entries(self):
        return [
            {'make':'Mercedes-Benz','model':'E-Class','chassis':'W211', 'year':2006,'engine':'M272','ecu':'ME9.7'},
            {'make':'Kia','model':'Forte','chassis':'BD','year':2017,'engine':'2.0','ecu':'SIM2K'},
        ]
    def create_session(self, vehicle):
        self.calls.append({'api':'create_session','vehicle':vehicle})
        return {'session_id':'local-visible-qa-001','state':'CREATED'}
    def ingest_evidence(self, session_id, text):
        self.calls.append({'api':'ingest_evidence','text':text})
        self.evidence.append({'status':'reported','fact':text,'source':'driver'})
        return {'ok':True}
    def add_dtc(self, session_id, code):
        self.calls.append({'api':'add_dtc','code':code})
        self.dtcs.append(code)
        return {'ok':True}
    def analyze(self, session_id, language='en'):
        self.calls.append({'api':'analyze','language':language})
        return {'session_id':session_id,'state':'ANALYSIS_READY',
                'evidence':list(self.evidence), 'hypotheses':[
                    {'category':'LPG injection / calibration',
                     'statement':'Possible LPG delivery or calibration issue; confirm with measured test evidence.',
                     'status':'possible'},
                    {'category':'Ignition under LPG load',
                     'statement':'Verify only if LPG delivery is ruled out.', 'status':'possible'}]}
    def decision_plan(self, session_id):
        self.calls.append({'api':'decision_plan'})
        return {'candidates':[{'id':'lpg-pressure', 'name':'Check LPG pressure',
                              'purpose':'Verify delivery under load', 'priority_score':0.91,'risk':'LOW'}],
                'missing_questions':['Does it also happen on petrol?']}
    def record_test_result(self, session_id, test_id, result, measurements=None, notes='',language='en'):
        data={'test_id':test_id,'result':result,'notes':notes,'language':language}
        self.results.append(data)
        self.calls.append({'api':'record_test_result',**data})
        return {'status':'ok'}
    def acquisition_status(self, session_id):
        return {'state':'STOPPED'}
    def acquisition_records(self, session_id):
        return {'records':[{'numeric_value':700},{'numeric_value':1500}]}
    def ai_provider_info(self):
        return {'available':False,'model':'mock-provider','reason':'simulated offline test'}
    def telemetry_summary(self, session_id):
        return {'signals':[{'pid':'RPM','count':2,'min_value':700,'max_value':1500,'mean':1100,'event_count':1}]}
    def __getattr__(self, name):
        raise AssertionError(f'Unexpected outbound API call: {name}. Real network is forbidden in source UI smoke.')


def run_visible_source(ev: Evidence, hold_seconds: float) -> None:
    from PySide6.QtCore import Qt, QTimer, QCoreApplication, QEvent
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QPushButton, QComboBox, QDialog, QDialogButtonBox
    from apps.desktop import ui
    from apps.desktop.models import Vehicle

    app = QApplication.instance() or QApplication([])
    platform = app.platformName().lower()
    if platform in {'offscreen', 'minimal'}:
        raise RuntimeError(f'Qt platform={platform}: visible tests require a real Windows desktop (unset QT_QPA_PLATFORM).')
    ev.source_mode = f'actual Qt window / platform={platform}, in-memory mocked API and storage'
    vehicle = Vehicle('Mercedes-Benz','E-Class','W211',2006,'M272',['Petrol','LPG'],'ME9.7')
    api = FakeBackend()
    store = EphemeralVehicles(vehicle)
    windows = []
    errors = []

    def button(parent, label):
        matches = [w for w in parent.findChildren(QPushButton) if w.text().strip() == label]
        assert matches, f'Button missing: {label}'
        return matches[0]

    def click(widget):
        assert widget.isVisible() and widget.isEnabled(), f'Button not interactive: {widget.text()}'
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
        app.processEvents()

    def nav(window, index):
        button = window.top_navigation_buttons[index]
        assert button.isVisible() and button.isEnabled(), f'Top navigation item unavailable: {index}'
        QTest.mouseClick(button, Qt.MouseButton.LeftButton)
        app.processEvents()
        assert window.page_index() == index, f'Navigation click failed: {index}'
        assert button.isChecked(), f'Inactive top navigation item: {index}'
        assert window.pages[index].isVisible(), f'Page {index} not visible'

    def save_settings(window, language, dark, shot_name):
        def apply_modal():
            dlg = app.activeModalWidget()
            if not isinstance(dlg, QDialog):
                errors.append(f'Settings modal did not appear for {language}')
                return
            try:
                combos = dlg.findChildren(QComboBox)
                assert len(combos) >= 2, 'Settings combos not found'
                for combo, data in ((combos[0], language),(combos[1], dark)):
                    index = combo.findData(data)
                    assert index >= 0, f'Cannot select settings {data}'
                    combo.setCurrentIndex(index)
                ev.shot(dlg, shot_name, app)
                controls = dlg.findChild(QDialogButtonBox)
                assert controls is not None
                click(controls.button(QDialogButtonBox.StandardButton.Save))
            except Exception as exc:
                errors.append(f'Settings modal error: {type(exc).__name__}: {exc}')
                dlg.reject()
        QTimer.singleShot(120, apply_modal)
        window._open_settings()  # actual modal/Save-button UI, not direct preferences mutation
        assert not errors, errors[-1] if errors else 'Settings dialog failure'
        assert window.language == language, f'Wrong language {window.language}'
        assert window.dark_theme is dark, f'Wrong theme {window.dark_theme}'
        assert EphemeralSettings.values['language'] == language
        assert EphemeralSettings.values['dark_theme'] is dark

    # API is seeded / no network, and user QSettings/profile data is never loaded.
    with ExitStack() as stack:
        stack.enter_context(patch.object(ui, 'QSettings', EphemeralSettings))
        stack.enter_context(patch.object(ui, 'VehicleStore', lambda: store))
        stack.enter_context(patch.object(ui, 'DiagnosticApiClient', lambda: api))
        stack.enter_context(patch.object(ui.MainWindow, 'refresh_all', lambda _self: None))
        # Synchronous in-memory worker runs still use the application callbacks.
        stack.enter_context(patch.object(ui.MainWindow, 'run_worker', lambda _self, work, done: done(work())))
        window = ui.MainWindow()
        windows.append(window)
        try:
            window._apply_language()
            window.show()
            window.raise_()
            window.activateWindow()
            app.processEvents()
            ev.record('Visible window opens with full-width top navigation', lambda: check_start(window, ev, app, platform))

            def navigation_test():
                assert len(window.top_navigation_buttons) == 13
                for n,label in enumerate(('dashboard','vehicles','devices','diagnostic','live-data','network',
                    'tests','dtc','ai-analysis','reports','teach-ai','symptoms','main-menu')):
                    nav(window,n)
                    ev.shot(window, f'01-navigation-{n+1:02d}-{label}.png', app)
                return '13/13 pages opened via real Qt mouse events; 13 screenshots'
            ev.record('All 13 top navigation pages: real mouse clicks and screenshots', navigation_test)

            def catalog_test():
                nav(window,1)
                dialog = ui.VehicleDialog(window)
                try:
                    dialog.show()
                    app.processEvents()
                    assert dialog.make.findText('Mercedes-Benz') >= 0
                    dialog.make.setCurrentText('Mercedes-Benz')
                    assert dialog.model.findText('E-Class') >= 0
                    dialog.model.setCurrentText('E-Class')
                    assert dialog.chassis.findText('W211') >= 0
                    dialog.chassis.setCurrentText('W211')
                    selection=dialog.vehicle()
                    assert selection.make=='Mercedes-Benz' and selection.chassis=='W211'
                    ev.shot(dialog, '02-vehicle-catalog-dialog.png', app)
                    dialog.reject() # no local profile mutation
                    return f'W211 catalog cascades work; selection {selection.model}, {selection.chassis}; cancelled without write'
                finally:
                    dialog.close()
                    dialog.deleteLater()
            ev.record('Vehicle dialog cascading selection and cancel', catalog_test)

            def theme_lang_test():
                save_settings(window, 'ru', False, '03-settings-russian-light.png')
                ev.shot(window,'04-russian-light-window.png',app)
                save_settings(window, 'hy', True, '05-settings-armenian-dark.png')
                ev.shot(window,'06-armenian-dark-window.png',app)
                save_settings(window, 'en', True, '07-settings-english-dark.png')
                ev.shot(window,'08-english-dark-window.png',app)
                return 'EN/RU/HY language selections and dark/light theme via real Save button, in-memory settings'
            ev.record('Settings dialog: language, theme, Save, visual snapshots', theme_lang_test)

            def workflow():
                window.online=True  # simulated backend; MUST NOT be reported as live backend
                window.active_vehicle=vehicle
                window.refresh_pages()
                nav(window,3)
                click(button(window.pages[3], 'New session'))
                assert window.session and window.session.session_id == 'local-visible-qa-001'
                diagnostic = window.pages[3]
                symptom = 'Mercedes W211 M272: shaking during acceleration on LPG below 2000 RPM; petrol normal.'
                diagnostic.symptom.setFocus()
                QTest.keyClicks(diagnostic.symptom, symptom)
                diagnostic.dtc.setFocus()
                QTest.keyClicks(diagnostic.dtc, 'P0302')
                click(button(diagnostic, 'Add evidence + Analyze'))
                assert api.dtcs == ['P0302']
                assert any('LPG below 2000 RPM' in e['fact'] for e in api.evidence)
                assert 'LPG injection' in diagnostic.hypotheses.toPlainText()
                assert 'not confirmed' in diagnostic.summary.toPlainText()
                assert window.decision['candidates'][0]['id']=='lpg-pressure'
                ev.shot(window, '09-diagnostic-golden-P0302.png',app)
                return 'Real Qt typing/buttons → simulated Create Session + evidence + P0302 + hypotheses + decision plan'
            ev.record('Golden scenario: symptom, P0302, hypothesis, recommendation', workflow)

            def tests_workflow():
                nav(window,6)
                page=window.pages[6]
                assert page.list.count() == 1
                QTest.mouseClick(page.list.viewport(), Qt.MouseButton.LeftButton,
                                 pos=page.list.visualItemRect(page.list.item(0)).center())
                app.processEvents()
                assert page.list.currentItem().data(Qt.ItemDataRole.UserRole)=='lpg-pressure'
                for code in ('PASS','FAIL','INCOMPLETE'):
                    nav(window,6)  # decision callback returns to Diagnostic after each submission
                    if page.list.currentItem() is None and page.list.count():
                        QTest.mouseClick(page.list.viewport(), Qt.MouseButton.LeftButton,
                             pos=page.list.visualItemRect(page.list.item(0)).center())
                    idx=page.result.findData(code)
                    assert idx>=0, f'Missing canonical result {code}'
                    page.result.setCurrentIndex(idx)
                    page.notes.clear()
                    QTest.keyClicks(page.notes, f'Visible QA simulated result {code}')
                    click(button(page,'Record selected result'))
                    assert api.results[-1]['result']==code
                    ev.shot(window, f'10-diagnostic-test-result-{code.lower()}.png',app)
                assert [x['result'] for x in api.results] == ['PASS','FAIL','INCOMPLETE']
                return '3 canonical statuses submitted through visible UI and verified in fake API record'
            ev.record('Recommended test result: PASS / FAIL / INCOMPLETE', tests_workflow)

            def telemetry_network():
                nav(window,4)
                window.telemetry=api.telemetry_summary(window.session.session_id)
                window.pages[4]._records_data=api.acquisition_records(window.session.session_id)['records']
                window.pages[4].refresh()
                app.processEvents()
                assert window.pages[4].table.rowCount()==1
                assert window.pages[4].table.item(0,0).text()=='RPM'
                ev.shot(window,'11-visible-live-data-rpm.png',app)
                window.network={'ecus':[{'ecu_id':'ME9.7','bus':'CAN','state':'INFERRED','confidence':0.65}]}
                nav(window,5)
                window.pages[5].refresh()
                assert 'ME9.7' in window.pages[5].tree.toPlainText()
                ev.shot(window,'12-visible-ecu-network.png',app)
                window.pages[4].timer.stop()
                return 'Simulated RPM telemetry visible; inferred ECU network rendered'
            ev.record('Live Data and ECU Network visual render', telemetry_network)

            def device_navigation():
                nav(window,2)
                window.devices=[{'device_id':'simulated-vci-1','manufacturer':'QA','model':'Mock Adapter',
                                 'connection_type':'USB','status':'disconnected','metadata':{}}]
                window.pages[2].refresh()
                assert window.pages[2].list.count()==1
                ev.shot(window,'13-visible-device-page-mock-vci.png',app)
                return 'Mock adapter displayed; no real OBD/USB/BLE access'
            ev.record('Device page mock data and visible layout', device_navigation)

            # Final visual inspection interval; no unattended background work.
            if hold_seconds>0:
                nav(window,0)
                print(f'[REAL-UI] Native Qt window remains visible for {hold_seconds:.1f}s to inspect.', flush=True)
                QTest.qWait(int(hold_seconds*1000))
        finally:
            try:
                window.pages[4].timer.stop()
                window.close()
                window.deleteLater()
                app.processEvents()
                QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
                app.processEvents()
            except Exception:
                traceback.print_exc()


def check_start(window, ev, app, platform):
    assert window.isVisible()
    assert len(window.top_navigation_buttons)==13 and len(window.pages)==13
    assert not hasattr(window, "nav")
    assert window.page_index()==12
    assert window.width()>=800 and window.height()>=500
    shot=ev.shot(window,'00-visible-main-menu-startup.png',app)
    return f'Qt platform={platform}, window={window.width()}x{window.height()}, screenshot={shot}'


def run_visible_exe(ev: Evidence, exe_arg: str, timeout: float) -> None:
    """Launch REAL Windows packaged EXE on screen and capture a new native window."""
    if sys.platform != 'win32':
        raise RuntimeError('Visible frozen EXE mode requires Windows.')
    exe = Path(exe_arg)
    if not exe.is_absolute():
        exe = ROOT / exe
    exe=exe.resolve()
    if not exe.is_file():
        raise FileNotFoundError(f'EXE not found: {exe}')
    with exe.open('rb') as stream:
        exe_hash=hashlib.file_digest(stream, 'sha256').hexdigest()
    (ev.path/'exe-sha256.txt').write_text(f'{exe_hash}  {exe}\n',encoding='utf-8')
    # Qt packaged window may use locale-specific title. Collect newly visible top-level
    # process windows and prefer recognizable workstation titles.
    import ctypes
    from ctypes import wintypes
    from PIL import ImageGrab
    user32=ctypes.windll.user32
    ENUM=ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes=(ENUM, wintypes.LPARAM)
    user32.IsWindowVisible.argtypes=(wintypes.HWND,)
    user32.GetWindowTextLengthW.argtypes=(wintypes.HWND,)
    user32.GetWindowTextW.argtypes=(wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetWindowRect.argtypes=(wintypes.HWND,ctypes.POINTER(wintypes.RECT))

    def windows():
        output={}
        @ENUM
        def callback(hwnd, _lp):
            if not user32.IsWindowVisible(hwnd): return True
            length=user32.GetWindowTextLengthW(hwnd)
            if not length: return True
            buf=ctypes.create_unicode_buffer(length+1)
            user32.GetWindowTextW(hwnd,buf,len(buf))
            r=wintypes.RECT()
            if user32.GetWindowRect(hwnd,ctypes.byref(r)):
                if r.right-r.left>=400 and r.bottom-r.top>=280:
                    output[int(hwnd)]=(buf.value,(r.left,r.top,r.right,r.bottom))
            return True
        user32.EnumWindows(callback,0)
        return output

    before=windows()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            endpoint=self.path.split('?',1)[0]
            payload={'/health':{'status':'ok'}, '/api/v1/devices':{'devices':[]},
                     '/api/v1/vehicle-catalog/entries':[]}.get(endpoint)
            if payload is None:
                self.send_error(404)
                return
            raw=json.dumps(payload).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        def log_message(self,*_args): pass

    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.daemon_threads=True
    server_thread=threading.Thread(target=server.serve_forever,daemon=True)
    server_thread.start()
    ev.exe_mode='actual frozen EXE, native Windows visible window + real screenshot, local fake HTTP backend'
    with tempfile.TemporaryDirectory(prefix='ai-car-visible-exe-') as td:
        env=os.environ.copy()
        env['APPDATA']=td
        env['AI_CAR_BACKEND_URL']=f'http://127.0.0.1:{server.server_port}'
        env['AI_CAR_DISABLE_LLM_AUTOSTART']='1'
        env['AI_CAR_TEST_AUTOCLOSE_MS']='18000'
        env['AI_CAR_SHUTDOWN_TRACE_PATH']=str(ev.path/'exe-shutdown.log')
        env['AI_CAR_DISABLE_NATIVE_TASKBAR_ICON']='1'
        env['NO_PROXY']='127.0.0.1,localhost'
        env['no_proxy']='127.0.0.1,localhost'
        env.pop('QT_QPA_PLATFORM',None)
        env.pop('PYTHONPATH',None)
        env.pop('PYTHONHOME',None)
        console=ev.path/'exe-console.log'
        start=time.monotonic()
        process=None
        new_window=None
        snap=None
        try:
            with console.open('wb') as output:
                process=subprocess.Popen([str(exe)],cwd=str(exe.parent),env=env,stdout=output,stderr=subprocess.STDOUT)
                while time.monotonic()-start<min(14,timeout-2):
                    candidates=[(hwnd,name,rect) for hwnd,(name,rect) in windows().items() if hwnd not in before]
                    preferred=[v for v in candidates if ('diagnostic' in v[1].lower() or 'workstation' in v[1].lower() or 'ախտորոշ' in v[1].lower() or 'диагност' in v[1].lower())]
                    if preferred:
                        new_window=preferred[0]
                        break
                    if process.poll() is not None: break
                    time.sleep(.3)
                if new_window:
                    hwnd,title,rect=new_window
                    # Show the app foreground before capturing a visible screen.
                    user32.SetForegroundWindow(wintypes.HWND(hwnd))
                    time.sleep(.8)
                    screenshot=ImageGrab.grab(bbox=rect,all_screens=True)
                    filename=ev.images/'20-frozen-exe-visible-window.png'
                    screenshot.save(str(filename))
                    snap=filename.relative_to(ev.path).as_posix()
                try:
                    exit_code=process.wait(timeout=max(1,timeout-(time.monotonic()-start)))
                except subprocess.TimeoutExpired:
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                                   check=False,timeout=15,capture_output=True)
                    process.wait(timeout=10)
                    raise AssertionError('Packaged EXE did not auto-close before timeout')
            trace=(ev.path/'exe-shutdown.log').read_text(encoding='utf-8',errors='replace') if (ev.path/'exe-shutdown.log').exists() else ''
            expected=['smoke: main_window_shown','ui: QApplication.exec returned rc=0',
                      'main: backend/LLM cleanup complete']
            missing=[m for m in expected if m not in trace]
            assert exit_code==0, f'EXE exit={exit_code}; log={console}'
            assert new_window is not None, f'No new packaged EXE workstation top-level window detected; log={console}'
            assert snap, 'Could not capture a real EXE window screenshot'
            assert not missing, f'Missing shutdown trace checkpoints: {missing}'
            return f'EXE exit=0, visible hwnd={new_window[0]}, screenshot={snap}, sha256={exe_hash}, clean shutdown verified'
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=3)
            if process and process.poll() is None:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                               check=False,capture_output=True,timeout=15)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('source','exe','all'),default='all')
    p.add_argument('--exe',default='dist-release/icon-preview/AICarScanner.exe')
    p.add_argument('--hold-seconds',type=float,default=4)
    p.add_argument('--exe-timeout',type=float,default=50)
    p.add_argument('--out',default='desktop-test-reports/real-ui-acceptance')
    args=p.parse_args()
    if not 0<=args.hold_seconds<=60 or args.exe_timeout<22:
        p.error('hold-seconds must be 0..60 and exe-timeout >=22')
    report=Path(args.out)
    if not report.is_absolute(): report=ROOT/report
    report=report.resolve()
    report.mkdir(parents=True,exist_ok=True)
    ev=Evidence(report)
    print(f'[REAL-UI] ROOT: {ROOT}\n[REAL-UI] REPORT: {report}',flush=True)
    print('[REAL-UI] Running visible GUI; do not lock the Windows session or run via SSH/headless.',flush=True)
    if args.mode in ('source','all'):
        def source_suite():
            starting = len(ev.cases)
            run_visible_source(ev, args.hold_seconds)
            failures = [item['case'] for item in ev.cases[starting:] if item['status'] == 'FAIL']
            if failures:
                raise AssertionError('Source UI subcases failed: ' + ', '.join(failures))
            return 'All visible source UI subcases passed'
        ev.record('Visible source test harness completed without crash', source_suite)
    if args.mode in ('exe','all'):
        ev.record('Packaged EXE visible startup, screenshot and shutdown',
                  lambda:run_visible_exe(ev,args.exe,args.exe_timeout),mode='frozen-exe')
    return 0 if ev.finish() else 1


if __name__=='__main__':
    raise SystemExit(main())
