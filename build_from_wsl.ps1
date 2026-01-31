# ========================================
# REBUILD COMPLETO - Copia + Build + Test
# ========================================
# Execute este script no PowerShell Windows
# Ele fara tudo automaticamente!

param(
    [switch]$SkipTest
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "       PDF2MD - REBUILD COMPLETO COM FIX PYWEBVIEW             " -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

# ========================================
# PASSO 1: COPIAR CODIGO CORRIGIDO
# ========================================

Write-Host "[1/3] Copiando codigo corrigido do WSL..." -ForegroundColor Yellow
Write-Host ""

$wslSource = "\\wsl`$\Ubuntu\home\fbmoulin\projetos2\pdftotext"
$windowsDest = "C:\Users\fbmou\Desktop\pdftotext_build"

# Lista de arquivos a copiar
$files = @(
    "app_ui.py",
    "build_exe.py",
    "src\utils\config.py"
)

$copySuccess = $true

foreach ($file in $files) {
    $source = Join-Path $wslSource $file
    $dest = Join-Path $windowsDest $file

    Write-Host "  Copiando: $file" -ForegroundColor Gray

    try {
        # Criar diretorio se necessario
        $destDir = Split-Path -Parent $dest
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }

        # Copiar arquivo
        Copy-Item -Path $source -Destination $dest -Force
        Write-Host "    [OK]" -ForegroundColor Green
    }
    catch {
        Write-Host "    [ERRO]: $_" -ForegroundColor Red
        $copySuccess = $false
    }
}

if (-not $copySuccess) {
    Write-Host ""
    Write-Host "[ERRO] Erro ao copiar arquivos. Abortando." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Arquivos copiados com sucesso!" -ForegroundColor Green
Write-Host ""

# ========================================
# PASSO 2: REBUILDAR EXECUTAVEIS
# ========================================

Write-Host "[2/3] Reconstruindo executaveis..." -ForegroundColor Yellow
Write-Host ""

Set-Location $windowsDest

# Ativar ambiente virtual
Write-Host "  Ativando ambiente virtual..." -ForegroundColor Gray
& ".\venv_windows\Scripts\Activate.ps1"

# Executar build
Write-Host "  Executando PyInstaller..." -ForegroundColor Gray
Write-Host ""

try {
    python build_exe.py

    if ($LASTEXITCODE -ne 0) {
        throw "Build falhou com codigo $LASTEXITCODE"
    }
}
catch {
    Write-Host ""
    Write-Host "[ERRO] Erro no build: $_" -ForegroundColor Red
    exit 1
}

# ========================================
# PASSO 3: VERIFICAR RESULTADO
# ========================================

Write-Host ""
Write-Host "[3/3] Verificando resultado..." -ForegroundColor Yellow
Write-Host ""

$debugExe = "dist\PDF2MD_debug.exe"
$releaseExe = "dist\PDF2MD.exe"

if (Test-Path $debugExe) {
    $debugSize = (Get-Item $debugExe).Length / 1MB
    $debugSizeStr = [math]::Round($debugSize, 1)
    Write-Host "  [OK] PDF2MD_debug.exe criado ($debugSizeStr MB)" -ForegroundColor Green
} else {
    Write-Host "  [ERRO] PDF2MD_debug.exe NAO encontrado" -ForegroundColor Red
}

if (Test-Path $releaseExe) {
    $releaseSize = (Get-Item $releaseExe).Length / 1MB
    $releaseSizeStr = [math]::Round($releaseSize, 1)
    Write-Host "  [OK] PDF2MD.exe criado ($releaseSizeStr MB)" -ForegroundColor Green
} else {
    Write-Host "  [ERRO] PDF2MD.exe NAO encontrado" -ForegroundColor Red
}

# ========================================
# RESULTADO FINAL
# ========================================

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Green
Write-Host "                   [OK] BUILD CONCLUIDO!                       " -ForegroundColor Green
Write-Host "===============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "PROXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Testar versao DEBUG:" -ForegroundColor White
Write-Host "   .\dist\PDF2MD_debug.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Deve abrir SEM erro de recursao" -ForegroundColor Gray
Write-Host "   Deve abrir SEM mensagem 'Modo Demonstracao'" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Se funcionar, usar versao RELEASE:" -ForegroundColor White
Write-Host "   .\dist\PDF2MD.exe" -ForegroundColor Cyan
Write-Host ""

# Opcao de abrir automaticamente
if (-not $SkipTest) {
    Write-Host ""
    $response = Read-Host "Deseja abrir PDF2MD_debug.exe agora para testar? (S/N)"

    if ($response -eq 'S' -or $response -eq 's') {
        Write-Host ""
        Write-Host "Abrindo PDF2MD_debug.exe..." -ForegroundColor Yellow
        Write-Host "Verifique se:" -ForegroundColor Gray
        Write-Host "  - Console abre sem erros de recursao" -ForegroundColor Gray
        Write-Host "  - Aplicativo abre sem 'Modo Demonstracao'" -ForegroundColor Gray
        Write-Host "  - Botao 'Extrair PDF' funciona" -ForegroundColor Gray
        Write-Host ""

        Start-Process ".\dist\PDF2MD_debug.exe"
    }
}

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Gray
Write-Host ""
