"""Yüzen kontrol paneli (Adım 8 sonrası iyileştirme).

Yakalama modunda ekranın sağ üstünde kalan, sürüklenebilir küçük her zaman-üstte
çubuk. Kullanıcının ana ekrana dönebilmesi ve hızlı işlem yapabilmesi için:
    [Yakala]  [⚙ Ayarlar]  [Ana Menü]  [Bitir]      •  N soru
Sinyaller: yakala_istegi, ayarlar_istegi, ana_menu_istegi, bitir_istegi.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui import theme


class FloatingPanel(QWidget):
    yakala_istegi = Signal()
    ayarlar_istegi = Signal()
    ana_menu_istegi = Signal()
    bitir_istegi = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag: Optional[QPoint] = None
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setObjectName("FloatPanel")
        self.setStyleSheet(
            f"QWidget#FloatPanel {{ background:{theme.SURFACE};"
            f" border:1px solid {theme.BORDER}; border-radius:12px; }}"
            f"QLabel {{ color:{theme.TEXT}; }}"
        )

        dis = QVBoxLayout(self)
        dis.setContentsMargins(12, 8, 12, 8)
        dis.setSpacing(6)

        ust = QHBoxLayout()
        self.lbl_baslik = QLabel("Yakalama modu")
        self.lbl_baslik.setObjectName("CardTitle")
        self.lbl_sayi = QLabel("0 soru")
        self.lbl_sayi.setObjectName("CardMeta")
        ust.addWidget(self.lbl_baslik)
        ust.addStretch(1)
        ust.addWidget(self.lbl_sayi)
        dis.addLayout(ust)

        row = QHBoxLayout()
        row.setSpacing(6)
        self.btn_yakala = self._btn("Yakala", "Primary")
        self.btn_yakala.clicked.connect(self.yakala_istegi.emit)
        self.btn_ayar = self._btn("⚙", None, w=40)
        self.btn_ayar.clicked.connect(self.ayarlar_istegi.emit)
        self.btn_menu = self._btn("Ana Menü", None)
        self.btn_menu.clicked.connect(self.ana_menu_istegi.emit)
        self.btn_bitir = self._btn("Bitir", None)
        self.btn_bitir.clicked.connect(self.bitir_istegi.emit)
        for b in (self.btn_yakala, self.btn_ayar, self.btn_menu, self.btn_bitir):
            row.addWidget(b)
        dis.addLayout(row)

        self.adjustSize()

    def _btn(self, metin: str, obj: Optional[str], w: int = 0) -> QPushButton:
        b = QPushButton(metin)
        if obj:
            b.setObjectName(obj)
        b.setCursor(Qt.PointingHandCursor)
        b.setMinimumHeight(34)
        if w:
            b.setFixedWidth(w)
        return b

    # --------------------------- herk API ---------------------------
    def set_bilgi(self, proje_adi: str, soru_adedi: int) -> None:
        self.lbl_baslik.setText(proje_adi or "Yakalama modu")
        self.lbl_sayi.setText(f"{soru_adedi} soru")
        self.adjustSize()

    def sag_ust_yerlestir(self, ekran_geo) -> None:
        w = self.sizeHint().width()
        x = ekran_geo.right() - w - 24
        y = ekran_geo.top() + 24
        self.move(max(ekran_geo.left(), x), y)

    # --------------------------- sürükleme ---------------------------
    def mousePressEvent(self, e):  # noqa: N802
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):  # noqa: N802
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):  # noqa: N802
        self._drag = None
