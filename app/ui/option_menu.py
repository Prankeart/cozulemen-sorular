"""Şık seçim menüsü (Adım 5).

Ekranın sağ altında çıkan, sürüklenebilir küçük pencere:
  - "Soru N • doğru şık?" başlığı
  - A B C D (E) dairesel şık butonları (tek seçim)
  - "Kaydet ve kapat" (seçilen şıkla) ve "İptal"
Sinyaller: kaydet(str sik), iptal(). Esc -> iptal.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui import theme

SIK_HARFLERI = ["A", "B", "C", "D", "E"]

_SIK_QSS = f"""
QPushButton#SikBtn {{
    background: {theme.SURFACE};
    border: 2px solid {theme.BORDER};
    border-radius: 20px;
    color: {theme.TEXT};
    font-weight: 700;
    font-size: 16px;
}}
QPushButton#SikBtn:hover {{ border: 2px solid {theme.ACCENT}; }}
QPushButton#SikBtn:checked {{
    background: {theme.ACCENT};
    border: 2px solid {theme.ACCENT};
    color: #ffffff;
}}
"""


class OptionMenu(QWidget):
    kaydet = Signal(str)
    iptal = Signal()

    def __init__(self, sik_sayisi: int = 4, soru_no: int = 1, parent=None):
        super().__init__(parent)
        self._sik_sayisi = max(4, min(5, int(sik_sayisi)))
        self._soru_no = soru_no
        self._drag: Optional[QPoint] = None
        self._secili: Optional[str] = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName("OptionMenu")
        self.setStyleSheet(
            f"QWidget#OptionMenu {{ background:{theme.SURFACE};"
            f" border:1px solid {theme.BORDER}; border-radius:14px; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        baslik = QLabel(f"Soru {soru_no}  •  doğru şık?")
        baslik.setObjectName("CardTitle")
        baslik.setAlignment(Qt.AlignCenter)
        lay.addWidget(baslik)

        # şık butonları
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setAlignment(Qt.AlignCenter)
        self._grup = QButtonGroup(self)
        self._grup.setExclusive(True)
        for harf in SIK_HARFLERI[: self._sik_sayisi]:
            b = QPushButton(harf)
            b.setObjectName("SikBtn")
            b.setCheckable(True)
            b.setFixedSize(40, 40)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(_SIK_QSS)
            b.toggled.connect(lambda on, h=harf: self._sik_sec(on, h))
            self._grup.addButton(b)
            row.addWidget(b)
        lay.addLayout(row)

        # alt butonlar
        alt = QHBoxLayout()
        iptal = QPushButton("İptal")
        iptal.setCursor(Qt.PointingHandCursor)
        iptal.clicked.connect(self._iptal_et)
        kaydet = QPushButton("Kaydet ve kapat")
        kaydet.setObjectName("Primary")
        kaydet.setCursor(Qt.PointingHandCursor)
        kaydet.clicked.connect(self._kaydet)
        alt.addWidget(iptal)
        alt.addWidget(kaydet)
        lay.addLayout(alt)

        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self._iptal_et)

        self.adjustSize()

    # --------------------------- etkileşim ---------------------------
    def _sik_sec(self, on: bool, harf: str) -> None:
        if on:
            self._secili = harf

    def _kaydet(self) -> None:
        if not self._secili:
            return
        self.kaydet.emit(self._secili)
        self.close()

    def _iptal_et(self) -> None:
        self.iptal.emit()
        self.close()

    # --------------------------- sürükleme ---------------------------
    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):  # noqa: N802
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):  # noqa: N802
        self._drag = None


def sag_alt_konum(widget: QWidget, ekran_geo) -> None:
    """Widget'ı ekranın sağ altına (kenar boşluğuyla) yerleştirir."""
    w, h = widget.sizeHint().width(), widget.sizeHint().height()
    x = ekran_geo.right() - w - 24
    y = ekran_geo.bottom() - h - 24
    widget.move(max(ekran_geo.left(), x), max(ekran_geo.top(), y))
