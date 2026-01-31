"""
lex-pdftotext: Extração de texto de PDFs jurídicos brasileiros (PJe).

Uso simples:
    from lex_pdftotext import extract_pdf
    text, metadata = extract_pdf("documento.pdf")

Uso avançado:
    from lex_pdftotext.extractors import PyMuPDFExtractor
    from lex_pdftotext.processors import TextNormalizer, MetadataParser
    from lex_pdftotext.formatters import MarkdownFormatter
"""

__version__ = "1.0.0"

from .extractors import PyMuPDFExtractor
from .formatters import JSONFormatter, MarkdownFormatter, TableFormatter
from .processors import MetadataParser, TextNormalizer

__all__ = [
    # Version
    "__version__",
    # Extractors
    "PyMuPDFExtractor",
    # Processors
    "TextNormalizer",
    "MetadataParser",
    # Formatters
    "MarkdownFormatter",
    "JSONFormatter",
    "TableFormatter",
    # High-level API
    "extract_pdf",
    "extract_metadata",
]


def extract_pdf(
    pdf_path: str,
    normalize: bool = True,
    include_metadata: bool = True,
) -> tuple:
    """
    Extrai texto e metadados de um PDF jurídico.

    Args:
        pdf_path: Caminho para o arquivo PDF
        normalize: Se True, normaliza o texto (UPPERCASE → sentence case)
        include_metadata: Se True, extrai metadados (processo, partes, advogados)

    Returns:
        tuple: (texto_extraido, metadados) onde metadados é DocumentMetadata ou None

    Example:
        >>> text, metadata = extract_pdf("processo.pdf")
        >>> print(metadata.process_number)
        '0001234-56.2024.8.08.0012'
    """
    from .extractors import PyMuPDFExtractor
    from .processors import MetadataParser, TextNormalizer

    with PyMuPDFExtractor(pdf_path) as extractor:
        raw_text = extractor.extract_text()

    text = raw_text
    if normalize:
        normalizer = TextNormalizer()
        text = normalizer.normalize(raw_text)

    metadata = None
    if include_metadata:
        parser = MetadataParser()
        metadata = parser.parse(text)

    return text, metadata


def extract_metadata(pdf_path: str):
    """
    Extrai apenas os metadados de um PDF jurídico.

    Args:
        pdf_path: Caminho para o arquivo PDF

    Returns:
        DocumentMetadata: Metadados extraídos do documento

    Example:
        >>> metadata = extract_metadata("processo.pdf")
        >>> print(metadata.lawyers)
        ['João Silva – OAB/ES 12345']
    """
    text, metadata = extract_pdf(pdf_path, normalize=True, include_metadata=True)
    return metadata
