"""Yüzen panel + kart dosya açma davranışı testleri.

Çalıştırma:
    python -m unittest tests.test_floating_panel -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import app.core.paths as paths  # noqa: E402
from app.db import database as dbmod  # noqa: E402


class _TempDB(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        t = Path(self.tmp.name)
        dbmod._db = None
        self._eski_db = paths.DB_PATH
        paths.DB_PATH = t / "t.sqlite3"
        self.db = dbmod.get_db()

    def tearDown(self):
        self.db.close()
        dbmod._db = None
        paths.DB_PATH = self._eski_db
        self.tmp.cleanup()


class FloatingPanelTest(_TempDB):
    def test_yapilar_ve_bilgi(self):
        from PySide6.QtWidgets import QApplication
        from app.ui.floating_panel import FloatingPanel

        QApplication.instance() or QApplication([])
        p = FloatingPanel()
        p.set_bilgi("TYT Deneme", 7)
        self.assertIn("TYT Deneme", p.lbl_baslik.text())
        self.assertIn("7", p.lbl_sayi.text())
        # dört sinyal tanımlı
        for ad in ("yakala_istegi", "ayarlar_istegi", "ana_menu_istegi", "bitir_istegi"):
            self.assertTrue(hasattr(p, ad))

    def test_controller_panel_goster_gizle(self):
        from PySide6.QtWidgets import QApplication
        from app.core.capture_controller import CaptureController

        QApplication.instance() or QApplication([])
        ctl = CaptureController()
        ctl.db = self.db
        ctl.proje_id = None
        ctl.proje_adi = "Panel Testi"
        ctl._panel_goster()
        self.assertIsNotNone(ctl.panel)
        ctl._panel_gizle()
        self.assertIsNone(ctl.panel)


class CardOpenFileTest(_TempDB):
    def test_uretilen_dosya_var_yok(self):
        from PySide6.QtWidgets import QApplication
        from app.ui.main_window import MainWindow

        QApplication.instance() or QApplication([])
        w = MainWindow()
        pid = self.db.proje_olustur("T", tur="pdf")

        # dosya yok -> None
        self.assertIsNone(w._uretilen_dosya(pid))

        # gerçek dosya oluştur ve yolu kaydet
        dosya = Path(self.tmp.name) / "T.pdf"
        dosya.write_bytes(b"%PDF-1.4 test")
        self.db.proje_dosya_yolu_set(pid, str(dosya))
        bulunan = w._uretilen_dosya(pid)
        self.assertIsNotNone(bulunan)
        self.assertTrue(Path(bulunan).exists())
