"""Base interface for PDF text extractors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..utils.exceptions import InvalidPathError


class PDFExtractor(ABC):
    """Abstract base class for PDF text extraction."""

    def __init__(self, pdf_path: str | Path):
        """
        Initialize the extractor.

        Args:
            pdf_path: Path to the PDF file to extract text from

        Raises:
            InvalidPathError: If file doesn't exist or isn't a PDF
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise InvalidPathError(f"Arquivo não encontrado: {pdf_path}")
        if not self.pdf_path.suffix.lower() == ".pdf":
            raise InvalidPathError(f"Arquivo deve ser PDF: {pdf_path}")

    @abstractmethod
    def extract_text(self) -> str:
        """
        Extract all text from the PDF.

        Returns:
            str: Complete text extracted from all pages
        """
        pass

    @abstractmethod
    def extract_text_by_page(self) -> list[str]:
        """
        Extract text page by page.

        Returns:
            list[str]: List of text strings, one per page
        """
        pass

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """
        Extract PDF metadata.

        Returns:
            dict: PDF metadata (title, author, creation date, etc.)
        """
        pass

    @abstractmethod
    def get_page_count(self) -> int:
        """
        Get the total number of pages.

        Returns:
            int: Number of pages in the PDF
        """
        pass
