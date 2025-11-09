Usage Guide
===========

This guide covers advanced usage scenarios and best practices.

Advanced Text Extraction
-------------------------

Extracting with Formatting
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preserve text formatting information::

    from src.extractors.pymupdf_extractor import PyMuPDFExtractor

    with PyMuPDFExtractor("document.pdf") as extractor:
        # Standard extraction
        plain_text = extractor.extract_text()

        # With formatting preserved
        formatted_text = extractor.extract_text_with_formatting()

        # By page
        pages = extractor.extract_text_by_page()
        for i, page_text in enumerate(pages, 1):
            print(f"Page {i}: {len(page_text)} characters")

Image Extraction
~~~~~~~~~~~~~~~~

Extract images from PDFs::

    with PyMuPDFExtractor("document.pdf") as extractor:
        images = extractor.extract_images()

        for img in images:
            print(f"Page {img['page_num']}: {img['width']}x{img['height']}")
            img['image'].save(f"image_{img['page_num']}_{img['image_index']}.png")

Text Normalization
------------------

Custom Normalization
~~~~~~~~~~~~~~~~~~~~

Configure text normalization::

    from src.processors.text_normalizer import TextNormalizer

    normalizer = TextNormalizer(
        remove_repetitive_content=True,
        threshold=3  # Remove lines repeated 3+ times
    )

    clean_text = normalizer.normalize(raw_text)

Selective Processing
~~~~~~~~~~~~~~~~~~~~

Apply specific normalization steps::

    # Remove page markers only
    text = normalizer.remove_page_markers(raw_text)

    # Clean line breaks only
    text = normalizer.clean_line_breaks(text)

Metadata Parsing
----------------

Custom Metadata Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    from src.processors.metadata_parser import MetadataParser

    parser = MetadataParser()
    metadata = parser.parse(text)

    # Access structured data
    if metadata.is_initial_petition:
        print("This is an initial petition")
        print(f"Court: {metadata.court}")
        print(f"Case value: {metadata.case_value}")

    # Format metadata as Markdown
    metadata_md = parser.format_metadata_as_markdown(metadata)

Output Formatting
-----------------

Markdown Variants
~~~~~~~~~~~~~~~~~

Generate different Markdown formats::

    from src.formatters.markdown_formatter import MarkdownFormatter

    formatter = MarkdownFormatter()

    # Basic Markdown
    basic_md = formatter.format(text, metadata)

    # With automatic section detection
    structured_md = formatter.format_with_sections(text, metadata)

    # RAG-optimized chunks
    chunks = formatter.format_for_rag(
        text,
        metadata=metadata,
        chunk_size=1000
    )

JSON Export
~~~~~~~~~~~

Structured JSON output::

    from src.formatters.json_formatter import JSONFormatter

    formatter = JSONFormatter()

    # Flat structure
    flat_json = formatter.format(text, metadata, hierarchical=False)

    # Hierarchical with paragraphs
    hier_json = formatter.format(text, metadata, hierarchical=True)

    # As string
    json_str = formatter.format_to_string(
        text,
        metadata,
        indent=2  # Pretty-printed
    )

Table Processing
----------------

Advanced Table Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    from src.extractors.table_extractor import TableExtractor

    extractor = TableExtractor("document.pdf")

    # Custom table detection settings
    tables = extractor.extract_tables(
        table_settings={
            'vertical_strategy': 'lines',
            'horizontal_strategy': 'lines',
            'snap_tolerance': 3
        }
    )

    # Check for tables
    if extractor.has_tables():
        print(f"Found {extractor.get_table_count()} tables")

Table Formatting
~~~~~~~~~~~~~~~~

Format tables as Markdown::

    from src.formatters.table_formatter import TableFormatter

    formatter = TableFormatter()

    for table in tables:
        # Format as Markdown
        md_table = formatter.format_table(table['data'])

        # With caption
        captioned = formatter.format_table_with_caption(
            table,
            caption=f"Table from page {table['page']}"
        )

Error Handling
--------------

Validation
~~~~~~~~~~

Validate PDFs before processing::

    from src.utils.validators import PDFValidator
    from pathlib import Path

    pdf_path = Path("document.pdf")

    try:
        PDFValidator.validate_all(
            pdf_path,
            max_size_mb=100,
            max_pages=1000
        )
        # Safe to process
    except Exception as e:
        print(f"Validation failed: {e}")

Performance Monitoring
----------------------

Track Performance
~~~~~~~~~~~~~~~~~

::

    from src.utils.cache import get_performance_monitor

    monitor = get_performance_monitor()

    # Your code here...

    # View metrics
    metrics = monitor.get_metrics()
    print(monitor.report())

Caching
~~~~~~~

Enable image description caching::

    from src.processors.image_analyzer import ImageAnalyzer

    analyzer = ImageAnalyzer(
        api_key="your-gemini-key",
        enable_cache=True
    )

    # First call hits API
    desc1 = analyzer.describe_image(image)

    # Second call uses cache
    desc2 = analyzer.describe_image(image)  # Fast!

Configuration Management
-------------------------

Load Configuration
~~~~~~~~~~~~~~~~~~

::

    from src.utils.config import get_config, reload_config

    # Get default config
    config = get_config()

    # Reload from file
    config = reload_config(Path("config.yaml"))

    # Access settings
    print(f"Max size: {config.max_pdf_size_mb}MB")
    print(f"Chunk size: {config.chunk_size}")

Best Practices
--------------

1. **Always use context managers** for PyMuPDFExtractor
2. **Validate PDFs** before processing large batches
3. **Enable caching** for repeated image analysis
4. **Monitor performance** in production environments
5. **Configure chunk size** based on your vector database
6. **Use structured Markdown** for better RAG results
