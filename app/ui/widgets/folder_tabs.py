"""Klasör sekmeleri çubuğu.

Üstte "Tümü" + kayıtlı klasörler; sonda "+ Klasör" butonu.
Sinyaller:
    klasor_secildi(Optional[int])   # None => Tümü
    klasor_ekle_istegi()
    klasor_sil_istegi(int, str)     # klasor_id, ad (sağ tık ile)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class FolderTabs(QWidget):
    klasor_secildi = Signal(object)          # Optional[int]
    klasor_ekle_istegi = Signal()
    klasor_sil_istegi = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TabsBar")
        self._buttons: dict[int, QPushButton] = {}  # klasor_id(None->-1)->btn
        self._adlar: dict[int, str] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 0)

        hbar = QHBoxLayout()
        hbar.setSpacing(6)

        # yatay kaydırılabilir alan (çok klasör taşarsa)
        self._inner = QWidget()
        self._inner_lay = QHBoxLayout(self._inner)
        self._inner_lay.setContentsMargins(0, 0, 0, 0)
        self._inner_lay.setSpacing(6)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(self._inner)
        hbar.addWidget(scroll, 1)

        add_btn = QPushButton("+ Klasör")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.klasor_ekle_istegi.emit)
        hbar.addWidget(add_btn)

        root.addLayout(hbar)

        # "Tümü" sabit sekmesi
        self._tum_btn = self._make_btn(None, "Tümü")
        self._inner_lay.addWidget(self._tum_btn)
        self._tum_btn.click()  # varsayılan seçim

    # --------------------------- yardımcılar ---------------------------
    def _make_btn(self, klasor_id: Optional[int], ad: str) -> QPushButton:
        btn = QPushButton(ad)
        btn.setProperty("tab", "true")
        btn.setProperty("selected", "false")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _=False, k=klasor_id: self._select(k))
        if klasor_id is not None:
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, k=klasor_id, a=ad: self._menu(pos, k, a)
            )
        self._group.addButton(btn)
        self._buttons[klasor_id if klasor_id is not None else -1] = btn
        return btn

    def _select(self, klasor_id: Optional[int]) -> None:
        for btn in self._buttons.values():
            btn.setProperty("selected", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        key = klasor_id if klasor_id is not None else -1
        btn = self._buttons[key]
        btn.setProperty("selected", "true")
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        self.klasor_secildi.emit(klasor_id)

    def _menu(self, pos, klasor_id: int, ad: str) -> None:
        menu = QMenu(self)
        sil = QAction("Klasörü sil", menu)
        sil.triggered.connect(lambda: self.klasor_sil_istegi.emit(klasor_id, ad))
        menu.addAction(sil)
        menu.exec(self._buttons[klasor_id].mapToGlobal(pos))

    # --------------------------- herk API ---------------------------
    def yenile(self, klasorler: list[tuple[int, str]], secili: Optional[int] = None) -> None:
        """Klasör listesini yeniden kurar. klasorler: [(id, ad), ...]."""
        # mevcut klasör butonlarını temizle (Tümü kalır)
        for key in [k for k in self._buttons if k != -1]:
            btn = self._buttons.pop(key)
            self._group.removeButton(btn)
            self._inner_lay.removeWidget(btn)
            btn.deleteLater()
        self._adlar = {}
        for cid, ad in klasorler:
            self._adlar[cid] = ad
            self._inner_lay.addWidget(self._make_btn(cid, ad))
        self._inner_lay.addStretch(1)
        # seçimi uygula
        if secili is not None and secili in self._buttons:
            self._select(secili)
        else:
            self._select(None)
