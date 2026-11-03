"""Proje kartı: kapak önizlemesi + ad + soru sayısı.

Karta sol tıklayınca `tiklandi(proje_id)` sinyali yayınlanır. Sağ tık için
contextMenuPolicy Custom ayarlanmıştır; menüyü ana ekran yönetir.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)

from app.core import paths


class ProjectCard(QFrame):
    tiklandi = Signal(int)  # proje_id

    def __init__(self, proje, parent=None):
        super().__init__(parent)
        self.proje_id = int(proje["id"])
        self.proje = proje
        self.setObjectName("ProjectCard")
        self.setFixedSize(220, 220)
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # --- kapak önizlemesi ---
        self.cover = QLabel("PDF")
        self.cover.setObjectName("Cover")
        self.cover.setAlignment(Qt.AlignCenter)
        self.cover.setFixedSize(196, 130)
        self._load_cover()
        lay.addWidget(self.cover)

        # --- ad ---
        title = QLabel(self._elide(proje["ad"], 24))
        title.setObjectName("CardTitle")
        title.setToolTip(proje["ad"])
        lay.addWidget(title)

        # --- meta: soru sayısı + tür ---
        tur = "PDF" if proje["tur"] == "pdf" else "Word"
        meta = QLabel(f"{proje['soru_adedi']} soru  •  {tur}  •  {proje['sik_sayisi']} şık")
        meta.setObjectName("CardMeta")
        lay.addWidget(meta)

        lay.addStretch(1)

    def _load_cover(self):
        """İlk soru görseli varsa kapak olarak göster; yoksa tür etiketi kalır."""
        cover_path = self._first_image()
        if not cover_path:
            return
        pix = QPixmap(str(cover_path))
        if pix.isNull():
            return
        self.cover.setPixmap(
            pix.scaled(self.cover.size(), Qt.KeepAspectRatio,
                       Qt.SmoothTransformation)
        )
        self.cover.setText("")

    def _first_image(self) -> Path | None:
        from app.db import get_db
        rows = get_db().soru_liste(self.proje_id)
        if not rows:
            return None
        return paths.abs_from_base(rows[0]["gorsel_yolu"])

    @staticmethod
    def _elide(s: str, n: int) -> str:
        return s if len(s) <= n else s[: n - 1] + "…"

    def mouseReleaseEvent(self, event):  # noqa: N802 (Qt naming)
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.tiklandi.emit(self.proje_id)
        super().mouseReleaseEvent(event)
