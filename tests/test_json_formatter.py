"""Tests for JSON formatter."""

import json
import tempfile
from pathlib import Path

import pytest

from src.formatters.json_formatter import JSONFormatter
from src.processors.metadata_parser import DocumentMetadata


@pytest.fixture
def sample_text():
    """Sample legal document text."""
    return """PROCESSO 1234567-89.2024.1.00.0000

Num. 12345678

Autor: JOÃO DA SILVA
Réu: EMPRESA XYZ LTDA

PETIÇÃO INICIAL

Por meio desta, vem o autor apresentar suas razões.

Assinado eletronicamente em 15/01/2024
Dr. JOSÉ SANTOS – OAB/SP 123456"""


@pytest.fixture
def sample_metadata():
    """Sample document metadata."""
    return DocumentMetadata(
        process_number="1234567-89.2024.1.00.0000",
        document_ids=["12345678"],
        court="Tribunal de Justiça",
        author="JOÃO DA SILVA",
        defendant="EMPRESA XYZ LTDA",
        lawyers=[{"name": "JOSÉ SANTOS", "oab": "123456", "state": "SP"}],
        signature_dates=["15/01/2024"],
        is_initial_petition=True,
        is_decision=False,
        is_certificate=False,
        sections=["PETIÇÃO INICIAL"],
        case_value=None,
    )


class TestJSONFormatterFormat:
    """Test JSON formatter format method."""

    def test_format_basic(self, sample_text):
        """Test basic format without metadata."""
        formatter = JSONFormatter()
        result = formatter.format(sample_text, include_metadata=False)

        assert isinstance(result, dict)
        assert "format_version" in result
        assert result["format_version"] == "1.0"
        assert "document_type" in result
        assert "content" in result
        assert result["content"]["text"] == sample_text

    def test_format_with_metadata(self, sample_text, sample_metadata):
        """Test format with metadata included."""
        formatter = JSONFormatter()
        result = formatter.format(sample_text, metadata=sample_metadata, include_metadata=True)

        assert "metadata" in result
        assert result["metadata"]["process_number"] == "1234567-89.2024.1.00.0000"
        assert result["metadata"]["parties"]["author"] == "JOÃO DA SILVA"
        assert result["metadata"]["parties"]["defendant"] == "EMPRESA XYZ LTDA"
        assert len(result["metadata"]["lawyers"]) == 1
        assert result["metadata"]["lawyers"][0]["name"] == "JOSÉ SANTOS"

    def test_format_auto_extracts_metadata(self, sample_text):
        """Test that format auto-extracts metadata when not provided."""
        formatter = JSONFormatter()
        result = formatter.format(sample_text, metadata=None, include_metadata=True)

        assert "metadata" in result
        assert result["metadata"]["process_number"] == "1234567-89.2024.1.00.0000"

    def test_format_hierarchical(self, sample_text, sample_metadata):
        """Test hierarchical formatting."""
        formatter = JSONFormatter()
        result = formatter.format(
            sample_text, metadata=sample_metadata, hierarchical=True, include_metadata=False
        )

        assert "content" in result
        assert "paragraph_count" in result["content"]
        assert "paragraphs" in result["content"]
        assert isinstance(result["content"]["paragraphs"], list)
        assert len(result["content"]["paragraphs"]) > 0

    def test_format_hierarchical_with_sections(self, sample_text, sample_metadata):
        """Test hierarchical formatting includes detected sections."""
        formatter = JSONFormatter()
        result = formatter.format(sample_text, metadata=sample_metadata, hierarchical=True)

        assert "content" in result
        assert "detected_sections" in result["content"]
        assert "PETIÇÃO INICIAL" in result["content"]["detected_sections"]


class TestJSONFormatterFormatToString:
    """Test JSON formatter format_to_string method."""

    def test_format_to_string_default_indent(self, sample_text):
        """Test formatting to string with default indentation."""
        formatter = JSONFormatter()
        result = formatter.format_to_string(sample_text, include_metadata=False)

        assert isinstance(result, str)
        # Check it's valid JSON
        data = json.loads(result)
        assert data["format_version"] == "1.0"

    def test_format_to_string_compact(self, sample_text):
        """Test formatting to compact JSON string."""
        formatter = JSONFormatter()
        result = formatter.format_to_string(sample_text, include_metadata=False, indent=None)

        assert isinstance(result, str)
        # Compact JSON shouldn't have newlines (except possibly in content)
        data = json.loads(result)
        assert data["format_version"] == "1.0"

    def test_format_to_string_custom_indent(self, sample_text):
        """Test formatting with custom indentation."""
        formatter = JSONFormatter()
        result = formatter.format_to_string(sample_text, include_metadata=False, indent=4)

        assert isinstance(result, str)
        assert "    " in result  # Should have 4-space indentation


class TestJSONFormatterDocumentType:
    """Test document type determination."""

    def test_determine_document_type_initial_petition(self, sample_text):
        """Test identifying initial petition."""
        metadata = DocumentMetadata(is_initial_petition=True)
        formatter = JSONFormatter()
        result = formatter._determine_document_type(metadata)
        assert result == "initial_petition"

    def test_determine_document_type_decision(self, sample_text):
        """Test identifying decision."""
        metadata = DocumentMetadata(is_decision=True)
        formatter = JSONFormatter()
        result = formatter._determine_document_type(metadata)
        assert result == "decision"

    def test_determine_document_type_certificate(self, sample_text):
        """Test identifying certificate."""
        metadata = DocumentMetadata(is_certificate=True)
        formatter = JSONFormatter()
        result = formatter._determine_document_type(metadata)
        assert result == "certificate"

    def test_determine_document_type_generic(self, sample_text):
        """Test fallback to generic legal document."""
        metadata = DocumentMetadata()
        formatter = JSONFormatter()
        result = formatter._determine_document_type(metadata)
        assert result == "legal_document"


