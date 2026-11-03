"""Ekran görüntüsü alma (mss + Pillow).

Tek monitörde sanal masaüstünün tamamını yakalar; global kenar kutusunu
(sol, üst, genişlik, yükseklik) ve PIL.Image döndürür. QImage/QPixmap dönüşümü
PNG baytları üzerinden yapılır (ImageQt/numpy bağımlılığı olmadan).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

from PIL import Image


@dataclass
class EkranGoruntusu:
    image: Image.Image
    left: int
    top: int
    width: int
    height: int

    def crop(self, x: int, y: int, w: int, h: int) -> Image.Image:
        """Global ekran koordinatlarına göre kırp (sol/üst ofseti düşülür)."""
        x0 = max(0, x - self.left)
        y0 = max(0, y - self.top)
        x1 = min(self.width, x0 + w)
        y1 = min(self.height, y0 + h)
        if x1 <= x0 or y1 <= y0:
            return self.image.crop((0, 0, 1, 1))
        return self.image.crop((x0, y0, x1, y1))


def grab_screen(monitors_index: int = 0) -> Optional[EkranGoruntusu]:
    """Tüm ekranın (varsayılan: sanal masaüstü) görüntüsünü alır."""
    try:
        import mss
    except Exception:
        return None
    # mss 10.x: MSS önerilir; eski sürümler için mss.mss yedekte
    yap = getattr(mss, "MSS", None) or mss.mss
    with yap() as sct:
        mon = sct.monitors[monitors_index]
        shot = sct.grab(mon)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return EkranGoruntusu(
            image=img,
            left=int(mon["left"]),
            top=int(mon["top"]),
            width=int(mon["width"]),
            height=int(mon["height"]),
        )


def pil_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def pil_to_qpixmap(img: Image.Image):
    """PIL.Image -> QPixmap (arayüzde gösterim için)."""
    from PySide6.QtGui import QPixmap

    data = pil_to_bytes(img, "PNG")
    pix = QPixmap()
    pix.loadFromData(data, "PNG")
    return pix
