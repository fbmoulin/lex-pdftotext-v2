# Script para atualizar codigo corrigido do WSL
# Execute no PowerShell Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Atualizando Codigo Corrigido" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$wslSource = "\\wsl`$\Ubuntu\home\fbmoulin\projetos2\pdftotext"
$windowsDest = "C:\Users\fbmou\Desktop\pdftotext_build"

Write-Host "Copiando arquivos corrigidos do WSL..." -ForegroundColor Yellow
Write-Host ""

# Lista de arquivos a copiar
$files = @(
    "app_ui.py",
    "build_exe.py",
    "src\utils\config.py"
)

$success = $true

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
        Write-Host "    OK" -ForegroundColor Green
    }
    catch {
        Write-Host "    ERRO: $_" -ForegroundColor Red
        $success = $false
    }
}

Write-Host ""
if ($success) {
    Write-Host "Arquivos atualizados com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Proximo passo:" -ForegroundColor Yellow
    Write-Host "  python build_exe.py" -ForegroundColor Cyan
} else {
    Write-Host "Alguns arquivos falharam ao copiar" -ForegroundColor Red
}

Write-Host ""
Write-Host "Pressione Enter para continuar..." -ForegroundColor Gray
Read-Host
