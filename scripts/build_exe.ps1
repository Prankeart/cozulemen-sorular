# Test PDF Üretici - Windows .exe derleme betiği (Adım 8)
# Kullanım (Proje kökünde, PowerShell):
#   powershell -ExecutionPolicy Bypass -File scripts/build_exe.ps1
# Çıktı: dist\TestPDFUretici\TestPDFUretici.exe

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "1/3) Sanal ortam (venv)..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"

Write-Host "2/3) Bağımlılıklar..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

Write-Host "3/3) PyInstaller ile derleniyor..." -ForegroundColor Cyan
pyinstaller --noconfirm --clean build.spec

Write-Host ""
Write-Host "BİTTİ. Uygulama: dist\TestPDFUretici\TestPDFUretici.exe" -ForegroundColor Green
Write-Host "İpucu: data/ klasörü exe'in yanına oluşur (veritabanı + görseller)."
