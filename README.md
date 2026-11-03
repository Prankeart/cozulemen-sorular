# Test PDF Üretici 📄

Ekran görüntüsünden otomatik **test/quiz PDF (veya Word)** üreten masaüstü uygulaması.

Öğrenci/öğretmen olarak bilgisayar ekranındaki soruların görüntüsünü alırsın, her soru için
doğru şıkkı işaretlersin; uygulama bunları düzenli bir test dosyasına dönüştürür ve son
sayfaya **cevap anahtarı** ekler.

> Python + PySide6 ile geliştirilmiştir. Arayüz tamamen Türkçe, modern ve sade.

---

## 📥 İndir ve Kur (Windows)

En güncel **tek dosya exe** için: **Releases** → `TestPDFUretici.exe` dosyasını indir.

1. `TestPDFUretici.exe` dosyasını indir (Python kurulu olmasına gerek **yok**).
2. İstediğin bir klasöre koy (örn. Masaüstü veya `Program Files`).
3. Çift tıkla → çalışır. İlk açılışta exe'in yanındaki `data/` klasöründe
   veritabanı, görseller, çıktılar ve ayarlar tutulur.

> **Not (Windows SmartScreen):** İmzasız exe'lerde ilk çalıştırmada "Windows korudu"
> uyarısı çıkabilir → **Daha fazla bilgi → Yine de çalıştır**. Bu normaldir; ileride
> kod imzalama (code signing) ile kaldırılabilir.

Kaynak koddan çalıştırmak istersen aşağıdaki **Kurulum** bölümüne bak.

---

## ✨ Özellikler

- **Global kısayolla yakalama** (varsayılan `Ctrl+Shift+S`) — değiştirilebilir.
- Tam ekran, yarı saydam **alan seçim katmanı** (kesikli çerçeve + "Seçilen alan" etiketi).
- Sürüklenebilir **şık seçim menüsü** (A B C D E + "Kaydet ve kapat").
- **Sistem tepsisi** ve **yüzen kontrol paneli** (Yakala / Ayarlar / Ana Menü / Bitir).
- **Proje/klasör yönetimi**: TYT, AYT, Biyoloji… klasörleri; kart ızgarası; sağ tık menüsü.
- **Stil seçenekleri**: tek/iki sütun, sütun ayracı, soru arası boşluk, vurgu rengi, yazı tipi,
  soru altı çizgisi; **canlı önizleme**.
- **Çok geniş sorular** otomatik olarak iki sütunu kaplayan tam genişlikte basılır.
- Çıktı: **PDF (ReportLab)** veya **Word (python-docx)** + son sayfada cevap anahtarı.
- **Seçilebilir kayıt yeri**; uygulama klasörleri bu kök altında gerçek alt klasör olur.
- Türkçe karakter desteği (Windows TTF fontları otomatik kaydedilir).
- Hata günlüğü ve yalın mimari (SQLite + görseller klasörde).

---

##  Gereksinimler

- **Windows** (ekran yakalama/tepsi/global kısayol bu platformda test edildi)
- **Python 3.11+** (3.13 ile geliştirildi)

Bağımlılıklar: `PySide6`, `mss`, `Pillow`, `pynput`, `reportlab`, `python-docx`.

---

## 🚀 Kurulum ve çalıştırma

```powershell
git clone <repo-adresi>
cd test-pdf-uretici            # klasör adına göre değişebilir
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Kullanım akışı
1. **+ Yeni PDF** → isim, klasör, şık sayısı (4/5), tür (PDF/Word) ve stil ayarları → **Oluştur**.
2. Program arka plana geçer; **Ctrl+Shift+S** ile soru alanını seç.
3. Sağ altta çıkan menüde **doğru şıkkı** işaretle → **Kaydet ve kapat**.
4. Tüm soruları yakala → yüzen panel/tepsiden **Bitir**.
5. PDF/Word, seçtiğin **çıktı klasörü** içindeki ilgili alt klasöre kaydedilir.

Karta sol tık → üretilmiş dosyayı açar; sağ tık → yeniden adlandır / taşı / tekrar dışa aktar / sil.

---

## 📦 .exe olarak paketleme (Windows)

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean build.spec
# Çıktı: dist\TestPDFUretici\TestPDFUretici.exe
```
`data/` klasörü exe'in yanına oluşur. İkon için `assets/ikon.ico` ekleyip `build.spec`'te
`icon="assets/ikon.ico"` yapabilirsin.

---

##  Proje yapısı

```
app/
  core/    paths, capture, hotkey, capture_controller, settings, errors
  db/      schema.sql, database (profil/klasor/proje/soru CRUD)
  ui/      main_window, new_pdf_dialog, selection_overlay, option_menu,
           tray, floating_panel, style_preview, settings_dialog, theme, widgets/
  export/  pdf_exporter, word_exporter, dest
assets/    statik kaynaklar (ikon vb.)
data/      (çalışma anında oluşur; .gitignore'da) veritabanı, görseller, çıktılar, loglar
scripts/   demo_pdf.py, demo_word.py, build_exe.ps1
tests/     unittest testleri
main.py    giriş noktası
build.spec PyInstaller yapılandırması
```

---

## ✅ Testler

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🔒 Gizlilik

Tüm veriler yalnızca senin bilgisayarında saklanır (`data/` altında SQLite + görseller).
Uygulama internete bağlanmaz.

---

## 📄 Lisans

Açık kaynak. İstersen repo'ya bir LICENSE dosyası ekleyebilirsin
(ör. MIT). `assets/` içindeki Inter yazı tipi Google Fonts/OFL lisansına tabidir.
