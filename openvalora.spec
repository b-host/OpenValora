# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build specification for OpenValora.
Compatível com Linux (AppImage) e Windows (Portable / Zip).
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('app/templates', 'app/templates'),
    ('app/static', 'app/static'),
    ('sample_data', 'sample_data'),
    ('app/core/var_catalog.json', 'app/core'),
    ('var_catalog.json', '.'),
    ('OpenValora.png', '.'),
    ('ValoraOpen.png', '.'),
    ('packaging', 'packaging'),
]

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'pydantic',
    'numpy',
    'scipy',
    'scipy.special',
    'scipy.stats',
    'scipy.spatial.transform._rotation_groups',
    'sklearn',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._typedefs',
    'sklearn.tree._utils',
    'openpyxl',
    'xlrd',
    'xlwt',
    'multipart',
    'python_multipart',
    'webview',
    'webview.platforms',
]

if sys.platform.startswith('linux'):
    hiddenimports += [
        'webview.platforms.gtk',
        'gi',
        'gi.repository.Gtk',
        'gi.repository.WebKit2',
        'gi.repository.GLib',
        'gi.repository.GObject',
        'gi.repository.Gio',
        'gi.repository.Gdk',
    ]
elif sys.platform.startswith('win'):
    hiddenimports += [
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
    ]
elif sys.platform == 'darwin':
    hiddenimports += [
        'webview.platforms.cocoa',
    ]

hiddenimports += collect_submodules('app')

if sys.platform.startswith('win'):
    icon_file = 'packaging/openvalora.ico' if os.path.exists('packaging/openvalora.ico') else 'packaging/valoraopen.ico'
elif sys.platform == 'darwin':
    icon_file = 'packaging/openvalora.icns' if os.path.exists('packaging/openvalora.icns') else 'packaging/openvalora.png'
else:
    icon_file = 'packaging/openvalora.png' if os.path.exists('packaging/openvalora.png') else 'packaging/valoraopen.png'

if not os.path.exists(icon_file):
    icon_file = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'notebook'],
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
    name='openvalora',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='OpenValora.app',
        icon=icon_file,
        bundle_identifier='org.openvalora.app',
        info_plist={
            'CFBundleName': 'OpenValora',
            'CFBundleDisplayName': 'OpenValora',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': 'True',
        }
    )
