"""
Backward compatibility module.
All functionality moved to lex_pdftotext package.

This module provides backward compatibility for existing code that imports from 'src.*'.
New code should import from 'lex_pdftotext.*' directly.
"""

# Re-export submodules for backward compatibility
from .lex_pdftotext import extractors
from .lex_pdftotext import formatters
from .lex_pdftotext import processors
from .lex_pdftotext import utils

# Re-export main classes
from .lex_pdftotext import (
    __version__,
    PyMuPDFExtractor,
    TextNormalizer,
    MetadataParser,
    MarkdownFormatter,
    JSONFormatter,
    TableFormatter,
    extract_pdf,
    extract_metadata,
)

__all__ = [
    "__version__",
    # Submodules
    "extractors",
    "formatters",
    "processors",
    "utils",
    # Classes
    "PyMuPDFExtractor",
    "TextNormalizer",
    "MetadataParser",
    "MarkdownFormatter",
    "JSONFormatter",
    "TableFormatter",
    # Functions
    "extract_pdf",
    "extract_metadata",
]
