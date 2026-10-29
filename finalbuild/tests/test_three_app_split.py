"""Deployment identities, thin clients, and centralized source contracts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import pytest
import yaml

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('role',['user','customer','market'])
def test_three_fixed_desktop_entrypoints_without_backend_import(role):
    code=f'''import runpy,sys
sys.argv=['client','--check']
try:runpy.run_module('apps.{role}.main',run_name='__main__')
except SystemExit as e:assert e.code==0
assert not any(k=='fastapi' or k.startswith('sqlalchemy') or k.startswith('backend.') for k in sys.modules)
'''
    response=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True,timeout=15)
    assert response.returncode==0,response.stderr
    assert json.loads(response.stdout)['application']==role.upper()


@pytest.mark.parametrize('role',['user','customer','market'])
def test_three_real_qt_windows_open_and_close_without_backend(role,tmp_path):
    pytest.importorskip('PySide6')
    env={**os.environ,'QT_QPA_PLATFORM':'offscreen','XDG_CONFIG_HOME':str(tmp_path),'AI_CAR_BACKEND_URL':'http://127.0.0.1:9'}
    code=f"""import runpy,sys
sys.argv=['client','--smoke']
try:runpy.run_module('apps.{role}.main',run_name='__main__')
except SystemExit as error:assert error.code==0
assert not any(k=='fastapi' or k.startswith('sqlalchemy') or k.startswith('backend.') for k in sys.modules)
"""
    result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert 'backend] Importing' not in result.stdout


def test_backend_import_check_is_independent_and_does_not_create_database(tmp_path):
    file=tmp_path/'not-created.sqlite'
    result=subprocess.run([sys.executable,'-m','backend.main','--check','--database',str(file)],cwd=ROOT,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert str(ROOT/'backend/vehicle/obd/client.py') in result.stdout
    assert not file.exists()
    assert sorted(p.name for p in (ROOT/'vehicle').glob('*.py'))==['__init__.py']


def test_ios_has_exactly_three_coinstallable_application_targets():
    data=yaml.safe_load((ROOT/'apps/mobile-ios/project.yml').read_text())
    apps={k:v for k,v in data['targets'].items() if v['type']=='application'}
    assert set(apps)=={'AICarScannerUser','AICarScannerCustomer','AICarScannerMarket'}
    ids={v['settings']['base']['PRODUCT_BUNDLE_IDENTIFIER'] for v in apps.values()}
    assert ids=={'com.aicarscaner.user','com.aicarscaner.customer','com.aicarscaner.market'}
    for name,app in apps.items():assert app['settings']['base']['AI_CAR_WORKSPACE']==name.removeprefix('AICarScanner').upper()
    import plistlib
    plist=plistlib.loads((ROOT/'apps/mobile-ios/AICarScanner/Info.plist').read_bytes())
    assert plist['CFBundleIdentifier']=='$(PRODUCT_BUNDLE_IDENTIFIER)'
    assert plist['CFBundleExecutable']=='$(EXECUTABLE_NAME)'


def test_android_three_application_ids_and_variant_workspace_values():
    source=(ROOT/'apps/mobile-android/app/build.gradle.kts').read_text()
    for role in ('user','customer','market'):
        assert f'create("{role}")' in source and f'applicationId = "com.aicarscaner.{role}"' in source
        assert f'\\"{role.upper()}\\"' in source
    manifest=ET.parse(ROOT/'apps/mobile-android/app/src/main/AndroidManifest.xml')
    application=manifest.getroot().find('application')
    assert application.attrib['{http://schemas.android.com/apk/res/android}label']=='${appLabel}'


def test_backend_docker_does_not_copy_a_second_vehicle_stack_or_desktop_code():
    docker=(ROOT/'infrastructure/docker/backend.Dockerfile').read_text()
    assert 'COPY backend backend' in docker and '"backend.main"' in docker
    assert 'COPY vehicle vehicle' not in docker and 'COPY apps' not in docker


def test_independent_backend_bootstrap_migrates_explicit_database_without_gui(monkeypatch,tmp_path):
    from backend import main,server
    from sqlalchemy import create_engine,inspect
    db=tmp_path/'private-backend'/'business.sqlite';started=[]
    monkeypatch.delenv('DATABASE_URL',raising=False)
    monkeypatch.setenv('AI_CAR_ECOSYSTEM_ENABLED','0')
    monkeypatch.setenv('AI_CAR_BACKEND_HOST','127.0.0.1')
    monkeypatch.setenv('AI_CAR_BACKEND_PORT','8001')
    monkeypatch.setattr(server,'main',lambda:started.append('server'))
    assert main.main(['--database',str(db),'--migrate','--port','8123'])==0
    assert started==['server'] and os.environ['AI_CAR_ECOSYSTEM_ENABLED']=='1'
    assert os.environ['AI_CAR_BACKEND_PORT']=='8123'
    engine=create_engine('sqlite:///'+str(db))
    try:assert {'ecosystem_accounts','ecosystem_diagnostics'}.issubset(inspect(engine).get_table_names())
    finally:engine.dispose()
    if os.name!='nt':assert db.stat().st_mode & 0o777==0o600
