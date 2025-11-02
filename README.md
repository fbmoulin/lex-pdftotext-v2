# PDF Legal Text Extractor

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/fbmoulin/pdftotext)
[![PyPI](https://img.shields.io/badge/GUI-PyWebview-green.svg)](https://pywebview.flowrl.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Projeto criado por [Lex Intelligentia](https://lexintelligentia.com)** - Soluções inteligentes para análise jurídica

Extração e estruturação de texto de documentos PDF processuais brasileiros (formato PJe).

**Disponível em duas versões**:
- 🖥️ **Interface Gráfica (GUI)** - Aplicativo Windows stand-alone
- ⌨️ **Interface de Linha de Comando (CLI)** - Terminal/script

## 🎯 Objetivo

Este projeto extrai texto completo de PDFs de processos judiciais brasileiros, removendo elementos irrelevantes (logos, números de página) e estruturando o conteúdo em formato Markdown hierárquico com metadados, otimizado para:

- **Pipelines RAG** (Retrieval Augmented Generation)
- **Sistemas de análise jurídica** (Lex Intelligentia, FIRAC+)
- **Automações** (n8n, Zapier)
- **Bancos de dados vetoriais** (Qdrant, Pinecone, Chroma)

## ✨ Funcionalidades

✅ Extração rápida e precisa de texto (PyMuPDF)
✅ Remoção automática de ruído (logos, URLs, códigos de verificação)
✅ Normalização de texto (conversão de UPPERCASE excessivo para sentence case)
✅ Extração de metadados jurídicos:
  - Números de processo (formato CNJ)
  - IDs de documentos (Num. XXXXXXXX)
  - Partes (autor, réu)
  - Advogados e OABs
  - Juízes
  - Datas de assinatura digital
  - Vara/tribunal

✅ Detecção automática de tipo de documento (petição inicial, decisão, certidão)
✅ Saída estruturada em Markdown hierárquico
✅ Processamento em lote (batch)
✅ **Merge inteligente** - Mescla automaticamente PDFs do mesmo processo
✅ **Organização automática** - Move PDFs processados para pasta separada
✅ **Busca recursiva** - Processa subpastas (processos com múltiplos volumes)
✅ CLI amigável

## 📦 Instalação

### 1. Clone o repositório (ou baixe os arquivos)

```bash
cd /home/fbmoulin/projetos2/pdftotext
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Interface Gráfica (GUI)

#### Windows - Aplicativo Stand-Alone

Se você tem o executável `PDF2MD.exe`:

1. Execute `PDF2MD.exe`
2. Escolha uma das abas:
   - **Extrair PDF**: Processa um único PDF
   - **Processamento em Lote**: Processa múltiplos PDFs
   - **Mesclar Processos**: Agrupa PDFs do mesmo processo
3. Selecione arquivos/pasta
4. Configure opções (normalização, metadados)
5. Clique no botão para processar

**Vantagens da GUI**:
- ✅ Não requer Python instalado
- ✅ Interface visual intuitiva
- ✅ Ideal para usuários não-técnicos
- ✅ Instalador Windows disponível

**Para desenvolvedores**:

```bash
# Executar interface gráfica em modo desenvolvimento
python app_ui.py

# Criar executável Windows
python build_exe.py
```

Veja [BUILD_GUIDE.md](BUILD_GUIDE.md) para instruções completas de empacotamento.

---

### Interface de Linha de Comando (CLI)

#### Comando Básico: Extrair um PDF

```bash
python main.py extract documento.pdf
```

Isso gera `documento.md` com o texto estruturado.

### Especificar arquivo de saída

```bash
python main.py extract documento.pdf -o saida.md
```

### Opções de extração

```bash
# Saída em texto plano (sem Markdown)
python main.py extract documento.pdf --format txt

# Sem normalização de texto (preservar UPPERCASE)
python main.py extract documento.pdf --no-normalize

# Sem metadados no cabeçalho
python main.py extract documento.pdf --no-metadata

# Com estruturação automática de seções
python main.py extract documento.pdf --structured
```

### Processar múltiplos PDFs (batch)

```bash
# Processar todos PDFs em uma pasta
python main.py batch ./data/input

# Especificar pasta de saída
python main.py batch ./data/input -o ./data/output
```

### Mesclar PDFs do mesmo processo

```bash
# Mescla automaticamente PDFs com o mesmo número de processo
python main.py merge ./data/input

# Mesclar apenas um processo específico
python main.py merge ./data/input --process-number 0000865-32.2016.8.08.0012
```

**Como funciona:**
1. Busca PDFs recursivamente em `data/input/` e subpastas
2. Agrupa automaticamente por número de processo (extraído do conteúdo ou nome)
3. Cria um arquivo mesclado por processo (apenas se tiver 2+ PDFs)
4. Move PDFs processados para `data/input/processado/` preservando estrutura

**Exemplo de saída:**
```
📊 Encontrados 3 processo(s) diferente(s):
   • Processo 0000865-32.2016.8.08.0012: 2 arquivo(s)
   • Processo 0127351-38.2011.8.08.0012: 7 arquivo(s)
   • Processo 5015904-66.2025.8.08.0012: 1 arquivo(s)

📝 Mesclando 2 arquivo(s) do processo 0000865-32.2016.8.08.0012...
   ✅ Salvo em: data/input/processo_0000865-32.2016.8.08.0012_merged.md
   📦 2 PDF(s) movido(s) para: data/input/processado

⏭️  Processo 5015904-66.2025.8.08.0012: apenas 1 arquivo, pulando merge...
```

### Ver informações sem extrair texto completo

```bash
python main.py info documento.pdf
```

Mostra:
- Metadados do PDF (páginas, autor, data)
- Número do processo
- Partes
- Advogados
- IDs dos documentos
- Tipo de documento

### Ajuda

```bash
python main.py --help
python main.py extract --help
python main.py batch --help
python main.py merge --help
```

## 📂 Estrutura do Projeto

```
pdftotext/
├── src/                     # Código-fonte principal
│   ├── extractors/          # Extração de texto (PyMuPDF)
│   │   ├── base.py          # Interface abstrata
│   │   └── pymupdf_extractor.py
│   ├── processors/          # Processamento de texto
│   │   ├── text_normalizer.py    # Normalização (UPPERCASE → sentence case)
│   │   └── metadata_parser.py    # Extração de metadados
│   ├── formatters/          # Formatação de saída
│   │   └── markdown_formatter.py # Markdown estruturado
│   └── utils/
│       ├── patterns.py      # Padrões regex para PJe
│       ├── exceptions.py    # Exceções customizadas
│       └── validators.py    # Validação de PDFs
├── assets/                  # Assets para GUI
│   ├── html/
│   │   └── index.html       # Interface web
│   ├── logo.ico             # Ícone do aplicativo (criar)
│   └── ICON_CREATION.md     # Guia para criar ícone
├── data/                    # Dados do usuário
│   ├── input/               # PDFs a processar
│   │   ├── processo-1.pdf              # PDFs individuais
│   │   ├── 0000865-32.2016.8.08.0012/  # Subpasta para múltiplos volumes
│   │   │   ├── volume-1.pdf
│   │   │   └── volume-2.pdf
│   │   └── processado/                 # PDFs já processados (auto-criado)
│   │       └── [mesma estrutura do input]
│   └── output/              # Textos extraídos (.md gerados aqui)
├── tests/                   # Testes unitários
├── main.py                  # CLI principal
├── app_ui.py                # GUI principal (PyWebview)
├── build_exe.py             # Script de build
├── installer.iss            # Script Inno Setup
├── requirements.txt
├── BUILD_GUIDE.md           # Guia de build e distribuição
├── SECURITY_IMPROVEMENTS.md # Melhorias de segurança
├── CHANGELOG_SECURITY.md    # Changelog de segurança
├── WORKFLOW.md              # Guia completo de uso CLI
├── OCR_GUIDE.md             # Guia para PDFs escaneados
├── CLAUDE.md                # Instruções para Claude Code
└── README.md
```

## 📁 Organização de Arquivos

### Processos com Múltiplos Volumes

Para processos com vários PDFs (volumes, anexos), organize em **subpastas**:

```bash
mkdir -p data/input/0000865-32.2016.8.08.0012
mv volume*.pdf data/input/0000865-32.2016.8.08.0012/
```

### Pasta 'processado'

Após extração/merge, PDFs são **automaticamente movidos** para `data/input/processado/`:

- **Organização**: Separa PDFs já processados dos pendentes
- **Segurança**: Evita reprocessamento acidental
- **Limpeza**: Após validar os .md, pode deletar PDFs processados

**Veja detalhes completos em:** [WORKFLOW.md](./WORKFLOW.md)

## 🔧 Uso Programático (Python)

```python
from src.extractors import PyMuPDFExtractor
from src.processors import TextNormalizer, MetadataParser
from src.formatters import MarkdownFormatter

# Extrair texto
with PyMuPDFExtractor("documento.pdf") as extractor:
    raw_text = extractor.extract_text()
    page_count = extractor.get_page_count()

# Normalizar
normalizer = TextNormalizer()
clean_text = normalizer.normalize(raw_text)

# Extrair metadados
parser = MetadataParser()
metadata = parser.parse(clean_text)

print(f"Processo: {metadata.process_number}")
print(f"IDs: {metadata.document_ids}")
print(f"Advogados: {metadata.lawyers}")

# Formatar como Markdown
formatter = MarkdownFormatter()
markdown = formatter.format(clean_text, metadata)

# Salvar
MarkdownFormatter.save_to_file(markdown, "output.md")
```

### Formato RAG (chunks com metadados)

```python
formatter = MarkdownFormatter()
chunks = formatter.format_for_rag(clean_text, metadata, chunk_size=1000)

for chunk in chunks:
    print(f"Chunk {chunk['chunk_index']}:")
    print(chunk['text'][:100])
    print(chunk['metadata'])
```

## 📋 Exemplo de Saída

### Entrada: `5022930-18.2025.8.08.0012.pdf`

### Saída: `5022930-18.2025.8.08.0012.md`

```markdown
# Processo 5022930-18.2025.8.08.0012

## Metadados

**Processo:** 5022930-18.2025.8.08.0012
**IDs dos Documentos:** 79670915, 79670916, 79670917
**Órgão Julgador:** 2ª Vara Cível de Cariacica/ES
**Valor da Causa:** R$ 40.000,00
**Autor(a):** Ana Luiza da Cruz Santos Alves
**Réu/Ré:** SAMP Espírito Santo Assistência Médica S.A.

**Advogados:**
- Edvaldo Souza de Oliveira – OAB/ES 43.156

**Datas de Assinatura:** 25/09/2025, 30/09/2025

**Tipo de Documento:** Petição Inicial

---

## Texto Integral

Excelentíssimo senhor doutor juiz de direito da vara cível da comarca de Cariacica/ES

Ana Luiza da Cruz Santos Alves, representada por sua mãe Ana Cristina da Cruz dos Santos...

[texto completo normalizado]
```

## 🧪 Testes

```bash
# Rodar testes (quando implementados)
pytest tests/
```

## 🔍 Padrões Regex Suportados

O projeto detecta automaticamente:

- **Números de processo**: `NNNNNNN-DD.AAAA.J.TT.OOOO` (formato CNJ)
- **IDs de documentos**: `Num. 12345678`
- **OABs**: `Nome Completo – OAB/UF 12345`
- **Assinaturas digitais**: `assinado eletronicamente em DD/MM/AAAA`
- **Partes**: `Autor:`, `Réu:`, `Requerente:`
- **Valor da causa**: `Valor da causa: R$ XX.XXX,XX`
- **Varas**: `Nª Vara ...`

## 🤝 Integração com RAG

O formato Markdown gerado é otimizado para:

1. **Chunking semântico** - Seções hierárquicas facilitam divisão em chunks
2. **Preservação de contexto** - Metadados mantidos com o texto
3. **Tokenização limpa** - Texto normalizado melhora embeddings
4. **Indexação** - Estrutura clara para busca vetorial

### Exemplo de Pipeline RAG

```python
from src import PyMuPDFExtractor, TextNormalizer, MetadataParser, MarkdownFormatter

# Pipeline completo
def process_for_rag(pdf_path):
    # 1. Extrair
    with PyMuPDFExtractor(pdf_path) as extractor:
        text = extractor.extract_text()

    # 2. Normalizar
    normalizer = TextNormalizer()
    clean = normalizer.normalize(text)

    # 3. Metadados
    parser = MetadataParser()
    metadata = parser.parse(clean)

    # 4. Chunks para RAG
    formatter = MarkdownFormatter()
    chunks = formatter.format_for_rag(clean, metadata, chunk_size=1000)

    return chunks

# Usar com LangChain, LlamaIndex, etc.
chunks = process_for_rag("processo.pdf")
# → ingerir em vector store
```

## 📚 Bibliotecas Utilizadas

- **PyMuPDF (fitz)** - Extração rápida e precisa de texto
- **pdfplumber** - Fallback para tabelas (futuro)
- **click** - Interface CLI
- **tqdm** - Barras de progresso
- **pytest** - Testes

## 🛠️ Melhorias Futuras

- [ ] Suporte nativo a OCR para PDFs escaneados (veja [OCR_GUIDE.md](./OCR_GUIDE.md) para soluções atuais)
- [ ] Extração de tabelas estruturadas
- [ ] Detecção automática de seções (NLP)
- [ ] API REST (FastAPI)
- [ ] Interface web
- [ ] Exportação JSON estruturado
- [ ] Integração direta com vector databases
- [ ] Análise FIRAC+ automática

## 📄 Licença

Este projeto é licenciado sob a **MIT License**.

Copyright (c) 2025 Lex Intelligentia
Desenvolvido por Felipe Bertrand Sardenberg Moulin

Você tem permissão para usar, copiar, modificar, mesclar, publicar, distribuir, sublicenciar e/ou vender cópias deste software, sujeito às condições da licença MIT.

Veja o arquivo [LICENSE](./LICENSE) para o texto completo da licença.

## 👤 Autoria

**Criado por**: [Lex Intelligentia](https://lexintelligentia.com)
**Desenvolvedor**: Felipe Bertrand Sardenberg Moulin

---

## 📦 Build e Distribuição

### Criar Executável Windows

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Criar ícone (opcional)
# Ver assets/ICON_CREATION.md

# 3. Build executável
python build_exe.py
```

**Resultado**: `dist/PDF2MD.exe` (aplicativo stand-alone)

### Criar Instalador Windows

1. Instale [Inno Setup](https://jrsoftware.org/isdl.php)
2. Abra `installer.iss` no Inno Setup Compiler
3. Clique em **Build → Compile** (F9)

**Resultado**: `Output/PDF2MD_Setup.exe` (instalador completo)

### Distribuição

**Opções disponíveis**:
1. **Executável**: `dist/PDF2MD.exe` - Stand-alone, copiar e executar
2. **Portável**: `dist/PDF2MD_Portable.zip` - Pacote ZIP com docs
3. **Instalador**: `Output/PDF2MD_Setup.exe` - Instalação completa

**Guia completo**: Ver [BUILD_GUIDE.md](./BUILD_GUIDE.md)

---

**Documentação complementar:**
- [BUILD_GUIDE.md](./BUILD_GUIDE.md) - **Build, empacotamento e distribuição**
- [WORKFLOW.md](./WORKFLOW.md) - Guia completo de uso CLI
- [OCR_GUIDE.md](./OCR_GUIDE.md) - Como processar PDFs escaneados
- [SECURITY_IMPROVEMENTS.md](./SECURITY_IMPROVEMENTS.md) - Melhorias de segurança
- [CLAUDE.md](./CLAUDE.md) - Instruções para Claude Code
