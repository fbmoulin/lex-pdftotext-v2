# Guia de Build e Distribuição - PDF Legal Extractor

> **Projeto da [Lex Intelligentia](https://lexintelligentia.com)** - Desenvolvido por Felipe Moulin

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Preparação do Ambiente](#preparação-do-ambiente)
3. [Criação do Ícone](#criação-do-ícone)
4. [Build do Executável](#build-do-executável)
5. [Criação do Instalador](#criação-do-instalador)
6. [Testes](#testes)
7. [Distribuição](#distribuição)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Pré-requisitos

### Software Necessário

1. **Python 3.8+** instalado no Windows
   - Download: https://www.python.org/downloads/

2. **Inno Setup 6** (para criar instalador)
   - Download: https://jrsoftware.org/isdl.php
   - Instale a versão padrão

3. **Git** (opcional, para controle de versão)
   - Download: https://git-scm.com/download/win

### Verificar Instalações

```powershell
# Verificar Python
python --version

# Verificar pip
pip --version

# Verificar Git (opcional)
git --version
```

---

## 🛠️ Preparação do Ambiente

### 1. Clonar/Baixar Projeto

```powershell
# Se usando Git
git clone https://github.com/seu-usuario/pdftotext.git
cd pdftotext

# Ou extrair ZIP manualmente
```

### 2. Criar Ambiente Virtual

```powershell
# Criar venv
python -m venv venv

# Ativar venv
.\venv\Scripts\activate

# Verificar ativação (prompt deve mostrar "(venv)")
```

### 3. Instalar Dependências

```powershell
# Instalar todas as dependências
pip install -r requirements.txt

# Verificar instalação
pip list
```

Dependências principais:
- `pywebview` - Interface gráfica
- `pymupdf` - Extração de PDF
- `pyinstaller` - Empacotamento
- `click` - CLI
- `tqdm` - Progress bars

### 4. Testar Aplicativo Localmente

```powershell
# Testar interface gráfica
python app_ui.py

# Testar CLI
python main.py --help
```

Se tudo funcionar, prossiga para o build.

---

## 🎨 Criação do Ícone

### Opção 1: Ferramenta Online (Recomendado)

1. Acesse https://icoconvert.com/
2. Faça upload de imagem PNG (512x512 ou maior)
3. Selecione resoluções: 16, 32, 48, 64, 128, 256
4. Baixe `logo.ico`
5. Salve em `/assets/logo.ico`

### Opção 2: Usar Emoji Temporário

```powershell
# Download via PowerShell (requer internet)
Invoke-WebRequest -Uri "https://emoji-favicon.vercel.app/api/📄?size=256" -OutFile "assets\logo.ico"
```

### Opção 3: Criar Manualmente

Veja instruções detalhadas em [`assets/ICON_CREATION.md`](assets/ICON_CREATION.md).

### Verificar Ícone

```powershell
# Listar propriedades
Get-ItemProperty assets\logo.ico | Select-Object *

# Abrir no visualizador padrão
start assets\logo.ico
```

---

## 🏗️ Build do Executável

### Método Automático (Recomendado)

```powershell
# Executar script de build
python build_exe.py
```

O script irá:
1. ✅ Verificar PyInstaller
2. 🧹 Limpar builds anteriores
3. 🔨 Construir executável
4. ✅ Verificar build
5. 📦 Criar pacote portável (ZIP)

### Método Manual (Avançado)

```powershell
# Build básico
pyinstaller --onefile --windowed --icon=assets\logo.ico --name=PDF2MD app_ui.py

# Build com assets incluídos
pyinstaller --onefile --windowed --icon=assets\logo.ico --name=PDF2MD `
  --add-data="assets;assets" `
  --add-data="src;src" `
  --hidden-import=fitz `
  --hidden-import=webview `
  app_ui.py
```

### Resultado

Após o build bem-sucedido:

```
dist/
└── PDF2MD.exe          # Executável (70-150 MB)
└── PDF2MD_Portable.zip # Pacote ZIP portável
```

### Testar Executável

```powershell
# Executar
.\dist\PDF2MD.exe

# Se aparecer erro, executar com logs
.\dist\PDF2MD.exe --debug
```

---

## 📦 Criação do Instalador

### 1. Abrir Inno Setup

- Inicie o **Inno Setup Compiler**
- Arquivo → Abrir... → Selecione `installer.iss`

### 2. Configurar Script (Opcional)

Edite `installer.iss` se necessário:

```ini
#define MyAppVersion "1.0.0"        ; Versão
#define MyAppPublisher "Seu Nome"   ; Autor
#define MyAppURL "https://..."      ; URL (opcional)
```

### 3. Compilar Instalador

1. No Inno Setup, clique em **Build → Compile** (ou F9)
2. Aguarde compilação (30-60 segundos)
3. Verifique mensagem "Successful compile"

### 4. Localizar Instalador

```
Output/
└── PDF2MD_Setup.exe    # Instalador (70-150 MB)
```

### 5. Testar Instalador

```powershell
# Executar instalador
.\Output\PDF2MD_Setup.exe

# Seguir assistente de instalação
# Verificar:
# - Instalação em C:\Program Files\PDF Legal Extractor
# - Ícone na Área de Trabalho
# - Ícone no Menu Iniciar
# - Funcionalidade do aplicativo
```

### 6. Testar Desinstalador

- Painel de Controle → Programas → Desinstalar um programa
- Selecione "PDF Legal Extractor"
- Clique em "Desinstalar"
- Verifique remoção completa

---

## 🧪 Testes

### Checklist de Testes

#### Build

- [ ] Executável gerado sem erros
- [ ] Tamanho razoável (< 200 MB)
- [ ] Ícone visível no arquivo .exe

#### Instalador

- [ ] Instalação sem erros
- [ ] Atalho criado no desktop
- [ ] Ícone no Menu Iniciar
- [ ] Desinstalação funciona

#### Funcionalidade

- [ ] Aplicativo abre normalmente
- [ ] Interface carrega corretamente
- [ ] **Extract**: Processa PDF individual
- [ ] **Batch**: Processa múltiplos PDFs
- [ ] **Merge**: Mescla processos
- [ ] Arquivos .md gerados corretamente
- [ ] PDFs movidos para pasta `processado/`

#### Compatibilidade

- [ ] Windows 10 Home
- [ ] Windows 10 Pro
- [ ] Windows 11

### Teste em Máquina Limpa

**Importante**: Teste em máquina sem Python instalado!

1. Use máquina virtual (VirtualBox, VMware)
2. Ou computador de colega/amigo
3. Execute instalador
4. Verifique todas as funcionalidades

---

## 📤 Distribuição

### Opções de Distribuição

#### 1. Executável Stand-Alone

**Arquivo**: `dist/PDF2MD.exe`

**Uso**:
- Copiar para qualquer pasta
- Executar diretamente
- Nenhuma instalação necessária

**Ideal para**:
- Uso pessoal
- Pendrive
- Compartilhamento rápido

#### 2. Pacote Portável (ZIP)

**Arquivo**: `dist/PDF2MD_Portable.zip`

**Conteúdo**:
- PDF2MD.exe
- LEIA-ME.txt
- README.md (opcional)

**Uso**:
- Extrair em qualquer pasta
- Executar PDF2MD.exe
- Criar atalho manualmente

**Ideal para**:
- Distribuição em rede interna
- Email/WhatsApp (se tamanho permitir)

#### 3. Instalador Windows

**Arquivo**: `Output/PDF2MD_Setup.exe`

**Uso**:
- Executar instalador
- Seguir assistente
- Aplicativo instalado no sistema

**Ideal para**:
- Distribuição profissional
- Múltiplos usuários
- Tribunal/escritório

### Compartilhamento

#### Rede Interna

```powershell
# Copiar para pasta compartilhada
copy Output\PDF2MD_Setup.exe \\servidor\compartilhado\instaladores\
```

#### Pendrive

```powershell
# Copiar para pendrive
copy Output\PDF2MD_Setup.exe E:\Instaladores\
```

#### Email (Se tamanho permitir)

- Compactar instalador com senha (opcional)
- Enviar com instruções de instalação

#### OneDrive/Google Drive

- Fazer upload do instalador
- Gerar link de compartilhamento
- Enviar link por email/WhatsApp

---

## 🐛 Troubleshooting

### Problema: PyInstaller não encontrado

```powershell
# Reinstalar PyInstaller
pip uninstall pyinstaller
pip install pyinstaller==6.0.0
```

### Problema: Erro "Module not found"

Adicione ao comando PyInstaller:

```powershell
--hidden-import=nome_do_modulo
```

Ou edite `build_exe.py` e adicione à lista `hidden_imports`.

### Problema: Antivírus bloqueia executável

**Causa**: Executável não assinado digitalmente

**Solução temporária**:
1. Windows Defender → Proteção contra vírus e ameaças
2. Gerenciar configurações
3. Adicionar exclusão → Arquivo
4. Selecione `PDF2MD.exe`

**Solução profissional**:
- Adquirir certificado de assinatura de código (Code Signing)
- Assinar executável com `signtool.exe`

### Problema: Interface não carrega

**Causa**: Assets não incluídos no build

**Solução**:
```powershell
# Reconstruir com assets
pyinstaller --onefile --windowed --icon=assets\logo.ico --name=PDF2MD `
  --add-data="assets;assets" `
  --add-data="src;src" `
  app_ui.py
```

### Problema: "VCRUNTIME140.dll not found"

**Causa**: Microsoft Visual C++ Redistributable ausente

**Solução**:
1. Baixe: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Instale no computador destino

### Problema: Tamanho do executável muito grande

**Causas**:
- Inclusão de bibliotecas desnecessárias
- Assets muito grandes

**Soluções**:
1. Use `--exclude-module` para remover módulos não usados
2. Otimize imagens em `assets/`
3. Use compressão UPX:

```powershell
pip install upx
pyinstaller --onefile --windowed --upx-dir=caminho\upx app_ui.py
```

---

## 📊 Resumo de Comandos

```powershell
# Setup
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Testar
python app_ui.py

# Build
python build_exe.py

# Compilar instalador
# (Abrir installer.iss no Inno Setup e pressionar F9)

# Distribuir
copy Output\PDF2MD_Setup.exe <destino>
```

---

## 📚 Próximos Passos

### Melhorias Futuras

1. **Assinatura Digital**
   - Adquirir certificado EV
   - Assinar executável e instalador

2. **Auto-Update**
   - Implementar verificação de versão
   - Download automático de atualizações

3. **Multi-Plataforma**
   - Build para macOS (.app, .dmg)
   - Build para Linux (AppImage, .deb)

4. **CI/CD**
   - GitHub Actions para build automático
   - Release automático no GitHub

### Recursos

- [PyInstaller Docs](https://pyinstaller.org/en/stable/)
- [Inno Setup Docs](https://jrsoftware.org/ishelp/)
- [Code Signing Guide](https://learn.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)

---

## 📝 Changelog

### Versão 1.0.0 (2025-11-01)
- Lançamento inicial
- Interface gráfica completa
- Processamento de PDFs judiciais
- Instalador Windows

---

**Desenvolvido por**: Felipe Bertrand Sardenberg Moulin
**Licença**: MIT License - Ver arquivo [LICENSE](./LICENSE)
**Suporte**: [GitHub Issues](https://github.com/fbmoulin/pdftotext/issues)
