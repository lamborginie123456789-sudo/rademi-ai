# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['rademi.py'],
    pathex=[],
    binaries=[('C:/Users/maart/AppData/Local/Programs/Python/Python313/Lib/site-packages/llama_cpp/lib/*', 'llama_cpp/lib')],
    datas=[('index.html', '.'), ('style.css', '.'), ('charts.js', '.'), ('cards.js', '.'), ('app.js', '.')],
    hiddenimports=['pycaw', 'comtypes', 'PIL', 'clr'],
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
    name='RADEMI_AI_v2',
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
    uac_admin=True,
)
