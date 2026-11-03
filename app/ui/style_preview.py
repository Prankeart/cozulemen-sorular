"""Canlı stil önizlemesi (Adım 7).

Yeni PDF penceresindeki "Önizle" kutusu: seçilen stil (sütun, ayraç, boşluk,
renk, yazı tipi) değiştikçe örnek bir test sayfasını yeniden çizer.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

# stil fontu -> Qt font ailesi
_QT_FONT = {
    "Helvetica": "Arial",
    "Times-Roman": "Times New Roman",
    "Courier": "Courier New",
}

ORNEK_SAYI = 4


class StylePreview(QWidget):
    def __init__(self, stil: dict | None = None, parent=None):
        super().__init__(parent)
        self.stil = dict(stil or {})
        self.setMinimumHeight(150)

    def set_stil(self, stil: dict) -> None:
        self.stil = dict(stil)
        self.update()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()

        iki = self.stil.get("sayfa_tarzi") == "iki"
        ncol = 2 if iki else 1
        renk = QColor(self.stil.get("renk", "#2f6f4f"))
        font_aile = _QT_FONT.get(self.stil.get("font", "Helvetica"), "Arial")
        gap = float(self.stil.get("soru_boslugu", 24)) * 0.5

        # sayfa zemini
        p.fillRect(self.rect(), QColor("#ffffff"))
        p.setPen(QPen(QColor("#e6e2d8")))
        p.drawRect(0, 0, w - 1, h - 1)

        m = 10
        gutter = 12 if iki else 0
        content_w = w - 2 * m - (ncol - 1) * gutter
        col_w = content_w / ncol
        col_x = [m + i * (col_w + gutter) for i in range(ncol)]

        # ayraç çizgisi
        if iki and self.stil.get("ayrac", "cizgi") == "cizgi":
            p.setPen(QPen(renk, 1))
            x = col_x[1] - gutter / 2
            p.drawLine(int(x), m, int(x), h - m)

        # başlık
        f = QFont(font_aile, 9)
        f.setBold(True)
        p.setFont(f)
        p.setPen(renk)
        p.drawText(QRect(m, 4, content_w, 16), Qt.AlignLeft | Qt.AlignVCenter,
                   "Test")

        # örnek sorular
        y0 = 26
        item_h = (h - y0 - m - (ORNEK_SAYI - 1) * gap) / ORNEK_SAYI
        item_h = max(14, item_h)
        numf = QFont(font_aile, 8)
        numf.setBold(True)
        boxf = QFont(font_aile, 7)

        for i in range(ORNEK_SAYI):
            kolon = i % ncol
            satir = i // ncol
            x = col_x[kolon]
            y = y0 + satir * (item_h + gap)
            if y + item_h > h - m:
                break
            # numara
            p.setFont(numf)
            p.setPen(renk)
            p.drawText(QRect(int(x), int(y), 20, 12), Qt.AlignLeft, f"{i + 1})")
            # görsel yer tutucu
            bx, by = int(x), int(y + 13)
            bw, bh = int(col_w), int(item_h - 13)
            if bh <= 0:
                continue
            p.setPen(QPen(QColor("#d8d4c8")))
            p.setBrush(QColor("#f3f1ea"))
            p.drawRoundedRect(bx, by, bw, bh, 4, 4)
            p.setPen(QColor("#a9a596"))
            p.setFont(boxf)
            p.drawText(QRect(bx, by, bw, bh), Qt.AlignCenter, "soru görseli")
            # soru altı çizgisi
            if self.stil.get("soru_alti_cizgi") == "cizgi":
                ly = by + bh + 2
                p.setPen(QPen(QColor("#c9c5b8"), 1))
                p.drawLine(bx, ly, bx + bw, ly)

        p.end()
