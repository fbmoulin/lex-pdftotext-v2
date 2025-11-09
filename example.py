#!/usr/bin/env python3
"""
Example: Using the PDF Legal Text Extractor programmatically.

This script demonstrates how to use the library in your own Python code.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors import PyMuPDFExtractor
from src.formatters import MarkdownFormatter
from src.processors import MetadataParser, TextNormalizer


def example_basic_extraction(pdf_path: str):
    """
    Example 1: Basic text extraction from PDF.
    """
    print("=" * 60)
    print("EXAMPLE 1: Basic Text Extraction")
    print("=" * 60)

    with PyMuPDFExtractor(pdf_path) as extractor:
        # Get basic info
        page_count = extractor.get_page_count()
        print(f"\n📄 PDF: {Path(pdf_path).name}")
        print(f"   Páginas: {page_count}")

        # Extract text
        text = extractor.extract_text()
        print(f"   Caracteres extraídos: {len(text)}")
        print("\n   Primeiros 200 caracteres:")
        print(f"   {text[:200]}...\n")


def example_with_normalization(pdf_path: str):
    """
    Example 2: Extract and normalize text.
    """
    print("=" * 60)
    print("EXAMPLE 2: Text Extraction + Normalization")
    print("=" * 60)

    # Extract
    with PyMuPDFExtractor(pdf_path) as extractor:
        raw_text = extractor.extract_text()

    print(f"\n📄 Texto bruto: {len(raw_text)} caracteres")

    # Normalize
    normalizer = TextNormalizer()
    clean_text = normalizer.normalize(raw_text)
    clean_text = normalizer.remove_page_markers(clean_text)

    print(f"   Texto normalizado: {len(clean_text)} caracteres")
    print(f"   Redução: {len(raw_text) - len(clean_text)} caracteres\n")


def example_metadata_extraction(pdf_path: str):
    """
    Example 3: Extract metadata from legal document.
    """
    print("=" * 60)
    print("EXAMPLE 3: Metadata Extraction")
    print("=" * 60)

    # Extract and normalize text
    with PyMuPDFExtractor(pdf_path) as extractor:
        raw_text = extractor.extract_text()

    normalizer = TextNormalizer()
    text = normalizer.normalize(raw_text)

    # Extract metadata
    parser = MetadataParser()
    metadata = parser.parse(text)

    print("\n⚖️  Metadados Jurídicos:\n")

    if metadata.process_number:
        print(f"   Processo: {metadata.process_number}")

    if metadata.document_ids:
        print(f"   IDs dos Documentos: {', '.join(metadata.document_ids[:3])}")
        if len(metadata.document_ids) > 3:
            print(f"   ... e mais {len(metadata.document_ids) - 3}")

    if metadata.court:
        print(f"   Vara/Tribunal: {metadata.court}")

    if metadata.case_value:
        print(f"   Valor da Causa: R$ {metadata.case_value}")

    if metadata.author:
        print(f"   Autor: {metadata.author}")

    if metadata.defendant:
        print(f"   Réu: {metadata.defendant}")

    if metadata.lawyers:
        print("\n   Advogados:")
        for lawyer in metadata.lawyers:
            print(f"      - {lawyer['name']} (OAB/{lawyer['state']} {lawyer['oab']})")

    if metadata.signature_dates:
        print(f"\n   Assinaturas: {', '.join(metadata.signature_dates)}")

    # Document type
    doc_types = []
    if metadata.is_initial_petition:
        doc_types.append("Petição Inicial")
    if metadata.is_decision:
        doc_types.append("Decisão")
    if metadata.is_certificate:
        doc_types.append("Certidão")

    if doc_types:
        print(f"\n   Tipo: {', '.join(doc_types)}")

    print()


def example_markdown_output(pdf_path: str, output_path: str = "example_output.md"):
    """
    Example 4: Generate structured Markdown output.
    """
    print("=" * 60)
    print("EXAMPLE 4: Markdown Output")
    print("=" * 60)

    # Full pipeline
    with PyMuPDFExtractor(pdf_path) as extractor:
        raw_text = extractor.extract_text()

    normalizer = TextNormalizer()
    text = normalizer.normalize(raw_text)
    text = normalizer.remove_page_markers(text)

    parser = MetadataParser()
    metadata = parser.parse(text)

    # Format as Markdown
    formatter = MarkdownFormatter()
    markdown = formatter.format(text, metadata, include_metadata_header=True)

    # Save
    MarkdownFormatter.save_to_file(markdown, output_path)

    print(f"\n✅ Markdown salvo em: {output_path}")
    print(f"   Tamanho: {len(markdown)} caracteres")
    print("\n   Preview (primeiras 500 caracteres):")
    print(f"\n{markdown[:500]}...\n")


def example_rag_chunks(pdf_path: str):
    """
    Example 5: Generate chunks for RAG pipeline.
    """
    print("=" * 60)
    print("EXAMPLE 5: RAG Chunks")
    print("=" * 60)

    # Full pipeline
    with PyMuPDFExtractor(pdf_path) as extractor:
        raw_text = extractor.extract_text()

    normalizer = TextNormalizer()
    text = normalizer.normalize(raw_text)

    parser = MetadataParser()
    metadata = parser.parse(text)

    # Generate chunks for RAG
    formatter = MarkdownFormatter()
    chunks = formatter.format_for_rag(text, metadata, chunk_size=1000)

    print("\n🤖 Chunks para RAG:")
    print(f"   Total de chunks: {len(chunks)}")
    print("\n   Exemplo - Chunk 0:")
    print(f"   Texto: {chunks[0]['text'][:200]}...")
    print(f"   Metadata: {chunks[0]['metadata']}")
    print()


def main():
    """Run all examples."""

    # Check if PDF path provided
    if len(sys.argv) < 2:
        print("❌ Erro: Forneça o caminho do PDF")
        print(f"\nUso: python {sys.argv[0]} <caminho_do_pdf>")
        print(f"Exemplo: python {sys.argv[0]} data/input/processo.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Validate PDF exists
    if not Path(pdf_path).exists():
        print(f"❌ Erro: Arquivo não encontrado: {pdf_path}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("PDF LEGAL TEXT EXTRACTOR - EXAMPLES")
    print("=" * 60)
    print(f"\nPDF: {pdf_path}\n")

    try:
        # Run examples
        example_basic_extraction(pdf_path)
        example_with_normalization(pdf_path)
        example_metadata_extraction(pdf_path)
        example_markdown_output(pdf_path)
        example_rag_chunks(pdf_path)

        print("=" * 60)
        print("✅ Todos os exemplos executados com sucesso!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
