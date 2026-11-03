"""Adım 3 testi: Yeni PDF diyaloğu form + stil -> proje kaydı.

Çalıştırma:
    python -m unittest tests.test_new_pdf -v
Diyalog modal olarak açılmaz; alanlar doldurulup olustur() çağrılır.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

import app.core.paths as paths  # noqa: E402
from app.db import database as dbmod  # noqa: E402


class NewPdfTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        dbmod._db = None
        self._eski_db = paths.DB_PATH
        paths.DB_PATH = Path(self.tmp.name) / "t.sqlite3"
        self.db = dbmod.get_db()

    def tearDown(self):
        self.db.close()
        dbmod._db = None
        paths.DB_PATH = self._eski_db
        self.tmp.cleanup()

    def _make_dialog(self):
        from app.ui.new_pdf_dialog import NewPdfDialog
        return NewPdfDialog()

    def test_stil_topla_varsayilan(self):
        d = self._make_dialog()
        stil = d.stil_topla()
        self.assertEqual(stil["sayfa_tarzi"], "tek")
        self.assertEqual(stil["ayrac"], "cizgi")
        self.assertEqual(stil["soru_boslugu"], 24)
        self.assertEqual(stil["font"], "Helvetica")
        self.assertTrue(stil["renk"].startswith("#"))

    def test_form_doldur_ve_kaydet(self):
        d = self._make_dialog()
        d.ed_isim.setText("Fen Testi")
        # klasör: listede birini seç
        d.cb_klasor.setCurrentIndex(min(1, d.cb_klasor.count() - 1))
        d.cb_sik.setCurrentIndex(1)          # 5 şık
        d.cb_tur.setCurrentIndex(1)          # Word
        d.cb_sayfa.setCurrentIndex(1)        # iki sütun
        d.cb_ayrac.setCurrentIndex(1)        # yok
        d.sl_bosluk.setValue(40)
        d.cb_font.setCurrentText("Times (Klasik)")
        d.olustur()

        self.assertIsNotNone(d.proje_id)
        p = self.db.proje_getir(d.proje_id)
        self.assertEqual(p["ad"], "Fen Testi")
        self.assertEqual(p["sik_sayisi"], 5)
        self.assertEqual(p["tur"], "word")
        stil = self.db.proje_stil_getir(d.proje_id)
        self.assertEqual(stil["sayfa_tarzi"], "iki")
        self.assertEqual(stil["ayrac"], "yok")
        self.assertEqual(stil["soru_boslugu"], 40)
        self.assertEqual(stil["font"], "Times-Roman")

    def test_bos_isim_varsayilana_duser(self):
        d = self._make_dialog()
        d.ed_isim.setText("   ")
        d.olustur()
        p = self.db.proje_getir(d.proje_id)
        self.assertEqual(p["ad"], "Adsız Proje")


if __name__ == "__main__":
    unittest.main(verbosity=2)
