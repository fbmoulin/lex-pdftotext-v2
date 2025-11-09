"""Tests for image extraction functionality."""

import pytest
import io
from pathlib import Path
from PIL import Image
from unittest.mock import Mock, patch, MagicMock
import sys

from src.extractors.pymupdf_extractor import PyMuPDFExtractor
from src.processors.image_analyzer import format_image_description_markdown
from src.utils.exceptions import PDFExtractionError

# Check if google-generativeai is available
try:
    import google.generativeai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Only import ImageAnalyzer if we can mock google-generativeai
if HAS_GEMINI:
    from src.processors.image_analyzer import ImageAnalyzer


class TestPyMuPDFExtractorImages:
    """Test image extraction from PyMuPDFExtractor."""

    @patch('fitz.open')
    def test_extract_images_basic(self, mock_fitz_open):
        """Test basic image extraction."""
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        # Create mock page with one image
        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1, 0, 100, 100, 8, 'jpeg', 'DeviceRGB', '', 'Im1', '')]

        mock_doc.__getitem__.return_value = mock_page

        # Create mock image data
        test_image = Image.new('RGB', (100, 100), color='red')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()

        mock_doc.extract_image.return_value = {
            'image': img_bytes,
            'ext': 'jpeg'
        }

        mock_fitz_open.return_value = mock_doc

        # Test extraction
        with patch.object(Path, 'exists', return_value=True):
            extractor = PyMuPDFExtractor('/fake/path.pdf', validate=False)
            extractor.doc = mock_doc
            images = extractor.extract_images()

        assert len(images) == 1
        assert images[0]['page_num'] == 1
        assert images[0]['image_index'] == 0
        assert images[0]['width'] == 100
        assert images[0]['height'] == 100
        assert images[0]['xref'] == 1
        assert images[0]['format'] == 'jpeg'
        assert isinstance(images[0]['image'], Image.Image)

    @patch('fitz.open')
    def test_extract_images_multiple_pages(self, mock_fitz_open):
        """Test image extraction from multiple pages."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2

        # Create test image
        test_image = Image.new('RGB', (50, 50), color='blue')
        img_buffer = io.BytesIO()
        test_image.save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()

        # Page 1: one image
        mock_page1 = MagicMock()
        mock_page1.get_images.return_value = [(1, 0, 50, 50, 8, 'png', 'DeviceRGB', '', 'Im1', '')]

        # Page 2: two images
        mock_page2 = MagicMock()
        mock_page2.get_images.return_value = [
            (2, 0, 50, 50, 8, 'png', 'DeviceRGB', '', 'Im2', ''),
            (3, 0, 50, 50, 8, 'png', 'DeviceRGB', '', 'Im3', '')
        ]

        mock_doc.__getitem__.side_effect = [mock_page1, mock_page2]
        mock_doc.extract_image.return_value = {'image': img_bytes, 'ext': 'png'}

        mock_fitz_open.return_value = mock_doc

        with patch.object(Path, 'exists', return_value=True):
            extractor = PyMuPDFExtractor('/fake/path.pdf', validate=False)
            extractor.doc = mock_doc
            images = extractor.extract_images()

        assert len(images) == 3
        assert images[0]['page_num'] == 1
        assert images[1]['page_num'] == 2
        assert images[2]['page_num'] == 2

    @patch('fitz.open')
    def test_extract_images_no_images(self, mock_fitz_open):
        """Test extraction from PDF with no images."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.get_images.return_value = []  # No images

        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        with patch.object(Path, 'exists', return_value=True):
            extractor = PyMuPDFExtractor('/fake/path.pdf', validate=False)
            extractor.doc = mock_doc
            images = extractor.extract_images()

        assert len(images) == 0

    @patch('fitz.open')
    def test_extract_images_handles_corrupt_images(self, mock_fitz_open):
        """Test extraction handles corrupt/invalid images gracefully."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1, 0, 100, 100, 8, 'jpeg', 'DeviceRGB', '', 'Im1', '')]

        mock_doc.__getitem__.return_value = mock_page

        # Simulate extraction error
        mock_doc.extract_image.side_effect = Exception("Corrupt image data")

        mock_fitz_open.return_value = mock_doc

        with patch.object(Path, 'exists', return_value=True):
            extractor = PyMuPDFExtractor('/fake/path.pdf', validate=False)
            extractor.doc = mock_doc
            images = extractor.extract_images()

        # Should skip corrupt image and return empty list
        assert len(images) == 0

    @patch('fitz.open')
    def test_extract_images_document_not_open(self, mock_fitz_open):
        """Test extraction opens document if not already open."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1

        mock_page = MagicMock()
        mock_page.get_images.return_value = []

        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        with patch.object(Path, 'exists', return_value=True):
            extractor = PyMuPDFExtractor('/fake/path.pdf', validate=False)
            # Don't set extractor.doc - it should open automatically
            images = extractor.extract_images()

        # Should have opened the document
        assert extractor.doc is not None


