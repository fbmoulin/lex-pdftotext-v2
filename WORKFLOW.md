# Workflow de Processamento de PDFs

## Estrutura de Pastas Recomendada

```
data/
├── input/                          # PDFs a processar
│   ├── processo-1.pdf              # PDFs individuais
│   ├── processo-2.pdf
│   └── 0000865-32.2016.8.08.0012/  # Subpasta para múltiplos volumes
│       ├── volume-1.pdf
│       ├── volume-2.pdf
│       └── volume-3.pdf
├── output/                         # Arquivos .md gerados
└── processado/                     # PDFs já processados (auto-criado)
    └── [mesma estrutura do input]
```

## Organização de Arquivos

### Processo com Múltiplos Volumes

Quando um processo tem múltiplos PDFs (volumes, anexos, etc.), organize-os em uma **subpasta** com o
número do processo:

```bash
mkdir -p data/input/0000865-32.2016.8.08.0012
mv volume*.pdf data/input/0000865-32.2016.8.08.0012/
```

### Processos Individuais

PDFs de processos únicos podem ficar diretamente em `data/input/`:

```bash
data/input/5015904-66.2025.8.08.0012.pdf
```

## Comandos Disponíveis

### 1. Extract - Processar PDF Individual

Extrai texto de um único PDF e **move automaticamente** para `processado/`:

```bash
python main.py extract data/input/processo.pdf

# Com opções
python main.py extract data/input/processo.pdf -o saida.md --no-normalize
```

**Resultado:**

- Cria: `processo.md`
- Move: `data/input/processo.pdf` → `data/input/processado/processo.pdf`

### 2. Batch - Processar Múltiplos PDFs

Processa todos os PDFs em um diretório e **move automaticamente** para `processado/`:

```bash
python main.py batch data/input -o data/output

# Opções
python main.py batch data/input --format txt --no-metadata
```

**Resultado:**

- Cria: `data/output/*.md` (um por PDF)
- Move: Todos PDFs → `data/input/processado/`

**Nota:** Não processa subpastas. Use `merge` para processos com múltiplos volumes.

### 3. Merge - Mesclar PDFs do Mesmo Processo

**Busca recursiva** em subpastas, agrupa por número de processo e mescla:

```bash
python main.py merge data/input

# Mesclar apenas um processo específico
python main.py merge data/input --process-number 0000865-32.2016.8.08.0012
```

**Comportamento:**

1. Busca PDFs em `data/input/` e subpastas
1. Agrupa por número de processo (extraído do conteúdo ou nome do arquivo)
1. Cria um arquivo mesclado por processo (apenas se tiver 2+ PDFs)
1. **Move PDFs processados** para `processado/` preservando estrutura de subpastas
1. Pula processos com apenas 1 PDF (a menos que use `--process-number`)

**Resultado:**

```
📊 Encontrados 3 processo(s) diferente(s):
   • Processo 0000865-32.2016.8.08.0012: 2 arquivo(s)
   • Processo 0127351-38.2011.8.08.0012: 7 arquivo(s)
   • Processo 5015904-66.2025.8.08.0012: 1 arquivo(s)

📝 Mesclando 2 arquivo(s) do processo 0000865-32.2016.8.08.0012...
   ✅ Salvo em: data/input/processo_0000865-32.2016.8.08.0012_merged.md
   📦 2 PDF(s) movido(s) para: data/input/processado

📝 Mesclando 7 arquivo(s) do processo 0127351-38.2011.8.08.0012...
   ✅ Salvo em: data/input/processo_0127351-38.2011.8.08.0012_merged.md
   📦 7 PDF(s) movido(s) para: data/input/processado

⏭️  Processo 5015904-66.2025.8.08.0012: apenas 1 arquivo, pulando merge...
```

### 4. Info - Visualizar Metadados

Mostra metadados sem processar (não move o arquivo):

```bash
python main.py info data/input/processo.pdf
```

## Workflow Recomendado

### Cenário 1: Processo com Múltiplos Volumes

```bash
# 1. Organizar em subpasta
mkdir -p data/input/0000865-32.2016.8.08.0012
mv *.pdf data/input/0000865-32.2016.8.08.0012/

# 2. Mesclar
python main.py merge data/input

# Resultado:
# - Arquivo: processo_0000865-32.2016.8.08.0012_merged.md
# - PDFs movidos para: data/input/processado/0000865-32.2016.8.08.0012/
```

### Cenário 2: Múltiplos Processos Individuais

