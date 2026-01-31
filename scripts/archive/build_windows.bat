@echo off
REM ============================================================
REM PDF Legal Extractor - Windows Build Script (CMD)
REM ============================================================

echo ============================================================
echo PDF Legal Extractor - Windows Build Script
echo ============================================================
echo.

REM 1. Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado! Instale Python 3.8+ de python.org
    pause
    exit /b 1
)
python --version
echo.

REM 2. Criar ambiente virtual
echo [2/4] Criando ambiente virtual limpo...
if exist venv_build (
    echo    Removendo ambiente antigo...
    rmdir /s /q venv_build
)
python -m venv venv_build
if errorlevel 1 (
    echo ERRO: Falha ao criar ambiente virtual
    pause
    exit /b 1
)
echo    OK
echo.

REM 3. Instalar dependências
echo [3/4] Instalando dependencias...
call venv_build\Scripts\activate.bat
echo    Atualizando pip...
python -m pip install --upgrade pip --quiet
echo    Instalando PyMuPDF, click, tqdm, pywebview, pyinstaller...
pip install PyMuPDF click tqdm pywebview pyinstaller --quiet
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias
    pause
    exit /b 1
)
echo    OK
echo.

REM 4. Executar build
echo [4/4] Executando build...
echo.
python build_exe.py
if errorlevel 1 (
    echo.
    echo ERRO: Build falhou!
    pause
    exit /b 1
)

REM 5. Resumo
echo.
echo ============================================================
echo Build concluido com sucesso!
echo ============================================================
echo.
echo Arquivos gerados:
dir /b dist\PDF2MD.exe 2>nul && echo    [OK] dist\PDF2MD.exe
dir /b dist\PDF2MD_Portable.zip 2>nul && echo    [OK] dist\PDF2MD_Portable.zip
echo.
echo Proximos passos:
echo 1. Testar: .\dist\PDF2MD.exe
echo 2. Criar instalador com Inno Setup (installer.iss)
echo 3. Distribuir: dist\PDF2MD.exe ou dist\PDF2MD_Portable.zip
echo.
pause
