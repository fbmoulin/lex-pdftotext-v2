"""Tests for PyMuPDF extractor functionality."""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.extractors.pymupdf_extractor import PyMuPDFExtractor
from src.utils.exceptions import PDFExtractionError
from src.utils.timeout import TimeoutError


class TestPyMuPDFExtractorInit:
    """Test PyMuPDFExtractor initialization."""

    @patch("src.extractors.pymupdf_extractor.PDFValidator.validate_all")
    def test_init_with_validation(self, mock_validate, tmp_path):
        """Test initialization with validation enabled."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        extractor = PyMuPDFExtractor(pdf_file, validate=True)

        assert extractor.pdf_path == pdf_file
        assert extractor.doc is None
        assert extractor.open_timeout == 30
        mock_validate.assert_called_once()

    def test_init_without_validation(self, tmp_path):
        """Test initialization with validation disabled."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        extractor = PyMuPDFExtractor(pdf_file, validate=False)

        assert extractor.pdf_path == pdf_file
        assert extractor.doc is None

    @patch("src.extractors.pymupdf_extractor.PDFValidator.validate_all")
    def test_init_validation_fails(self, mock_validate, tmp_path):
        """Test initialization fails when validation fails."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_validate.side_effect = PDFExtractionError("Invalid PDF")

        with pytest.raises(PDFExtractionError, match="Invalid PDF"):
            PyMuPDFExtractor(pdf_file, validate=True)

    def test_init_custom_timeout(self, tmp_path):
        """Test initialization with custom timeout."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        extractor = PyMuPDFExtractor(pdf_file, validate=False, open_timeout=60)

        assert extractor.open_timeout == 60

    def test_init_custom_max_size(self, tmp_path):
        """Test initialization with custom max size."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        with patch("src.extractors.pymupdf_extractor.PDFValidator.validate_all") as mock_validate:
            PyMuPDFExtractor(pdf_file, validate=True, max_size_mb=100)

            # Verify max_size_mb was passed to validator
            call_args = mock_validate.call_args
            assert call_args[1]["max_size_mb"] == 100


class TestPyMuPDFExtractorOpenPDFWithTimeout:
    """Test _open_pdf_with_timeout() method."""

    @patch("fitz.open")
    def test_open_pdf_success(self, mock_fitz_open, tmp_path):
        """Test successful PDF opening."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        doc = extractor._open_pdf_with_timeout()

        assert doc == mock_doc
        mock_fitz_open.assert_called_once_with(str(pdf_file))

    @patch("fitz.open")
    def test_open_pdf_timeout(self, mock_fitz_open, tmp_path):
        """Test PDF opening timeout."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Mock slow PDF opening
        def slow_open(*args, **kwargs):
            import time

            time.sleep(10)
            return MagicMock()

        mock_fitz_open.side_effect = slow_open

        extractor = PyMuPDFExtractor(pdf_file, validate=False, open_timeout=1)

        with pytest.raises(TimeoutError, match="PDF opening exceeded timeout"):
            extractor._open_pdf_with_timeout()


class TestPyMuPDFExtractorContextManager:
    """Test context manager functionality."""

    @patch("fitz.open")
    def test_context_manager_opens_document(self, mock_fitz_open, tmp_path):
        """Test context manager opens document on enter."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)

        with extractor:
            assert extractor.doc == mock_doc

    @patch("fitz.open")
    def test_context_manager_closes_document(self, mock_fitz_open, tmp_path):
        """Test context manager closes document on exit."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)

        with extractor:
            pass

        mock_doc.close.assert_called_once()
        assert extractor.doc is None

    @patch("fitz.open")
    def test_context_manager_closes_on_exception(self, mock_fitz_open, tmp_path):
        """Test context manager closes document even on exception."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)

        try:
            with extractor:
                raise ValueError("Test error")
        except ValueError:
            pass

        mock_doc.close.assert_called_once()
        assert extractor.doc is None


class TestPyMuPDFExtractorExtractText:
    """Test extract_text() method."""

    @patch("fitz.open")
    def test_extract_text_single_page(self, mock_fitz_open, tmp_path):
        """Test text extraction from single page."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text from page 1"
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        text = extractor.extract_text()

        assert "Sample text from page 1" in text
        mock_page.get_text.assert_called()

    @patch("fitz.open")
    def test_extract_text_multiple_pages(self, mock_fitz_open, tmp_path):
        """Test text extraction from multiple pages."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3

        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 text"
        mock_page3 = MagicMock()
        mock_page3.get_text.return_value = "Page 3 text"

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2, mock_page3]
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        text = extractor.extract_text()

        assert "Page 1 text" in text
        assert "Page 2 text" in text
        assert "Page 3 text" in text
        assert text.count("\n\n") >= 2  # Pages separated by double newline

    @patch("fitz.open")
    def test_extract_text_skips_empty_pages(self, mock_fitz_open, tmp_path):
        """Test extraction skips empty/whitespace-only pages."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3

        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "   \n\n  "  # Whitespace only
        mock_page3 = MagicMock()
        mock_page3.get_text.return_value = "Page 3 text"

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2, mock_page3]
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        text = extractor.extract_text()

        assert "Page 1 text" in text
        assert "Page 3 text" in text
        # Should not have empty page content

    @patch("fitz.open")
    def test_extract_text_handles_page_errors(self, mock_fitz_open, tmp_path):
        """Test extraction continues when individual pages fail."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3

        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 text"
        mock_page2 = MagicMock()
        mock_page2.get_text.side_effect = Exception("Page error")
        mock_page3 = MagicMock()
        mock_page3.get_text.return_value = "Page 3 text"

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2, mock_page3]
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        text = extractor.extract_text()

        # Should have page 1 and 3, but skip page 2
        assert "Page 1 text" in text
        assert "Page 3 text" in text


