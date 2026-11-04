"""Adım 6 testleri: PDF üretimi (tek/iki sütun, cevap anahtarı).

Çalıştırma:
    python -m unittest tests.test_pdf -v
Gerçek PNG dosyaları üretilip PDF yazılır; imza, sayfa ve boyut doğrulanır.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402

from app.export.pdf_exporter import export_pdf  # noqa: E402


def _stil(**k):
    base = {"sayfa_tarzi": "tek", "ayrac": "cizgi", "soru_boslugu": 24,
            "renk": "#2f6f4f", "font": "Helvetica"}
    base.update(k)
    return base


class PdfExportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.dir = Path(self.tmp.name)
        self.gorsel_yollari = []
        for i in range(1, 6):
            p = self.dir / f"s{i}.png"
            Image.new("RGB", (300, 120), (20 * i, 60, 120)).save(p)
            self.gorsel_yollari.append(str(p))

    def tearDown(self):
        self.tmp.cleanup()

    def _sorular(self, n):
        sikler = ["A", "B", "C", "D", "E"]
        yollar = self.gorsel_yollari
        return [
            {"soru_no": i + 1, "gorsel_yolu": yollar[i % len(yollar)],
             "dogru_sik": sikler[i % 5]}
            for i in range(n)
        ]

    def _pdf_bilgi(self, yol):
        veri = Path(yol).read_bytes()
        return veri[:5], veri.count(b"/Type /Page") + veri.count(b"/Type/Page")

    def test_pdf_olusur(self):
        proje = {"ad": "Deneme", "sik_sayisi": 4}
        out = str(self.dir / "c1.pdf")
        yol = export_pdf(proje, self._sorular(5), _stil(), out)
        self.assertEqual(Path(yol), Path(out))
        imza, sayfa = self._pdf_bilgi(yol)
        self.assertEqual(imza, b"%PDF-")
        self.assertGreater(Path(yol).stat().st_size, 1000)
        self.assertGreaterEqual(sayfa, 2)  # soru sayfası + cevap anahtarı

    def test_bos_soru_hata(self):
        proje = {"ad": "Bos", "sik_sayisi": 4}
        with self.assertRaises(ValueError):
            export_pdf(proje, [], _stil(), str(self.dir / "bos.pdf"))

    def test_iki_sutun_cok_sayfa(self):
        proje = {"ad": "Iki", "sik_sayisi": 5}
        out = str(self.dir / "c2.pdf")
        # uzun görseller -> taşma -> birden çok sayfa
        for i in range(1, 6):
            p = self.dir / f"s{i}.png"
            Image.new("RGB", (200, 600), (10, 10, 10)).save(p)
        yol = export_pdf(proje, self._sorular(12), _stil(sayfa_tarzi="iki"), out)
        imza, sayfa = self._pdf_bilgi(yol)
        self.assertEqual(imza, b"%PDF-")
        self.assertGreaterEqual(sayfa, 2)

    def test_uzun_cevap_anahtari_sayfalani(self):
        # 259 soru: cevap anahtarı tek sayfaya sığmaz; hepsi görünmeli (regresyon)
        proje = {"ad": "Uzun", "sik_sayisi": 4}
        out = str(self.dir / "uzun.pdf")
        sor = self._sorular(259)
        export_pdf(proje, sor, _stil(sayfa_tarzi="iki"), out)

        try:
            import pypdfium2 as pdfium
            import re
        except Exception:
            self.skipTest("pypdfium2 yok; metin çıkarımı atlandı")
        d = pdfium.PdfDocument(out)
        nums = set()
        for pg in d:
            t = pg.get_textpage().get_text_bounded()
            for m in re.finditer(r"(\d+)\s*-\s*([A-E])", t):
                nums.add(int(m.group(1)))
        self.assertEqual(nums, set(range(1, 260)))
        # soru sayfaları + çok sayfalı cevap anahtarı => en az 2 sayfa
        self.assertGreaterEqual(len(d), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
