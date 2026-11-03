"""Adım 4 testleri: kısayol normalize, ekran yakalama, seçim kırpma.

Çalıştırma:
    python -m unittest tests.test_capture -v
"""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402

from app.core.capture import EkranGoruntusu  # noqa: E402
from app.core.hotkey import DEFAULT_HOTKEY, normalize  # noqa: E402


class HotkeyTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("Ctrl+Shift+S"), "<ctrl>+<shift>+s")
        self.assertEqual(normalize("ctrl+alt+k"), "<ctrl>+<alt>+k")
        self.assertEqual(normalize(""), DEFAULT_HOTKEY)
        self.assertEqual(normalize("<ctrl>+<shift>+s"), "<ctrl>+<shift>+s")


class CropTest(unittest.TestCase):
    def test_ekran_crop_global(self):
        img = Image.new("RGB", (200, 100), (255, 0, 0))
        e = EkranGoruntusu(image=img, left=0, top=0, width=200, height=100)
        c = e.crop(10, 20, 50, 30)
        self.assertEqual(c.size, (50, 30))

    def test_ofsetli_crop(self):
        img = Image.new("RGB", (200, 100), (0, 255, 0))
        e = EkranGoruntusu(image=img, left=100, top=50, width=200, height=100)
        # global (120,60) -> yerel (20,10)
        c = e.crop(120, 60, 40, 40)
        self.assertEqual(c.size, (40, 40))
        self.assertEqual(c.getpixel((5, 5)), (0, 255, 0))


class GrabTest(unittest.TestCase):
    def test_grab_returns_image(self):
        from app.core.capture import grab_screen

        e = grab_screen()
        if e is None:
            self.skipTest("ekran yakalama bu ortamda yok")
        self.assertGreater(e.width, 0)
        self.assertGreater(e.height, 0)
        self.assertEqual(e.image.size, (e.width, e.height))


class SelectionOverlayTest(unittest.TestCase):
    def test_yayinla_kirpar(self):
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtWidgets import QApplication
        from app.ui.selection_overlay import SelectionOverlay

        app = QApplication.instance() or QApplication([])
        _ = QGuiApplication.primaryScreen()  # ekran erişilebilir mi kontrol
        vgen = app.primaryScreen().virtualGeometry()
        w, h = max(1, vgen.width()), max(1, vgen.height())

        img = Image.new("RGB", (w, h), (10, 200, 10))
        e = EkranGoruntusu(image=img, left=0, top=0, width=w, height=h)

        ov = SelectionOverlay(e)
        # ölçeği birebir yap (offscreen=1:1 varsayımı)
        ov._scale_x = ov._scale_y = 1.0

        alinan = {}
        ov.tamamlandi.connect(lambda crop: alinan.setdefault("crop", crop))
        ov._yayinla(QRect(5, 5, 60, 40))
        self.assertIn("crop", alinan)
        self.assertEqual(alinan["crop"].size, (60, 40))

    def test_kucuk_secim_yayinlamaz(self):
        from PySide6.QtCore import QRect
        from PySide6.QtWidgets import QApplication
        from app.ui.selection_overlay import SelectionOverlay

        app = QApplication.instance() or QApplication([])
        img = Image.new("RGB", (400, 300), (0, 0, 0))
        e = EkranGoruntusu(image=img, left=0, top=0, width=400, height=300)
        ov = SelectionOverlay(e)
        ov._scale_x = ov._scale_y = 1.0
        salindi = []
        ov.tamamlandi.connect(lambda *_: salindi.append(1))
        # MIN_SELECT altındaki alan seçim sayılmaz
        self.assertFalse(ov._seckim_gecerli(QRect(0, 0, 2, 2)))
        self.assertEqual(salindi, [])


class ControllerTest(unittest.TestCase):
    def test_secim_bitti_sinyali(self):
        from PySide6.QtWidgets import QApplication
        from app.core.capture_controller import CaptureController

        app = QApplication.instance() or QApplication([])
        ctl = CaptureController()
        gelen = {}
        ctl.bolge_hazir.connect(lambda crop: gelen.setdefault("crop", crop))
        ctl._secim_bitti("SAF-CROP")
        self.assertEqual(gelen.get("crop"), "SAF-CROP")


if __name__ == "__main__":
    unittest.main(verbosity=2)
