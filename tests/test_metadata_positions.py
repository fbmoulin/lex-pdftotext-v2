"""Tests for metadata with position tracking."""

from src.lex_pdftotext.processors.metadata_parser import DocumentMetadata, MetadataParser


class TestDocumentMetadataPositions:
    """Test DocumentMetadata position fields."""

    def test_metadata_has_position_fields(self):
        """DocumentMetadata should have document_positions field."""
        metadata = DocumentMetadata()

        assert hasattr(metadata, "document_positions")
        assert isinstance(metadata.document_positions, list)

    def test_metadata_has_section_anchors(self):
        """DocumentMetadata should have section_anchors field."""
        metadata = DocumentMetadata()

        assert hasattr(metadata, "section_anchors")
        assert isinstance(metadata.section_anchors, dict)


class TestMetadataParserPositions:
    """Test MetadataParser position extraction."""

    def test_parser_extracts_positions(self):
        """Parser should extract document ID positions."""
        text = """Processo 1234567-89.2024.8.08.0012

Num. 11111111 - Petição Inicial

Conforme exposto...

Num. 22222222 - Decisão"""

        parser = MetadataParser()
        metadata = parser.parse(text)

        assert len(metadata.document_positions) == 2
        assert metadata.document_positions[0]["id"] == "11111111"
        assert metadata.document_positions[1]["id"] == "22222222"

    def test_parser_generates_anchors(self):
        """Parser should generate anchor IDs for sections."""
        text = """Processo 1234567-89.2024.8.08.0012

I - DOS FATOS

Texto dos fatos...

II - DO DIREITO

Texto do direito..."""

        parser = MetadataParser()
        metadata = parser.parse(text)

        assert len(metadata.section_anchors) >= 2
        assert "dos-fatos" in metadata.section_anchors or "DOS FATOS" in metadata.sections
