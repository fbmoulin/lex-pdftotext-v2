# Script para Copiar do WSL e Fazer Build
# Execute este script no PowerShell Windows

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PDF Legal Extractor - Copy & Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configurações
$wslPath = "\\wsl$\Ubuntu\home\fbmoulin\projetos2\pdftotext"
$windowsPath = "$env:USERPROFILE\Desktop\pdftotext"

Write-Host "OPÇÃO 1: Copiar projeto para Windows e fazer build" -ForegroundColor Yellow
Write-Host "OPÇÃO 2: Fazer build direto no WSL (requer configuração)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Escolha (1 ou 2): " -ForegroundColor Cyan -NoNewline
$choice = Read-Host

if ($choice -eq "1") {
    # OPÇÃO 1: Copiar e buildar
    Write-Host "`n[1/3] Copiando arquivos do WSL para Windows..." -ForegroundColor Yellow
    Write-Host "  Origem: $wslPath" -ForegroundColor Gray
    Write-Host "  Destino: $windowsPath" -ForegroundColor Gray
    Write-Host ""

    if (Test-Path $wslPath) {
        Write-Host "  ✓ Pasta WSL encontrada" -ForegroundColor Green

        # Criar pasta destino
        if (Test-Path $windowsPath) {
            Write-Host "  ! Pasta destino já existe" -ForegroundColor Yellow
            Write-Host "    Deseja substituir? (S/N): " -ForegroundColor Yellow -NoNewline
            $replace = Read-Host
            if ($replace -eq "S" -or $replace -eq "s") {
                Remove-Item $windowsPath -Recurse -Force
                Write-Host "  ✓ Pasta antiga removida" -ForegroundColor Green
            } else {
                Write-Host "  ! Usando pasta existente" -ForegroundColor Yellow
                $windowsPath = "$env:USERPROFILE\Desktop\pdftotext_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
                Write-Host "  ! Nova pasta: $windowsPath" -ForegroundColor Yellow
            }
        }

        # Copiar arquivos (excluindo venv, dist, build, __pycache__)
        Write-Host "`n  Copiando arquivos..." -ForegroundColor Gray
        Write-Host "  (Isso pode levar 1-2 minutos)" -ForegroundColor Gray

        $excludeDirs = @('venv', 'venv_windows', 'dist', 'build', '__pycache__', '.git', 'node_modules')

        # Usar robocopy para cópia eficiente
        $robocopyArgs = @(
            $wslPath,
            $windowsPath,
            '/E',
            '/NFL', '/NDL', '/NJH', '/NJS', '/nc', '/ns', '/np',
            '/XD'
        ) + $excludeDirs

        $result = robocopy @robocopyArgs

        if ($LASTEXITCODE -le 7) {
            Write-Host "`n  ✓ Arquivos copiados com sucesso" -ForegroundColor Green
            Write-Host ""
        } else {
            Write-Host "`n  ✗ Erro ao copiar arquivos" -ForegroundColor Red
            Write-Host "  Tente copiar manualmente ou verifique permissões" -ForegroundColor Yellow
            exit 1
        }

        # Navegar para pasta
        Write-Host "[2/3] Navegando para pasta do projeto..." -ForegroundColor Yellow
        Set-Location $windowsPath
        Write-Host "  ✓ Pasta atual: $windowsPath" -ForegroundColor Green
        Write-Host ""

        # Executar build
        Write-Host "[3/3] Executando build..." -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""

        # Verificar Python
        try {
            $pythonVer = python --version 2>&1
            Write-Host "  ✓ $pythonVer" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Python não encontrado!" -ForegroundColor Red
            Write-Host "  Instale Python de: https://www.python.org/downloads/" -ForegroundColor Yellow
            pause
            exit 1
        }

        # Criar venv
        Write-Host "`n  Criando ambiente virtual..." -ForegroundColor Gray
        python -m venv venv_windows

        # Ativar venv
        & ".\venv_windows\Scripts\Activate.ps1"

        # Instalar dependências
        Write-Host "  Instalando dependências..." -ForegroundColor Gray
        Write-Host "  (Isso pode levar 3-5 minutos)" -ForegroundColor Gray
        python -m pip install --upgrade pip --quiet
        pip install -r requirements.txt --quiet

        # Build
        Write-Host "`n  Executando PyInstaller..." -ForegroundColor Gray
        python build_exe.py

        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan

        if (Test-Path "dist\PDF2MD.exe") {
            Write-Host "   ✓ BUILD CONCLUÍDO COM SUCESSO!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Executável criado em:" -ForegroundColor White
            Write-Host "  $windowsPath\dist\PDF2MD.exe" -ForegroundColor Cyan
            Write-Host ""

            # Abrir pasta
            explorer dist

            Write-Host "Deseja criar atalho no Desktop? (S/N): " -ForegroundColor Yellow -NoNewline
            $shortcut = Read-Host
            if ($shortcut -eq "S" -or $shortcut -eq "s") {
                $WshShell = New-Object -ComObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\PDF2MD.lnk")
                $Shortcut.TargetPath = "$windowsPath\dist\PDF2MD.exe"
                $Shortcut.WorkingDirectory = "$windowsPath\dist"
                $Shortcut.Description = "PDF Legal Extractor"
                $Shortcut.Save()
                Write-Host "  ✓ Atalho criado no Desktop" -ForegroundColor Green
            }
        } else {
            Write-Host "   ✗ BUILD FALHOU" -ForegroundColor Red
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Verifique os erros acima" -ForegroundColor Yellow
        }

    } else {
        Write-Host "  ✗ Pasta WSL não encontrada: $wslPath" -ForegroundColor Red
        Write-Host ""
        Write-Host "Verifique:" -ForegroundColor Yellow
        Write-Host "  1. WSL está instalado e rodando" -ForegroundColor Gray
        Write-Host "  2. O caminho está correto" -ForegroundColor Gray
        Write-Host "  3. Ubuntu está em execução" -ForegroundColor Gray
    }

} else {
    # OPÇÃO 2: Build direto no WSL
    Write-Host "`nOPÇÃO 2 ainda não implementada." -ForegroundColor Yellow
    Write-Host "Use OPÇÃO 1 ou copie os arquivos manualmente." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
