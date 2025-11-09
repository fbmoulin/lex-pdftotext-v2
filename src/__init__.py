"""PDF to text extraction for legal documents."""

__version__ = "0.1.0"

from .extractors import PyMuPDFExtractor
from .formatters import MarkdownFormatter
from .processors import MetadataParser, TextNormalizer

__all__ = ["PyMuPDFExtractor", "TextNormalizer", "MetadataParser", "MarkdownFormatter"]
