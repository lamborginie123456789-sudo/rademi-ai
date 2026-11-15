# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['rademi.py'],
    pathex=[],
    binaries=[('C:/Users/maart/AppData/Local/Programs/Python/Python313/Lib/site-packages/llama_cpp/lib/*', 'llama_cpp/lib')],
    datas=[('index.html', '.'), ('style.css', '.'), ('charts.js', '.'), ('cards.js', '.'), ('app.js', '.')],
    hiddenimports=['pycaw', 'comtypes', 'PIL', 'qrcode', 'mss'],
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
    [],
    exclude_binaries=True,
    name='RADEMI_AI',
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
    uac_admin=True,
    icon=['rademi.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RADEMI_AI',
)