class TestJSONFormatterMetadata:
    """Test metadata formatting."""

    def test_format_metadata_complete(self, sample_metadata):
        """Test formatting complete metadata."""
        formatter = JSONFormatter()
        result = formatter._format_metadata(sample_metadata)

        assert result["process_number"] == "1234567-89.2024.1.00.0000"
        assert result["document_ids"] == ["12345678"]
        assert result["court"] == "Tribunal de Justiça"
        assert result["parties"]["author"] == "JOÃO DA SILVA"
        assert result["parties"]["defendant"] == "EMPRESA XYZ LTDA"
        assert len(result["lawyers"]) == 1
        assert result["dates"]["signatures"] == ["15/01/2024"]
        assert result["classification"]["is_initial_petition"] is True
        assert result["classification"]["is_decision"] is False
        assert result["sections"] == ["PETIÇÃO INICIAL"]

    def test_format_metadata_minimal(self):
        """Test formatting minimal metadata."""
        metadata = DocumentMetadata()
        formatter = JSONFormatter()
        result = formatter._format_metadata(metadata)

        assert result["process_number"] is None
        assert result["document_ids"] == []
        assert result["lawyers"] == []


class TestJSONFormatterHierarchical:
    """Test hierarchical content formatting."""

    def test_format_hierarchical_basic(self):
        """Test basic hierarchical formatting."""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        metadata = DocumentMetadata()
        formatter = JSONFormatter()
        result = formatter._format_hierarchical(text, metadata)

        assert result["text"] == text
        assert result["character_count"] == len(text)
        assert result["word_count"] == len(text.split())
        assert result["paragraph_count"] == 3
        assert len(result["paragraphs"]) == 3

    def test_format_hierarchical_with_sections(self):
        """Test hierarchical formatting includes sections."""
        text = "Some text"
        metadata = DocumentMetadata(sections=["Introduction", "Body", "Conclusion"])
        formatter = JSONFormatter()
        result = formatter._format_hierarchical(text, metadata)

        assert "detected_sections" in result
        assert len(result["detected_sections"]) == 3

    def test_format_hierarchical_empty_paragraphs(self):
        """Test hierarchical formatting ignores empty paragraphs."""
        text = "Paragraph 1\n\n\n\n\n\nParagraph 2"
        metadata = DocumentMetadata()
        formatter = JSONFormatter()
        result = formatter._format_hierarchical(text, metadata)

        # Should only count non-empty paragraphs
        assert result["paragraph_count"] == 2


class TestJSONFormatterSaveToFile:
    """Test saving JSON to file."""

    def test_save_to_file_string_path(self, sample_text):
        """Test saving with string path."""
        formatter = JSONFormatter()
        data = formatter.format(sample_text, include_metadata=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "output.json")
            formatter.save_to_file(data, output_path)

            assert Path(output_path).exists()
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded["format_version"] == "1.0"

    def test_save_to_file_path_object(self, sample_text):
        """Test saving with Path object."""
        formatter = JSONFormatter()
        data = formatter.format(sample_text, include_metadata=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            formatter.save_to_file(data, output_path)

            assert output_path.exists()
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded["format_version"] == "1.0"

    def test_save_to_file_creates_directory(self, sample_text):
        """Test saving creates parent directories."""
        formatter = JSONFormatter()
        data = formatter.format(sample_text, include_metadata=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "output.json"
            formatter.save_to_file(data, output_path)

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_save_to_file_compact(self, sample_text):
        """Test saving with compact format."""
        formatter = JSONFormatter()
        data = formatter.format(sample_text, include_metadata=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "compact.json"
            formatter.save_to_file(data, output_path, indent=None)

            assert output_path.exists()
            content = output_path.read_text()
            # Compact JSON should be smaller
            assert len(content) < len(json.dumps(data, indent=2))

    def test_save_to_file_custom_indent(self, sample_text):
        """Test saving with custom indentation."""
        formatter = JSONFormatter()
        data = formatter.format(sample_text, include_metadata=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "custom.json"
            formatter.save_to_file(data, output_path, indent=4)

            assert output_path.exists()
            content = output_path.read_text()
            assert "    " in content  # Should have 4-space indentation


class TestJSONFormatterIntegration:
    """Integration tests for JSON formatter."""

    def test_complete_workflow(self, sample_text):
        """Test complete workflow from text to JSON file."""
        formatter = JSONFormatter()

        # Format
        data = formatter.format(sample_text, include_metadata=True, hierarchical=True)

        # Verify structure
        assert "format_version" in data
        assert "document_type" in data
        assert "metadata" in data
        assert "content" in data

        # Convert to string
        json_str = formatter.format_to_string(sample_text, include_metadata=True, hierarchical=True)
        assert isinstance(json_str, str)

        # Save to file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "complete.json"
            formatter.save_to_file(data, output_path)
            assert output_path.exists()

    def test_roundtrip(self, sample_text, sample_metadata):
        """Test that data can be saved and loaded back."""
        formatter = JSONFormatter()
        original_data = formatter.format(sample_text, metadata=sample_metadata)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "roundtrip.json"
            formatter.save_to_file(original_data, output_path)

            with open(output_path) as f:
                loaded_data = json.load(f)

            # Verify data matches
            assert loaded_data["format_version"] == original_data["format_version"]
            assert loaded_data["metadata"]["process_number"] == original_data["metadata"]["process_number"]
            assert loaded_data["content"]["text"] == original_data["content"]["text"]