@pytest.mark.skipif(not HAS_GEMINI, reason="google-generativeai not installed")
class TestImageAnalyzerDescribe:
    """Test ImageAnalyzer description functionality."""

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'})
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_describe_image_basic(self, mock_model_class, mock_configure):
        """Test basic image description."""
        # Create mock model and response
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "**Tipo:** Foto\n**Descrição:** Teste"

        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        analyzer = ImageAnalyzer(enable_cache=False)

        test_image = Image.new('RGB', (100, 100), color='red')
        description = analyzer.describe_image(test_image, context="documento", page_num=1)

        assert "Tipo" in description
        assert "Descrição" in description
        assert mock_model.generate_content.called

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'})
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_describe_image_uses_cache(self, mock_model_class, mock_configure):
        """Test image description uses cache."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Cached description"

        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        analyzer = ImageAnalyzer(enable_cache=True)

        test_image = Image.new('RGB', (100, 100), color='red')

        # First call - should hit API
        desc1 = analyzer.describe_image(test_image, context="doc")
        assert mock_model.generate_content.call_count == 1

        # Second call with same image - should use cache
        desc2 = analyzer.describe_image(test_image, context="doc")
        assert mock_model.generate_content.call_count == 1  # Not called again
        assert desc1 == desc2

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'})
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_describe_image_handles_api_error(self, mock_model_class, mock_configure):
        """Test image description handles API errors."""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")

        mock_model_class.return_value = mock_model

        analyzer = ImageAnalyzer(enable_cache=False)

        test_image = Image.new('RGB', (100, 100), color='red')

        # Should raise exception
        with pytest.raises(Exception):
            analyzer.describe_image(test_image, context="doc")

    def test_describe_image_no_api_key(self):
        """Test ImageAnalyzer requires API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                ImageAnalyzer()

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'})
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_describe_image_resizes_large_images(self, mock_model_class, mock_configure):
        """Test large images are resized before API call."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Description"

        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        analyzer = ImageAnalyzer(max_image_size_mb=1, enable_cache=False)

        # Create large image (should trigger resize)
        large_image = Image.new('RGB', (5000, 5000), color='red')

        description = analyzer.describe_image(large_image, context="doc")

        # Should have called API (image was resized and sent)
        assert mock_model.generate_content.called


@pytest.mark.skipif(not HAS_GEMINI, reason="google-generativeai not installed")
class TestImageAnalyzerBatch:
    """Test batch image analysis."""

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'})
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_describe_images_batch(self, mock_model_class, mock_configure):
        """Test batch image description."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Description"

        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        analyzer = ImageAnalyzer(enable_cache=False)

        images = [
            {'image': Image.new('RGB', (100, 100), color='red'), 'page_num': 1},
            {'image': Image.new('RGB', (100, 100), color='blue'), 'page_num': 2}
        ]

        results = analyzer.describe_images_batch(images, context="doc")

        assert len(results) == 2
        assert all('description' in result for result in results)
        assert results[0]['page_num'] == 1
        assert results[1]['page_num'] == 2

    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'})
    @patch('google.generativeai.configure')
    @patch('google.generativeai.GenerativeModel')
    def test_describe_images_batch_handles_errors(self, mock_model_class, mock_configure):
        """Test batch processing continues on individual errors."""
        mock_model = MagicMock()

        # First call succeeds, second fails, third succeeds
        mock_model.generate_content.side_effect = [
            MagicMock(text="Success 1"),
            Exception("API Error"),
            MagicMock(text="Success 2")
        ]

        mock_model_class.return_value = mock_model

        analyzer = ImageAnalyzer(enable_cache=False)

        images = [
            {'image': Image.new('RGB', (100, 100), color='red'), 'page_num': 1},
            {'image': Image.new('RGB', (100, 100), color='blue'), 'page_num': 2},
            {'image': Image.new('RGB', (100, 100), color='green'), 'page_num': 3}
        ]

        results = analyzer.describe_images_batch(images, context="doc")

        # All 3 results should be present
        assert len(results) == 3

        # First and third should have real descriptions
        assert "Success 1" in results[0]['description']
        assert "Success 2" in results[2]['description']

        # Second should have error
        assert "Erro" in results[1]['description']


class TestFormatImageDescription:
    """Test image description formatting."""

    def test_format_image_description_markdown(self):
        """Test formatting image description as Markdown."""
        image_data = {
            'page_num': 5,
            'width': 800,
            'height': 600,
            'description': '**Tipo:** Foto\n**Descrição:** Teste'
        }

        result = format_image_description_markdown(image_data, index=3)

        assert '### 🖼️ Imagem 3' in result
        assert 'Página 5' in result
        assert '800x600 pixels' in result
        assert 'Tipo:' in result
        assert 'Descrição:' in result

    def test_format_image_description_no_description(self):
        """Test formatting when description is missing."""
        image_data = {
            'page_num': 1,
            'width': 100,
            'height': 100
        }

        result = format_image_description_markdown(image_data, index=1)

        assert '### 🖼️ Imagem 1' in result
        assert '[Sem descrição]' in result

    def test_format_image_description_missing_metadata(self):
        """Test formatting handles missing metadata gracefully."""
        image_data = {
            'description': 'Test description'
        }

        result = format_image_description_markdown(image_data, index=1)

        # Should use '?' for missing values
        assert 'Página ?' in result
        assert '?x? pixels' in result
