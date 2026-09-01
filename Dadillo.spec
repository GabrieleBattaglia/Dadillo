# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Dadillo.py'],
    pathex=[],
    binaries=[],
    datas=[],
    # Servono al controllo aggiornamenti di GBUtils: senza, l'eseguibile parte
    # ma non riesce a contattare GitHub. Non toglierli.
    hiddenimports=[
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'chardet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'numpy', 'pytest', 'pygame', 'sounddevice', 'pygments', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Dadillo',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Dadillo',
)
