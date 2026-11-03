"""Adım 2 smoke testi: GUI'yi offscreen kur, klasör/proje CRUD'unu dene.

Çalıştırma:
    python tests/smoke_ui.py
Etkileşimli pencere açmaz; yalnızca hatasız inşa edildiğini doğrular.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# projeyi import edilebilir kıl
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# testler gerçek data/ kirlenmesin diye geçici DB hedefle
import app.core.paths as paths  # noqa: E402

_tmp = tempfile.mkdtemp()
paths.DB_PATH = Path(_tmp) / "smoke.sqlite3"

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.db import database as dbmod  # noqa: E402
from app.ui import theme  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(theme.build_qss())

    db = dbmod.get_db()
    # örnek klasör ve projeler
    kimya = db.klasor_ekle("Kimya")
    p1 = db.proje_olustur("TYT Deneme", klasor_id=db.klasor_liste()[0]["id"],
                          sik_sayisi=4, tur="pdf")
    p2 = db.proje_olustur("Kimya Notları", klasor_id=kimya, sik_sayisi=5, tur="word")
    db.soru_ekle(p1, "data/gorseller/x.png", "A")
    db.soru_ekle(p1, "data/gorseller/x.png", "C")

    from app.ui.main_window import MainWindow
    w = MainWindow()
    w.resize(1120, 720)

    assert w._kolon_sayisi() >= 1
    # Tümü: 2 proje
    w._klasor_secildi(None)
    kartlar = w.grid.count()
    assert kartlar >= 2, f"kart sayısı beklenen>=2, gelen={kartlar}"

    # Kimya klasörü: 1 proje
    w._klasor_secildi(kimya)
    kartlar2 = w.grid.count()
    assert kartlar2 == 1, f"Kimya kart=1 beklenen, gelen={kartlar2}"

    # klasör sil (dalog çıkarmadan, db üzerinden) -> klasör düşer
    db.klasor_sil(kimya)
    w._yenile()
    assert not db.klasor_var_mi("Kimya")

    # proje sil (db üzerinden)
    db.proje_sil(p2)
    w._yenile()
    assert db.proje_getir(p2) is None

    print("UI SMOKE OK | Tümü kart:", kartlar, "| Kimya kart:", kartlar2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
