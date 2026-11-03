"""PDF üretimi (Adım 6) - reportlab.

Stile göre soru görsellerini "1)", "2)" numaralarıyla yerleştirir:
  - tek/iki sütun; iki sütunda sütunlar arasında ayraç çizgisi (seçilirse)
  - sorular arası boşluk (kaydırıcı değeri)
  - vurgu rengi (numara + başlık) ve yazı tipi
  - soru bulunduğu sütuna sığmazsa bölünmeden sonraki sütuna/sayfaya geçer
Son sayfada "Cevap Anahtarı" ızgarası: "1 - A, 2 - B ...".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from app.core import paths
from app.db import get_db

# --------------------------- sabitler ---------------------------
PAGE_W, PAGE_H = A4
MARGIN = 40
GUTTER = 26            # iki sütun arası boşluk (ayraç buraya çizilir)
NUM_H = 16             # soru numarası satır yüksekliği
NUM_FONT_SIZE = 12
NUM_GAP = 8            # numara ile görsel arası boşluk
SORU_LINE_GAP = 7      # soru altı çizgisi için ek alan
WIDE_RATIO = 2.0       # genişlik/yükseklik >= bu ise (yükseklik, genişliğin yarısından az) soru tam genişlik
ANSWER_FONT = "Helvetica-Bold"

# --------------------------- Türkçe TTF fontları ---------------------------
# reportlab'ın standart fontları (Helvetica/Times/Courier) WinAnsi kullanır ve
# ı, ğ, ş, İ gibi Türkçe glifleri çizemez. Bu yüzden Windows'un TTF fontlarını
# kaydeder, bulunamazsa standart isme düşeriz.
_FONT_DIR = Path("C:/Windows/Fonts")
_ADI_TTF = {  # aile -> denenecek dosya adları
    "Arial": ["arial.ttf", "ariblk.ttf"],
    "TimesNewRoman": ["times.ttf"],
    "CourierNew": ["cour.ttf"],
}
_STIL_FONT_AILE = {  # stil fontu (reportlab adı) -> TTF ailesi
    "Helvetica": "Arial",
    "Times-Roman": "TimesNewRoman",
    "Courier": "CourierNew",
}
_kayitli: set[str] = set()


def _ttf_kaydet(aile: str) -> bool:
    if aile in _kayitli:
        return True
    for fn in _ADI_TTF.get(aile, []):
        p = _FONT_DIR / fn
        if p.exists():
            try:
                pdfmetrics.registerFont(TTFont(aile, str(p)))
                _kayitli.add(aile)
                return True
            except Exception:
                continue
    return False


def resolve_font(stil_fontu: str) -> str:
    """Stil fontunu Türkçe destekli TTF'ye çevirir; yoksa olduğu gibi döner."""
    aile = _STIL_FONT_AILE.get(stil_fontu, "Arial")
    if _ttf_kaydet(aile):
        return aile
    return stil_fontu



@dataclass
class SoruGorsel:
    no: int
    yol: str
    sik: str
    genislik: int
    yukseklik: int


def _gecerli_dosya_adi(ad: str) -> str:
    ad = re.sub(r'[\\/:*?"<>|]', "_", (ad or "").strip()) or "test"
    return ad[:80]


def _soru_gorselleri(sorular) -> list[SoruGorsel]:
    out = []
    for s in sorular:
        p = paths.abs_from_base(s["gorsel_yolu"])
        iw, ih = 100, 60
        if p and p.exists():
            try:
                with Image.open(p) as im:
                    iw, ih = im.size
            except Exception:
                pass
        out.append(SoruGorsel(s["soru_no"], str(p) if p else "", s["dogru_sik"], iw, ih))
    return out


def _hex(renk: str) -> HexColor:
    try:
        return HexColor(renk)
    except Exception:
        return HexColor("#2f6f4f")


def _olcek(g: SoruGorsel, avail_w: float, max_h: float, soru_alti: bool):
    """Görseli avail_w genişliğine ölçekler, yüksekliği max_h ile sınırlar.

    (img_w, img_h, item_h) döner; item_h = numara + boşluk + görsel (+ çizgi).
    """
    img_w = avail_w
    img_h = avail_w * (g.yukseklik / max(1, g.genislik))
    if img_h > max_h:
        img_h = max_h
        img_w = img_h * (g.genislik / max(1, g.yukseklik))
        if img_w > avail_w:
            img_w = avail_w
    item_h = NUM_H + NUM_GAP + img_h + (SORU_LINE_GAP if soru_alti else 0)
    return img_w, img_h, item_h


