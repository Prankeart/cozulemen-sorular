# Test PDF Üretici - TEK DOSYA .exe derleme (dağıtım için)
# Kullanım (Proje kökünde, PowerShell):
#   powershell -ExecutionPolicy Bypass -File scripts/build_portable.ps1
# Çıktı: dist\TestPDFUretici.exe  (indir-çalıştır; Python gerekmez)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Bağımlılıklar hazırlanıyor..." -ForegroundColor Cyan
python -m pip install --upgrade pip | Out-Null
pip install -r requirements.txt
pip install pyinstaller

Write-Host "Tek dosya exe derleniyor (birkaç dakika sürebilir)..." -ForegroundColor Cyan
pyinstaller --noconfirm --clean build_onefile.spec

$exe = Join-Path $root "dist\TestPDFUretici.exe"
if (Test-Path $exe) {
    $mb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
    Write-Host ""
    Write-Host "HAZIR: $exe ($mb MB)" -ForegroundColor Green
    Write-Host "Bunu GitHub Release'e yükle ki herkes indirip çalıştırabilsin."
} else {
    Write-Host "Derleme başarısız görünüyor; dist\TestPDFUretici.exe yok." -ForegroundColor Red
    exit 1
}
