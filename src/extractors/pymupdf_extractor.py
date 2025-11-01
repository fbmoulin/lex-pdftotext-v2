"""PyMuPDF (fitz) implementation of PDF text extractor."""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Any

from .base import PDFExtractor
from ..utils.validators import PDFValidator
from ..utils.exceptions import PDFExtractionError


class PyMuPDFExtractor(PDFExtractor):
    """
    Fast PDF text extractor using PyMuPDF (fitz).

    This is the recommended extractor for most use cases due to:
    - Excellent speed (42ms vs 2.5s for pdfminer)
    - High-quality text extraction
    - Good handling of whitespace and formatting
    """

    def __init__(self, pdf_path: str | Path, validate: bool = True, max_size_mb: int = 500):
        """
        Initialize PyMuPDF extractor.

        Args:
            pdf_path: Path to the PDF file
            validate: Whether to validate PDF before processing (default: True)
            max_size_mb: Maximum allowed file size in MB (default: 500)

        Raises:
            PDFExtractionError: If validation fails
        """
        super().__init__(pdf_path)
        self.doc: fitz.Document | None = None

        # Validate PDF if requested
        if validate:
            try:
                PDFValidator.validate_all(self.pdf_path, max_size_mb=max_size_mb)
            except PDFExtractionError:
                # Re-raise validation errors
                raise

    def __enter__(self):
        """Context manager entry."""
        self.doc = fitz.open(self.pdf_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close document."""
        if self.doc:
            self.doc.close()
            self.doc = None

    def _ensure_document_open(self):
        """Ensure document is open, open if not."""
        if self.doc is None:
            self.doc = fitz.open(self.pdf_path)

    def extract_text(self) -> str:
        """
        Extract all text from the PDF.

        Returns:
            str: Complete text from all pages, separated by page breaks
        """
        self._ensure_document_open()

        pages = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text("text")  # Extract as plain text
            # Skip completely empty or whitespace-only pages
            if text.strip():
                pages.append(text)

        # Join pages with simple double newline (will be cleaned later)
        return "\n\n".join(pages)

    def extract_text_by_page(self) -> list[str]:
        """
        Extract text page by page.

        Returns:
            list[str]: List of text strings, one per page
        """
        self._ensure_document_open()

        pages = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            text = page.get_text("text")
            pages.append(text)

        return pages

    def get_metadata(self) -> dict[str, Any]:
        """
        Extract PDF metadata.

        Returns:
            dict: PDF metadata including title, author, creation date, etc.
        """
        self._ensure_document_open()

        metadata = self.doc.metadata
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'keywords': metadata.get('keywords', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', ''),
            'page_count': len(self.doc)
        }

    def get_page_count(self) -> int:
        """
        Get the total number of pages.

        Returns:
            int: Number of pages in the PDF
        """
        self._ensure_document_open()
        return len(self.doc)

    def extract_text_with_formatting(self) -> str:
        """
        Extract text while preserving some formatting information.

        Returns:
            str: Text with basic formatting preserved
        """
        self._ensure_document_open()

        pages = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            # Extract as dict to get more structure
            text_dict = page.get_text("dict")

            # Build formatted text from blocks
            page_text = []
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        line_text = ""
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                        if line_text.strip():
                            page_text.append(line_text)

            pages.append("\n".join(page_text))

        return "\n\n--- PÁGINA {} ---\n\n".join(
            [f"\n\n--- PÁGINA {i+1} ---\n\n{text}" for i, text in enumerate(pages)]
        ).lstrip("\n\n--- PÁGINA 1 ---\n\n")

    def close(self):
        """Explicitly close the document."""
        if self.doc:
            self.doc.close()
            self.doc = None
