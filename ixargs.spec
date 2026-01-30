# PyInstaller spec for ixargs
# Build: pyinstaller ixargs.spec

block_cipher = None

import os
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# rich loads unicode data modules by name (e.g. unicode17-0-0); include them
# so the built binary works when run from any directory
_rich_unicode = [
    "rich._unicode_data",
    "rich._unicode_data.unicode4-1-0",
    "rich._unicode_data.unicode5-0-0",
    "rich._unicode_data.unicode5-1-0",
    "rich._unicode_data.unicode5-2-0",
    "rich._unicode_data.unicode6-0-0",
    "rich._unicode_data.unicode6-1-0",
    "rich._unicode_data.unicode6-2-0",
    "rich._unicode_data.unicode6-3-0",
    "rich._unicode_data.unicode7-0-0",
    "rich._unicode_data.unicode8-0-0",
    "rich._unicode_data.unicode9-0-0",
    "rich._unicode_data.unicode10-0-0",
    "rich._unicode_data.unicode11-0-0",
    "rich._unicode_data.unicode12-0-0",
    "rich._unicode_data.unicode12-1-0",
    "rich._unicode_data.unicode13-0-0",
    "rich._unicode_data.unicode14-0-0",
    "rich._unicode_data.unicode15-0-0",
    "rich._unicode_data.unicode15-1-0",
    "rich._unicode_data.unicode16-0-0",
    "rich._unicode_data.unicode17-0-0",
]

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
    ]
    + _rich_unicode,
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
