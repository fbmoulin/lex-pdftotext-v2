"""PDF to text extraction for legal documents."""

__version__ = "0.1.0"

from .extractors import PyMuPDFExtractor
from .processors import TextNormalizer, MetadataParser
from .formatters import MarkdownFormatter

__all__ = [
    'PyMuPDFExtractor',
    'TextNormalizer',
    'MetadataParser',
    'MarkdownFormatter'
]
