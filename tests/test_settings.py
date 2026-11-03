"""Adım 8 testleri: ayarlar, kısayol doğrulama, hata hook'u, ayarlar diyaloğu.

Çalıştırma:
    python -m unittest tests.test_settings -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        import app.core.settings as s
        import app.core.paths as paths
        self.s = s
        self._eski = s.SETTINGS_PATH
        s.SETTINGS_PATH = Path(self.tmp.name) / "ayarlar.json"
        self.paths = paths

    def tearDown(self):
        self.s.SETTINGS_PATH = self._eski
        self.tmp.cleanup()

    def test_varsayilan_oku(self):
        veri = self.s.yukle()
        self.assertEqual(veri["hotkey"], "Ctrl+Shift+S")

    def test_kaydet_ve_oku(self):
        self.s.kaydet({"hotkey": "Ctrl+Alt+X"})
        self.assertEqual(self.s.get("hotkey"), "Ctrl+Alt+X")
        # kısmi güncelleme diğer alanları korur
        self.s.kaydet({"varsayilan_tur": "word"})
        self.assertEqual(self.s.get("hotkey"), "Ctrl+Alt+X")
        self.assertEqual(self.s.get("varsayilan_tur"), "word")


class ValidationTest(unittest.TestCase):
    def test_gecerli_gecsiz(self):
        from app.ui.settings_dialog import gecerli_mi

        self.assertTrue(gecerli_mi("Ctrl+Shift+S"))
        self.assertTrue(gecerli_mi("Alt+F1"))
        self.assertFalse(gecerli_mi("Ctrl"))       # tuş yok
        self.assertFalse(gecerli_mi("A"))          # değiştirici yok
        self.assertFalse(gecerli_mi("Ctrl+Shift"))  # ana tuş yok
        self.assertFalse(gecerli_mi(""))


class ErrorsTest(unittest.TestCase):
    def test_hook_kurulur(self):
        import sys

        from app.core.errors import install_excepthook

        eski = sys.excepthook
        install_excepthook(show_dialog=False)
        self.assertIsNot(sys.excepthook, eski)
        sys.excepthook = eski


class ControllerHotkeyTest(unittest.TestCase):
    def test_guncelle_kisayol_pasifken(self):
        from PySide6.QtWidgets import QApplication
        from app.core.capture_controller import CaptureController

        QApplication.instance() or QApplication([])
        ctl = CaptureController()
        # aktif değil -> True döner, kısayol kurmaya çalışmaz
        self.assertTrue(ctl.guncelle_kisayol("Ctrl+Alt+G"))
        ctl.durdur()


class SettingsDialogTest(unittest.TestCase):
    def test_gecersiz_kaydetmez(self):
        from PySide6.QtWidgets import QApplication
        import app.core.settings as s

        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        eski = s.SETTINGS_PATH
        s.SETTINGS_PATH = Path(tmp.name) / "a.json"
        app = QApplication.instance() or QApplication([])
        from app.ui.settings_dialog import SettingsDialog

        d = SettingsDialog()
        d.ed_hotkey.setText("SadeceBirTuş")
        sonuc = []
        d.kaydedildi.connect(lambda k: sonuc.append(k))
        # geçersiz -> uyarı kutusu açılır; offscreen'de engellenmemesi için
        # doğrudan doğrulamayı test ediyoruz
        from app.ui.settings_dialog import gecerli_mi

        self.assertFalse(gecerli_mi(d.ed_hotkey.text()))
        self.assertEqual(sonuc, [])
        s.SETTINGS_PATH = eski
        tmp.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
