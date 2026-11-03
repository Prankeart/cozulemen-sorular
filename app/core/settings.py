"""Kalıcı uygulama ayarları (Adım 8).

Ayarlar data/ayarlar.json içinde tutulur (şık/görsel verisi DB'de, kullanıcı
tercihleri burada). Varsayılanlar her zaman birleştirilerek döner.
"""

from __future__ import annotations

import json
from typing import Any

from app.core import paths
from app.core.hotkey import DEFAULT_HOTKEY_GORUNUM

SETTINGS_PATH = paths.DATA_DIR / "ayarlar.json"

VARSAYILANLAR: dict[str, Any] = {
    "hotkey": DEFAULT_HOTKEY_GORUNUM,          # "Ctrl+Shift+S"
    "varsayilan_sik_sayisi": 4,
    "varsayilan_tur": "pdf",
    "cikti_klasoru": str(paths.EXPORT_DIR),    # PDF/Word kayıt yeri (kök)
}


def yukle() -> dict[str, Any]:
    """Ayarları okur; eksik alanlara varsayılanı uygular."""
    veri = dict(VARSAYILANLAR)
    try:
        if SETTINGS_PATH.exists():
            veri.update(json.loads(SETTINGS_PATH.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        pass
    return veri


def kaydet(guncelleme: dict[str, Any]) -> dict[str, Any]:
    """Kısmi güncellemeyi mevcut ayarlara ekler, diske yazar, döner."""
    veri = yukle()
    veri.update(guncelleme or {})
    paths.ensure_dirs()
    try:
        SETTINGS_PATH.write_text(
            json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        pass
    return veri


def get(alan: str, varsayilan: Any = None) -> Any:
    return yukle().get(alan, varsayilan if varsayilan is not None else VARSAYILANLAR.get(alan))
