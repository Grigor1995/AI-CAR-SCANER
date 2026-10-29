from pathlib import Path
import os
role=os.environ.get('AI_CAR_PRODUCT','USER').upper()
if role not in ('USER','CUSTOMER','MARKET'):raise ValueError('Unknown product')
root=Path(SPEC).resolve().parents[3]
name='AI-Car-'+role.title()
assets=Path(os.environ.get('AI_CAR_ICON_STAGE_DIR',str(root/'assets')))
a=Analysis([str(root/'apps'/role.lower()/'main.py')],pathex=[str(root)],binaries=[],
    datas=[(str(root/'assets/app_icons'/role.lower()/'icon.png'),'assets/app_icons/'+role.lower())],
    hiddenimports=['PySide6.QtCore','PySide6.QtGui','PySide6.QtWidgets','requests','apps.desktop.product_app','apps.desktop.business_workspace','apps.desktop.theme'],
    hookspath=[],hooksconfig={},runtime_hooks=[str(root/'apps/desktop/qt_early_runtime_hook.py')],excludes=['tkinter'],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name=name,console=False,icon=str(root/'assets/app_icons'/role.lower()/'icon.ico'))
