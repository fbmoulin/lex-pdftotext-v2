@echo off
REM Script Simples de Build - PDF Legal Extractor
REM Clique duas vezes neste arquivo para criar o executavel

echo ========================================
echo    PDF Legal Extractor - Build
echo ========================================
echo.

REM Verificar Python
echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Python nao encontrado!
    echo   Instale de: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   OK Python encontrado
echo.

REM Ativar ambiente virtual
echo [2/4] Ativando ambiente virtual...
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo   OK Ambiente ativado
) else if exist venv_windows\Scripts\activate.bat (
    call venv_windows\Scripts\activate.bat
    echo   OK Ambiente ativado
) else (
    echo   ! Criando ambiente virtual...
    python -m venv venv_windows
    call venv_windows\Scripts\activate.bat
    echo   OK Ambiente criado e ativado
)
echo.

REM Instalar dependencias
echo [3/4] Instalando dependencias...
echo   (Isso pode levar alguns minutos...)
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo   X Erro ao instalar dependencias
    pause
    exit /b 1
)
echo   OK Dependencias instaladas
echo.

REM Executar build
echo [4/4] Criando executavel...
echo ========================================
echo.
python build_exe.py
echo.

REM Verificar resultado
echo ========================================
if exist dist\PDF2MD.exe (
    echo    BUILD CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\PDF2MD.exe
    echo.
    echo Deseja abrir a pasta dist? (S/N^)
    choice /c SN /n /m "Resposta: "
    if errorlevel 2 goto :skip_open
    if errorlevel 1 explorer dist
    :skip_open
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
) else (
    echo    BUILD FALHOU
    echo ========================================
    echo.
    echo Verifique os erros acima.
    echo Para ajuda, abra: INSTRUÇÕES_BUILD_WINDOWS.md
    echo.
    pause
)