```bash
# Processar todos de uma vez
python main.py batch data/input -o data/output

# Resultado:
# - Arquivos: data/output/*.md
# - PDFs movidos para: data/input/processado/
```

### Cenário 3: Verificar Antes de Processar

```bash
# Ver metadados sem processar
python main.py info data/input/processo.pdf

# Se OK, processar
python main.py extract data/input/processo.pdf
```

## Pasta 'processado'

### Por Que Mover PDFs?

1. **Organização**: Separar PDFs já processados dos pendentes
1. **Segurança**: Evitar reprocessamento acidental
1. **Limpeza**: Após validar os .md, pode deletar PDFs processados para economizar espaço

### Estrutura Preservada

A estrutura de subpastas é **preservada** em `processado/`:

```
data/input/processado/
├── 5015904-66.2025.8.08.0012.pdf
└── 0000865-32.2016.8.08.0012/
    ├── volume-1.pdf
    └── volume-2.pdf
```

### Exclusão Automática

O comando `merge` **ignora** PDFs já em `processado/`:

```bash
python main.py merge data/input  # Não processa data/input/processado/*
```

## Limpeza após Processamento

Após validar os arquivos .md gerados:

```bash
# Deletar todos PDFs processados
rm -rf data/input/processado

# Ou deletar processo específico
rm -rf data/input/processado/0000865-32.2016.8.08.0012
```

## Detecção de Número de Processo

O sistema detecta o número do processo em ordem de prioridade:

1. **Conteúdo do PDF**: Regex CNJ `NNNNNNN-DD.AAAA.J.TT.OOOO`
1. **Nome do arquivo**: Se não encontrar no conteúdo
1. **"UNKNOWN"**: Se não encontrar em nenhum lugar (ainda assim mescla)

### Formato CNJ Esperado

```
0000865-32.2016.8.08.0012
  │      │   │   │ │   │
  │      │   │   │ │   └── Código da vara
  │      │   │   │ └────── Código do tribunal
  │      │   │   └──────── Segmento judiciário
  │      │   └──────────── Ano de ajuizamento
  │      └──────────────── Dígito verificador
  └─────────────────────── Número sequencial
```

## Opções Comuns

### Formatos de Saída

```bash
--format markdown  # Padrão
--format txt       # Texto puro
```

### Normalização

```bash
--normalize          # Padrão: converte MAIÚSCULAS, limpa ruído
--no-normalize       # Mantém texto original
```

### Metadados

```bash
--metadata           # Padrão: inclui cabeçalho de metadados
--no-metadata        # Somente texto
```

### Estruturação Automática

```bash
--structured         # Detecta e estrutura seções (apenas extract)
--no-structured      # Padrão
```

## Exemplos Práticos

### Processar Todo o Diretório

```bash
# Mesclar processos com múltiplos volumes + processar individuais
python main.py merge data/input
python main.py batch data/input -o data/output

# Após validar, limpar
rm -rf data/input/processado
```

### Processar Apenas um Processo Específico

```bash
python main.py merge data/input --process-number 0000865-32.2016.8.08.0012
```

### Extrair sem Normalização

```bash
python main.py extract documento.pdf --no-normalize --no-metadata -o raw.txt
```

## Troubleshooting

### "Nenhum arquivo PDF encontrado"

- Verifique se há PDFs em `data/input/` ou subpastas
- PDFs em `processado/` são ignorados automaticamente

### "Processo UNKNOWN"

- PDF não contém número de processo no formato CNJ
- Solução: Renomear arquivo com número do processo ou processar manualmente

### PDFs Escaneados

- Consulte: [OCR_GUIDE.md](OCR_GUIDE.md)
- Use `ocrmypdf` para converter em PDF pesquisável

## Performance

- **PyMuPDF**: 60x mais rápido que alternativas
- **Batch**: Processa ~10-20 PDFs/segundo (depende do tamanho)
- **Merge**: Processa subpastas recursivamente

## Próximos Passos

Após gerar os .md:

1. **Validar**: Revisar arquivos gerados em `data/output/`
1. **RAG**: Importar para pipeline de IA (Qdrant, Pinecone, etc.)
1. **Limpar**: Deletar PDFs em `processado/` se confirmado OK
1. **Organizar**: Mover .md para repositório de documentos

______________________________________________________________________

**Desenvolvido por**: [Lex Intelligentia](https://lexintelligentia.com) - Felipe Bertrand Sardenberg
Moulin **Licença**: MIT License - Ver [LICENSE](./LICENSE)
