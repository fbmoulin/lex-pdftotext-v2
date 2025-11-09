Quick Start Guide
=================

This guide will help you get started with PDF Text Extractor quickly.

Simple Text Extraction
-----------------------

Extract text from a single PDF::

    from pathlib import Path
    from src.extractors.pymupdf_extractor import PyMuPDFExtractor
    from src.processors.text_normalizer import TextNormalizer
    from src.formatters.markdown_formatter import MarkdownFormatter

    # Extract and normalize
    with PyMuPDFExtractor("document.pdf") as extractor:
        raw_text = extractor.extract_text()

    normalizer = TextNormalizer()
    clean_text = normalizer.normalize(raw_text)

    # Save as Markdown
    formatter = MarkdownFormatter()
    markdown = formatter.format(clean_text)
    formatter.save_to_file(markdown, "output.md")

With Metadata Extraction
-------------------------

Extract structured metadata::

    from src.processors.metadata_parser import MetadataParser

    # Parse metadata
    parser = MetadataParser()
    metadata = parser.parse(clean_text)

    # Access metadata
    print(f"Process: {metadata.process_number}")
    print(f"Author: {metadata.author}")
    print(f"Defendant: {metadata.defendant}")
    print(f"Lawyers: {metadata.lawyers}")

RAG-Optimized Output
--------------------

Generate chunks for vector databases::

    formatter = MarkdownFormatter()
    chunks = formatter.format_for_rag(
        clean_text,
        metadata=metadata,
        chunk_size=1000
    )

    # Each chunk contains text + metadata
    for chunk in chunks:
        print(f"Chunk {chunk['chunk_index']}")
        print(f"Text: {chunk['text'][:100]}...")
        print(f"Metadata: {chunk['metadata']}")

Table Extraction
----------------

Extract tables from PDFs::

    from src.extractors.table_extractor import TableExtractor

    extractor = TableExtractor("document.pdf")

    # Extract all tables
    tables = extractor.extract_tables()

    for table in tables:
        print(f"Page {table['page']}: {table['rows']}x{table['cols']} table")
        print(table['data'])

    # Export to CSV
    csv_files = extractor.extract_tables_as_csv("./output/")

JSON Export
-----------

Export as structured JSON::

    from src.formatters.json_formatter import JSONFormatter

    formatter = JSONFormatter()

    # Format as JSON
    data = formatter.format(
        clean_text,
        metadata=metadata,
        hierarchical=True
    )

    # Save to file
    formatter.save_to_file(data, "output.json")

CLI Usage
---------

The package includes command-line tools::

    # Extract single PDF
    pdftotext-legal extract document.pdf

    # Extract with specific format
    pdftotext-legal extract document.pdf --format json

    # Batch process directory
    pdftotext-legal batch ./pdfs/ --output ./output/

    # Extract tables
    pdftotext-legal extract-tables document.pdf

    # Show metadata only
    pdftotext-legal info document.pdf

Configuration
-------------

Create a ``config.yaml`` file::

    # PDF Processing
    max_pdf_size_mb: 500
    max_pdf_pages: 10000

    # Text Processing
    chunk_size: 1000

    # Output
    output_dir: "data/output"
    default_format: "markdown"

Or use environment variables::

    export MAX_PDF_SIZE_MB=500
    export CHUNK_SIZE=1000
    export OUTPUT_DIR="./output"

Next Steps
----------

* Read the :doc:`usage` guide for detailed examples
* Explore the :doc:`api/index` reference for all available methods
* Check the :doc:`contributing` guide to contribute to the project
