"""SQLite veritabanı katmanı (Adım 1).

Tek sorumluluk: şemayı oluşturmak/totumlamak ve profil, klasor, proje, soru
üzerinde CRUD yardımcı fonksiyonları sağlamak. Arayüzden bağımsızdır, böylece
test edilebilir.

Kullanım:
    from app.db import get_db
    db = get_db()
    db.ayarlare_getir()          # profil + örnek klasörleri tohumlar
    proje_id = db.proje_olustur("TYT Matematik", klasor_id=1, sik_sayisi=4,
                                tur="pdf", stil=db.varsayilan_stil())
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from app.core import paths

SCHEMA_FILE = Path(__file__).with_name("schema.sql")

# Klasör sekmeleri için örnek başlangıç listesi (Adım 2'de kullanılacak).
VARSAYILAN_KLASORLER = ["TYT", "AYT", "Biyoloji", "Fizik", "Matematik", "Tarih"]

# Stil panelinin (Adım 3) varsayılan değerleri.
VARSAYILAN_STIL: dict[str, Any] = {
    "sayfa_tarzi": "tek",       # "tek" | "iki"
    "ayrac": "cizgi",           # "cizgi" | "yok"
    "soru_alti_cizgi": "yok",   # "cizgi" | "yok" (her soru altına çizgi)
    "genis_tam_genislik": "kapali",  # "acik" | "kapali" (geniş soru iki sütunu kaplasın)
    "soru_boslugu": 24,         # piksel benzeri birim; kaydırıcı
    "renk": "#2f6f4f",          # vurgu rengi (hex)
    "font": "Helvetica",        # yazı tipi adı
}


class Database:
    """SQLite bağlantısı ve veri yardımcıları."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        paths.ensure_dirs()
        self.db_path = Path(db_path) if db_path else paths.DB_PATH
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")

    # ----------------------------- kurulum -----------------------------
    def init_schema(self) -> None:
        """schema.sql içindeki tabloları/indeksleri oluşturur."""
        sql = SCHEMA_FILE.read_text(encoding="utf-8")
        self.conn.executescript(sql)
        self.conn.commit()

    def seed(self) -> None:
        """Profil yoksa varsayılan profil ve örnek klasörleri ekler."""
        self.init_schema()
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM profil")
        if cur.fetchone()["c"] == 0:
            cur.execute("INSERT INTO profil (ad) VALUES (?)", ("Öğrenci",))
        for sira, ad in enumerate(VARSAYILAN_KLASORLER):
            cur.execute(
                "INSERT OR IGNORE INTO klasor (ad, sira) VALUES (?, ?)",
                (ad, sira),
            )
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    # ----------------------------- yardımcılar -----------------------------
    @staticmethod
    def varsayilan_stil(**degisiklik: Any) -> dict[str, Any]:
        """Kopya olarak varsayılan stil sözlüğü; isteğe bağlı alan geçersiz kılınır."""
        stil = dict(VARSAYILAN_STIL)
        stil.update(degisiklik)
        return stil

    # ----------------------------- profil -----------------------------
    def profil_getir(self) -> Optional[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM profil ORDER BY id LIMIT 1").fetchone()

    def profil_adi_set(self, ad: str) -> None:
        p = self.profil_getir()
        if p is None:
            self.conn.execute("INSERT INTO profil (ad) VALUES (?)", (ad,))
        else:
            self.conn.execute("UPDATE profil SET ad = ? WHERE id = ?", (ad, p["id"]))
        self.conn.commit()

    def profil_avatar_set(self, avatar_yolu: Optional[str]) -> None:
        p = self.profil_getir()
        if p is not None:
            rel = paths.rel_to_base(avatar_yolu) if avatar_yolu else None
            self.conn.execute(
                "UPDATE profil SET avatar_yolu = ? WHERE id = ?", (rel, p["id"])
            )
            self.conn.commit()

    # ----------------------------- klasör -----------------------------
    def klasor_liste(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM klasor ORDER BY sira, ad"
        ).fetchall()

    def klasor_ekle(self, ad: str) -> Optional[int]:
        ad = (ad or "").strip()
        if not ad:
            return None
        cur = self.conn.cursor()
        cur.execute("SELECT MAX(sira) AS m FROM klasor")
        sira = (cur.fetchone()["m"] or 0) + 1
        try:
            cur.execute("INSERT INTO klasor (ad, sira) VALUES (?, ?)", (ad, sira))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None  # aynı isimde klasör var

    def klasor_sil(self, klasor_id: int) -> None:
        # Projeler ON DELETE SET NULL ile klasörsüz kalır (silinmez).
        self.conn.execute("DELETE FROM klasor WHERE id = ?", (klasor_id,))
        self.conn.commit()

    def klasor_var_mi(self, ad: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM klasor WHERE ad = ?", ((ad or "").strip(),)
        ).fetchone()
        return row is not None

    # ----------------------------- proje -----------------------------
    def proje_olustur(
        self,
        ad: str,
        klasor_id: Optional[int] = None,
        sik_sayisi: int = 4,
        tur: str = "pdf",
        stil: Optional[dict[str, Any]] = None,
    ) -> int:
        if sik_sayisi not in (4, 5):
            raise ValueError("sik_sayisi 4 veya 5 olmalı")
        if tur not in ("pdf", "word"):
            raise ValueError("tur 'pdf' veya 'word' olmalı")
        stil_json = json.dumps(stil or self.varsayilan_stil(), ensure_ascii=False)
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO proje (klasor_id, ad, sik_sayisi, tur, stil)
               VALUES (?, ?, ?, ?, ?)""",
            (klasor_id, (ad or "").strip() or "Adsız Proje", sik_sayisi, tur, stil_json),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def proje_getir(self, proje_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM proje WHERE id = ?", (proje_id,)
        ).fetchone()

    def proje_liste(self, klasor_id: Optional[int] = None) -> list[sqlite3.Row]:
        """klasor_id None ise 'Tümü' (tüm projeler) döner."""
        if klasor_id is None:
            cur = self.conn.execute(
                """SELECT p.*, k.ad AS klasor_ad,
                          (SELECT COUNT(*) FROM soru s WHERE s.proje_id = p.id) AS soru_adedi
                   FROM proje p LEFT JOIN klasor k ON k.id = p.klasor_id
                   ORDER BY p.guncelleme DESC"""
            )
        else:
            cur = self.conn.execute(
                """SELECT p.*, k.ad AS klasor_ad,
                          (SELECT COUNT(*) FROM soru s WHERE s.proje_id = p.id) AS soru_adedi
                   FROM proje p LEFT JOIN klasor k ON k.id = p.klasor_id
                   WHERE p.klasor_id = ?
                   ORDER BY p.guncelleme DESC""",
                (klasor_id,),
            )
        return cur.fetchall()

    def proje_stil_getir(self, proje_id: int) -> dict[str, Any]:
        p = self.proje_getir(proje_id)
        if p is None:
            return self.varsayilan_stil()
        try:
            return json.loads(p["stil"])
        except (json.JSONDecodeError, TypeError):
            return self.varsayilan_stil()

    def proje_stil_set(self, proje_id: int, stil: dict[str, Any]) -> None:
        self.conn.execute(
            """UPDATE proje SET stil = ?,
                      guncelleme = datetime('now','localtime') WHERE id = ?""",
            (json.dumps(stil, ensure_ascii=False), proje_id),
        )
        self.conn.commit()

    def proje_yeniden_adlandir(self, proje_id: int, yeni_ad: str) -> None:
        self.conn.execute(
            """UPDATE proje SET ad = ?,
                      guncelleme = datetime('now','localtime') WHERE id = ?""",
            ((yeni_ad or "").strip() or "Adsız Proje", proje_id),
        )
        self.conn.commit()

    def proje_tasi(self, proje_id: int, klasor_id: Optional[int]) -> None:
        self.conn.execute(
            """UPDATE proje SET klasor_id = ?,
                      guncelleme = datetime('now','localtime') WHERE id = ?""",
            (klasor_id, proje_id),
        )
        self.conn.commit()

    def proje_dosya_yolu_set(self, proje_id: int, dosya_yolu: Optional[str]) -> None:
        rel = paths.rel_to_base(dosya_yolu) if dosya_yolu else None
        self.conn.execute(
            """UPDATE proje SET dosya_yolu = ?,
                      guncelleme = datetime('now','localtime') WHERE id = ?""",
            (rel, proje_id),
        )
        self.conn.commit()

    def proje_sil(self, proje_id: int) -> None:
        # ON DELETE CASCADE ilgili soruları da siler.
        self.conn.execute("DELETE FROM proje WHERE id = ?", (proje_id,))
        self.conn.commit()

    # ----------------------------- soru -----------------------------
    def soru_siradaki_no(self, proje_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT MAX(soru_no) AS m FROM soru WHERE proje_id = ?", (proje_id,)
        )
        return (cur.fetchone()["m"] or 0) + 1

    def soru_ekle(
        self,
        proje_id: int,
        gorsel_yolu: str,
        dogru_sik: str,
        soru_no: Optional[int] = None,
    ) -> int:
        dogru_sik = (dogru_sik or "").strip().upper()
        if dogru_sik not in ("A", "B", "C", "D", "E"):
            raise ValueError("dogru_sik A-E aralığında olmalı")
        if soru_no is None:
            soru_no = self.soru_siradaki_no(proje_id)
        rel = paths.rel_to_base(gorsel_yolu)
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO soru (proje_id, soru_no, gorsel_yolu, dogru_sik)
               VALUES (?, ?, ?, ?)""",
            (proje_id, soru_no, rel, dogru_sik),
        )
        cur.execute(
            "UPDATE proje SET guncelleme = datetime('now','localtime') WHERE id = ?",
            (proje_id,),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def soru_liste(self, proje_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM soru WHERE proje_id = ? ORDER BY soru_no", (proje_id,)
        ).fetchall()

    def soru_adet(self, proje_id: int) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM soru WHERE proje_id = ?", (proje_id,))
        return int(cur.fetchone()["c"])

    def soru_sil(self, soru_id: int) -> None:
        self.conn.execute("DELETE FROM soru WHERE id = ?", (soru_id,))
        self.conn.commit()

    def soru_son_sil(self, proje_id: int) -> Optional[sqlite3.Row]:
        """Son eklenen (en büyük soru_no) soruyu siler ve silinen satırı döner."""
        son = self.conn.execute(
            """SELECT * FROM soru WHERE proje_id = ?
               ORDER BY soru_no DESC LIMIT 1""",
            (proje_id,),
        ).fetchone()
        if son is None:
            return None
        self.conn.execute("DELETE FROM soru WHERE id = ?", (son["id"],))
        self.conn.commit()
        return son

    def cevap_anahtari(self, proje_id: int) -> list[tuple[int, str]]:
        """(soru_no, dogru_sik) listesi - Cevap Anahtarı sayfası için."""
        rows = self.conn.execute(
            "SELECT soru_no, dogru_sik FROM soru WHERE proje_id = ? ORDER BY soru_no",
            (proje_id,),
        ).fetchall()
        return [(r["soru_no"], r["dogru_sik"]) for r in rows]


# ----------------------------- modül singleton -----------------------------
_db: Optional[Database] = None


def get_db(reinit: bool = False) -> Database:
    """Uygulama genisinde tek Database örneği döndürür (lazy init + seed)."""
    global _db
    if _db is None or reinit:
        _db = Database()
        _db.seed()
    return _db
