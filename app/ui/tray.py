"""Sistem tepsisi (Adım 5).

Yakalama modunda pencere arka plana alınır; tepsi ikonundan:
  - soru sayısı görülür,
  - son soru silinir / yeniden çekilir,
  - yakalama bitirilir,
  - pencere gösterilebilir / çıkılır.
İkon programatik üretilir (asset bağımlılığı yok).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.ui import theme


def _ikon_uret() -> QIcon:
    px = 64
    pm = QPixmap(px, px)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setBrush(QColor(theme.ACCENT))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(4, 4, px - 8, px - 8, 14, 14)
    p.setPen(QColor("#ffffff"))
    f = p.font()
    f.setPixelSize(34)
    f.setBold(True)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignCenter, "T")
    p.end()
    return QIcon(pm)


class TrayController(QObject):
    son_soru_sil = Signal()
    yeniden_cekm = Signal()
    bitir = Signal()
    goster = Signal()
    cikis = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._icon = _ikon_uret()
        self._tray = QSystemTrayIcon(self._icon, parent)
        self._soru_adedi = 0
        self._build_menu()
        self._tray.setContextMenu(self._menu)
        self._tray.activated.connect(self._cift_tik)

    # --------------------------- kurulum ---------------------------
    def _build_menu(self) -> None:
        self._menu = QMenu()
        self._durum = QAction("Durum: 0 soru", self._menu)
        self._durum.setEnabled(False)
        self._menu.addAction(self._durum)
        self._menu.addSeparator()

        self._sil = QAction("Son soruyu sil", self._menu)
        self._sil.triggered.connect(self.son_soru_sil.emit)
        self._menu.addAction(self._sil)

        self._yeniden = QAction("Son soruyu yeniden çek", self._menu)
        self._yeniden.triggered.connect(self.yeniden_cekm.emit)
        self._menu.addAction(self._yeniden)

        self._menu.addSeparator()
        self._bitir = QAction("Yakalamayı bitir", self._menu)
        self._bitir.triggered.connect(self.bitir.emit)
        self._menu.addAction(self._bitir)

        self._goster = QAction("Pencereyi göster", self._menu)
        self._goster.triggered.connect(self.goster.emit)
        self._menu.addAction(self._goster)

        self._cikis = QAction("Çıkış", self._menu)
        self._cikis.triggered.connect(self.cikis.emit)
        self._menu.addAction(self._cikis)

    def desteklenir(self) -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    def ac(self) -> None:
        self._tray.show()

    def gizle(self) -> None:
        self._tray.hide()

    # --------------------------- durum ---------------------------
    def set_soru_adedi(self, n: int) -> None:
        self._soru_adedi = int(n)
        self._durum.setText(f"Durum: {self._soru_adedi} soru")
        self._tray.setToolTip(f"Test PDF Üretici — {self._soru_adedi} soru")

    def mesaj(self, baslik: str, metin: str, ms: int = 4000) -> None:
        self._tray.showMessage(baslik, metin, self._icon, ms)

    def _cift_tik(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:  # sol tık: pencereyi göster
            self.goster.emit()
