# ============================================================
# PDF Legal Extractor - Windows Build Script
# ============================================================
# Este script automatiza a criacao do executavel Windows

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PDF Legal Extractor - Windows Build Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar se Python esta instalado
Write-Host "[1/4] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Python nao encontrado! Instale Python 3.8+ de python.org" -ForegroundColor Red
    exit 1
}

# 2. Criar ambiente virtual
Write-Host ""
Write-Host "[2/4] Criando ambiente virtual limpo..." -ForegroundColor Yellow
if (Test-Path "venv_build") {
    Write-Host "   Removendo ambiente antigo..." -ForegroundColor Gray
    Remove-Item -Recurse -Force venv_build
}

python -m venv venv_build
if (-not $?) {
    Write-Host "ERRO: Falha ao criar ambiente virtual" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Ambiente virtual criado" -ForegroundColor Green

# 3. Ativar ambiente virtual e instalar dependencias
Write-Host ""
Write-Host "[3/4] Instalando dependencias..." -ForegroundColor Yellow
& "venv_build\Scripts\Activate.ps1"

Write-Host "   Atualizando pip..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet

Write-Host "   Instalando PyMuPDF, click, tqdm, pywebview, pyinstaller..." -ForegroundColor Gray
pip install PyMuPDF click tqdm pywebview pyinstaller --quiet

if (-not $?) {
    Write-Host "ERRO: Falha ao instalar dependencias" -ForegroundColor Red
    deactivate
    exit 1
}
Write-Host "OK: Dependencias instaladas" -ForegroundColor Green

# 4. Executar build
Write-Host ""
Write-Host "[4/4] Iniciando build do executavel..." -ForegroundColor Yellow
Write-Host ""

python build_exe.py

if (-not $?) {
    Write-Host ""
    Write-Host "ERRO: Build falhou!" -ForegroundColor Red
    deactivate
    exit 1
}

# 5. Verificar resultado
Write-Host ""
Write-Host "OK: Build concluido!" -ForegroundColor Green
Write-Host ""
Write-Host "Arquivos gerados:" -ForegroundColor Cyan
if (Test-Path "dist\PDF2MD.exe") {
    $size = (Get-Item "dist\PDF2MD.exe").Length / 1MB
    Write-Host "   [OK] dist\PDF2MD.exe ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
}
if (Test-Path "dist\PDF2MD_Portable.zip") {
    $size = (Get-Item "dist\PDF2MD_Portable.zip").Length / 1MB
    Write-Host "   [OK] dist\PDF2MD_Portable.zip ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Processo concluido!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "PROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Testar executavel:" -ForegroundColor White
Write-Host "   > .\dist\PDF2MD.exe" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Criar instalador (opcional):" -ForegroundColor White
Write-Host "   - Instale Inno Setup: https://jrsoftware.org/isdl.php" -ForegroundColor Gray
Write-Host "   - Abra installer.iss no Inno Setup Compiler" -ForegroundColor Gray
Write-Host "   - Pressione F9 para compilar" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Distribuir:" -ForegroundColor White
Write-Host "   - Executavel stand-alone: dist\PDF2MD.exe" -ForegroundColor Gray
Write-Host "   - Pacote portavel: dist\PDF2MD_Portable.zip" -ForegroundColor Gray
Write-Host "   - Instalador (apos Inno Setup): Output\PDF2MD_Setup.exe" -ForegroundColor Gray
Write-Host ""

# Desativar ambiente virtual
deactivate
