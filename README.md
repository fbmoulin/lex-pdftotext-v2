# PDF Legal Text Extractor

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/release-v0.5.0-brightgreen.svg)](https://github.com/fbmoulin/lex-pdftotext-v2/releases)
[![Tests](https://img.shields.io/badge/tests-323%20passed-brightgreen.svg)](https://github.com/fbmoulin/lex-pdftotext-v2)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/fbmoulin/lex-pdftotext-v2)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)
[![MCP](https://img.shields.io/badge/MCP-Claude%20Desktop-blueviolet.svg)](https://modelcontextprotocol.io/)

> **Projeto criado por [Lex Intelligentia](https://lexintelligentia.com)** - Soluções inteligentes
> para análise jurídica

Extração e estruturação de texto de documentos PDF processuais brasileiros (formato PJe).

**Disponível em quatro versões**:

- 🌐 **Dashboard Web (Next.js)** - Interface moderna com shadcn/ui para processamento de PDFs
- 🖥️ **Interface Gráfica (GUI)** - Aplicativo Windows stand-alone com design moderno dark theme
- ⌨️ **Interface de Linha de Comando (CLI)** - Terminal/script
- 🤖 **MCP Server** - Integração nativa com Claude Desktop

## 🎯 Objetivo

Este projeto extrai texto completo de PDFs de processos judiciais brasileiros, removendo elementos
irrelevantes (logos, números de página) e estruturando o conteúdo em formato Markdown hierárquico
com metadados, otimizado para:

- **Pipelines RAG** (Retrieval Augmented Generation)
- **Sistemas de análise jurídica** (Lex Intelligentia, FIRAC+)
- **Automações** (n8n, Zapier)
- **Bancos de dados vetoriais** (Qdrant, Pinecone, Chroma)

## ✨ Funcionalidades

### Extração e Processamento

✅ Extração rápida e precisa de texto (PyMuPDF - 60x mais rápido) ✅ **Análise de imagens com IA** -
Detecta e descreve imagens usando Google Gemini Vision ✅ **Extração de tabelas** - Detecta e extrai
tabelas estruturadas do PDF (Markdown ou CSV) ✅ Remoção automática de ruído:

- Logos, URLs, códigos de verificação
- Rodapés repetitivos de escritórios de advocacia
- Endereços, telefones, emails duplicados ✅ Normalização de texto (conversão de UPPERCASE excessivo
  para sentence case)

### Extração de Metadados

✅ Extração inteligente de metadados jurídicos:

- Números de processo (formato CNJ)
- IDs de documentos (Num. XXXXXXXX)
- Partes (autor, réu)
- Advogados e OABs
- Juízes
- Datas de assinatura digital
- Vara/tribunal
- Valor da causa

### Interface e Organização

✅ **Interface moderna dark theme** - Design sofisticado com glassmorphism e animações ✅ Detecção
automática de tipo de documento (petição inicial, decisão, certidão) ✅ Saída estruturada em Markdown
hierárquico ou JSON ✅ **Monitoramento de performance** - Rastreamento de métricas de processamento ✅
Processamento em lote (batch) ✅ **Merge inteligente** - Mescla automaticamente PDFs do mesmo
processo ✅ **Organização automática** - Move PDFs processados para pasta separada ✅ **Busca
recursiva** - Processa subpastas (processos com múltiplos volumes) ✅ **Exportação flexível** - Abrir
pasta ou salvar em local personalizado ✅ CLI amigável com comandos intuitivos ✅ **Pacote
PyPI-ready** - Instalável com pip install

### Novidades v0.5.0

✅ **Índice de Peças Processuais (`--indexed`)** - Gera índice navegável com:

- Tabela de conteúdo com âncoras para cada documento
- Detecção automática de tipo (petição, decisão, certidão, etc.)
- Ícones visuais para cada tipo de peça
- Cross-references entre documentos

✅ **MCP Server para Claude Desktop** - Integração nativa com Claude:

- Ferramenta `extract_legal_pdf` - Extração completa com índice
- Ferramenta `extract_metadata_only` - Apenas metadados
- Ferramenta `list_document_ids` - Lista IDs com posições

✅ **Docker Support** - Deploy com containers:

- `docker-compose.yml` para desenvolvimento
- `docker-compose.prod.yml` para produção
- Imagens separadas para API, Worker e Frontend

✅ **Dashboard Web (Next.js)** - Interface moderna:

- Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- Páginas: Extrair, Lote, Mesclar, Tabelas, Histórico, Info
- Suporte a dark/light mode
- React Query para cache e polling de jobs

## 📚 Documentação

**📖 [Documentação Completa](https://fbmoulin.github.io/pdftotext/)** disponível no GitHub Pages

A documentação inclui:

- **[Guia de Instalação](https://fbmoulin.github.io/pdftotext/installation.html)** - Instruções
  detalhadas de setup
- **[Quick Start](https://fbmoulin.github.io/pdftotext/quickstart.html)** - Comece a usar em 5
  minutos
- **[Guia de Uso](https://fbmoulin.github.io/pdftotext/usage.html)** - Exemplos avançados e casos de
  uso
- **[Referência da API](https://fbmoulin.github.io/pdftotext/api/index.html)** - Documentação
  completa de todas as classes e funções
- **[Guia de Contribuição](https://fbmoulin.github.io/pdftotext/contributing.html)** - Como
  contribuir com o projeto
- **[Changelog](https://fbmoulin.github.io/pdftotext/changelog.html)** - Histórico de versões e
  métricas de qualidade

### Métricas de Qualidade (v0.5.0)

- ✅ **323 testes passando**
- ✅ **0 erros Ruff** (linter limpo)
- ✅ **0 issues de segurança** (Bandit)
- ✅ **Type checked** (MyPy)

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

### 4. Configure a API do Gemini (Opcional - para análise de imagens)

Para habilitar a análise de imagens com IA:

```bash
# Windows (PowerShell como Administrador)
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'sua-chave-aqui', 'User')

# Linux/macOS
export GEMINI_API_KEY='sua-chave-aqui'
# Adicione ao ~/.bashrc ou ~/.zshrc para persistir
```

**Obter chave da API:**

1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
1. Crie uma API key gratuita
1. Configure a variável de ambiente acima

**Nota:** A análise de imagens é opcional. Se não configurada, o app funcionará normalmente sem esta
feature.

## ⚙️ Configuração

O aplicativo suporta configuração através de três fontes (em ordem de precedência):

1. **Variáveis de ambiente** (.env ou sistema)
1. **Arquivo config.yaml** (raiz do projeto)
1. **Valores padrão** (configuração interna)

### Arquivo config.yaml

Crie ou edite o arquivo `config.yaml` na raiz do projeto:

```yaml
# PDF Processing
max_pdf_size_mb: 500          # Tamanho máximo de PDF (MB)
max_pdf_pages: 10000           # Número máximo de páginas
pdf_open_timeout: 30           # Timeout para abrir PDF (segundos)

# Text Processing
chunk_size: 1000               # Tamanho de chunk para RAG (caracteres)
min_chunk_size: 100            # Tamanho mínimo de chunk
max_chunk_size: 10000          # Tamanho máximo de chunk

# Image Processing
max_image_size_mb: 4           # Tamanho máximo de imagem (MB)
enable_image_analysis: false   # Habilitar análise de imagens com Gemini

# API Configuration
gemini_rate_limit: 60          # Requisições por minuto ao Gemini

# Output
output_dir: data/output        # Diretório de saída padrão
default_format: markdown       # Formato: markdown ou txt

# Logging
log_level: INFO                # DEBUG, INFO, WARNING, ERROR, CRITICAL
log_file: logs/pdftotext.log   # Arquivo de log
log_max_bytes: 10485760        # Tamanho máximo do log (10MB)
log_backup_count: 5            # Número de backups de log

# Disk Space
min_disk_space_mb: 100         # Espaço livre mínimo requerido (MB)

# Validation
validate_pdfs: true            # Validar PDFs antes de processar
validate_output_paths: true    # Validar caminhos de saída

# Performance
batch_size: 10                 # Arquivos por atualização de progresso
```

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (ou configure no sistema):

```bash
# API Configuration (prioritário)
GEMINI_API_KEY=sua-chave-api-aqui

# Override de configurações (opcional)
CHUNK_SIZE=2000
LOG_LEVEL=DEBUG
ENABLE_IMAGE_ANALYSIS=true
OUTPUT_DIR=custom/output

# Todas as opções de config.yaml podem ser sobrescritas
# Formato: NOME_CAMPO_EM_MAIÚSCULA=valor
```

### Precedência de Configuração

```
Variáveis de Ambiente > config.yaml > Valores Padrão
```

**Exemplo:**

- `config.yaml` define `chunk_size: 1000`
- `.env` define `CHUNK_SIZE=5000`
- **Resultado:** Usa `5000` (env tem prioridade)

### Validação Automática

O sistema valida e ajusta automaticamente:

- **chunk_size**: Forçado entre `min_chunk_size` e `max_chunk_size`
- **log_level**: Deve ser DEBUG, INFO, WARNING, ERROR ou CRITICAL
- Valores inválidos são corrigidos para defaults com aviso no log

### Verificar Configuração Atual

```python
from src.utils.config import get_config

config = get_config()
print(config.to_dict())  # Mostra toda configuração carregada
```

## 🚀 Uso

### Dashboard Web (Next.js) 🆕

Interface web moderna para processamento de PDFs.

#### Desenvolvimento Local

```bash
# 1. Iniciar backend
source venv/bin/activate
uvicorn src.lex_pdftotext.api.main:app --reload --port 8000

# 2. Iniciar frontend (em outro terminal)
cd frontend
bun install
bun run dev

# 3. Acessar http://localhost:3000
```

#### Docker (Recomendado)

```bash
cd docker
docker compose up --build

# Acesse:
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

#### Funcionalidades do Dashboard

| Página | Descrição |
|--------|-----------|
| **Extrair** | Upload de PDF único com opções de processamento |
| **Lote** | Processamento de múltiplos PDFs simultaneamente |
| **Mesclar** | Combinar PDFs do mesmo processo |
| **Tabelas** | Extrair tabelas como Markdown ou CSV |
| **Histórico** | Acompanhar status de todos os jobs |
| **Info** | Ver metadados sem extração completa |

**Opções de processamento:**
- ✅ Normalizar texto
- ✅ Incluir metadados
- ✅ Estruturar seções
- ✅ Indexar peças processuais
- 🤖 Analisar imagens (Gemini Vision)

---

### Interface Gráfica (GUI)

#### Windows - Aplicativo Stand-Alone

Se você tem o executável `PDF2MD.exe`:

1. Execute `PDF2MD.exe`
1. **Aprecie a interface moderna dark theme** com efeitos de glassmorphism
1. Escolha uma das abas:
   - **Extrair PDF**: Processa um único PDF
   - **Processamento em Lote**: Processa múltiplos PDFs
   - **Mesclar Processos**: Agrupa PDFs do mesmo processo
1. Selecione arquivos/pasta
1. Configure opções:
   - ✅ Normalizar texto
   - ✅ Incluir metadados
   - ✅ Estruturar seções
   - 🤖 **Analisar imagens (Gemini)** - Descreve imagens encontradas no PDF
1. Clique no botão para processar
1. Use os botões de exportação para abrir pasta ou salvar em outro local

**Vantagens da GUI**:

- ✅ Design moderno dark theme com animações suaves
- ✅ Não requer Python instalado
- ✅ Interface visual intuitiva e responsiva
- ✅ Análise de imagens com IA integrada
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

______________________________________________________________________

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

# Saída em JSON estruturado
python main.py extract documento.pdf --format json

# Sem normalização de texto (preservar UPPERCASE)
python main.py extract documento.pdf --no-normalize

# Sem metadados no cabeçalho
python main.py extract documento.pdf --no-metadata

# Com estruturação automática de seções
python main.py extract documento.pdf --structured

# 🆕 Com índice de peças processuais e cross-references
python main.py extract documento.pdf --indexed
```

### Índice de Peças Processuais (--indexed)

O flag `--indexed` gera um índice navegável no início do documento:

```markdown
## 📑 Índice de Peças Processuais

| # | ID | Tipo | Linha |
|---|-----|------|-------|
| 1 | [79670915](#doc-79670915) | 📋 Petição | 45 |
| 2 | [79670916](#doc-79670916) | ⚖️ Decisão | 234 |
| 3 | [79670917](#doc-79670917) | 📜 Certidão | 567 |

---

<!-- doc-79670915 -->
[Conteúdo do documento...]
```

**Benefícios:**

- Navegação rápida entre peças do processo
- Identificação visual do tipo de documento
- Âncoras para referência direta

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
1. Agrupa automaticamente por número de processo (extraído do conteúdo ou nome)
1. Cria um arquivo mesclado por processo (apenas se tiver 2+ PDFs)
1. Move PDFs processados para `data/input/processado/` preservando estrutura

### Extrair tabelas de PDFs

```bash
# Extrair todas as tabelas como Markdown
python main.py extract-tables documento.pdf

# Extrair tabelas como arquivos CSV separados
python main.py extract-tables documento.pdf --format csv

# Especificar pasta de saída para CSVs
python main.py extract-tables documento.pdf --format csv -o ./tabelas/

# Sem metadados das tabelas (página, posição)
python main.py extract-tables documento.pdf --no-metadata
```

**O que extrai:**

- Detecta automaticamente tabelas estruturadas no PDF
- Formato Markdown: uma tabela por página com metadados
- Formato CSV: um arquivo por tabela
- Alinhamento automático de colunas numéricas

### Ver métricas de performance

```bash
# Mostrar estatísticas de processamento
python main.py perf-report

# Exportar métricas como JSON
python main.py perf-report --json

# Resetar métricas após visualizar
python main.py perf-report --reset
```

**Métricas rastreadas:**

- Tempo de normalização de texto
- Tempo de extração de metadados
- Tempo de chunking para RAG
- Tempo de extração de tabelas

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

## 🤖 MCP Server (Claude Desktop)

Integração nativa com Claude Desktop via Model Context Protocol (MCP).

### Instalação

1. **Configure o Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pdf-legal-extractor": {
      "command": "python",
      "args": ["/caminho/para/pdftotext/mcp_server/server.py"]
    }
  }
}
```

2. **Reinicie o Claude Desktop**

### Ferramentas Disponíveis

| Ferramenta              | Descrição                                                  |
| ----------------------- | ---------------------------------------------------------- |
| `extract_legal_pdf`     | Extrai texto completo com índice, metadados e normalização |
| `extract_metadata_only` | Extrai apenas metadados (processo, partes, advogados)      |
| `list_document_ids`     | Lista IDs de documentos com tipo e posição                 |

### Exemplo de Uso no Claude

```
Usuário: Extraia o PDF em /home/user/processo.pdf

Claude: [Usa extract_legal_pdf]

## Processo 5022930-18.2025.8.08.0012

### 📑 Índice de Peças Processuais
| # | ID | Tipo | Linha |
|---|-----|------|-------|
| 1 | 79670915 | 📋 Petição | 45 |
...
```

## 📂 Estrutura do Projeto

```
pdftotext/
├── src/
│   ├── lex_pdftotext/       # 🆕 Pacote principal (v0.5.0)
│   │   ├── extractors/      # Extração de texto (PyMuPDF)
│   │   ├── processors/      # Normalização, metadados, ImageAnalyzer
│   │   ├── formatters/      # Markdown, JSON, índice
│   │   ├── api/             # 🆕 FastAPI routes
│   │   ├── models/          # 🆕 SQLAlchemy models
│   │   ├── storage/         # 🆕 S3/local storage
│   │   ├── worker/          # 🆕 Background tasks
│   │   └── utils/           # Patterns, config, validators
│   └── [shims]              # Backward compatibility
├── frontend/                # 🆕 Next.js Dashboard (v0.6.0)
│   ├── app/                 # App Router pages
│   │   ├── extract/         # Extração de PDF
│   │   ├── batch/           # Processamento em lote
│   │   ├── merge/           # Mesclar PDFs
│   │   ├── tables/          # Extração de tabelas
│   │   ├── jobs/            # Histórico de jobs
│   │   └── info/            # Informações do PDF
│   ├── components/          # React components
│   │   ├── ui/              # shadcn/ui components
│   │   └── layout/          # Sidebar, Header
│   └── lib/                 # API client, React Query
├── mcp_server/              # MCP Server (Claude Desktop)
│   ├── server.py            # Servidor MCP
│   └── requirements.txt
├── docker/                  # Docker support
│   ├── Dockerfile.api
│   ├── Dockerfile.worker
│   ├── Dockerfile.frontend  # 🆕 Next.js container
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
├── tests/                   # 323 testes
│   ├── test_extraction.py
│   ├── test_api.py
│   └── test_saas.py
├── assets/html/             # Interface GUI (desktop)
├── main.py                  # CLI principal
├── app_ui.py                # GUI (PyWebview)
└── pyproject.toml           # Package config
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
    print(chunk["text"][:100])
    print(chunk["metadata"])
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
1. **Preservação de contexto** - Metadados mantidos com o texto
1. **Tokenização limpa** - Texto normalizado melhora embeddings
1. **Indexação** - Estrutura clara para busca vetorial

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

**Core:**

- **PyMuPDF (fitz)** - Extração rápida e precisa de texto (60x mais rápido)
- **Pillow (PIL)** - Processamento de imagens extraídas
- **google-generativeai** - Análise de imagens com Gemini Vision API

**Interface:**

- **pywebview** - Interface gráfica moderna com HTML/CSS/JS
- **click** - Interface CLI elegante

**Utilidades:**

- **tqdm** - Barras de progresso
- **python-dotenv** - Gerenciamento de variáveis de ambiente

**Build:**

- **pyinstaller** - Empacotamento como executável Windows

**Desenvolvimento:**

- **pytest** - Framework de testes

## 🛠️ Melhorias Futuras

- [ ] Suporte nativo a OCR para PDFs escaneados (veja [OCR_GUIDE.md](./OCR_GUIDE.md) para soluções
  atuais)
- [x] ~~Extração de tabelas estruturadas~~ ✅ v0.4.0
- [ ] Detecção automática de seções (NLP)
- [ ] Cache de análises de imagens
- [ ] Retry logic para API calls do Gemini
- [x] ~~API REST (FastAPI)~~ ✅ v0.5.0
- [x] ~~Interface web responsiva~~ ✅ v0.6.0 (Next.js + shadcn/ui)
- [x] ~~Exportação JSON estruturado~~ ✅ v0.4.0
- [ ] Integração direta com vector databases
- [ ] Análise FIRAC+ automática
- [ ] Suporte a mais idiomas de interface
- [x] ~~Índice de peças processuais~~ ✅ v0.5.0
- [x] ~~MCP Server (Claude Desktop)~~ ✅ v0.5.0
- [x] ~~Docker support~~ ✅ v0.5.0

## 📄 Licença

Este projeto é licenciado sob a **MIT License**.

Copyright (c) 2025 Lex Intelligentia Desenvolvido por Felipe Bertrand Sardenberg Moulin

Você tem permissão para usar, copiar, modificar, mesclar, publicar, distribuir, sublicenciar e/ou
vender cópias deste software, sujeito às condições da licença MIT.

Veja o arquivo [LICENSE](./LICENSE) para o texto completo da licença.

## 👤 Autoria

**Criado por**: [Lex Intelligentia](https://lexintelligentia.com) **Desenvolvedor**: Felipe Bertrand
Sardenberg Moulin

______________________________________________________________________

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
1. Abra `installer.iss` no Inno Setup Compiler
1. Clique em **Build → Compile** (F9)

**Resultado**: `Output/PDF2MD_Setup.exe` (instalador completo)

### Distribuição

**Opções disponíveis**:

1. **Executável**: `dist/PDF2MD.exe` - Stand-alone, copiar e executar
1. **Portável**: `dist/PDF2MD_Portable.zip` - Pacote ZIP com docs
1. **Instalador**: `Output/PDF2MD_Setup.exe` - Instalação completa

**Guia completo**: Ver [BUILD_GUIDE.md](./BUILD_GUIDE.md)

______________________________________________________________________

**Documentação complementar:**

- [BUILD_GUIDE.md](./BUILD_GUIDE.md) - **Build, empacotamento e distribuição**
- [WORKFLOW.md](./WORKFLOW.md) - Guia completo de uso CLI
- [OCR_GUIDE.md](./OCR_GUIDE.md) - Como processar PDFs escaneados
- [SECURITY_IMPROVEMENTS.md](./SECURITY_IMPROVEMENTS.md) - Melhorias de segurança
- [CLAUDE.md](./CLAUDE.md) - Instruções para Claude Code
