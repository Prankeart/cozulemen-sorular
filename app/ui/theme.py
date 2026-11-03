"""Uygulama teması: renk paleti + QSS stil sayfası.

HTML tasarım referansından çıkarılan tokenlar:
  - sayfa arka planı: #faf9f5 (sıcak kırık beyaz)
  - modern, sade, açık renkli görünüm
  - buton yüksekliği en az 40 px
Arayüz metinleri Türkçe.
"""

from __future__ import annotations

# --------------------------- renk paleti ---------------------------
BG = "#faf9f5"           # pencere arka planı
SURFACE = "#ffffff"      # kart / panel yüzeyi
SURFACE_2 = "#f3f1ea"    # ikincil yüzey (hafif gri-bej)
BORDER = "#e6e2d8"       # ince çizgiler
TEXT = "#2b2b28"         # ana metin
TEXT_MUTED = "#8a877e"   # ikincil metin
ACCENT = "#2f6f4f"       # vurgu (yeşil) - varsayılan stil rengiyle uyumlu
ACCENT_HOVER = "#357f5a"
DANGER = "#b4423a"       # silme

MIN_BTN_H = 40           # px - kural: buton yüksekliği en az 40

FONT_FAMILY = "Segoe UI, Inter, 'Helvetica Neue', Arial, sans-serif"


def build_qss() -> str:
    """Tüm uygulamaya uygulanacak QSS metnini döndürür."""
    return f"""
* {{
    font-family: {FONT_FAMILY};
    font-size: 14px;
    color: {TEXT};
}}
QMainWindow, QWidget {{
    background: {BG};
}}

/* ---------- sol panel ---------- */
#LeftPanel {{
    background: {SURFACE};
    border-right: 1px solid {BORDER};
}}
#AppName {{
    font-size: 18px;
    font-weight: 700;
    color: {ACCENT};
}}
#ProfileName {{
    font-size: 15px;
    font-weight: 600;
}}
#Avatar {{
    background: {ACCENT};
    color: #ffffff;
    border-radius: 28px;
    font-size: 22px;
    font-weight: 700;
}}

/* ---------- butonlar ---------- */
QPushButton {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    min-height: {MIN_BTN_H}px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background: {SURFACE_2};
}}
QPushButton#Primary {{
    background: {ACCENT};
    color: #ffffff;
    border: none;
    font-weight: 600;
}}
QPushButton#Primary:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton:disabled {{
    color: {TEXT_MUTED};
    background: {SURFACE_2};
}}

/* ---------- klasör sekmeleri ---------- */
#TabsBar {{
    background: {BG};
}}
QPushButton[tab="true"] {{
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 6px;
    min-height: {MIN_BTN_H}px;
    padding: 4px 14px;
    color: {TEXT_MUTED};
}}
QPushButton[tab="true"]:hover {{
    background: {SURFACE_2};
}}
QPushButton[tab="true"][selected="true"] {{
    color: {ACCENT};
    font-weight: 700;
    border-bottom: 2px solid {ACCENT};
    background: {SURFACE};
}}

/* ---------- kart ızgarası ---------- */
#ScrollArea, #GridHost {{
    background: {BG};
}}
QScrollArea {{ border: none; background: {BG}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

#ProjectCard {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
#ProjectCard:hover {{
    border: 1px solid {ACCENT};
}}
#CardTitle {{ font-weight: 700; font-size: 15px; }}
#CardMeta  {{ color: {TEXT_MUTED}; font-size: 12px; }}
#Cover {{
    background: {SURFACE_2};
    border-radius: 10px;
    color: {TEXT_MUTED};
}}

/* ---------- giriş kutuları ---------- */
QLineEdit, QComboBox {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    min-height: {MIN_BTN_H}px;
    padding: 4px 10px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {ACCENT}; }}
"""
