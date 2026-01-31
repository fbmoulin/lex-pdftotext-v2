"""PyMuPDF (fitz) implementation of PDF text extractor."""

import io
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from PIL import Image

from ..utils.cache import get_performance_monitor
from ..utils.config import get_config
from ..utils.constants import PAGE_LOG_INTERVAL
from ..utils.exceptions import PDFExtractionError
from ..utils.logger import get_logger
from ..utils.timeout import TimeoutError
from ..utils.validators import PDFValidator
from .base import PDFExtractor

# Initialize logger, performance monitor, and config
logger = get_logger(__name__)
performance = get_performance_monitor()
config = get_config()


class PyMuPDFExtractor(PDFExtractor):
    """
    Fast PDF text extractor using PyMuPDF (fitz).

    This is the recommended extractor for most use cases due to:
    - Excellent speed (42ms vs 2.5s for pdfminer)
    - High-quality text extraction
    - Good handling of whitespace and formatting
    """

    def __init__(
        self,
        pdf_path: str | Path,
        validate: bool = True,
        max_size_mb: int = 500,
        open_timeout: int = 30,
    ):
        """
        Initialize PyMuPDF extractor.

        Args:
            pdf_path: Path to the PDF file
            validate: Whether to validate PDF before processing (default: True)
            max_size_mb: Maximum allowed file size in MB (default: 500)
            open_timeout: Timeout in seconds for opening PDF (default: 30)

        Raises:
            PDFExtractionError: If validation fails
        """
        super().__init__(pdf_path)
        self.doc: fitz.Document | None = None
        self.open_timeout = open_timeout

        logger.info(f"Initializing PyMuPDF extractor for: {pdf_path}")

        # Validate PDF if requested
        if validate:
            try:
                logger.debug("Validating PDF...")
                PDFValidator.validate_all(self.pdf_path, max_size_mb=max_size_mb)
                logger.debug("PDF validation successful")
            except PDFExtractionError as e:
                logger.error(f"PDF validation failed: {e}")
                # Re-raise validation errors
                raise

    def _open_pdf_with_timeout(self) -> fitz.Document:
        """
        Open PDF with timeout to prevent infinite hangs.

        Returns:
            Opened fitz.Document

        Raises:
            TimeoutError: If PDF opening exceeds timeout
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fitz.open, str(self.pdf_path))
            try:
                logger.debug(f"Opening PDF with {self.open_timeout}s timeout...")
                doc = future.result(timeout=self.open_timeout)
                logger.info(f"PDF opened successfully: {len(doc)} pages")
                return doc
            except FuturesTimeoutError:
                future.cancel()
                error_msg = f"PDF opening exceeded timeout of {self.open_timeout} seconds"
                logger.error(error_msg)
                raise TimeoutError(error_msg) from None

    def __enter__(self):
        """Context manager entry."""
        self.doc = self._open_pdf_with_timeout()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close document."""
        if self.doc:
            logger.debug("Closing PDF document")
            self.doc.close()
            self.doc = None

    def _ensure_document_open(self):
        """Ensure document is open, open if not."""
        if self.doc is None:
            self.doc = self._open_pdf_with_timeout()

    @performance.track("pdf_text_extraction")
    def extract_text(self) -> str:
        """
        Extract all text from the PDF.

        Returns:
            str: Complete text from all pages, separated by page breaks

        Raises:
            TimeoutError: If text extraction takes too long
        """
        self._ensure_document_open()
        assert self.doc is not None

        logger.info(f"Extracting text from {len(self.doc)} pages")
        pages = []

        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]

                # Extract text with timeout for potentially slow pages
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(page.get_text, "text")
                    try:
                        text = future.result(timeout=config.page_extraction_timeout)
                    except FuturesTimeoutError:
                        logger.warning(
                            f"Page {page_num + 1} extraction timed out after {config.page_extraction_timeout}s, skipping"
                        )
                        continue

                # Skip completely empty or whitespace-only pages
                if text.strip():
                    pages.append(text)

                if (page_num + 1) % PAGE_LOG_INTERVAL == 0:
                    logger.debug(f"Processed {page_num + 1}/{len(self.doc)} pages")

            except Exception as e:
                logger.error(f"Error extracting text from page {page_num + 1}: {e}")
                # Continue with other pages
                continue

        logger.info(f"Text extraction completed: {len(pages)} non-empty pages")

        # Join pages with simple double newline (will be cleaned later)
        return "\n\n".join(pages)

    def extract_text_by_page(self) -> list[str]:
        """
        Extract text page by page.

        Returns:
            list[str]: List of text strings, one per page
        """
        self._ensure_document_open()
        assert self.doc is not None

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
        assert self.doc is not None

        metadata = self.doc.metadata
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "page_count": len(self.doc),
        }

    def get_page_count(self) -> int:
        """
        Get the total number of pages.

        Returns:
            int: Number of pages in the PDF
        """
        self._ensure_document_open()
        assert self.doc is not None
        return len(self.doc)

    def extract_text_with_formatting(self) -> str:
        """
        Extract text while preserving some formatting information.

        Returns:
            str: Text with basic formatting preserved
        """
        self._ensure_document_open()
        assert self.doc is not None

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

        # Build page-separated text
        result = "\n\n--- PÁGINA {} ---\n\n".join(
            [f"\n\n--- PÁGINA {i + 1} ---\n\n{text}" for i, text in enumerate(pages)]
        )
        # Remove first page marker prefix
        prefix = "\n\n--- PÁGINA 1 ---\n\n"
        if result.startswith(prefix):
            result = result[len(prefix) :]
        return result

    def extract_images(self) -> list[dict[str, Any]]:
        """
        Extract all images from the PDF with their metadata.

        Returns:
            list[dict]: List of image dictionaries containing:
                - page_num: Page number where image was found (1-indexed)
                - image_index: Index of image on that page
                - image: PIL Image object
                - width: Image width in pixels
                - height: Image height in pixels
                - xref: Internal PDF reference number
        """
        self._ensure_document_open()
        assert self.doc is not None

        images = []
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]  # Image XREF reference

                try:
                    # Extract the image
                    base_image = self.doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))

                    # Store image info
                    images.append(
                        {
                            "page_num": page_num + 1,  # 1-indexed for users
                            "image_index": img_index,
                            "image": pil_image,
                            "width": pil_image.width,
                            "height": pil_image.height,
                            "xref": xref,
                            "format": base_image.get("ext", "unknown"),
                        }
                    )

                except Exception:
                    # Skip images that can't be extracted (e.g., inline images, forms)
                    continue

        return images

    def close(self):
        """Explicitly close the document."""
        if self.doc:
            self.doc.close()
            self.doc = None
