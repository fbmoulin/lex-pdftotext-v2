"""Tests for procedural piece index generation."""

import pytest

from src.lex_pdftotext.formatters.index_generator import IndexGenerator
from src.lex_pdftotext.processors.metadata_parser import DocumentMetadata


class TestIndexGenerator:
    """Test index generation for procedural pieces."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata with positions."""
        metadata = DocumentMetadata(
            process_number="0018456-36.2018.8.08.0012",
            document_ids=["11111111", "22222222", "33333333"],
            document_positions=[
                {
                    "id": "11111111",
                    "line": 10,
                    "position": 100,
                    "context_before": "Petição Inicial",
                    "context_after": "apresentada",
                },
                {
                    "id": "22222222",
                    "line": 50,
                    "position": 500,
                    "context_before": "Decisão",
                    "context_after": "proferida",
                },
                {
                    "id": "33333333",
                    "line": 80,
                    "position": 800,
                    "context_before": "Certidão",
                    "context_after": "expedida",
                },
            ],
            is_initial_petition=True,
            is_decision=True,
            is_certificate=True,
            sections=["DOS FATOS", "DO DIREITO", "DOS PEDIDOS"],
            section_anchors={
                "DOS FATOS": "sec-dos-fatos",
                "DO DIREITO": "sec-do-direito",
                "DOS PEDIDOS": "sec-dos-pedidos",
            },
        )
        return metadata

    def test_generate_index_table(self, sample_metadata):
        """Should generate markdown table with document index."""
        generator = IndexGenerator()
        index = generator.generate_index_table(sample_metadata)

        assert "## Índice de Peças Processuais" in index
        assert "11111111" in index
        assert "22222222" in index
        assert "#doc-11111111" in index

    def test_generate_anchor_for_document(self, sample_metadata):
        """Should generate proper anchor ID for document."""
        generator = IndexGenerator()
        anchor = generator.generate_anchor("12345678")

        assert anchor == "doc-12345678"

    def test_generate_document_header(self, sample_metadata):
        """Should generate header with anchor for document piece."""
        generator = IndexGenerator()
        header = generator.generate_document_header(
            doc_id="11111111",
            doc_type="Petição Inicial",
            date="25/09/2025",
            signatory="Advogado Nome",
        )

        assert '<a id="doc-11111111"></a>' in header
        assert "Petição Inicial" in header

    def test_detect_document_type_from_context(self, sample_metadata):
        """Should detect document type from surrounding context."""
        generator = IndexGenerator()

        assert generator.detect_type("Petição Inicial apresentada") == "Petição Inicial"
        assert generator.detect_type("Decisão proferida pelo juiz") == "Decisão"
        assert generator.detect_type("Certidão expedida") == "Certidão"
        assert generator.detect_type("texto sem tipo") == "Documento"

    def test_generate_cross_reference_link(self, sample_metadata):
        """Should generate cross-reference link to document."""
        generator = IndexGenerator()
        link = generator.generate_cross_reference("12345678")

        assert link == "[#12345678](#doc-12345678)"


class TestIndexGeneratorIcons:
    """Test icon assignment for document types."""

    def test_petition_icon(self):
        generator = IndexGenerator()
        assert generator.get_icon("Petição Inicial") == "📄"
        assert generator.get_icon("Petição") == "📄"

    def test_decision_icon(self):
        generator = IndexGenerator()
        assert generator.get_icon("Decisão") == "⚖️"
        assert generator.get_icon("Sentença") == "⚖️"
        assert generator.get_icon("Despacho") == "⚖️"

    def test_certificate_icon(self):
        generator = IndexGenerator()
        assert generator.get_icon("Certidão") == "📋"
        assert generator.get_icon("Termo") == "📋"

    def test_default_icon(self):
        generator = IndexGenerator()
        assert generator.get_icon("Outro") == "📎"
