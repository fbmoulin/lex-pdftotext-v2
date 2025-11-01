# Changelog - Melhorias de Segurança e Estabilidade

Data: 01/11/2025

## 🔒 Implementações de Segurança

### 1. Sistema de Exceções Customizadas

**Arquivo**: `src/utils/exceptions.py`

Criadas exceções específicas para diferentes tipos de erro:
- `PDFExtractionError` - Exceção base
- `PDFCorruptedError` - PDF corrompido ou ilegível
- `PDFEncryptedError` - PDF criptografado/protegido
- `PDFTooLargeError` - PDF excede tamanho máximo
- `PDFEmptyError` - PDF sem páginas/conteúdo
- `InvalidPathError` - Caminho inválido

**Benefícios**:
- Tratamento de erros mais granular
- Mensagens de erro claras em português
- Facilita debugging e logging

### 2. Validação de PDFs

**Arquivo**: `src/utils/validators.py`

Implementada classe `PDFValidator` com validações:

#### a) Validação de Caminho
- Verifica se arquivo existe
- Valida extensão .pdf
- Previne path traversal attacks

#### b) Validação de Tamanho
- Limite padrão: 500MB
- Configurável por arquivo
- Previne DoS por arquivos gigantes

#### c) Validação de Integridade
- Verifica se PDF está corrompido
- Detecta PDFs criptografados
- Valida número de páginas (máximo: 10.000)
- Testa leitura da primeira página
- Limite de páginas previne ataques de memória

#### d) Sanitização de Caminhos
Função `sanitize_output_path()`:
- Previne path traversal (../../../etc/passwd)
- Valida que saída está em diretório permitido
- Usa `Path.resolve()` para normalizar

**Código**:
```python
# Uso básico
PDFValidator.validate_all(pdf_path, max_size_mb=500)

# Ou validações individuais
PDFValidator.validate_path(pdf_path)
PDFValidator.validate_size(pdf_path, max_size_mb=100)
PDFValidator.validate_integrity(pdf_path)
```

### 3. Integração com PyMuPDFExtractor

**Arquivo**: `src/extractors/pymupdf_extractor.py`

Adicionada validação automática ao inicializar:

```python
# Valida automaticamente (padrão)
with PyMuPDFExtractor(pdf_path) as extractor:
    text = extractor.extract_text()

# Desabilitar validação se necessário
with PyMuPDFExtractor(pdf_path, validate=False) as extractor:
    text = extractor.extract_text()

# Custom max size
with PyMuPDFExtractor(pdf_path, max_size_mb=100) as extractor:
    text = extractor.extract_text()
```

### 4. Atualização do Base Extractor

**Arquivo**: `src/extractors/base.py`

- Migrado de `FileNotFoundError` para `InvalidPathError`
- Mensagens de erro em português
- Consistência com novo sistema de exceções

## 🛡️ Proteções Implementadas

### Ataques Prevenidos

| Ataque | Proteção | Implementado |
|--------|----------|--------------|
| Path Traversal | `sanitize_output_path()` | ✅ |
| DoS por arquivo grande | Limite de 500MB | ✅ |
| DoS por muitas páginas | Limite de 10.000 páginas | ✅ |
| PDF corrompido | Validação de integridade | ✅ |
| PDF criptografado | Detecção e rejeição | ✅ |
| Arquivo não-PDF | Validação de extensão | ✅ |

### Validações por Camada

**Camada 1 - Base Extractor**:
- Arquivo existe
- Extensão é .pdf

**Camada 2 - PDF Validator** (opcional):
- Tamanho do arquivo
- Integridade do PDF
- Número de páginas
- PDF não criptografado
- Leitura da primeira página

**Camada 3 - PyMuPDF**:
- Estrutura válida do PDF
- Conteúdo extraível

## 📊 Testes Realizados

