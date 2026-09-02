# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Dadillo.py'],
    # GBUtils, che fornisce il controllo aggiornamenti, non e' installato fra i
    # pacchetti: sta accanto al progetto e di solito si trova per PYTHONPATH.
    # Dichiararlo qui rende la compilazione ripetibile su qualsiasi macchina che
    # rispetti la struttura di E:\git\mine.
    pathex=['../GBUtils'],
    binaries=[],
    # Dadillo non carica nessuna risorsa esterna, ne' immagini ne' suoni:
    # tutto quello che gli serve sono i suoi file di dati, che nascono accanto
    # all'eseguibile e non vanno impacchettati.
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
    # Dadillo usa solo wxPython e la libreria standard. Queste sono installate
    # sulla macchina di sviluppo e arriverebbero nel pacchetto seguendo le
    # catene di import, prime fra tutte le funzioni audio di GBUtils, che
    # Dadillo non chiama mai: escluderle tiene il pacchetto alla sua misura.
    excludes=[
        'matplotlib',
        'scipy',
        'numpy',
        'pytest',
        'pygame',
        'sounddevice',
        'pygments',
        'tkinter',
        'PIL',
        'IPython',
    ],
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
