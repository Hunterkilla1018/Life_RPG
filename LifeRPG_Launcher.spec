# LifeRPG_Launcher.spec
block_cipher = None

a = Analysis(
    ['bootstrap.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'game_logic',
        'app_gui',
        'main',
    ],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LifeRPG_Launcher',
    console=True,   # keep console for diagnostics
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='LifeRPG_Launcher'
)
