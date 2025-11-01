# ============================================================
# PDF Legal Extractor - Windows Build Script
# ============================================================
# Este script automatiza a criação do executável Windows

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PDF Legal Extractor - Windows Build Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar se Python está instalado
Write-Host "🔍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado! Instale Python 3.8+ de python.org" -ForegroundColor Red
    exit 1
}

# 2. Criar ambiente virtual
Write-Host ""
Write-Host "📦 Criando ambiente virtual limpo..." -ForegroundColor Yellow
if (Test-Path "venv_build") {
    Write-Host "   Removendo ambiente antigo..." -ForegroundColor Gray
    Remove-Item -Recurse -Force venv_build
}

python -m venv venv_build
if (-not $?) {
    Write-Host "❌ Erro ao criar ambiente virtual" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Ambiente virtual criado" -ForegroundColor Green

# 3. Ativar ambiente virtual e instalar dependências
Write-Host ""
Write-Host "📥 Instalando dependências..." -ForegroundColor Yellow
& "venv_build\Scripts\Activate.ps1"

Write-Host "   Atualizando pip..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet

Write-Host "   Instalando PyMuPDF, click, tqdm, pywebview, pyinstaller..." -ForegroundColor Gray
pip install PyMuPDF click tqdm pywebview pyinstaller --quiet

if (-not $?) {
    Write-Host "❌ Erro ao instalar dependências" -ForegroundColor Red
    deactivate
    exit 1
}
Write-Host "✅ Dependências instaladas" -ForegroundColor Green

# 4. Executar build
Write-Host ""
Write-Host "🔨 Iniciando build do executável..." -ForegroundColor Yellow
Write-Host ""

python build_exe.py

if (-not $?) {
    Write-Host ""
    Write-Host "❌ Build falhou!" -ForegroundColor Red
    deactivate
    exit 1
}

# 5. Verificar resultado
Write-Host ""
Write-Host "✅ Build concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📂 Arquivos gerados:" -ForegroundColor Cyan
if (Test-Path "dist\PDF2MD.exe") {
    $size = (Get-Item "dist\PDF2MD.exe").Length / 1MB
    Write-Host "   ✓ dist\PDF2MD.exe ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
}
if (Test-Path "dist\PDF2MD_Portable.zip") {
    $size = (Get-Item "dist\PDF2MD_Portable.zip").Length / 1MB
    Write-Host "   ✓ dist\PDF2MD_Portable.zip ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎉 Processo concluído!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Testar executável:" -ForegroundColor White
Write-Host "   > .\dist\PDF2MD.exe" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Criar instalador (opcional):" -ForegroundColor White
Write-Host "   - Instale Inno Setup: https://jrsoftware.org/isdl.php" -ForegroundColor Gray
Write-Host "   - Abra installer.iss no Inno Setup Compiler" -ForegroundColor Gray
Write-Host "   - Pressione F9 para compilar" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Distribuir:" -ForegroundColor White
Write-Host "   - Executável stand-alone: dist\PDF2MD.exe" -ForegroundColor Gray
Write-Host "   - Pacote portável: dist\PDF2MD_Portable.zip" -ForegroundColor Gray
Write-Host "   - Instalador (após Inno Setup): Output\PDF2MD_Setup.exe" -ForegroundColor Gray
Write-Host ""

# Desativar ambiente virtual
deactivate
