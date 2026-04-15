# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import tkinterdnd2

tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), 'tkdnd')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(tkdnd_path, 'tkinterdnd2/tkdnd')],
    hiddenimports=['tkinterdnd2', 'keyring.backends.Windows', 'keyring.backends.macOS', 'keyring.backends.macOS.api'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Payro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='universal2' if sys.platform == 'darwin' else None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Payro.app',
        icon=None,
        bundle_identifier='com.payro.app',
    )
