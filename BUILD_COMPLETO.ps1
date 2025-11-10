# Build Completo - PDF Legal Extractor
# Execute no PowerShell Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PDF Legal Extractor - Build Completo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuracoes
$wslSource = "\\wsl`$\Ubuntu\home\fbmoulin\projetos2\pdftotext"
$windowsDest = "$env:USERPROFILE\Desktop\pdftotext_build"

# Verificar origem
Write-Host "[1/5] Verificando pasta WSL..." -ForegroundColor Yellow
if (-not (Test-Path $wslSource)) {
    Write-Host "  ERRO: Pasta WSL nao encontrada!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  OK - Pasta encontrada" -ForegroundColor Green

# Remover destino se existir
if (Test-Path $windowsDest) {
    Write-Host "  Removendo pasta antiga..." -ForegroundColor Gray
    Remove-Item $windowsDest -Recurse -Force -ErrorAction SilentlyContinue
}

# Criar pasta destino
Write-Host ""
Write-Host "[2/5] Criando pasta de destino..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $windowsDest -Force | Out-Null
Write-Host "  OK - Pasta criada: $windowsDest" -ForegroundColor Green

# Copiar arquivos importantes
Write-Host ""
Write-Host "[3/5] Copiando arquivos..." -ForegroundColor Yellow
Write-Host "  (Aguarde 1-2 minutos...)" -ForegroundColor Gray

$excludeDirs = @('venv', 'venv_windows', 'dist', 'build', '__pycache__', '.git', '.pytest_cache', 'node_modules')

# Copiar todos os arquivos exceto pastas excluidas
Get-ChildItem -Path $wslSource -Recurse -Force | Where-Object {
    $item = $_
    $exclude = $false
    foreach ($dir in $excludeDirs) {
        if ($item.FullName -like "*\$dir\*" -or $item.Name -eq $dir) {
            $exclude = $true
            break
        }
    }
    -not $exclude
} | ForEach-Object {
    $targetPath = $_.FullName.Replace($wslSource, $windowsDest)

    if ($_.PSIsContainer) {
        New-Item -ItemType Directory -Path $targetPath -Force -ErrorAction SilentlyContinue | Out-Null
    } else {
        $targetDir = Split-Path -Parent $targetPath
        if (-not (Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }
        Copy-Item -Path $_.FullName -Destination $targetPath -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "  OK - Arquivos copiados" -ForegroundColor Green

# Navegar para pasta
Write-Host ""
Write-Host "[4/5] Preparando ambiente..." -ForegroundColor Yellow
Set-Location $windowsDest

# Verificar Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO: Python nao encontrado!" -ForegroundColor Red
    Write-Host "  Instale: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "  OK - $pythonVersion" -ForegroundColor Green

# Criar venv
Write-Host "  Criando ambiente virtual..." -ForegroundColor Gray
python -m venv venv_windows 2>&1 | Out-Null

if (-not (Test-Path "venv_windows\Scripts\Activate.ps1")) {
    Write-Host "  ERRO ao criar venv!" -ForegroundColor Red
    pause
    exit 1
}

# Ativar venv
& ".\venv_windows\Scripts\Activate.ps1"

# Atualizar pip
Write-Host "  Atualizando pip..." -ForegroundColor Gray
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# Instalar dependencias
Write-Host "  Instalando dependencias..." -ForegroundColor Gray
Write-Host "  (Isso pode levar 3-5 minutos)" -ForegroundColor Gray
pip install -r requirements.txt --quiet 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERRO ao instalar dependencias!" -ForegroundColor Red
    Write-Host "  Tentando instalar com output visivel..." -ForegroundColor Yellow
    pip install -r requirements.txt
    pause
    exit 1
}

Write-Host "  OK - Dependencias instaladas" -ForegroundColor Green

# Build
Write-Host ""
Write-Host "[5/5] Executando build..." -ForegroundColor Yellow
Write-Host "  (Isso pode levar 2-5 minutos)" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python build_exe.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Verificar resultado
if (Test-Path "dist\PDF2MD.exe") {
    Write-Host "   BUILD CONCLUIDO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    $exeSize = (Get-Item "dist\PDF2MD.exe").Length / 1MB
    $exeSizeRounded = [math]::Round($exeSize, 2)

    Write-Host "Executavel criado:" -ForegroundColor White
    Write-Host "  Local: $windowsDest\dist\PDF2MD.exe" -ForegroundColor Cyan
    Write-Host "  Tamanho: $exeSizeRounded MB" -ForegroundColor Gray
    Write-Host ""

    # Abrir pasta
    Start-Process explorer.exe -ArgumentList "$windowsDest\dist"

    Write-Host "Criar atalho no Desktop? (S/N): " -ForegroundColor Yellow -NoNewline
    $criar = Read-Host

    if ($criar -eq "S" -or $criar -eq "s") {
        $WshShell = New-Object -ComObject WScript.Shell
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $Shortcut = $WshShell.CreateShortcut("$desktopPath\PDF2MD.lnk")
        $Shortcut.TargetPath = "$windowsDest\dist\PDF2MD.exe"
        $Shortcut.WorkingDirectory = "$windowsDest\dist"
        $Shortcut.Description = "PDF Legal Extractor"
        $Shortcut.Save()
        Write-Host "  Atalho criado no Desktop!" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "SUCESSO! Pode usar o executavel agora." -ForegroundColor Green

} else {
    Write-Host "   BUILD FALHOU" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verifique os erros acima." -ForegroundColor Yellow
    Write-Host "A pasta do projeto esta em: $windowsDest" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Pressione Enter para sair..." -ForegroundColor Gray
Read-Host
