# -*- mode: python ; coding: utf-8 -*-
# PyInstaller TEK DOSYA (.exe) spec - dağıtım için
#
# Build:  pyinstaller --noconfirm --clean build_onefile.spec
# Çıktı:  dist/TestPDFUretici.exe  (tek dosya; indir-çalıştır)
#
# data/ (veritabanı, görseller, çıktılar, ayarlar) exe'in yanına oluşur.

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
    a.binaries,
    a.datas,
    [],
    name="TestPDFUretici",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # pencere/tepsi uygulaması: konsol yok
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # istersen assets/ikon.ico
)
