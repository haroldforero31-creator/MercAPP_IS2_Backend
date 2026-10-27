# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

BASE_DIR = os.path.abspath(os.getcwd())
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'MercAPP_IS2_Frontend'))

templates_src = os.path.join(FRONTEND_DIR, 'templates')
static_src = os.path.join(FRONTEND_DIR, 'static')

datas = [
    (templates_src, 'templates'),
    (static_src, 'static'),
    (templates_src, 'MercAPP_IS2_Frontend/templates'),
    (static_src, 'MercAPP_IS2_Frontend/static'),
]

if os.path.exists(os.path.join(BASE_DIR, '.env')):
    datas.append(('.env', '.'))

if os.path.exists(os.path.join(BASE_DIR, 'mercapp.ico')):
    datas.append(('mercapp.ico', '.'))

a = Analysis(
    ['launcher.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'app',
        'models',
        'models.database',
        'models.user',
        'models.product',
        'models.sale',
        'controllers',
        'dtos',
        'repositories',
        'services',
        'utilities',
        'utilities.helpers',
        'utilities.response_helper',
        'utilities.security',
        'email_validator',
        'flask_sqlalchemy',
        'flask_login',
        'flask_wtf',
        'flask_mail',
        'serial',
        'win32print',
        'unidecode',
        'waitress',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MercAPP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='mercapp.ico' if os.path.exists('mercapp.ico') else None
)
