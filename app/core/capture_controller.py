"""Yakalama modunu yöneten koordinatör (Adım 4 + Adım 5).

Akış:
  basla(proje_id): pencere gizlenir, tepsisi görünür, kısayol dinlenir.
  kısayol (Ctrl+Shift+S): ekran yakalanır -> seçim katmanı -> kırpılan görsel.
  seçim bitince: sağ altta şık menüsü (A–E + Kaydet ve kapat) açılır.
  kaydet: görsel data/gorseller altına yazılır, veritabanına soru eklenir
          (proje_id, soru_no otomatik, görsel_yolu, doğru_şık); tepsi sayacı artar.
  tepsi: son soruyu sil / yeniden çek / yakalamayı bitir / pencereyi göster.

Adım 6 dışa aktarmayı `mod_bitti` sinyatine bağlayacak.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from app.core import paths
from app.core import settings
from app.core.capture import grab_screen, pil_to_bytes
from app.core.hotkey import DEFAULT_HOTKEY, HotkeyManager
from app.db import get_db


class CaptureController(QObject):
    # (geriye uyum: Adım 4 sinyali)
    bolge_hazir = Signal(object)
    soru_kaydedildi = Signal(int)      # soru_no
    sayi_degisti = Signal(int)         # toplam soru adedi
    mod_basdi = Signal(int)            # proje_id
    mod_bitti = Signal(int)            # proje_id (dışa aktarma buradan tetiklenir)
    uyari = Signal(str, str)           # (başlık, mesaj)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.db = get_db()
        self.hotkey = HotkeyManager(self)
        self.hotkey.tetiklendi.connect(self._kisayol_tetiklendi)

        self._overlay = None
        self._menu = None
        self._aktif = False
        self.proje_id: Optional[int] = None
        self.proje_adi: str = ""
        self.sik_sayisi = 4
        self.pencere = None        # MainWindow (referans)
        self.tray = None           # TrayController (referans)
        self.panel = None          # FloatingPanel (yüzen kontrol çubuğu)

    # --------------------------- yapılandırma ---------------------------
    def set_window(self, pencere) -> None:
        self.pencere = pencere

    def set_tray(self, tray) -> None:
        self.tray = tray
        tray.son_soru_sil.connect(self._tray_son_sil)
        tray.yeniden_cekm.connect(self._tray_yeniden_cekm)
        tray.bitir.connect(self._tray_bitir)
        tray.goster.connect(self._pencere_goster)

    # --------------------------- durum ---------------------------
    @property
    def aktif(self) -> bool:
        return self._aktif

    def basla(self, proje_id: Optional[int] = None,
              kombinasyon: Optional[str] = None) -> bool:
        self.proje_id = proje_id
        if proje_id is not None:
            p = self.db.proje_getir(proje_id)
            self.sik_sayisi = int(p["sik_sayisi"]) if p else 4
            self.proje_adi = p["ad"] if p else ""
        # kısayol: açıkça verilmediyse ayarlardan okunur
        if kombinasyon is None:
            kombinasyon = settings.get("hotkey", DEFAULT_HOTKEY)
        ok = self.hotkey.start(kombinasyon)
        self._set_aktif(True)

        # pencereyi arka plana al, tepsiyi göster
        if self.pencere is not None:
            self.pencere.hide()
        if self.tray is not None:
            self.tray.ac()
            self.tray.mesaj("Yakalama modu",
                            "Yakala düğmesi veya kısayolla soru alanını seç.")
        # yüzen kontrol panelini göster
        self._panel_goster()
        self._sayi_guncelle()
        self.mod_basdi.emit(proje_id or -1)
        return ok

    def durdur(self) -> None:
        self.hotkey.stop()
        if self._overlay is not None:
            self._overlay.close()
            self._overlay = None
        if self._menu is not None:
            self._menu.close()
            self._menu = None
        self._panel_gizle()
        self._set_aktif(False)

    def guncelle_kisayol(self, kombinasyon: str) -> bool:
        """Kısayolu yeniden kurar (mod aktifse hemen dinler)."""
        if self._aktif:
            return self.hotkey.start(kombinasyon)
        return True

    def _set_aktif(self, deger: bool) -> None:
        self._aktif = deger

    # --------------------------- kısayol -> yakala ---------------------------
    def _kisayol_tetiklendi(self) -> None:
        if self._overlay is not None:
            return
        ekran = grab_screen()
        if ekran is None:
            self.uyari.emit("Hata", "Ekran görüntüsü alınamadı.")
            return
        self._show_overlay(ekran)

    def _show_overlay(self, ekran) -> None:
        from app.ui.selection_overlay import SelectionOverlay

        self._overlay = SelectionOverlay(ekran)
        self._overlay.tamamlandi.connect(self._secim_bitti)
        self._overlay.iptal.connect(self._secim_iptal)
        self._overlay.destroyed.connect(lambda: setattr(self, "_overlay", None))
        self._overlay.show()
        self._overlay.activateWindow()
        self._overlay.raise_()

    # --------------------------- seçim -> şık menüsü ---------------------------
    def _secim_bitti(self, crop) -> None:
        self._overlay = None
        self.bolge_hazir.emit(crop)
        self._menuyu_ac(crop)

    def _secim_iptal(self) -> None:
        self._overlay = None

    def _menuyu_ac(self, crop) -> None:
        from PySide6.QtWidgets import QApplication
        from app.ui.option_menu import OptionMenu, sag_alt_konum

        if self.proje_id is None:
            return
        soru_no = self.db.soru_siradaki_no(self.proje_id)
        menu = OptionMenu(sik_sayisi=self.sik_sayisi, soru_no=soru_no)
        menu.kaydet.connect(lambda sik, c=crop, n=soru_no: self._kaydet(c, sik, n))
        menu.iptal.connect(lambda: self._menu_kapat())
        menu.destroyed.connect(lambda: setattr(self, "_menu", None))
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else None
        menu.show()
        if geo is not None:
            sag_alt_konum(menu, geo)
        menu.activateWindow()
        self._menu = menu

    def _menu_kapat(self) -> None:
        self._menu = None

    # --------------------------- kayıt ---------------------------
    def _kaydet(self, crop, sik: str, soru_no: int) -> None:
        if self.proje_id is None:
            return
        yol = paths.image_path(self.proje_id, soru_no)
        yol.write_bytes(pil_to_bytes(crop, "PNG"))
        try:
            self.db.soru_ekle(self.proje_id, str(yol), sik, soru_no=soru_no)
        except ValueError as e:
            self.uyari.emit("Kayıt hatası", str(e))
            return
        self._menu = None
        self.soru_kaydedildi.emit(soru_no)
        self._sayi_guncelle()
        if self.tray is not None:
            self.tray.mesaj("Kaydedildi", f"Soru {soru_no} → {sik}")

    def _sayi_guncelle(self) -> None:
        n = self.db.soru_adet(self.proje_id) if self.proje_id else 0
        if self.tray is not None:
            self.tray.set_soru_adedi(n)
        if self.panel is not None:
            self.panel.set_bilgi(self.proje_adi, n)
        self.sayi_degisti.emit(n)

    # --------------------------- tepsi eylemleri ---------------------------
    def _tray_son_sil(self) -> None:
        if self.proje_id is None:
            return
        silinen = self.db.soru_son_sil(self.proje_id)
        if silinen is not None:
            self._dosya_sil(silinen["gorsel_yolu"])
        self._sayi_guncelle()

    def _tray_yeniden_cekm(self) -> None:
        if self.proje_id is None:
            return
        silinen = self.db.soru_son_sil(self.proje_id)
        if silinen is not None:
            self._dosya_sil(silinen["gorsel_yolu"])
        self._sayi_guncelle()
        # hemen yeniden yakala
        self._kisayol_tetiklendi()

    def _tray_bitir(self) -> None:
        pid = self.proje_id
        self.durdur()
        self._pencere_goster()
        if self.tray is not None:
            self.tray.gizle()
        if pid is not None:
            self.mod_bitti.emit(pid)

    def _pencere_goster(self) -> None:
        if self.pencere is not None:
            self.pencere.show()
            self.pencere.activateWindow()
            self.pencere.raise_()

    # --------------------------- yüzen panel ---------------------------
    def _panel_goster(self) -> None:
        from PySide6.QtWidgets import QApplication
        from app.ui.floating_panel import FloatingPanel

        if self.panel is None:
            self.panel = FloatingPanel()
            self.panel.yakala_istegi.connect(self._kisayol_tetiklendi)
            self.panel.ayarlar_istegi.connect(self._panel_ayarlar)
            self.panel.ana_menu_istegi.connect(self._pencere_goster)
            self.panel.bitir_istegi.connect(self._tray_bitir)
        self.panel.set_bilgi(self.proje_adi, self.db.soru_adet(self.proje_id)
                             if self.proje_id else 0)
        self.panel.show()
        screen = QApplication.primaryScreen()
        if screen is not None:
            self.panel.sag_ust_yerlestir(screen.availableGeometry())
        self.panel.raise_()

    def _panel_gizle(self) -> None:
        if self.panel is not None:
            self.panel.close()
            self.panel = None

    def _panel_ayarlar(self) -> None:
        """Paneldeki ⚙: ayarlar penceresini açar; kaydedilince kısayolu yeniler."""
        from app.ui.settings_dialog import SettingsDialog

        dlg = SettingsDialog()
        dlg.kaydedildi.connect(self.guncelle_kisayol)
        dlg.exec()

    @staticmethod
    def _dosya_sil(gorsel_yolu: str) -> None:
        p = paths.abs_from_base(gorsel_yolu)
        if p is not None:
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass
