"""Tam ekran, yarı saydam dikdörtgen seçim katmanı (Adım 4).

Kullanıcı fareyle bir alan seçer; kesikli çerçeve ve üstünde "Seçilen alan
GxY" etiketi görünür. Seçim bitince arka plan görüntüsünden kırpılmış PIL
görseli `tamamlandi` sinyaliyle iletilir. Esc ile `iptal`.

Yakalanan görüntü tüm sanal masaüstünü (tüm monitörler) kapsar; seçim mantıksal
Qt koordinatlarından görüntü piksellerine ölçeklenerek kırpılır (yüksek DPI'da
doğru sonuç için).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QGuiApplication,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QWidget

from app.core.capture import EkranGoruntusu, pil_to_qpixmap
from app.ui import theme

MIN_SELECT = 4  # bundan küçükse seçim sayılmaz


class SelectionOverlay(QWidget):
    tamamlandi = Signal(object)   # PIL.Image (kırpılmış)
    iptal = Signal()

    def __init__(self, ekran: EkranGoruntusu, parent=None):
        super().__init__(parent)
        self.ekran = ekran
        self._pixmap = pil_to_qpixmap(ekran.image)
        self._baslangic: Optional[QPoint] = None
        self._seckim: Optional[QRect] = None

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Window
        )
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setCursor(Qt.CrossCursor)
        self.setMouseTracking(True)

        # tüm sanal masaüstünü kapla (görüntünün mantıksal karşılığı)
        vgeom = QGuiApplication.primaryScreen().virtualGeometry()
        self.setGeometry(vgeom)
        self._origin = vgeom.topLeft()
        self._scale_x = ekran.image.width / max(1, vgeom.width())
        self._scale_y = ekran.image.height / max(1, vgeom.height())

    # --------------------------- boyama ---------------------------
    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)

        # donmuş ekran görüntüsü
        p.drawPixmap(self.rect(), self._pixmap)
        # karartma
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))

        if self._seckim_gecerli(self._seckim):
            r = self._seckim
            # seçili alanı aydınlat: karartmayı kaldırıp donmuş görüntüyü
            # bu dikdörtgende tekrar (parlak) çiz. (Clear kompozisyonu
            # saydam zemin olmadığı için siyaha neden oluyordu.)
            p.setClipRect(r)
            p.drawPixmap(self.rect(), self._pixmap)
            p.setClipping(False)

            pen = QPen(QColor(theme.ACCENT))
            pen.setStyle(Qt.DashLine)
            pen.setWidth(2)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawRect(r)

            # üstte etiket
            etiket = f"Seçilen alan  {r.width()}×{r.height()}"
            p.setFont(self.font())
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(etiket) + 14
            th = fm.height() + 8
            tx = r.left()
            ty = r.top() - th - 4
            if ty < 0:
                ty = r.top() + 4
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(theme.ACCENT)))
            p.drawRoundedRect(QRect(tx, ty, tw, th), 5, 5)
            p.setPen(QColor("#ffffff"))
            p.drawText(QRect(tx, ty, tw, th), Qt.AlignCenter, etiket)
        else:
            # ipucu
            p.setPen(QColor("#ffffff"))
            p.drawText(self.rect().adjusted(0, 40, 0, 0), Qt.AlignTop | Qt.AlignHCenter,
                       "Soru alanını fareyle seç  •  İptal için Esc")
        p.end()

    # --------------------------- fare ---------------------------
    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.LeftButton:
            self._baslangic = e.pos()
            self._seckim = QRect(self._baslangic, self._baslangic)
            self.update()

    def mouseMoveEvent(self, e):  # noqa: N802
        if self._baslangic is not None:
            self._seckim = QRect(self._baslangic, e.pos()).normalized()
            self.update()

    def mouseReleaseEvent(self, e):  # noqa: N802
        if e.button() != Qt.LeftButton or self._baslangic is None:
            return
        rect = QRect(self._baslangic, e.pos()).normalized()
        self._baslangic = None
        if self._seckim_gecerli(rect):
            self._seckim = rect
            self._yayinla(rect)
        else:
            self._seckim = None
            self.update()

    def _seckim_gecerli(self, r: Optional[QRect]) -> bool:
        return r is not None and r.width() >= MIN_SELECT and r.height() >= MIN_SELECT

    def _yayinla(self, r: QRect) -> None:
        # mantıksal widget koordinatı -> görüntü pikseli
        ix = int(r.left() * self._scale_x)
        iy = int(r.top() * self._scale_y)
        iw = max(1, int(r.width() * self._scale_x))
        ih = max(1, int(r.height() * self._scale_y))
        crop = self.ekran.image.crop((ix, iy, ix + iw, iy + ih))
        self.tamamlandi.emit(crop)
        self.close()

    # --------------------------- klavye ---------------------------
    def keyPressEvent(self, e):  # noqa: N802
        if e.key() == Qt.Key_Escape:
            self.iptal.emit()
            self.close()
        elif e.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self._seckim_gecerli(self._seckim):
                self._yayinla(self._seckim)  # type: ignore[arg-type]
