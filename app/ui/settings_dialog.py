"""Ayarlar penceresi (Adım 8).

Düzenlenebilir:
  - Global yakalama kısayolu (örn. "Ctrl+Shift+S")
  - PDF/Word çıktı klasörü (kök); uygulama klasörleri bu kök altında açılır
Değerler data/ayarlar.json içine kalıcı yazılır. Sinyaller: kaydedildi(str kısayol),
cikti_degisti(str yol).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core import settings
from app.core.hotkey import DEFAULT_HOTKEY_GORUNUM

_MODIFIERS = {"ctrl", "alt", "shift", "win", "cmd", "meta"}


def gecerli_mi(kombinasyon: str) -> bool:
    """En az bir değiştirici + bir tuç içermeli; '+' ile ayrılmış olmalı."""
    if "<" in kombinasyon:
        return True
    parcalar = [p.strip().lower() for p in kombinasyon.split("+") if p.strip()]
    if len(parcalar) < 2:
        return False
    mod = [p for p in parcalar if p in _MODIFIERS]
    diger = [p for p in parcalar if p not in _MODIFIERS]
    return bool(mod) and bool(diger) and len(diger) == 1


class SettingsDialog(QDialog):
    kaydedildi = Signal(str)   # yeni kısayol (görünüm)
    cikti_degisti = Signal(str)  # yeni çıktı kök klasörü

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.resize(460, 260)
        self.ayarlar = settings.yukle()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        form = QFormLayout()
        self.ed_hotkey = QLineEdit(self.ayarlar.get("hotkey", DEFAULT_HOTKEY_GORUNUM))
        self.ed_hotkey.setPlaceholderText("Örn. Ctrl+Shift+S")
        form.addRow("Yakalama kısayolu:", self.ed_hotkey)

        # çıktı klasörü satırı (alan + Seç... düğmesi)
        cikti_w = QWidget()
        cikti_l = QHBoxLayout(cikti_w)
        cikti_l.setContentsMargins(0, 0, 0, 0)
        cikti_l.setSpacing(6)
        self.ed_cikti = QLineEdit(self.ayarlar.get("cikti_klasoru", ""))
        self.ed_cikti.setPlaceholderText("PDF/Word kaydedilecek kök klasör")
        self.btn_sec = QPushButton("Seç…")
        self.btn_sec.setCursor(Qt.PointingHandCursor)
        self.btn_sec.clicked.connect(self._klasor_sec)
        cikti_l.addWidget(self.ed_cikti, 1)
        cikti_l.addWidget(self.btn_sec)
        form.addRow("Çıktı klasörü:", cikti_w)

        lay.addLayout(form)

        ipucu = QLabel(
            "Kısayol biçimi: Ctrl / Alt / Shift / Win + bir tuş.\n"
            "Uygulama klasörleri (TYT, AYT…) seçtiğin çıktı kökü altında oluşturulur."
        )
        ipucu.setObjectName("CardMeta")
        ipucu.setWordWrap(True)
        lay.addWidget(ipucu)

        btnlar = QHBoxLayout()
        varsayilan = QPushButton("Kısayolu varsayılana döndür")
        varsayilan.setCursor(Qt.PointingHandCursor)
        varsayilan.clicked.connect(
            lambda: self.ed_hotkey.setText(DEFAULT_HOTKEY_GORUNUM)
        )
        btnlar.addWidget(varsayilan)
        btnlar.addStretch(1)
        lay.addLayout(btnlar)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Kaydet")
        bb.button(QDialogButtonBox.Ok).setObjectName("Primary")
        bb.button(QDialogButtonBox.Cancel).setText("İptal")
        bb.accepted.connect(self._kaydet)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def _klasor_sec(self) -> None:
        baslangic = self.ed_cikti.text().strip()
        yol = QFileDialog.getExistingDirectory(
            self, "Çıktı klasörünü seç", baslangic
        )
        if yol:
            self.ed_cikti.setText(yol)

    def _kaydet(self) -> None:
        deger = self.ed_hotkey.text().strip()
        if not gecerli_mi(deger):
            QMessageBox.warning(
                self, "Geçersiz kısayol",
                "En az bir değiştirici (Ctrl/Alt/Shift/Win) ve bir tuş girin.\n"
                "Örnek: Ctrl+Shift+S",
            )
            return
        cikti = self.ed_cikti.text().strip()
        settings.kaydet({"hotkey": deger, "cikti_klasoru": cikti})
        self.kaydedildi.emit(deger)
        self.cikti_degisti.emit(cikti)
        self.accept()
