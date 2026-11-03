# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec (Adım 8) - Windows .exe
#
# Build:  pyinstaller build.spec
# Çıktı:  dist/TestPDFUretici/TestPDFUretici.exe  (onedin klasörü)
#
# Not: data/ (veritabanı, görseller, çıktılar) exe'in yanına yazılır;
# app/core/paths.py donmuş çalıştırmada BASE_DIR'i exe klasörü yapar.

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules("reportlab")
hiddenimports += collect_submodules("pynput")
hiddenimports += collect_submodules("mss")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("app/db/schema.sql", "app/db")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TestPDFUretici",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # GUI/tepsi uygulaması: konsol penceresi yok
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # istersen assets/ikon.ico göster
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TestPDFUretici",
)
