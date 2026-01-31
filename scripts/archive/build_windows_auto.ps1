# Script Automatizado de Build - PDF Legal Extractor
# Execute no PowerShell Windows (não WSL)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PDF Legal Extractor - Build Auto" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "[1/7] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python não encontrado!" -ForegroundColor Red
    Write-Host "    Instale Python de: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# 2. Verificar/Criar venv
Write-Host "`n[2/7] Verificando ambiente virtual..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  ✓ venv encontrado" -ForegroundColor Green
} elseif (Test-Path "venv_windows") {
    Write-Host "  ✓ venv_windows encontrado" -ForegroundColor Green
    $venvPath = "venv_windows"
} else {
    Write-Host "  ! Criando novo ambiente virtual..." -ForegroundColor Yellow
    python -m venv venv_windows
    $venvPath = "venv_windows"
    Write-Host "  ✓ venv_windows criado" -ForegroundColor Green
}

# 3. Determinar caminho de ativação
if (-not $venvPath) {
    if (Test-Path "venv\Scripts\activate.ps1") {
        $venvPath = "venv"
    } else {
        $venvPath = "venv_windows"
    }
}

# 4. Ativar ambiente virtual
Write-Host "`n[3/7] Ativando ambiente virtual..." -ForegroundColor Yellow
$activateScript = ".\$venvPath\Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "  ✓ Ambiente ativado" -ForegroundColor Green
} else {
    Write-Host "  ✗ Script de ativação não encontrado: $activateScript" -ForegroundColor Red
    exit 1
}

# 5. Atualizar pip
Write-Host "`n[4/7] Atualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "  ✓ pip atualizado" -ForegroundColor Green

# 6. Instalar dependências
Write-Host "`n[5/7] Instalando dependências..." -ForegroundColor Yellow
Write-Host "  (Isso pode levar alguns minutos...)" -ForegroundColor Gray
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependências instaladas" -ForegroundColor Green
} else {
    Write-Host "  ✗ Erro ao instalar dependências" -ForegroundColor Red
    exit 1
}

# 7. Verificar PyInstaller
Write-Host "`n[6/7] Verificando PyInstaller..." -ForegroundColor Yellow
$pyinstaller = pip show pyinstaller 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ PyInstaller instalado" -ForegroundColor Green
} else {
    Write-Host "  ! Instalando PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
    Write-Host "  ✓ PyInstaller instalado" -ForegroundColor Green
}

# 8. Executar build
Write-Host "`n[7/7] Executando build..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python build_exe.py

# 9. Verificar resultado
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if (Test-Path "dist\PDF2MD.exe") {
    Write-Host "   ✓ BUILD CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Executável criado em:" -ForegroundColor White
    Write-Host "  $(Resolve-Path 'dist\PDF2MD.exe')" -ForegroundColor Cyan
    Write-Host ""

    # Verificar tamanho
    $size = (Get-Item "dist\PDF2MD.exe").Length / 1MB
    Write-Host "Tamanho: $([math]::Round($size, 2)) MB" -ForegroundColor Gray
    Write-Host ""

    # Perguntar se quer abrir pasta
    Write-Host "Deseja abrir a pasta dist? (S/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -eq "S" -or $response -eq "s") {
        explorer dist
    }

    Write-Host ""
    Write-Host "Para testar o executável:" -ForegroundColor White
    Write-Host "  cd dist" -ForegroundColor Gray
    Write-Host "  .\PDF2MD.exe" -ForegroundColor Gray
    Write-Host ""

} else {
    Write-Host "   ✗ BUILD FALHOU" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verifique as mensagens de erro acima." -ForegroundColor Yellow
    Write-Host "Para mais ajuda, consulte: BUILD_GUIDE.md" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
