# PyInstaller spec for ixargs
# Build: pyinstaller ixargs.spec

block_cipher = None

import os
spec_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(spec_dir, "ixargs", "__main__.py")],
    pathex=[spec_dir],
    binaries=[],
    datas=[(os.path.join(spec_dir, "ixargs", "app.css"), "ixargs")],
    hiddenimports=[
        "textual",
        "textual.app",
        "textual.widgets",
        "textual.containers",
        "textual.screen",
        "textual.worker",
        "textual.binding",
        "textual.css",
        "rich",
        "rich.text",
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

# onedir: exe + COLLECT for faster launch (no unpack-to-temp)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ixargs",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ixargs",
)
