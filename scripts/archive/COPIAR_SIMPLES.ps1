# Script Simples - Copiar e Buildar
# Execute no PowerShell Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Copiar Projeto e Fazer Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuracoes
$wslSource = "\\wsl`$\Ubuntu\home\fbmoulin\projetos2\pdftotext"
$windowsDest = "$env:USERPROFILE\Desktop\pdftotext"

# Verificar origem
Write-Host "[1/4] Verificando pasta WSL..." -ForegroundColor Yellow
if (-not (Test-Path $wslSource)) {
    Write-Host "  ERRO: Pasta WSL nao encontrada!" -ForegroundColor Red
    Write-Host "  Caminho: $wslSource" -ForegroundColor Gray
    pause
    exit 1
}
Write-Host "  OK - Pasta encontrada" -ForegroundColor Green
Write-Host ""

# Perguntar se quer substituir
if (Test-Path $windowsDest) {
    Write-Host "Pasta de destino ja existe!" -ForegroundColor Yellow
    Write-Host "Deseja substituir? (S/N): " -ForegroundColor Yellow -NoNewline
    $resposta = Read-Host
    if ($resposta -eq "S" -or $resposta -eq "s") {
        Remove-Item $windowsDest -Recurse -Force
        Write-Host "Pasta antiga removida" -ForegroundColor Green
    } else {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $windowsDest = "$env:USERPROFILE\Desktop\pdftotext_$timestamp"
        Write-Host "Usando nova pasta: $windowsDest" -ForegroundColor Yellow
    }
}

# Copiar arquivos
Write-Host ""
Write-Host "[2/4] Copiando arquivos..." -ForegroundColor Yellow
Write-Host "  De: $wslSource" -ForegroundColor Gray
Write-Host "  Para: $windowsDest" -ForegroundColor Gray
Write-Host "  (Aguarde 1-2 minutos...)" -ForegroundColor Gray
Write-Host ""

$excludes = @('venv', 'venv_windows', 'dist', 'build', '__pycache__', '.git')
$robocopyArgs = @($wslSource, $windowsDest, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/XD') + $excludes

$null = robocopy @robocopyArgs

if ($LASTEXITCODE -le 7) {
    Write-Host "  OK - Arquivos copiados" -ForegroundColor Green
} else {
    Write-Host "  ERRO ao copiar!" -ForegroundColor Red
    pause
    exit 1
}

# Navegar para pasta
Write-Host ""
Write-Host "[3/4] Preparando ambiente..." -ForegroundColor Yellow
Set-Location $windowsDest

# Verificar Python
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO: Python nao encontrado!" -ForegroundColor Red
    Write-Host "  Instale de: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "  OK - $pythonCheck" -ForegroundColor Green

# Criar venv
Write-Host "  Criando ambiente virtual..." -ForegroundColor Gray
python -m venv venv_windows
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO ao criar venv!" -ForegroundColor Red
    pause
    exit 1
}

# Ativar venv
& ".\venv_windows\Scripts\Activate.ps1"

# Instalar dependencias
Write-Host "  Instalando dependencias (3-5 minutos)..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO ao instalar dependencias!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  OK - Dependencias instaladas" -ForegroundColor Green

# Build
Write-Host ""
Write-Host "[4/4] Executando build (2-3 minutos)..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python build_exe.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Verificar resultado
if (Test-Path "dist\PDF2MD.exe") {
    Write-Host "   BUILD CONCLUIDO COM SUCESSO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Executavel criado em:" -ForegroundColor White
    Write-Host "  $windowsDest\dist\PDF2MD.exe" -ForegroundColor Cyan
    Write-Host ""

    # Abrir pasta
    explorer dist

    Write-Host "Deseja criar atalho no Desktop? (S/N): " -ForegroundColor Yellow -NoNewline
    $atalho = Read-Host
    if ($atalho -eq "S" -or $atalho -eq "s") {
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\PDF2MD.lnk")
        $Shortcut.TargetPath = "$windowsDest\dist\PDF2MD.exe"
        $Shortcut.WorkingDirectory = "$windowsDest\dist"
        $Shortcut.Save()
        Write-Host "  Atalho criado!" -ForegroundColor Green
    }
} else {
    Write-Host "   BUILD FALHOU" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verifique os erros acima" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Pressione Enter para sair..." -ForegroundColor Gray
Read-Host
