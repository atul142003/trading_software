# -*- mode: python ; coding: utf-8 -*-

import os

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.png', '.'),
        ('indicators', 'indicators'),
        ('market_data', 'market_data'),
        ('ai', 'ai'),
        ('patterns', 'patterns'),
    ],
    hiddenimports=[
        'pandas',
        'numpy',
        'yfinance',
        'plotly',
        'streamlit',
        'scikit-learn',
        'xgboost',
        'joblib',
        'matplotlib',
        'openpyxl',
        'reportlab',
    ],
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
    name='ASA_Trading',
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
    icon='icon.png',
)
