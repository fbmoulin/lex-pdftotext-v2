# Build do Executável Windows

Este guia explica como criar o executável Windows (.exe) do PDF Legal Extractor.

## Pré-requisitos

- **Python 3.8+** instalado no Windows ([python.org/downloads](https://www.python.org/downloads/))
- Durante a instalação do Python, marque "Add Python to PATH"

## Opção 1: Script Automático (Recomendado)

### Usando PowerShell (Windows 10/11):

```powershell
# 1. Abrir PowerShell no diretório do projeto
cd C:\Projetos2\pdftotext
# ou pelo WSL:
cd \\wsl.localhost\Ubuntu\home\fbmoulin\projetos2\pdftotext

# 2. Executar script de build
.\build_windows.ps1
```

**Nota:** Se receber erro de execução de scripts, execute primeiro:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Usando CMD/Prompt de Comando:

```cmd
REM 1. Abrir CMD no diretório do projeto
cd C:\Projetos2\pdftotext

REM 2. Executar script de build
build_windows.bat
```

## Opção 2: Manual

Se preferir fazer manualmente:

```powershell
# 1. Criar ambiente virtual limpo
python -m venv venv_build

# 2. Ativar ambiente
venv_build\Scripts\activate

# 3. Instalar dependências
pip install PyMuPDF click tqdm pywebview pyinstaller

# 4. Executar build
python build_exe.py

# 5. Desativar ambiente
deactivate
```

## Resultado

Após o build, você terá:

- **`dist\PDF2MD.exe`** - Executável stand-alone (45-50 MB)
- **`dist\PDF2MD_Portable.zip`** - Pacote portável com README

## Criar Instalador (Opcional)

Para criar um instalador profissional:

1. **Baixe Inno Setup**: [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)

2. **Compile o instalador**:
   - Abra `installer.iss` no Inno Setup Compiler
   - Pressione **F9** ou clique em **Build → Compile**

3. **Resultado**: `Output\PDF2MD_Setup.exe`

## Distribuição

Você pode distribuir de 3 formas:

### 1. Executável Stand-Alone
- **Arquivo**: `dist\PDF2MD.exe`
- **Uso**: Copiar e executar diretamente
- **Vantagem**: Mais simples, sem instalação

### 2. Pacote Portável
- **Arquivo**: `dist\PDF2MD_Portable.zip`
- **Conteúdo**: Executável + README + instruções
- **Uso**: Extrair e executar
- **Vantagem**: Incluí documentação

### 3. Instalador Windows
- **Arquivo**: `Output\PDF2MD_Setup.exe`
- **Uso**: Executar instalador, cria ícones no menu iniciar e desktop
- **Vantagem**: Instalação profissional, integração com Windows

## Solução de Problemas

### Erro: "Python não encontrado"
- Instale Python de [python.org](https://www.python.org/downloads/)
- Durante instalação, marque "Add Python to PATH"
- Reinicie o terminal/PowerShell

### Erro: "Executável muito grande (>500MB)"
- Certifique-se de usar o script automático que cria ambiente virtual limpo
- **NÃO** execute o build no ambiente conda/anaconda global

### Erro: Windows Defender bloqueia executável
- Normal para executáveis não assinados
- Clique "Mais informações" → "Executar assim mesmo"
- Para distribuição profissional: considere assinar digitalmente (Code Signing)

### Erro: PyInstaller não gera .exe
- Verifique se está rodando no Windows (não no WSL)
- No WSL, PyInstaller gera executável Linux

## Build no Linux/WSL

Se quiser executável Linux:

```bash
# No WSL/Linux
cd /home/fbmoulin/projetos2/pdftotext

# Criar ambiente virtual
python3 -m venv venv_build
source venv_build/bin/activate

# Instalar dependências
pip install PyMuPDF click tqdm pywebview pyinstaller

# Build
python build_exe.py

# Resultado: dist/PDF2MD (sem extensão .exe)
```

## Notas Técnicas

- **Tamanho do executável**: ~45-50 MB (PyMuPDF é a maior dependência)
- **Tempo de build**: ~30-60 segundos
- **Compatibilidade**: Windows 10/11 (x64)
- **Antivírus**: Pode gerar falsos positivos (executáveis PyInstaller sem assinatura)

## Suporte

Para problemas, consulte:
- [BUILD_GUIDE.md](BUILD_GUIDE.md) - Guia completo de build
- [README.md](README.md) - Documentação do projeto
