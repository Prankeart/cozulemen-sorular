"""Örnek/önizleme Word üreticisi (veritabanına dokunmaz).

Adım 7 layout'unu (numara + görsel + ayraç + Cevap Anahtarı tablosu) görmek için:
    python scripts/demo_word.py
Çıktı: data/ciktilar/ornek_test.docx
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw  # noqa: E402

from app.core import paths  # noqa: E402
from app.export.word_exporter import export_word  # noqa: E402


def _sahte_soru(yol: Path, no: int, secenek_sayisi: int):
    img = Image.new("RGB", (640, 220), "#ffffff")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 637, 217], outline="#cccccc", width=2)
    d.text((14, 12), f"{no}. Bu bir ornek soru metnidir?", fill="#222222")
    for i, h in enumerate("ABCDE"[:secenek_sayisi]):
        y = 48 + i * 32
        d.ellipse([16, y, 36, y + 20], outline="#555555")
        d.text((20, y + 3), h, fill="#222222")
        d.text((48, y + 3), f"{h}) secenek metni {i + 1}", fill="#333333")
    img.save(yol)
    return str(yol)


def main() -> int:
    paths.ensure_dirs()
    out = paths.EXPORT_DIR / "ornek_test.docx"
    tmp = Path(tempfile.mkdtemp())
    sorular = []
    for no in range(1, 13):
        sik = 5 if no % 3 == 0 else 4
        yol = _sahte_soru(tmp / f"s{no}.png", no, sik)
        cevap = "ABCDE"[(no * 7) % sik]
        sorular.append({"soru_no": no, "gorsel_yolu": yol, "dogru_sik": cevap})

    proje = {"ad": "Örnek Test", "sik_sayisi": 5}
    stil = {
        "sayfa_tarzi": "iki", "ayrac": "cizgi", "soru_boslugu": 18,
        "renk": "#2f6f4f", "font": "Helvetica",
    }
    yol = export_word(proje, sorular, stil, str(out))
    print("Word üretildi:", yol)
    print("Boyut:", Path(yol).stat().st_size, "bayt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
