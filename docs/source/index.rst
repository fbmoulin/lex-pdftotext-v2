PDF Text Extractor for Legal Documents
========================================

Welcome to PDF Text Extractor's documentation! This library extracts and structures text from Brazilian legal PDF documents (PJe format), optimized for RAG pipelines and legal analysis systems.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   usage
   api/index
   contributing
   changelog

Features
--------

* **Smart Text Extraction**: Extracts text from PDFs while removing noise (logos, page numbers, verification codes)
* **Metadata Parsing**: Automatically extracts process numbers, parties, lawyers, dates, and document types
* **Hierarchical Markdown**: Generates structured Markdown with proper heading levels
* **RAG Optimization**: Semantic chunking for vector databases (Qdrant, Pinecone, Chroma)
* **Table Extraction**: Detects and extracts tables from PDFs with multiple output formats
* **Type-Safe**: 100% MyPy compliant with comprehensive type hints
* **Well-Tested**: 170+ tests with 77% code coverage

Quick Start
-----------

Installation::

    pip install pdftotext-legal

Basic usage::

    from pathlib import Path
    from src.extractors.pymupdf_extractor import PyMuPDFExtractor
    from src.processors.text_normalizer import TextNormalizer
    from src.processors.metadata_parser import MetadataParser
    from src.formatters.markdown_formatter import MarkdownFormatter

    # Extract text
    with PyMuPDFExtractor("document.pdf") as extractor:
        raw_text = extractor.extract_text()

    # Normalize and parse
    normalizer = TextNormalizer()
    clean_text = normalizer.normalize(raw_text)

    metadata_parser = MetadataParser()
    metadata = metadata_parser.parse(clean_text)

    # Format as Markdown
    formatter = MarkdownFormatter()
    markdown = formatter.format(clean_text, metadata)

    # Save
    formatter.save_to_file(markdown, "output.md")

CLI Usage::

    # Extract single PDF
    pdftotext-legal extract document.pdf

    # Extract with JSON output
    pdftotext-legal extract document.pdf --format json

    # Batch process directory
    pdftotext-legal batch ./pdfs/

    # Extract tables
    pdftotext-legal extract-tables document.pdf

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