class TestPyMuPDFExtractorExtractTextByPage:
    """Test extract_text_by_page() method."""

    @patch("fitz.open")
    def test_extract_text_by_page(self, mock_fitz_open, tmp_path):
        """Test page-by-page text extraction."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2"

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        pages = extractor.extract_text_by_page()

        assert len(pages) == 2
        assert pages[0] == "Page 1"
        assert pages[1] == "Page 2"


class TestPyMuPDFExtractorGetMetadata:
    """Test get_metadata() method."""

    @patch("fitz.open")
    def test_get_metadata(self, mock_fitz_open, tmp_path):
        """Test metadata extraction."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 10
        mock_doc.metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "subject": "Testing",
            "keywords": "test, pdf",
            "creator": "Test Creator",
            "producer": "Test Producer",
            "creationDate": "2025-01-01",
            "modDate": "2025-01-09",
        }
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        metadata = extractor.get_metadata()

        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "Test Author"
        assert metadata["subject"] == "Testing"
        assert metadata["keywords"] == "test, pdf"
        assert metadata["creator"] == "Test Creator"
        assert metadata["producer"] == "Test Producer"
        assert metadata["creation_date"] == "2025-01-01"
        assert metadata["modification_date"] == "2025-01-09"
        assert metadata["page_count"] == 10

    @patch("fitz.open")
    def test_get_metadata_missing_fields(self, mock_fitz_open, tmp_path):
        """Test metadata extraction with missing fields."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_doc.metadata = {}  # Empty metadata
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        metadata = extractor.get_metadata()

        # Should have empty strings for missing fields
        assert metadata["title"] == ""
        assert metadata["author"] == ""
        assert metadata["page_count"] == 5


class TestPyMuPDFExtractorGetPageCount:
    """Test get_page_count() method."""

    @patch("fitz.open")
    def test_get_page_count(self, mock_fitz_open, tmp_path):
        """Test page count retrieval."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 42
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        count = extractor.get_page_count()

        assert count == 42


class TestPyMuPDFExtractorExtractTextWithFormatting:
    """Test extract_text_with_formatting() method."""

    @patch("fitz.open")
    def test_extract_text_with_formatting(self, mock_fitz_open, tmp_path):
        """Test formatted text extraction."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.get_text.return_value = {
            "blocks": [
                {
                    "type": 0,  # Text block
                    "lines": [
                        {"spans": [{"text": "Line 1"}]},
                        {"spans": [{"text": "Line 2"}]},
                    ],
                }
            ]
        }

        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        text = extractor.extract_text_with_formatting()

        assert "Line 1" in text
        assert "Line 2" in text

    @patch("fitz.open")
    def test_extract_text_with_formatting_multiple_pages(self, mock_fitz_open, tmp_path):
        """Test formatted extraction with multiple pages."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = {
            "blocks": [{"type": 0, "lines": [{"spans": [{"text": "Page 1"}]}]}]
        }

        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = {
            "blocks": [{"type": 0, "lines": [{"spans": [{"text": "Page 2"}]}]}]
        }

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        text = extractor.extract_text_with_formatting()

        assert "Page 1" in text
        assert "Page 2" in text
        # Should have page markers
        assert "PÁGINA" in text


class TestPyMuPDFExtractorExtractImages:
    """Test extract_images() method."""

    @patch("fitz.open")
    def test_extract_images(self, mock_fitz_open, tmp_path):
        """Test image extraction."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Create a simple test image
        test_img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        test_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0)]  # xref=1

        mock_doc.__getitem__.return_value = mock_page
        mock_doc.extract_image.return_value = {
            "image": img_bytes.getvalue(),
            "ext": "png",
        }
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        images = extractor.extract_images()

        assert len(images) == 1
        assert images[0]["page_num"] == 1
        assert images[0]["image_index"] == 0
        assert images[0]["width"] == 100
        assert images[0]["height"] == 100
        assert images[0]["format"] == "png"
        assert isinstance(images[0]["image"], Image.Image)

    @patch("fitz.open")
    def test_extract_images_no_images(self, mock_fitz_open, tmp_path):
        """Test extraction when PDF has no images."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.get_images.return_value = []

        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        images = extractor.extract_images()

        assert len(images) == 0

    @patch("fitz.open")
    def test_extract_images_handles_errors(self, mock_fitz_open, tmp_path):
        """Test image extraction handles errors gracefully."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0)]

        mock_doc.__getitem__.return_value = mock_page
        mock_doc.extract_image.side_effect = Exception("Cannot extract image")
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        images = extractor.extract_images()

        # Should skip failed images
        assert len(images) == 0


class TestPyMuPDFExtractorClose:
    """Test close() method."""

    @patch("fitz.open")
    def test_close_closes_document(self, mock_fitz_open, tmp_path):
        """Test close method closes the document."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_fitz_open.return_value = mock_doc

        extractor = PyMuPDFExtractor(pdf_file, validate=False)
        extractor.doc = mock_doc

        extractor.close()

        mock_doc.close.assert_called_once()
        assert extractor.doc is None

    def test_close_when_no_document(self, tmp_path):
        """Test close when document is not open."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        extractor = PyMuPDFExtractor(pdf_file, validate=False)

        # Should not raise error
        extractor.close()

        assert extractor.doc is None
