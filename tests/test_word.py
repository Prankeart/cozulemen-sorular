"""Adım 7 testleri: Word üretimi + canlı önizleme.

Çalıştırma:
    python -m unittest tests.test_word -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402

from app.export.word_exporter import export_word  # noqa: E402


def _stil(**k):
    base = {"sayfa_tarzi": "tek", "ayrac": "cizgi", "soru_boslugu": 24,
            "renk": "#2f6f4f", "font": "Helvetica"}
    base.update(k)
    return base


class WordExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.dir = Path(self.tmp.name)
        self.yollar = []
        for i in range(1, 7):
            p = self.dir / f"s{i}.png"
            Image.new("RGB", (300, 120), (10 * i, 40, 90)).save(p)
            self.yollar.append(str(p))

    def tearDown(self):
        self.tmp.cleanup()

    def _sorular(self, n):
        sikler = ["A", "B", "C", "D", "E"]
        return [
            {"soru_no": i + 1, "gorsel_yolu": self.yollar[i % len(self.yollar)],
             "dogru_sik": sikler[i % 5]}
            for i in range(n)
        ]

    def test_docx_olusur(self):
        proje = {"ad": "Deneme", "sik_sayisi": 4}
        out = str(self.dir / "t.docx")
        yol = export_word(proje, self._sorular(6), _stil(), out)
        veri = Path(yol).read_bytes()
        self.assertEqual(veri[:2], b"PK")  # docx bir zip'tir
        self.assertGreater(len(veri), 3000)

    def test_cevap_anahtari_tablosu(self):
        from docx import Document

        proje = {"ad": "Iki", "sik_sayisi": 5}
        out = str(self.dir / "t2.docx")
        export_word(proje, self._sorular(6), _stil(sayfa_tarzi="iki"), out)
        doc = Document(out)
        self.assertGreaterEqual(len(doc.tables), 1)
        metinler = [c.text for row in doc.tables[-1].rows for c in row.cells]
        self.assertIn("1 - A", metinler)   # soru 1 -> sikler[0]
        self.assertIn("5 - E", metinler)   # soru 5 -> sikler[4]

    def test_bos_soru_hata(self):
        proje = {"ad": "Bos", "sik_sayisi": 4}
        with self.assertRaises(ValueError):
            export_word(proje, [], _stil(), str(self.dir / "bos.docx"))


class StylePreviewTest(unittest.TestCase):
    def test_set_stil_saklar(self):
        from PySide6.QtWidgets import QApplication
        from app.ui.style_preview import StylePreview

        QApplication.instance() or QApplication([])
        pv = StylePreview(_stil(sayfa_tarzi="iki"))
        pv.set_stil(_stil(renk="#ff0000", soru_boslugu=50))
        self.assertEqual(pv.stil["renk"], "#ff0000")
        self.assertEqual(pv.stil["soru_boslugu"], 50)

    def test_dialog_onizleme_tazele(self):
        from PySide6.QtWidgets import QApplication
        import app.core.paths as paths
        from app.db import database as dbmod

        QApplication.instance() or QApplication([])
        t = tempfile.mkdtemp()
        dbmod._db = None
        self._eski_db = paths.DB_PATH
        paths.DB_PATH = Path(t) / "t.sqlite3"
        db = dbmod.get_db()
        from app.ui.new_pdf_dialog import NewPdfDialog
        d = NewPdfDialog()
        d.cb_sayfa.setCurrentIndex(1)  # iki sütun -> tetiklenir
        self.assertEqual(d.prev.stil["sayfa_tarzi"], "iki")
        db.close()
        dbmod._db = None
        paths.DB_PATH = self._eski_db


if __name__ == "__main__":
    unittest.main(verbosity=2)
