# LifeRPG_Game.spec

block_cipher = None

a = Analysis(
    ['main.py'],      # 🔥 THIS MUST BE main.py
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=['bootstrap'],  # 🔒 Ensure launcher not bundled
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LifeRPG',
    console=True,   # keep True during debugging
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='LifeRPG'
)
