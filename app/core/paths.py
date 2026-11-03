"""Uygulama genelinde dizin/yol sabitleri.

Proje kökü, data/ ve görsel klasörleri tek yerden tanımlanır; böylece
veritabanı, yakalama ve dışa aktarma adımları aynı yolları kullanır.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Proje kökü: kaynakta .../PDF oluşturucu; donmuş (.exe) çalıştırmada exe'in
# bulunduğu klasör (data/ buraya yazılır, geçici _MEIPASS değil).
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "gorseller"        # kırpılmış soru görselleri
ASSETS_DIR = BASE_DIR / "assets"
EXPORT_DIR = DATA_DIR / "ciktilar"          # üretilen PDF/Word dosyaları
DB_PATH = DATA_DIR / "test_uretici.sqlite3"


def ensure_dirs() -> None:
    """Gerekli veri klasörlerini oluşturur (yoksa oluşturur, varsa dokunmaz)."""
    for d in (DATA_DIR, IMAGES_DIR, ASSETS_DIR, EXPORT_DIR):
        d.mkdir(parents=True, exist_ok=True)


def image_path(proje_id: int, soru_no: int, ext: str = "png") -> Path:
    """Bir soru görseli için varsayılan dosya yolu (data/gorseller altında)."""
    ensure_dirs()
    ad = f"proje{proje_id:04d}_soru{soru_no:04d}.{ext}"
    return IMAGES_DIR / ad


def rel_to_base(p: os.PathLike | str | Path) -> str:
    """Yolu mümkünse BASE_DIR'e göre göreli metne çevirir (DB'de saklamak için)."""
    path = Path(p)
    try:
        return str(path.resolve().relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def abs_from_base(rel: os.PathLike | str | Path | None) -> Path | None:
    """DB'deki (göreli olabilecek) yolu mutlak Path'e çevirir."""
    if rel is None or str(rel).strip() == "":
        return None
    path = Path(rel)
    if path.is_absolute():
        return path
    return BASE_DIR / path
