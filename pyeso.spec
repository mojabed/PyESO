# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["pyeso/cli.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "luaparser",
        "luaparser.astnodes",
        "luaparser.ast",
        "antlr4",
        "antlr4.atn",
        "antlr4.dfa",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "unittest", "email",
        "sqlite3", "multiprocessing",
        "concurrent", "asyncio", "distutils", "pydoc",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pyeso",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
