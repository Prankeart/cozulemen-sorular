"""Global kısayol dinleyicisi (pynput).

Varsayılan: Ctrl+Shift+S. pynput Listener kendi thread'inde çalışır; tetiklenme
Qt ana thread'ine bir sinyal (kuyruklu bağlantı) ile iletilir. Böylece arayüz ve
yakalama güvenle ana thread'de yürür.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal

DEFAULT_HOTKEY = "<ctrl>+<shift>+s"
DEFAULT_HOTKEY_GORUNUM = "Ctrl+Shift+S"

# kullanıcıya gösterilen/girilen ad -> pynput biçimi
_MOD = {
    "ctrl": "<ctrl>", "alt": "<alt>", "shift": "<shift>",
    "win": "<cmd>", "meta": "<cmd>", "cmd": "<cmd>",
}


def normalize(kombinasyon: str) -> str:
    """'Ctrl+Shift+S' -> '<ctrl>+<shift>+s'."""
    if not kombinasyon:
        return DEFAULT_HOTKEY
    k = kombinasyon.strip()
    if "<" in k:  # zaten pynput biçimi
        return k
    parcalar = [p.strip() for p in k.split("+") if p.strip()]
    out = []
    for p in parcalar:
        alt = p.lower()
        out.append(_MOD.get(alt, alt))
    return "+".join(out)


class HotkeyManager(QObject):
    tetiklendi = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._listener = None
        self._kombinasyon = DEFAULT_HOTKEY

    @property
    def kombinasyon(self) -> str:
        return self._kombinasyon

    def start(self, kombinasyon: str = DEFAULT_HOTKEY,
              handler: Optional[Callable[[], None]] = None) -> bool:
        """Küresel kısayolu dinlemeye başlar. hata olursa False."""
        self.stop()
        self._kombinasyon = normalize(kombinasyon)
        try:
            from pynput import keyboard
        except Exception:
            return False
        callback = handler if handler else self.tetiklendi.emit
        try:
            self._listener = keyboard.GlobalHotKeys(
                {self._kombinasyon: callback}
            )
            self._listener.daemon = True
            self._listener.start()
            return True
        except Exception:
            self._listener = None
            return False

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
