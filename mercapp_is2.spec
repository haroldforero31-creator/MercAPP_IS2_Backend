# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

backend_dir = os.path.abspath('.')
frontend_dir = os.path.abspath(os.path.join(backend_dir, '..', 'MercAPP_IS2_Frontend'))

datas = [
    (os.path.join(frontend_dir, 'templates'), 'MercAPP_IS2_Frontend/templates'),
    (os.path.join(frontend_dir, 'static'), 'MercAPP_IS2_Frontend/static'),
    ('.env', '.'),
    ('mercapp.ico', '.')
]

hidden_imports = [
    'app',
    'controllers',
    'controllers.user_controller',
    'controllers.product_controller',
    'controllers.sale_controller',
    'controllers.merki_controller',
    'services',
    'services.merki_service',
    'services.merki_queries',
    'repositories',
    'models',
    'dtos',
    'utilities',
    'utilities.helpers',
    'flask_sqlalchemy',
    'flask_login',
    'flask_mail',
    'waitress',
    'unidecode',
    'PIL',
    'serial',
    'serial.tools.list_ports',
    'win32print'
]

a = Analysis(
    ['launcher.py'],
    pathex=[backend_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MercAPP_IS2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='mercapp.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MercAPP_IS2'
)
