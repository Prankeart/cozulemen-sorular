"""Çıktı dosyalarının kayıt yeri (Adım 8 sonrası iyileştirme).

- Kullanıcı bir kök klasör seçer (ayar: cikti_klasoru; varsayılan data/ciktilar).
- Uygulamadaki her klasör (TYT, AYT, Biyoloji...) bu kök altında gerçek bir alt
  klasör olarak oluşturulur.
- Üretilen PDF/Word, projenin bağlı olduğu klasörün alt klasörüne kaydedilir;
  klasörsüz projeler kök klasöre yazılır.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from app.core import paths, settings


def _guvenli(ad: str) -> str:
    ad = re.sub(r'[\\/:*?"<>|]', "_", (ad or "").strip())
    return ad[:80] or "_"


def cikti_koku() -> Path:
    """Seçili kök çıktı klasörü (boş/eksikse data/ciktilar)."""
    ham = settings.get("cikti_klasoru", "") or ""
    ham = str(ham).strip()
    if not ham:
        return paths.EXPORT_DIR
    return Path(ham)


def klasor_dizini_olustur(ad: str, kok: Optional[Path] = None) -> Path:
    """Uygulama klasörü için kök altında gerçek alt klasör oluşturur."""
    kok = kok or cikti_koku()
    kok.mkdir(parents=True, exist_ok=True)
    d = kok / _guvenli(ad)
    d.mkdir(parents=True, exist_ok=True)
    return d


def tum_klasorleri_olustur(db) -> None:
    """Kayıtlı tüm klasörleri seçili kök altında (yeniden) oluşturur."""
    for k in db.klasor_liste():
        klasor_dizini_olustur(k["ad"])


def _klasor_adi(proje, db) -> Optional[str]:
    klasor_id = proje["klasor_id"] if "klasor_id" in proje.keys() else None
    if not klasor_id:
        return None
    for k in db.klasor_liste():
        if k["id"] == klasor_id:
            return k["ad"]
    return None


def hedef_klasor(proje, db, uzanti: str = ".pdf") -> Path:
    """Projenin dosyasının yazılacağı dizin (klasör alt dizini dahil)."""
    kok = cikti_koku()
    ad = _klasor_adi(proje, db)
    d = (kok / _guvenli(ad)) if ad else kok
    d.mkdir(parents=True, exist_ok=True)
    return d


def dosya_yolu(proje, db, uzanti: str = ".pdf") -> str:
    """hedef_klasor altında güvenli dosya adı ile tam yol üretir."""
    d = hedef_klasor(proje, db, uzanti)
    return str(d / (_guvenli(proje["ad"]) + uzanti))
