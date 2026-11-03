"""Yeni PDF penceresi (Adım 3).

Sol form   : PDF ismi, Klasör, Şık sayısı (4/5), Tür (PDF/Word), "Oluştur".
Sağ Stil   : Sayfa tarzı (tek/iki), Ayraç (çizgi/yok), Soru boşluğu (kaydırıcı),
             Renk (vurgu seçici), Tarz (yazı tipi).
Önizleme   : bu adımda yer tutucu; canlı önizleme Adım 7'de eklenecek.

"Oluştur"a basınca:
  - alanlar doğrulanır, stil sözlüğü hazırlanır,
  - proje veritabanına kaydedilir (dialog.proje_id dolu olur),
  - dialog Accepted ile kapanır.
Yakalama modu / tepsisi Adım 4-5'te bağlanacak.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.db import get_db
from app.ui import theme
from app.ui.style_preview import StylePreview

# Gösterim adı -> reportlab yazı tipi adı (Adım 6'da kullanılacak)
FONT_SECENEKLERI = {
    "Helvetica (Sade)": "Helvetica",
    "Times (Klasik)": "Times-Roman",
    "Courier (Daktilo)": "Courier",
}

# Ayraç ve sayfa tarzı için değer sözlükleri
SAYFA_TARZI = {"Tek sütun": "tek", "İki sütun": "iki"}
AYRAC = {"Çizgi": "cizgi", "Yok": "yok"}
SORU_ALTI = {"Yok": "yok", "Çizgi": "cizgi"}


class NewPdfDialog(QDialog):
    def __init__(self, parent=None, varsayilan_klasor: Optional[int] = None):
        super().__init__(parent)
        self.setWindowTitle("Yeni PDF")
        self.resize(760, 520)
        self.db = get_db()
        self.proje_id: Optional[int] = None
        self._varsayilan_klasor = varsayilan_klasor
        self._renk = theme.ACCENT

        govde = QHBoxLayout(self)
        govde.setContentsMargins(18, 18, 18, 18)
        govde.setSpacing(18)

        govde.addWidget(self._form_panel(), 1)
        govde.addWidget(self._stil_panel(), 1)

    # --------------------------- sol form ---------------------------
    def _form_panel(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        baslik = QLabel("Proje bilgileri")
        baslik.setObjectName("CardTitle")
        lay.addWidget(baslik)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.ed_isim = QLineEdit()
        self.ed_isim.setPlaceholderText("Örn. TYT Deneme 1")
        form.addRow("PDF ismi:", self.ed_isim)

        self.cb_klasor = QComboBox()
        self.cb_klasor.addItem("(Klasörsüz)", None)
        for k in self.db.klasor_liste():
            self.cb_klasor.addItem(k["ad"], k["id"])
        # ana ekrandaki seçili klasörü öncel seç (varsa)
        if self._varsayilan_klasor is not None:
            idx = self.cb_klasor.findData(self._varsayilan_klasor)
            if idx >= 0:
                self.cb_klasor.setCurrentIndex(idx)
        form.addRow("Klasör:", self.cb_klasor)

        self.cb_sik = QComboBox()
        self.cb_sik.addItem("4 şık (A–D)", 4)
        self.cb_sik.addItem("5 şık (A–E)", 5)
        form.addRow("Şık sayısı:", self.cb_sik)

        self.cb_tur = QComboBox()
        self.cb_tur.addItem("PDF", "pdf")
        self.cb_tur.addItem("Word", "word")
        form.addRow("Tür:", self.cb_tur)

        # varsayılanları ayarlardan uygula
        from app.core import settings
        sik = int(settings.get("varsayilan_sik_sayisi", 4))
        self.cb_sik.setCurrentIndex(0 if sik == 4 else 1)
        tur = settings.get("varsayilan_tur", "pdf")
        self.cb_tur.setCurrentIndex(0 if tur == "pdf" else 1)

        lay.addLayout(form)
        lay.addStretch(1)
        return w

    # --------------------------- sağ stil ---------------------------
    def _stil_panel(self) -> QWidget:
        grup = QGroupBox("Stil")
        lay = QVBoxLayout(grup)
        lay.setSpacing(12)

        # Sayfa tarzı
        self.cb_sayfa = QComboBox()
        for ad, val in SAYFA_TARZI.items():
            self.cb_sayfa.addItem(ad, val)
        lay.addWidget(QLabel("Sayfa tarzı:"))
        lay.addWidget(self.cb_sayfa)

        # Ayraç
        self.cb_ayrac = QComboBox()
        for ad, val in AYRAC.items():
            self.cb_ayrac.addItem(ad, val)
        lay.addWidget(QLabel("Sütun ayracı:"))
        lay.addWidget(self.cb_ayrac)

        # Soru altı çizgisi
        self.cb_soru_alti = QComboBox()
        for ad, val in SORU_ALTI.items():
            self.cb_soru_alti.addItem(ad, val)
        lay.addWidget(QLabel("Soru altı çizgisi:"))
        lay.addWidget(self.cb_soru_alti)

        # Soru boşluğu kaydırıcı
        self.sl_bosluk = QSlider(Qt.Horizontal)
        self.sl_bosluk.setRange(0, 80)
        self.sl_bosluk.setValue(24)
        self.lbl_bosluk = QLabel("24")
        self.sl_bosluk.valueChanged.connect(lambda v: self.lbl_bosluk.setText(str(v)))
        bosluk_row = QHBoxLayout()
        bosluk_row.addWidget(self.sl_bosluk, 1)
        bosluk_row.addWidget(self.lbl_bosluk)
        lay.addWidget(QLabel("Soru boşluğu:"))
        lay.addLayout(bosluk_row)

        # Renk seçici
        renk_row = QHBoxLayout()
        self.btn_renk = QPushButton()
        self.btn_renk.setFixedSize(56, 40)
        self.btn_renk.setCursor(Qt.PointingHandCursor)
        self.btn_renk.clicked.connect(self._renk_sec)
        renk_row.addWidget(self.btn_renk)
        self.lbl_renk = QLabel(theme.ACCENT)
        renk_row.addWidget(self.lbl_renk, 1)
        lay.addWidget(QLabel("Vurgu rengi:"))
        lay.addLayout(renk_row)
        self._renk_guncelle()

        # Tarz (yazı tipi)
        self.cb_font = QComboBox()
        for ad in FONT_SECENEKLERI:
            self.cb_font.addItem(ad)
        lay.addWidget(QLabel("Tarz (yazı tipi):"))
        lay.addWidget(self.cb_font)

        # Önizleme (Adım 7: canlı)
        self.prev = StylePreview()
        lay.addWidget(QLabel("Önizle:"))
        lay.addWidget(self.prev)

        lay.addStretch(1)

        # stiller değişince önizlemeyi tazele
        self.cb_sayfa.currentIndexChanged.connect(self._onizleme_tazele)
        self.cb_ayrac.currentIndexChanged.connect(self._onizleme_tazele)
        self.cb_soru_alti.currentIndexChanged.connect(self._onizleme_tazele)
        self.cb_font.currentIndexChanged.connect(self._onizleme_tazele)
        self.sl_bosluk.valueChanged.connect(lambda *_: self._onizleme_tazele())
        self._onizleme_tazele()

        # butonlar
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok = btn.button(QDialogButtonBox.Ok)
        ok.setText("Oluştur")
        ok.setObjectName("Primary")
        btn.button(QDialogButtonBox.Cancel).setText("İptal")
        btn.accepted.connect(self.olustur)
        btn.rejected.connect(self.reject)
        lay.addWidget(btn)
        return grup

    # --------------------------- renk ---------------------------
    def _renk_sec(self) -> None:
        c = QColorDialog_get(self._renk)
        if c is not None:
            self._renk = c
            self.lbl_renk.setText(c)
            self._renk_guncelle()
            self._onizleme_tazele()

    def _onizleme_tazele(self) -> None:
        if hasattr(self, "prev"):
            self.prev.set_stil(self.stil_topla())

    def _renk_guncelle(self) -> None:
        self.btn_renk.setStyleSheet(
            f"background:{self._renk}; border:1px solid {theme.BORDER}; border-radius:8px;"
        )

    # --------------------------- kaydet ---------------------------
    def stil_topla(self) -> dict[str, Any]:
        return self.db.varsayilan_stil(
            sayfa_tarzi=self.cb_sayfa.currentData(),
            ayrac=self.cb_ayrac.currentData(),
            soru_alti_cizgi=self.cb_soru_alti.currentData(),
            soru_boslugu=self.sl_bosluk.value(),
            renk=self._renk,
            font=FONT_SECENEKLERI[self.cb_font.currentText()],
        )

    def olustur(self) -> None:
        isim = self.ed_isim.text().strip() or "Adsız Proje"
        klasor_id = self.cb_klasor.currentData()
        sik = self.cb_sik.currentData()
        tur = self.cb_tur.currentData()
        stil = self.stil_topla()
        try:
            self.proje_id = self.db.proje_olustur(
                isim, klasor_id=klasor_id, sik_sayisi=sik, tur=tur, stil=stil
            )
        except ValueError as e:
            QMessageBox.warning(self, "Hata", str(e))
            return
        self.accept()


def QColorDialog_get(mevcut: str) -> Optional[str]:
    """QColorDialog ile hex renk seçer; iptal edilirse None."""
    from PySide6.QtWidgets import QColorDialog

    c = QColorDialog.getColor(QColor(mevcut), None, "Vurgu rengi seç")
    if c.isValid():
        return c.name()
    return None
