"""Hata yönetimi ve günlükleme (Adım 8).

- logging: data/logs/uygulama.log (dönmeli, 1 MB x 3)
- install_excepthook(): yakalanmayan hataları loglar ve (Qt varsa) kullanıcıya
  anlaşılır bir mesaj gösterir; program çökmeden çalışmaya devam edebilir.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core import paths

LOG_DIR = paths.DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "uygulama.log"
_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _logger = logging.getLogger("test_pdf_uretici")
    _logger.setLevel(logging.INFO)
    if not _logger.handlers:
        fh = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000,
                                 backupCount=3, encoding="utf-8")
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        _logger.addHandler(fh)
    return _logger


def install_excepthook(show_dialog: bool = True) -> None:
    """Yakalanmayan istisnalar için global hook kurar."""
    log = get_logger()

    def _hook(exc_type, exc, tb):
        import traceback

        metin = "".join(traceback.format_exception(exc_type, exc, tb))
        log.error("Yakalanmayan hata:\n%s", metin)
        if show_dialog:
            try:
                from PySide6.QtWidgets import QApplication, QMessageBox

                if QApplication.instance() is not None:
                    QMessageBox.critical(
                        None, "Beklenmeyen hata",
                        "Bir sorun oluştu ama program devam ediyor.\n"
                        f"Ayrıntı log dosyasında:\n{LOG_FILE}",
                    )
                    return
            except Exception:
                pass
        # konsola da yaz
        sys.stderr.write(metin)

    sys.excepthook = _hook
