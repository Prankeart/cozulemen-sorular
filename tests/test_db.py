"""Adım 1 veritabanı testleri (bağımlılık yok; stdlib unittest).

Çalıştırma (proje kökünde):
    python -m unittest tests.test_db -v
veya doğrudan:
    python tests/test_db.py
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.db.database import Database


class DBTest(unittest.TestCase):
    def setUp(self):
        # geçici DB üzerinde çalış, gerçek data/ kirlenmesin
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(db_path=Path(self.tmp.name) / "test.sqlite3")
        self.db.seed()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_seed_profil_ve_klasorler(self):
        self.assertIsNotNone(self.db.profil_getir())
        self.assertGreaterEqual(len(self.db.klasor_liste()), 6)

    def test_klasor_ekle_ve_tekil(self):
        yeni = self.db.klasor_ekle("Kimya")
        self.assertIsNotNone(yeni)
        # aynı isim tekrar eklenemez
        self.assertIsNone(self.db.klasor_ekle("Kimya"))

    def test_proje_crud(self):
        klasor = self.db.klasor_liste()[0]["id"]
        pid = self.db.proje_olustur("Deneme 1", klasor_id=klasor, sik_sayisi=5, tur="word")
        p = self.db.proje_getir(pid)
        self.assertEqual(p["ad"], "Deneme 1")
        self.assertEqual(p["sik_sayisi"], 5)
        self.assertEqual(p["tur"], "word")

        self.db.proje_yeniden_adlandir(pid, "Deneme 2")
        self.assertEqual(self.db.proje_getir(pid)["ad"], "Deneme 2")

        self.db.proje_stil_set(pid, self.db.varsayilan_stil(sayfa_tarzi="iki"))
        self.assertEqual(self.db.proje_stil_getir(pid)["sayfa_tarzi"], "iki")

    def test_proje_gecsiz_degerler(self):
        with self.assertRaises(ValueError):
            self.db.proje_olustur("X", sik_sayisi=3)
        with self.assertRaises(ValueError):
            self.db.proje_olustur("X", tur="txt")

    def test_soru_no_otomatik_ve_cevap_anahtari(self):
        pid = self.db.proje_olustur("Soru testi")
        g = "data/gorseller/ornek.png"
        self.db.soru_ekle(pid, g, "A")
        self.db.soru_ekle(pid, g, "C")
        self.db.soru_ekle(pid, g, "B")
        self.assertEqual(self.db.soru_adet(pid), 3)
        anahtar = self.db.cevap_anahtari(pid)
        self.assertEqual(anahtar, [(1, "A"), (2, "C"), (3, "B")])

        son = self.db.soru_son_sil(pid)
        self.assertEqual(son["soru_no"], 3)
        self.assertEqual(self.db.soru_adet(pid), 2)

    def test_soru_gecsiz_sik(self):
        pid = self.db.proje_olustur("X")
        with self.assertRaises(ValueError):
            self.db.soru_ekle(pid, "g.png", "Z")

    def test_proje_sil_cascade(self):
        pid = self.db.proje_olustur("Silinecek")
        self.db.soru_ekle(pid, "g.png", "A")
        self.db.proje_sil(pid)
        self.assertEqual(self.db.soru_adet(pid), 0)
        self.assertIsNone(self.db.proje_getir(pid))


if __name__ == "__main__":
    unittest.main(verbosity=2)
