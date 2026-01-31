@echo off
REM Script de Build - PDF Legal Extractor v2
REM Versao melhorada com verificacao de pasta

echo ========================================
echo    PDF Legal Extractor - Build v2
echo ========================================
echo.

REM Verificar se esta na pasta correta
echo [0/5] Verificando localizacao...
if not exist "build_exe.py" (
    echo   X ERRO: Este script deve ser executado na pasta do projeto!
    echo.
    echo   A pasta atual nao contem os arquivos necessarios.
    echo.
    echo   SOLUCAO:
    echo   1. Copie a pasta do projeto do WSL para o Windows
    echo   2. Ou navegue ate a pasta correta antes de executar
    echo.
    echo   Exemplo de copia:
    echo   xcopy \\wsl$\Ubuntu\home\fbmoulin\projetos2\pdftotext C:\pdftotext /E /I
    echo.
    pause
    exit /b 1
)
echo   OK Pasta correta detectada
echo.

REM Verificar Python
echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   X Python nao encontrado!
    echo   Instale de: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo   OK Python encontrado
echo.

REM Criar ambiente virtual se nao existir
echo [2/5] Preparando ambiente virtual...
if exist venv\Scripts\activate.bat (
    echo   OK Usando venv existente
    call venv\Scripts\activate.bat
) else if exist venv_windows\Scripts\activate.bat (
    echo   OK Usando venv_windows existente
    call venv_windows\Scripts\activate.bat
) else (
    echo   ! Criando novo ambiente virtual...
    python -m venv venv_windows
    if errorlevel 1 (
        echo   X Erro ao criar ambiente virtual
        echo.
        echo   Tente executar como Administrador ou verifique permissoes
        pause
        exit /b 1
    )
    call venv_windows\Scripts\activate.bat
    echo   OK Ambiente criado e ativado
)
echo.

REM Atualizar pip
echo [3/5] Atualizando pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo   ! Aviso: Nao foi possivel atualizar pip, continuando...
) else (
    echo   OK pip atualizado
)
echo.

REM Instalar dependencias
echo [4/5] Instalando dependencias...
echo   (Isso pode levar alguns minutos...)
if not exist requirements.txt (
    echo   X Arquivo requirements.txt nao encontrado!
    echo   Verifique se esta na pasta correta do projeto.
    pause
    exit /b 1
)
pip install -r requirements.txt
if errorlevel 1 (
    echo   X Erro ao instalar dependencias
    echo.
    echo   Tente:
    echo   - Executar como Administrador
    echo   - Verificar conexao com internet
    echo   - pip install -r requirements.txt --verbose
    pause
    exit /b 1
)
echo   OK Dependencias instaladas
echo.

REM Verificar PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo   ! Instalando PyInstaller...
    pip install pyinstaller
)

REM Executar build
echo [5/5] Criando executavel...
echo ========================================
echo.
python build_exe.py
set BUILD_RESULT=%ERRORLEVEL%
echo.

REM Verificar resultado
echo ========================================
if %BUILD_RESULT% EQU 0 (
    if exist dist\PDF2MD.exe (
        echo    BUILD CONCLUIDO COM SUCESSO!
        echo ========================================
        echo.
        echo Executavel criado em:
        cd
        echo dist\PDF2MD.exe
        echo.

        REM Mostrar tamanho
        for %%A in (dist\PDF2MD.exe) do (
            set size=%%~zA
            set /a size_mb=!size! / 1048576
        )
        echo Tamanho: aproximadamente 50-100 MB
        echo.

        echo Deseja abrir a pasta dist? (S/N)
        choice /c SN /n /m "Resposta: "
        if errorlevel 2 goto :skip_open
        if errorlevel 1 start explorer dist
        :skip_open
        echo.
    ) else (
        echo    BUILD COMPLETOU mas executavel nao encontrado
        echo ========================================
        echo.
        echo Verifique a pasta dist manualmente.
    )
) else (
    echo    BUILD FALHOU
    echo ========================================
    echo.
    echo Codigo de erro: %BUILD_RESULT%
    echo.
    echo Verifique os erros acima.
    echo.
    echo Dicas:
    echo - Execute como Administrador
    echo - Desabilite antivirus temporariamente
    echo - Verifique espaco em disco
    echo - Consulte: INSTRUÇÕES_BUILD_WINDOWS.md
)
echo.
echo Pressione qualquer tecla para sair...
pause >nul
