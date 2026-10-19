# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild/apps/desktop/main.py'],
    pathex=['C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild'],
    binaries=[],
    datas=[('C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild/shared/vehicle_catalog.json', 'shared'), ('C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild/assets/AI-Car-Scanner.ico', 'assets'), ('C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild/assets/AI-Car-Scanner.webp', 'assets'), ('C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild/assets/AI-Car-Scanner-mobile.png', 'assets')],
    hiddenimports=['apps.desktop.ui', 'apps.desktop.api_client'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild/apps/desktop/debug_runtime_hook.py', 'C:/Users/grigorg/Desktop/AI-CAR-SCANER/git/finalbuild/apps/desktop/qt_early_runtime_hook.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AICarScannerDebug',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AICarScannerDebug',
)