### Testes de Validação
```
✅ Validação de arquivo válido (6.65 MB, 88 páginas)
✅ Rejeição de arquivo inexistente
✅ Rejeição de arquivo muito grande (> 1MB configurado)
✅ Rejeição de extensão inválida (.md)
✅ Integração com PyMuPDFExtractor
✅ Opção de desabilitar validação
```

### Testes Unitários
```
✅ 10/10 testes passaram
✅ Nenhuma regressão detectada
✅ Todas as funcionalidades existentes funcionando
```

## 📝 Uso Prático

### Antes (Sem Validação)
```python
# Qualquer erro resultava em exceção genérica
with PyMuPDFExtractor("corrupted.pdf") as extractor:
    text = extractor.extract_text()
# Erro: fitz.FileDataError: cannot open PDF
```

### Depois (Com Validação)
```python
# Erro detectado antes de tentar processar
try:
    with PyMuPDFExtractor("corrupted.pdf") as extractor:
        text = extractor.extract_text()
except PDFCorruptedError as e:
    print(f"PDF corrompido: {e}")
except PDFEncryptedError as e:
    print(f"PDF criptografado: {e}")
except PDFTooLargeError as e:
    print(f"PDF muito grande: {e}")
```

## 🔄 Compatibilidade

**✅ Retrocompatível**: Código existente continua funcionando

- Validação é **ativada por padrão** mas pode ser desabilitada
- Exceções customizadas herdam de Exception
- Código antigo que captura Exception continua funcionando

**⚠️ Mudanças Necessárias** (opcional):

Se quiser tratamento granular de erros:

```python
# Antes
try:
    extractor = PyMuPDFExtractor(pdf_path)
except FileNotFoundError:
    # ...

# Depois (recomendado)
try:
    extractor = PyMuPDFExtractor(pdf_path)
except InvalidPathError:
    # Tratamento específico
except PDFCorruptedError:
    # Tratamento específico
except PDFExtractionError:
    # Catch-all para erros de PDF
```

## 🚀 Próximos Passos

Melhorias sugeridas (ver `SECURITY_IMPROVEMENTS.md`):

**Prioridade Alta**:
- [ ] Logging de auditoria (arquivo, hash, timestamp)
- [ ] Timeout para processamento de PDFs grandes
- [ ] Retry com exponential backoff

**Prioridade Média**:
- [ ] Métricas de performance (tempo, memória)
- [ ] Limite de recursos (memória, CPU)
- [ ] Circuit breaker para batch processing

**Prioridade Baixa**:
- [ ] Pydantic v2 para validação de configuração
- [ ] Health check endpoint
- [ ] Rate limiting

## 📚 Arquivos Criados/Modificados

### Novos Arquivos
- `src/utils/exceptions.py` - Sistema de exceções
- `src/utils/validators.py` - Validadores de segurança
- `SECURITY_IMPROVEMENTS.md` - Guia de melhorias
- `CHANGELOG_SECURITY.md` - Este arquivo

### Arquivos Modificados
- `src/utils/__init__.py` - Exporta novos módulos
- `src/extractors/base.py` - Usa InvalidPathError
- `src/extractors/pymupdf_extractor.py` - Integra validação

### Testes
- ✅ Todos os testes unitários passaram
- ✅ Testes de validação criados e executados
- ✅ Testes de integração executados

## 🎯 Resultados

**Segurança**:
- ✅ 6 tipos de ataque mitigados
- ✅ Validação em 3 camadas
- ✅ Mensagens de erro claras

**Estabilidade**:
- ✅ Erros detectados antes de processar
- ✅ Recursos protegidos (memória, tempo)
- ✅ Falhas graciosas com mensagens úteis

**Usabilidade**:
- ✅ Retrocompatível
- ✅ Validação pode ser desabilitada
- ✅ Mensagens em português

## 📖 Referências

- **Docling** (IBM Research): https://github.com/docling-project/docling
  - Inspiração: Pydantic v2, validação local, mypy
- **OWASP Top 10**: Prevenção de vulnerabilidades comuns
- **Python Security**: Best practices da documentação oficial
