# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Project Overview

This project extracts and structures text from Brazilian judicial PDF documents (PJe format),
removing irrelevant elements (logos, page numbers) and organizing content into hierarchical Markdown
format with metadata, optimized for RAG pipelines, legal analysis systems, and automation tools.

## Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run single test
pytest tests/test_extraction.py::TestRegexPatterns::test_extract_document_ids -v
```

## Common Commands

```bash
# CLI Usage
python main.py extract documento.pdf              # Extract single PDF
python main.py extract documento.pdf --format json # Export as JSON
python main.py batch ./data/input                 # Batch process directory
python main.py merge ./data/input                 # Merge PDFs by process number
python main.py extract-tables documento.pdf       # Extract tables from PDF
python main.py extract-tables doc.pdf --format csv # Extract tables as CSV
python main.py perf-report                        # Show performance metrics
python main.py info documento.pdf                 # Show metadata only

# Programmatic Usage Examples
python example.py data/input/processo.pdf         # Run all examples

# Testing
pytest tests/ -v                                  # Run all tests
pytest tests/test_extraction.py -v               # Run specific test file
pytest tests/test_table_extraction.py -v         # Run table extraction tests
```

## Architecture Overview

The codebase follows a **modular pipeline architecture** with clear separation of concerns:

### Core Pipeline Flow

```
PDF Input → Extractor → Normalizer → MetadataParser → Formatter → Output (MD/TXT)
```

### Module Responsibilities

1. **`src/extractors/`** - PDF extraction layer

   - `base.py`: Abstract interface (PDFExtractor) defining extraction contract
   - `pymupdf_extractor.py`: PyMuPDF implementation (context manager pattern)
   - `table_extractor.py`: Table detection and extraction using pdfplumber
   - Responsibility: Raw text and table extraction with page breaks

1. **`src/processors/`** - Text processing layer

   - `text_normalizer.py`: UPPERCASE → sentence case conversion, noise removal
   - `metadata_parser.py`: Extract structured metadata using regex patterns
   - Responsibility: Clean and analyze raw text

1. **`src/formatters/`** - Output formatting layer

   - `markdown_formatter.py`: Generate hierarchical Markdown, RAG chunks
   - `json_formatter.py`: Export structured data as JSON
   - `table_formatter.py`: Format tables as Markdown or CSV
   - Responsibility: Structure output for different use cases

1. **`src/utils/`** - Shared utilities

   - `patterns.py`: 15+ regex patterns for PJe document parsing
   - `cache.py`: Performance monitoring and image description caching
   - Responsibility: Domain-specific pattern matching and caching

1. **`main.py`** - CLI interface (Click-based)

   - Commands: `extract`, `batch`, `merge`, `extract-tables`, `perf-report`, `info`
   - Orchestrates the full pipeline

### Key Design Patterns

- **Strategy Pattern**: `PDFExtractor` base class with swappable implementations
- **Context Manager**: `PyMuPDFExtractor` manages document lifecycle
- **Dataclass**: `DocumentMetadata` for structured metadata
- **Pipeline Pattern**: Sequential processing stages

## Text Processing Rules

### Normalization (src/processors/text_normalizer.py)

- Converts UPPERCASE lines to sentence case EXCEPT:
  - Legal acronyms: OAB, STF, STJ, CPC, CDC, etc. (see `patterns.py::LEGAL_ACRONYMS`)
  - Roman numerals in section headers
- Removes noise: page numbers, URLs (`https://pje.cnj.jus.br/*`), verification codes
- Preserves paragraph structure (double newlines)

### Metadata Extraction (src/processors/metadata_parser.py)

Automatically detects from text:

- **Process numbers**: CNJ format `NNNNNNN-DD.AAAA.J.TT.OOOO`
- **Document IDs**: `Num. XXXXXXXX` (8 digits)
- **Lawyers**: `Name – OAB/ST 12345`
- **Parties**: `Autor:`, `Réu:`
- **Signatures**: `assinado eletronicamente em DD/MM/AAAA`
- **Document type**: Initial petition, decision, certificate (via keyword matching)

### RAG Optimization (src/formatters/markdown_formatter.py)

- `format()`: Standard Markdown with metadata header
- `format_with_sections()`: Auto-structured sections
- `format_for_rag()`: Chunks with attached metadata for vector databases
  - Default chunk size: 1000 characters
  - Paragraph-aware splitting
  - Each chunk includes: `{text, metadata, chunk_index}`

### Table Extraction (src/extractors/table_extractor.py)

- `extract_tables()`: Extract all tables from PDF with pdfplumber
  - Returns list of tables with metadata: page, bbox, data, rows, cols
  - Configurable table detection settings
- `extract_tables_as_csv()`: Export tables to separate CSV files
- `has_tables()`: Check if PDF contains tables
- Performance tracked with `@performance.track("table_extraction")`

### Table Formatting (src/formatters/table_formatter.py)

- `format_table()`: Convert table data to Markdown tables
  - Supports custom alignment (left/right/center)
  - Handles None values, uneven rows, pipe escaping
- `format_table_with_caption()`: Add captions and metadata
- `detect_alignment()`: Auto-detect numeric columns for right-alignment
- `format_all_tables()`: Batch format multiple tables

### JSON Export (src/formatters/json_formatter.py)

- `format()`: Convert processed text to structured JSON
  - Hierarchical or flat mode
  - Includes metadata, document type, sections
- `format_to_string()`: JSON export with custom indentation
- Used by CLI `--format json` option

### Performance Monitoring (src/utils/cache.py)

- `PerformanceMonitor`: Track operation timing
  - Decorator pattern: `@performance.track("operation_name")`
  - Tracks: text_normalization, metadata_extraction, rag_chunking, table_extraction
- `get_metrics()`: Get performance statistics
- `report()`: Generate human-readable performance report
- Used by `perf-report` CLI command

## Important Regex Patterns

All patterns are in `src/utils/patterns.py`:

```python
RegexPatterns.DOC_ID  # Num. 12345678
RegexPatterns.PROCESS_NUMBER  # NNNNNNN-DD.AAAA.J.TT.OOOO
RegexPatterns.LAWYER_OAB  # Name – OAB/UF 12345
RegexPatterns.SIGNATURE_DATE  # assinado eletronicamente em DD/MM/AAAA
RegexPatterns.LEGAL_ACRONYMS  # OAB|STF|STJ|CPC|... (preserve in UPPERCASE)
```

## Integration Context

Output is designed for:

- **RAG pipelines**: Markdown format optimized for semantic chunking
- **Legal AI systems**: Lex Intelligentia FIRAC+ analysis
- **Automation**: n8n, Zapier workflows
- **Vector databases**: Qdrant, Pinecone, Chroma (via `format_for_rag()`)

## Libraries Used

- **PyMuPDF (fitz)**: Fast PDF extraction (chosen for 60x speed vs alternatives)
- **click**: CLI framework
- **tqdm**: Progress bars for batch processing
- **pytest**: Testing framework

## Testing Strategy

Located in `tests/test_extraction.py`:

- Unit tests for regex patterns
- Text normalization validation
- Metadata extraction verification
- Document type detection tests
