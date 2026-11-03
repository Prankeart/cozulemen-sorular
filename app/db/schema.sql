-- ============================================================
--  Test PDF Üretici - SQLite Şeması (Adım 1)
--  Tablolar: profil, klasor, proje, soru
--  Görseller klasörde dosya olarak tutulur; DB'de sadece yol saklanır.
-- ============================================================

PRAGMA foreign_keys = ON;

-- Kullanıcı profili (tek satır beklenir; varsayılan tohumlanır)
CREATE TABLE IF NOT EXISTS profil (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ad            TEXT    NOT NULL,
    avatar_yolu   TEXT,
    olusturma     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Klasörler / sınav dersleri (Tümü haric; "Tümü" sanal bir filtredir)
CREATE TABLE IF NOT EXISTS klasor (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ad            TEXT    NOT NULL UNIQUE,
    sira          INTEGER NOT NULL DEFAULT 0,
    olusturma     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- PDF/Word projeleri
--   stil: JSON -> {sayfa_tarzi, ayrac, soru_boslugu, renk, font}
--   tur : 'pdf' | 'word'
--   sik_sayisi : 4 (A-D) | 5 (A-E)
CREATE TABLE IF NOT EXISTS proje (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    klasor_id     INTEGER,
    ad            TEXT    NOT NULL,
    sik_sayisi    INTEGER NOT NULL DEFAULT 4 CHECK (sik_sayisi IN (4, 5)),
    tur           TEXT    NOT NULL DEFAULT 'pdf' CHECK (tur IN ('pdf', 'word')),
    stil          TEXT    NOT NULL DEFAULT '{}',
    dosya_yolu    TEXT,               -- dışa aktarılan üretilecek dosyanın yolu
    olusturma     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    guncelleme    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (klasor_id) REFERENCES klasor(id) ON DELETE SET NULL
);

-- Yakalanan sorular
--   gorsel_yolu : data/ altındaki kırpılmış görselin yolu
--   dogru_sik   : 'A' | 'B' | 'C' | 'D' | 'E'
--   soru_no     : proje içinde otomatik artan numara
CREATE TABLE IF NOT EXISTS soru (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    proje_id      INTEGER NOT NULL,
    soru_no       INTEGER NOT NULL,
    gorsel_yolu   TEXT    NOT NULL,
    dogru_sik     TEXT    NOT NULL CHECK (dogru_sik IN ('A', 'B', 'C', 'D', 'E')),
    olusturma     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (proje_id, soru_no),
    FOREIGN KEY (proje_id) REFERENCES proje(id) ON DELETE CASCADE
);

-- Sık sorgular için indeksler
CREATE INDEX IF NOT EXISTS idx_proje_klasor ON proje(klasor_id);
CREATE INDEX IF NOT EXISTS idx_soru_proje   ON soru(proje_id, soru_no);
