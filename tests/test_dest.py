"""Çıktı kayıt yeri + klasör alt dizinleri testleri (dest modülü).

Çalıştırma:
    python -m unittest tests.test_dest -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402

import app.core.paths as paths  # noqa: E402
import app.core.settings as s  # noqa: E402
from app.db import database as dbmod  # noqa: E402


class DestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        t = Path(self.tmp.name)
        self.base = t / "cikti"
        dbmod._db = None
        self._eski_db = paths.DB_PATH
        self._eski_settings = s.SETTINGS_PATH
        paths.DB_PATH = t / "t.sqlite3"
        s.SETTINGS_PATH = t / "ayarlar.json"
        s.kaydet({"cikti_klasoru": str(self.base)})
        self.db = dbmod.get_db()

    def tearDown(self):
        self.db.close()
        dbmod._db = None
        paths.DB_PATH = self._eski_db
        s.SETTINGS_PATH = self._eski_settings
        self.tmp.cleanup()

    def test_klasor_alt_dizin(self):
        from app.export import dest

        kid = self.db.klasor_ekle("Geometri")
        pid = self.db.proje_olustur("Deneme 1", klasor_id=kid)
        proje = self.db.proje_getir(pid)
        yol = dest.dosya_yolu(proje, self.db, ".pdf")
        self.assertEqual(Path(yol).parent, self.base / "Geometri")
        self.assertTrue((self.base / "Geometri").is_dir())  # hedef_klasor mkdir eder

    def test_klasorsuz_kok(self):
        from app.export import dest

        pid = self.db.proje_olustur("Klasörsüz İş")
        proje = self.db.proje_getir(pid)
        yol = dest.dosya_yolu(proje, self.db, ".pdf")
        self.assertEqual(Path(yol).parent, self.base)

    def test_klasor_dizini_olustur(self):
        from app.export import dest

        d = dest.klasor_dizini_olustur("Fizik")
        self.assertTrue(d.is_dir())
        self.assertEqual(d.name, "Fizik")

    def test_tum_klasorler(self):
        from app.export import dest

        self.db.klasor_ekle("Biyoloji")
        self.db.klasor_ekle("Kimya")
        dest.tum_klasorleri_olustur(self.db)
        self.assertTrue((self.base / "Biyoloji").is_dir())
        self.assertTrue((self.base / "Kimya").is_dir())

    def test_adi_guvenli(self):
        from app.export import dest

        self.assertEqual(dest._guvenli('a/b:c*d'), "a_b_c_d")

    def test_pdf_klasor_altina_yazilir(self):
        from app.export import dest
        from app.export.pdf_exporter import export_project_pdf

        kid = self.db.klasor_ekle("Analiz")
        pid = self.db.proje_olustur("Cebir", klasor_id=kid, tur="pdf")
        img = self.tmp.name + "/q.png"
        Image.new("RGB", (300, 120), (0, 0, 120)).save(img)
        self.db.soru_ekle(pid, img, "A")

        yol = export_project_pdf(pid, self.db)
        self.assertEqual(Path(yol).parent, self.base / "Analiz")
        self.assertTrue(Path(yol).exists())
        # dosya yolu DB'ye de işlendi
        self.assertEqual(self.db.proje_getir(pid)["dosya_yolu"], yol)


if __name__ == "__main__":
    unittest.main(verbosity=2)
