"""Adım 5 testleri: şık menüsü + soru kaydetme + son soruyu silme.

Çalıştırma:
    python -m unittest tests.test_capture_mode -v
Gerçek kısayol/tepsi olmadan, koordinatörün kayıt/silme mantığı doğrulanır.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402

import app.core.paths as paths  # noqa: E402
from app.db import database as dbmod  # noqa: E402


class _OrnekImage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        t = Path(self.tmp.name)
        dbmod._db = None
        self._eski = (paths.DB_PATH, paths.IMAGES_DIR, paths.EXPORT_DIR,
                      paths.ensure_dirs)
        paths.DB_PATH = t / "t.sqlite3"
        paths.IMAGES_DIR = t / "gorseller"
        paths.EXPORT_DIR = t / "ciktilar"
        paths.ensure_dirs = lambda: paths.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        self.db = dbmod.get_db()

    def tearDown(self):
        self.db.close()
        dbmod._db = None
        (paths.DB_PATH, paths.IMAGES_DIR, paths.EXPORT_DIR,
         paths.ensure_dirs) = self._eski
        self.tmp.cleanup()

    def _controller(self, proje_id, sik_sayisi=4):
        from app.core.capture_controller import CaptureController

        ctl = CaptureController()
        ctl.db = self.db
        ctl.proje_id = proje_id
        ctl.sik_sayisi = sik_sayisi
        return ctl


class OptionMenuTest(_OrnekImage):
    def test_sik_buton_sayisi(self):
        from PySide6.QtWidgets import QApplication, QPushButton
        from app.ui.option_menu import OptionMenu

        QApplication.instance() or QApplication([])
        m4 = OptionMenu(sik_sayisi=4)
        m5 = OptionMenu(sik_sayisi=5)
        n4 = len([b for b in m4.findChildren(QPushButton) if b.objectName() == "SikBtn"])
        n5 = len([b for b in m5.findChildren(QPushButton) if b.objectName() == "SikBtn"])
        self.assertEqual(n4, 4)
        self.assertEqual(n5, 5)

    def test_secim_ve_kaydet_sinyali(self):
        from PySide6.QtWidgets import QApplication, QPushButton
        from app.ui.option_menu import OptionMenu

        QApplication.instance() or QApplication([])
        m = OptionMenu(sik_sayisi=4, soru_no=3)
        alinan = {}
        m.kaydet.connect(lambda sik: alinan.setdefault("sik", sik))
        b = [x for x in m.findChildren(QPushButton) if x.objectName() == "SikBtn"][1]
        b.setChecked(True)   # B
        m._kaydet()
        self.assertEqual(alinan.get("sik"), "B")

    def test_secimsiz_kaydet_yayinlamaz(self):
        from PySide6.QtWidgets import QApplication
        from app.ui.option_menu import OptionMenu

        QApplication.instance() or QApplication([])
        m = OptionMenu(sik_sayisi=4)
        salindi = []
        m.kaydet.connect(lambda *_: salindi.append(1))
        m._kaydet()
        self.assertEqual(salindi, [])


class SaveFlowTest(_OrnekImage):
    def test_kaydet_db_ve_dosya(self):
        pid = self.db.proje_olustur("T", sik_sayisi=4)
        ctl = self._controller(pid)
        emit = []
        ctl.soru_kaydedildi.connect(lambda n: emit.append(n))
        ctl.sayi_degisti.connect(lambda n: emit.append(("n", n)))

        crop = Image.new("RGB", (50, 30), (0, 0, 255))
        ctl._kaydet(crop, "C", 1)

        self.assertEqual(self.db.soru_adet(pid), 1)
        rows = self.db.soru_liste(pid)
        self.assertEqual(rows[0]["dogru_sik"], "C")
        self.assertTrue(paths.abs_from_base(rows[0]["gorsel_yolu"]).exists())
        self.assertIn(1, emit)

    def test_otomatik_sira_no(self):
        pid = self.db.proje_olustur("T")
        ctl = self._controller(pid)
        crop = Image.new("RGB", (20, 20))
        ctl._kaydet(crop, "A", self.db.soru_siradaki_no(pid))  # 1
        ctl._kaydet(crop, "B", self.db.soru_siradaki_no(pid))  # 2
        self.assertEqual(self.db.cevap_anahtari(pid), [(1, "A"), (2, "B")])

    def test_tray_son_sil_dosyayi_kaldirir(self):
        pid = self.db.proje_olustur("T")
        ctl = self._controller(pid)
        crop = Image.new("RGB", (20, 20))
        ctl._kaydet(crop, "A", 1)
        yol = paths.abs_from_base(self.db.soru_liste(pid)[0]["gorsel_yolu"])
        self.assertTrue(yol.exists())
        ctl._tray_son_sil()
        self.assertEqual(self.db.soru_adet(pid), 0)
        self.assertFalse(yol.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
