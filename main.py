"""Test PDF Üretici - giriş noktası.

Adım 5: yakalama modu uçtan uca bağlıdır. Proje oluşturulunca/açılınca pencere
arka plana alınır, sistem tepsisi görünür; Ctrl+Shift+S ile soru yakalanır, şık
işaretlenir ve veritabanına kaydedilir. Tepsiden soru yönetimi ve "bitir".
Dışa aktarma Adım 6'da `mod_bitti` sinyatine bağlanacak.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox


def run() -> int:
    from app.core.capture_controller import CaptureController
    from app.core.errors import get_logger, install_excepthook
    from app.db import get_db
    from app.ui.main_window import MainWindow
    from app.ui.theme import build_qss
    from app.ui.tray import TrayController

    install_excepthook()
    log = get_logger()
    log.info("Uygulama başlatıldı")

    app = QApplication(sys.argv)
    app.setApplicationName("Test PDF Üretici")
    app.setStyleSheet(build_qss())

    db = get_db()
    # seçili çıktı kökü altında uygulama klasörlerini hazırla
    try:
        from app.export import dest
        dest.tum_klasorleri_olustur(db)
    except OSError:
        pass
    pencere = MainWindow()
    controller = CaptureController()
    tray = TrayController()
    # tepsi varsa pencere kapanınca uygulama tepside devam etsin
    app.setQuitOnLastWindowClosed(not tray.desteklenir())

    controller.set_window(pencere)
    controller.set_tray(tray)

    def _uyari(baslik: str, metin: str):
        QMessageBox.warning(pencere, baslik, metin)

    def _mod_bitti(proje_id: int):
        p = db.proje_getir(proje_id)
        n = db.soru_adet(proje_id) if p else 0
        if p is None or n == 0:
            QMessageBox.information(
                pencere, "Bitti", "Yakalanan soru yok. Dosya üretilmedi."
            )
            return
        try:
            yol = pencere.disa_aktar(proje_id)
            tur = "Word" if yol.lower().endswith(".docx") else "PDF"
            QMessageBox.information(
                pencere, f"{tur} hazır",
                f"{n} soru + cevap anahtarı {tur} olarak üretildi:\n{yol}",
            )
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(pencere, "Üretim hatası", str(e))

    controller.uyari.connect(_uyari)
    controller.mod_bitti.connect(_mod_bitti)
    tray.cikis.connect(app.quit)

    def _ayar_guncelle(kombinasyon: str):
        controller.guncelle_kisayol(kombinasyon)
        log.info("Kısayol güncellendi: %s", kombinasyon)

    pencere.ayarlar_kaydedildi.connect(_ayar_guncelle)

    pencere.proje_acildi.connect(controller.basla)
    pencere.proje_olusturuldu.connect(controller.basla)

    if not tray.desteklenir():
        controller.uyari.emit(
            "Tepsi", "Sistem tepsisi kullanılamıyor; pencere görünür kalacak."
        )

    def _temiz():
        controller.durdur()
        tray.gizle()

    app.aboutToQuit.connect(_temiz)

    pencere.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
