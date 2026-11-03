"""Ana ekran (Adım 2).

Düzen:
  Sol panel : profil (avatar + isim) + "+ Yeni PDF" butonu (+ ipucu alt bilgi)
  Sağ üst   : klasör sekmeleri (Tümü + klasörler, + Klasör, sağ tık ile sil)
  Sağ içerik: seçili klasördeki proje kartlarının ızgarası
Karta sol tık -> proje açılır; sağ tık -> yeniden adlandır / taşı / sil / tekrar dışa aktar.

Bu adım arayüz ve klasör/proje CRUD'unu bağlar; "Yeni PDF" penceresi Adım 3,
açılınca başlayan yakalama Adım 4-5, dışa aktarma Adım 6'da gelir.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.db import get_db
from app.ui.widgets.folder_tabs import FolderTabs
from app.ui.widgets.project_card import ProjectCard

CARD_W = 220
CARD_H = 220
GAP = 18


class MainWindow(QWidget):
    yeni_pdf_istegi = Signal()          # (geriye uyum; dialog burada açılır)
    proje_acildi = Signal(int)          # proje_id (Adım 4-5 yakalama)
    proje_olusturuldu = Signal(int)     # yeni kaydedilen proje_id
    ayarlar_kaydedildi = Signal(str)    # değişen kısayol (görünüm)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test PDF Üretici")
        self.resize(1120, 720)
        self.db = get_db()
        self._secili_klasor: Optional[int] = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._sol_panel(), 0)

        sag = QVBoxLayout()
        sag.setContentsMargins(0, 0, 0, 0)
        sag.setSpacing(0)
        self.tabs = FolderTabs()
        sag.addWidget(self.tabs)
        sag.addWidget(self._grid_area(), 1)

        sag_wrap = QWidget()
        sag_wrap.setLayout(sag)
        root.addWidget(sag_wrap, 1)

        # sinyaller
        self.tabs.klasor_secildi.connect(self._klasor_secildi)
        self.tabs.klasor_ekle_istegi.connect(self._klasor_ekle)
        self.tabs.klasor_sil_istegi.connect(self._klasor_sil)

        self._yenile()

    # --------------------------- sol panel ---------------------------
    def _sol_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("LeftPanel")
        panel.setFixedWidth(260)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(20, 24, 20, 20)
        lay.setSpacing(14)

        baslik = QLabel("Test PDF Üretici")
        baslik.setObjectName("AppName")
        lay.addWidget(baslik)
        lay.addSpacing(10)

        self.avatar = QLabel("?")
        self.avatar.setObjectName("Avatar")
        self.avatar.setFixedSize(56, 56)
        self.avatar.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.avatar)

        self.profil_ad = QLabel("Yükleniyor…")
        self.profil_ad.setObjectName("ProfileName")
        self.profil_ad.setToolTip("Isme çift tıklayınca düzenle")
        self.profil_ad.setCursor(Qt.PointingHandCursor)
        self.profil_ad.installEventFilter(self)
        lay.addWidget(self.profil_ad)

        lay.addSpacing(6)
        self.btn_yeni = QPushButton("+ Yeni PDF")
        self.btn_yeni.setObjectName("Primary")
        self.btn_yeni.setCursor(Qt.PointingHandCursor)
        self.btn_yeni.clicked.connect(self._yeni_pdf_ac)
        lay.addWidget(self.btn_yeni)

        lay.addStretch(1)

        self.btn_ayarlar = QPushButton("⚙  Ayarlar")
        self.btn_ayarlar.setCursor(Qt.PointingHandCursor)
        self.btn_ayarlar.clicked.connect(self._ayarlar_ac)
        lay.addWidget(self.btn_ayarlar)

        ipucu = QLabel("İpucu: kartlara sağ tıklayarak yönetebilirsin.")
        ipucu.setObjectName("CardMeta")
        ipucu.setWordWrap(True)
        lay.addWidget(ipucu)

        self._profil_yenile()
        return panel

    def _profil_yenile(self) -> None:
        p = self.db.profil_getir()
        ad = p["ad"] if p else "Öğrenci"
        self.profil_ad.setText(ad)
        self.avatar.setText((ad[:1] or "?").upper())

    def _profil_duzenle(self, event=None) -> None:  # mouseDoubleClickEvent imzası
        p = self.db.profil_getir()
        mevcut = p["ad"] if p else ""
        ad, ok = QInputDialog.getText(self, "Profili düzenle", "İsim:", text=mevcut)
        if ok and ad.strip():
            self.db.profil_adi_set(ad.strip())
            self._profil_yenile()

    # --------------------------- kart ızgarası ---------------------------
    def _grid_area(self) -> QWidget:
        self._scroll = QScrollArea()
        self._scroll.setObjectName("ScrollArea")
        self._scroll.setWidgetResizable(True)
        self.grid_host = QWidget()
        self.grid_host.setObjectName("GridHost")
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(20, 12, 20, 20)
        self.grid.setSpacing(GAP)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._scroll.setWidget(self.grid_host)
        # yeniden akış için boyut değişikliğini dinle
        self._scroll.viewport().installEventFilter(self)
        return self._scroll

    def eventFilter(self, obj, event):  # noqa: N802
        scroll = getattr(self, "_scroll", None)
        if scroll is not None and obj is scroll.viewport() and event.type() == QEvent.Resize:
            self._yenile_izgara()
        if getattr(self, "profil_ad", None) is not None and obj is self.profil_ad \
                and event.type() == QEvent.MouseButtonDblClick:
            self._profil_duzenle()
            return True
        return super().eventFilter(obj, event)

    def _klasor_secildi(self, klasor_id: Optional[int]) -> None:
        self._secili_klasor = klasor_id
        self._yenile_izgara()

    # --------------------------- klasör ekle/sil ---------------------------
    def _klasor_ekle(self) -> None:
        ad, ok = QInputDialog.getText(self, "Yeni klasör", "Klasör adı:")
        if not ok or not ad.strip():
            return
        if self.db.klasor_var_mi(ad):
            QMessageBox.information(self, "MEVCUT", f"'{ad.strip()}' zaten var.")
            return
        self.db.klasor_ekle(ad.strip())
        # seçili çıktı kökü altında gerçek alt klasörü oluştur
        try:
            from app.export import dest
            dest.klasor_dizini_olustur(ad.strip())
        except OSError:
            pass
        self._yenile()

    def _klasor_sil(self, klasor_id: int, ad: str) -> None:
        if QMessageBox.question(
            self, "Klasörü sil",
            f"'{ad}' klasörü silinsin mi?\nİçindeki projeler silinmez, klasörsüz kalır.",
        ) != QMessageBox.Yes:
            return
        self.db.klasor_sil(klasor_id)
        if self._secili_klasor == klasor_id:
            self._secili_klasor = None
        self._yenile()

    # --------------------------- yeni PDF (Adım 3) ---------------------------
    def _yeni_pdf_ac(self) -> None:
        from app.ui.new_pdf_dialog import NewPdfDialog

        dlg = NewPdfDialog(self, varsayilan_klasor=self._secili_klasor)
        if dlg.exec() == NewPdfDialog.Accepted and dlg.proje_id:
            self._yenile()
            self.proje_olusturuldu.emit(int(dlg.proje_id))

    # --------------------------- ayarlar (Adım 8) ---------------------------
    def _ayarlar_ac(self) -> None:
        from app.ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog(self)
        dlg.kaydedildi.connect(self.ayarlar_kaydedildi.emit)
        dlg.cikti_degisti.connect(self._cikti_klasoru_degisti)
        dlg.exec()

    def _cikti_klasoru_degisti(self, yol: str) -> None:
        """Çıktı kökü değişince tüm klasörleri yeni kök altında oluşturur."""
        try:
            from app.export import dest
            dest.tum_klasorleri_olustur(self.db)
        except OSError:
            pass

    # --------------------------- kart etkileşimleri ---------------------------
    def _kart_tiklandi(self, proje_id: int) -> None:
        """Karta sol tık: üretilmiş dosya varsa aç, yoksa yakalamayı başlat."""
        dosya = self._uretilen_dosya(proje_id)
        if dosya is not None:
            self._dosya_karsa_ac(str(dosya))
        else:
            self.proje_acildi.emit(proje_id)

    def _uretilen_dosya(self, proje_id: int):
        from pathlib import Path

        from app.core import paths

        p = self.db.proje_getir(proje_id)
        if not p or not p["dosya_yolu"]:
            return None
        mutlak = paths.abs_from_base(p["dosya_yolu"])
        return mutlak if (mutlak and Path(mutlak).exists()) else None

    @staticmethod
    def _dosya_karsa_ac(yol: str) -> None:
        """Dosyayı varsayılan uygulamayla açar (Windows)."""
        import os

        try:
            if os.name == "nt":
                os.startfile(yol)
        except Exception:
            pass

    def _proje_getir(self, proje_id: int):
        return self.db.proje_getir(proje_id)

    def _proje_yeniden_adlandir(self, proje_id: int) -> None:
        p = self._proje_getir(proje_id)
        if not p:
            return
        ad, ok = QInputDialog.getText(self, "Yeniden adlandır", "Proje adı:", text=p["ad"])
        if ok and ad.strip():
            self.db.proje_yeniden_adlandir(proje_id, ad.strip())
            self._yenile_izgara()

    def _proje_tasi(self, proje_id: int) -> None:
        klasorler = self.db.klasor_liste()
        adlar = ["(Klasörsüz)"] + [k["ad"] for k in klasorler]
        secenek, ok = QInputDialog.getItem(
            self, "Klasöre taşı", "Hedef klasör:", adlar, 0, False
        )
        if not ok:
            return
        hedef = None if secenek == "(Klasörsüz)" else next(
            k["id"] for k in klasorler if k["ad"] == secenek
        )
        self.db.proje_tasi(proje_id, hedef)
        self._yenile_izgara()

    def _tekrar_disa(self, proje_id: int) -> None:
        try:
            yol = self.disa_aktar(proje_id)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Dışa aktarma hatası", str(e))
            return
        self._yenile_izgara()
        self.dosya_ac(yol)
        tur = "Word" if yol.lower().endswith(".docx") else "PDF"
        QMessageBox.information(self, "Hazır", f"{tur} üretildi:\n{yol}")

    def disa_aktar(self, proje_id: int) -> str:
        """Proje türüne göre dosya üretir, yolunu döndürür (PDF: Adım 6, Word: Adım 7)."""
        p = self.db.proje_getir(proje_id)
        if not p:
            raise ValueError("Proje bulunamadı")
        if self.db.soru_adet(proje_id) == 0:
            raise ValueError("Yakalanmış soru yok; önce soru ekleyin.")
        if p["tur"] == "pdf":
            from app.export.pdf_exporter import export_project_pdf
            return export_project_pdf(proje_id, self.db)
        from app.export.word_exporter import export_project_word
        return export_project_word(proje_id, self.db)

    @staticmethod
    def dosya_ac(yol: str) -> None:
        """Üretilen dosyayı Windows'ta klasöründe seçili gösterir."""
        import os
        import subprocess
        from pathlib import Path

        try:
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", str(Path(yol))])
        except Exception:
            pass

    def _proje_sil(self, proje_id: int) -> None:
        p = self._proje_getir(proje_id)
        if not p:
            return
        if QMessageBox.question(
            self, "Projeyi sil",
            f"'{p['ad']}' projesi ve {self.db.soru_adet(proje_id)} sorusu silinsin mi?",
        ) != QMessageBox.Yes:
            return
        self.db.proje_sil(proje_id)
        self._yenile_izgara()

    # --------------------------- yenileme ---------------------------
    def _yenile(self) -> None:
        self._profil_yenile()
        klasorler = [(k["id"], k["ad"]) for k in self.db.klasor_liste()]
        self.tabs.yenile(klasorler, self._secili_klasor)
        self._yenile_izgara()

    def _yenile_izgara(self) -> None:
        # mevcut kartları temizle
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w is not None:
                w.deleteLater()
        projeler = self.db.proje_liste(self._secili_klasor)
        if not projeler:
            bos = QLabel("Henüz proje yok. Sol paneldeki \"+ Yeni PDF\" ile başla.")
            bos.setObjectName("CardMeta")
            self.grid.addWidget(bos, 0, 0, Qt.AlignTop | Qt.AlignLeft)
            return
        cols = self._kolon_sayisi()
        for i, proje in enumerate(projeler):
            card = ProjectCard(proje)
            card.tiklandi.connect(self._kart_tiklandi)
            card.customContextMenuRequested.connect(
                lambda pos, pid=proje["id"], c=card: self._sag_menu(pos, pid, c)
            )
            self.grid.addWidget(card, i // cols, i % cols)
            card.show()

    def _sag_menu(self, pos, proje_id: int, kart: ProjectCard) -> None:
        menu = QMenu(self)
        eylemler = [
            ("Yakalamayı başlat", lambda: self.proje_acildi.emit(proje_id)),
            ("Yeniden adlandır", lambda: self._proje_yeniden_adlandir(proje_id)),
            ("Taşı", lambda: self._proje_tasi(proje_id)),
            ("Tekrar dışa aktar", lambda: self._tekrar_disa(proje_id)),
        ]
        dosya = self._uretilen_dosya(proje_id)
        if dosya is not None:
            eylemler.insert(0, ("Dosyayı aç", lambda: self._dosya_karsa_ac(str(dosya))))
        for metin, fn in eylemler:
            act = QAction(metin, menu)
            act.triggered.connect(fn)
            menu.addAction(act)
        menu.addSeparator()
        sil = QAction("Sil", menu)
        sil.triggered.connect(lambda: self._proje_sil(proje_id))
        menu.addAction(sil)
        menu.exec(kart.mapToGlobal(pos))

    def _kolon_sayisi(self) -> int:
        gen = self._scroll.viewport().width() - 40
        if gen <= 0:
            gen = 820
        return max(1, int(gen // (CARD_W + GAP)))
