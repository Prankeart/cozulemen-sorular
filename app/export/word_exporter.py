"""Word üretimi (Adım 7) - python-docx.

Stile göre soru görsellerini "1)", "2)" numaralarıyla yerleştirir:
  - tek/iki sütun (Word'ün kendi sütun akışı; sığmayan soru otomatik sonraki
    sütuna/sayfaya geçer, bölünmez)
  - iki sütunda sütunlar arası ayraç çizgisi (seçilirse)
  - sorular arası boşluk (kaydırıcı değeri, punto)
  - vurgu rengi (numara + başlık) ve yazı tipi
Son sayfada "Cevap Anahtarı" tablosu: "1 - A, 2 - B ...".
"""

from __future__ import annotations

import re
from typing import Optional

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor

from app.core import paths
from app.db import get_db

# stil fontu (reportlab adı) -> Word font adı
_WORD_FONT = {
    "Helvetica": "Arial",
    "Times-Roman": "Times New Roman",
    "Courier": "Courier New",
}

PAGE_W_MM, PAGE_H_MM = 210, 297     # A4
MARGIN_CM = 2.0
COL_SPACE_CM = 1.0


def _gecerli_dosya_adi(ad: str) -> str:
    ad = re.sub(r'[\\/:*?"<>|]', "_", (ad or "").strip()) or "test"
    return ad[:80]


def _rgb(hex_str: str) -> RGBColor:
    try:
        s = hex_str.lstrip("#")
        return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except Exception:
        return RGBColor(0x2F, 0x6F, 0x4F)


def _sutun_ayarla(section, num: int, space_cm: float, sep: bool) -> float:
    """Section'a sütun sayısı/boşluğu/ayraç uygular; sütun genişliği (cm) döner."""
    sectPr = section._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sectPr.append(cols)
    cols.set(qn("w:num"), str(num))
    cols.set(qn("w:space"), str(int(space_cm * 567)))  # cm -> twips (1cm≈567twip)
    cols.set(qn("w:equalWidth"), "1")
    if sep:
        cols.set(qn("w:sep"), "1")
    else:
        cols.attrib.pop(qn("w:sep"), None)

    content_cm = (PAGE_W_MM / 10) - 2 * MARGIN_CM - (num - 1) * space_cm
    return content_cm / num


def _run_font(par, font_adi: str, boyut: int, renk: RGBColor, bold: bool = False):
    for r in par.runs:
        r.font.name = font_adi
        r.font.size = Pt(boyut)
        r.font.color.rgb = renk
        r.font.bold = bold


def _alt_cizgi(par) -> None:
    """Paragrafın altına ince bir çizgi (w:pBdr/bottom) ekler."""
    pPr = par._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    alt = OxmlElement("w:bottom")
    alt.set(qn("w:val"), "single")
    alt.set(qn("w:sz"), "6")
    alt.set(qn("w:space"), "4")
    alt.set(qn("w:color"), "999999")
    pbdr.append(alt)
    pPr.append(pbdr)


def export_word(proje, sorular, stil: dict, out_path: Optional[str] = None) -> str:
    if not sorular:
        raise ValueError("Yakalanmış soru yok; önce soru ekleyin.")

    paths.ensure_dirs()
    if out_path is None:
        out_path = str(paths.EXPORT_DIR / (_gecerli_dosya_adi(proje["ad"]) + ".docx"))

    doc = Document()
    section = doc.sections[0]
    section.page_width = Mm(PAGE_W_MM)
    section.page_height = Mm(PAGE_H_MM)
    section.top_margin = section.bottom_margin = Cm(MARGIN_CM)
    section.left_margin = section.right_margin = Cm(MARGIN_CM)

    iki = stil.get("sayfa_tarzi") == "iki"
    ncol = 2 if iki else 1
    sep = stil.get("ayrac", "cizgi") == "cizgi"
    col_w_cm = _sutun_ayarla(section, ncol, COL_SPACE_CM, sep)

    font_adi = _WORD_FONT.get(stil.get("font", "Helvetica"), "Arial")
    renk = _rgb(stil.get("renk", "#2f6f4f"))
    gap = float(stil.get("soru_boslugu", 24))
    soru_alti = stil.get("soru_alti_cizgi", "yok") == "cizgi"

    # varsayılan stil fontunu ayarla
    style = doc.styles["Normal"]
    style.font.name = font_adi

    for s in sorular:
        no = s["soru_no"]
        yol = paths.abs_from_base(s["gorsel_yolu"])
        num = doc.add_paragraph()
        run = num.add_run(f"{no})")
        run.font.name = font_adi
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = renk
        num.paragraph_format.space_after = Pt(2)
        num.paragraph_format.keep_with_next = True

        if yol and yol.exists():
            p = doc.add_paragraph()
            try:
                p.add_run().add_picture(str(yol), width=Cm(col_w_cm))
            except Exception:
                pass
            if soru_alti:
                _alt_cizgi(p)
        bosluk = doc.add_paragraph()
        bosluk.paragraph_format.space_after = Pt(gap)

    # ---- cevap anahtarı (yeni sayfa) ----
    kirma = doc.add_paragraph()
    kirma.add_run().add_break(WD_BREAK.PAGE)
    # anahtar sayfasında tek sütun daha düzenli
    _sutun_ayarla(section, 1, COL_SPACE_CM, False)

    baslik = doc.add_paragraph()
    br = baslik.add_run("Cevap Anahtarı")
    br.font.name = font_adi
    br.font.size = Pt(20)
    br.font.bold = True
    br.font.color.rgb = renk

    tablo = doc.add_table(rows=0, cols=4)
    try:
        tablo.style = "Table Grid"
    except Exception:
        pass
    hucre = 3
    satir = None
    for i, s in enumerate(sorular):
        if i % hucre == 0:
            satir = tablo.add_row().cells
        j = i % hucre
        satir[j].text = f"{s['soru_no']} - {s['dogru_sik']}"
        for pr in satir[j].paragraphs:
            _run_font(pr, font_adi, 12, RGBColor(0x22, 0x22, 0x22))

    doc.save(out_path)
    return out_path


def export_project_word(proje_id: int, db=None) -> str:
    """Projeyi Word olarak üretir; dosya seçili çıktı kökü/klasör altına yazılır."""
    from app.export import dest

    db = db or get_db()
    proje = db.proje_getir(proje_id)
    if proje is None:
        raise ValueError("Proje bulunamadı")
    sorular = db.soru_liste(proje_id)
    stil = db.proje_stil_getir(proje_id)
    out_path = dest.dosya_yolu(proje, db, ".docx")
    yol = export_word(proje, sorular, stil, out_path)
    db.proje_dosya_yolu_set(proje_id, yol)
    return yol