def _draw_item(c: Canvas, g: SoruGorsel, x: float, top_y: float,
               img_w: float, img_h: float, item_h: float,
               font: str, renk: HexColor, soru_alti: bool) -> None:
    """Tek bir soruyu (numara + görsel + isteğe bağlı alt çizgi) çizer."""
    c.setFillColor(renk)
    c.setFont(font, NUM_FONT_SIZE)
    c.drawString(x, top_y - NUM_FONT_SIZE, f"{g.no})")
    img_bottom = top_y - item_h
    if g.yol:
        try:
            c.drawImage(g.yol, x, img_bottom, width=img_w, height=img_h,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass
    if soru_alti:
        c.setStrokeColor(HexColor("#999999"))
        c.setLineWidth(0.6)
        ly = img_bottom - 3
        c.line(x, ly, x + img_w, ly)


def export_pdf(
    proje,
    sorular,
    stil: dict,
    out_path: Optional[str] = None,
) -> str:
    """Projeyi PDF olarak üretir, yazılan dosya yolunu döndürür."""
    gorseller = _soru_gorselleri(sorular)
    if not gorseller:
        raise ValueError("Yakalanmış soru yok; önce soru ekleyin.")

    paths.ensure_dirs()
    if out_path is None:
        out_path = str(paths.EXPORT_DIR / (_gecerli_dosya_adi(proje["ad"]) + ".pdf"))

    ncol = 2 if stil.get("sayfa_tarzi") == "iki" else 1
    content_w = PAGE_W - 2 * MARGIN - (ncol - 1) * GUTTER
    col_w = content_w / ncol
    col_x = [MARGIN + i * (col_w + GUTTER) for i in range(ncol)]
    content_top = PAGE_H - MARGIN
    content_bottom = MARGIN

    renk = _hex(stil.get("renk", "#2f6f4f"))
    font = resolve_font(stil.get("font", "Helvetica"))
    gap = float(stil.get("soru_boslugu", 24))
    ayrac_cizgi = stil.get("ayrac", "cizgi") == "cizgi"
    soru_alti = stil.get("soru_alti_cizgi", "yok") == "cizgi"

    c = Canvas(out_path, pagesize=A4)
    full_w = PAGE_W - 2 * MARGIN
    # bir öğenin sığabileceği en büyük görsel yüksekliği
    max_h = content_top - content_bottom - NUM_H - NUM_GAP - gap - (
        SORU_LINE_GAP if soru_alti else 0
    )

    def ayraclari_ciz():
        if ayrac_cizgi and ncol > 1:
            c.setStrokeColor(renk)
            c.setLineWidth(0.7)
            x = col_x[1] - GUTTER / 2
            c.line(x, content_bottom, x, content_top)

    # satırları kur: (öğeler, tam_genişlik_mi)
    #  - normal sorular 2'şerli satırlar (yan yana iki sütun)
    #  - çok geniş soru tek başına tam genişlik satırı (akış bozulmadan)
    rows: list[tuple[list[SoruGorsel], bool]] = []
    buf: list[SoruGorsel] = []

    def flush_buf():
        i = 0
        while i < len(buf):
            rows.append((buf[i:i + 2], False))
            i += 2

    for g in gorseller:
        ratio = g.genislik / max(1, g.yukseklik)
        genis = ncol > 1 and ratio >= WIDE_RATIO
        if genis or ncol == 1:
            flush_buf(); buf.clear()
            rows.append(([g], True))
        else:
            buf.append(g)
    flush_buf()

    # yerleşim: satırlar dikey olarak akar; sığmayan satır yeni sayfaya geçer
    y = content_top
    ayraclari_ciz()
    for items, full in rows:
        avail = full_w if full else col_w
        xs = [MARGIN] if full else col_x
        olc = [_olcek(g, avail, max_h, soru_alti) for g in items]
        row_h = max(h for _, _, h in olc)
        if y - row_h < content_bottom:
            c.showPage()
            y = content_top
            ayraclari_ciz()
        for g, (iw, ih, ih_item), x in zip(items, olc, xs):
            _draw_item(c, g, x, y, iw, ih, ih_item, font, renk, soru_alti)
        y -= row_h + gap

    # cevap anahtarı (yeni sayfa)
    c.showPage()
    _cevap_anahtari(c, gorseller, stil, renk, font)
    c.save()
    return out_path


def _cevap_anahtari(c: Canvas, gorseller, stil, renk, font) -> None:
    iki_sutun = stil.get("sayfa_tarzi") == "iki"
    ncol = 2 if iki_sutun else 1

    # sütun ayraçları (soru sayfalarıyla aynı)
    if stil.get("ayrac", "cizgi") == "cizgi" and iki_sutun:
        c.setStrokeColor(renk)
        c.setLineWidth(0.7)
        content_w = PAGE_W - 2 * MARGIN - GUTTER
        col_w = content_w / 2
        x = MARGIN + col_w + GUTTER / 2
        c.line(x, MARGIN, x, PAGE_H - MARGIN)

    # başlık
    c.setFillColor(renk)
    c.setFont(font, 20)
    c.drawString(MARGIN, PAGE_H - MARGIN - 20, "Cevap Anahtarı")

    # ızgara: her sütunda yaklaşık 90 pt genişliğinde hücreler
    content_w = PAGE_W - 2 * MARGIN - (ncol - 1) * GUTTER
    col_w = content_w / ncol
    col_x = [MARGIN + i * (col_w + GUTTER) for i in range(ncol)]
    hucre_gen = 90.0
    satir_basina = max(1, int(col_w // hucre_gen))
    row_h = 20.0
    start_y = PAGE_H - MARGIN - 56
    satir_kapasitesi = max(1, int((start_y - MARGIN) // row_h))
    per_col = satir_basina * satir_kapasitesi

    c.setFont(font, 12)
    c.setFillColor(HexColor("#222222"))
    for idx, g in enumerate(gorseller):
        kolon = min(idx // per_col, ncol - 1) if ncol > 1 else 0
        local = idx - kolon * per_col
        r = local // satir_basina
        kc = local % satir_basina
        x = col_x[kolon] + kc * hucre_gen
        y = start_y - r * row_h
        c.drawString(x, y, f"{g.no} - {g.sik}")


def export_project_pdf(proje_id: int, db=None) -> str:
    """Veritabanındaki projeyi PDF olarak üretir; stil + soruları okur.

    Dosya, seçili çıktı kökü altında projenin klasörüne göre yazılır.
    """
    from app.export import dest

    db = db or get_db()
    proje = db.proje_getir(proje_id)
    if proje is None:
        raise ValueError("Proje bulunamadı")
    sorular = db.soru_liste(proje_id)
    stil = db.proje_stil_getir(proje_id)
    out_path = dest.dosya_yolu(proje, db, ".pdf")
    yol = export_pdf(proje, sorular, stil, out_path)
    db.proje_dosya_yolu_set(proje_id, yol)
    return yol
