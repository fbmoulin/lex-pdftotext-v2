"""Tests for markdown output with index and cross-references."""

import pytest

from src.formatters.markdown_formatter import MarkdownFormatter
from src.processors.metadata_parser import DocumentMetadata


class TestMarkdownWithIndex:
    """Test markdown generation with procedural index."""

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata with positions."""
        return DocumentMetadata(
            process_number="0018456-36.2018.8.08.0012",
            document_ids=["11111111", "22222222"],
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
            ],
            author="João Silva",
            defendant="Empresa XYZ",
            court="2ª Vara Cível",
            sections=["DOS FATOS", "DO DIREITO"],
            section_anchors={"DOS FATOS": "sec-dos-fatos", "DO DIREITO": "sec-do-direito"},
        )

    @pytest.fixture
    def sample_text(self):
        return """Texto da petição inicial...

Num. 11111111 - Petição apresentada

Conteúdo dos fatos...

Num. 22222222 - Decisão proferida

Conteúdo da decisão..."""

    def test_format_with_index_includes_table(self, sample_metadata, sample_text):
        """Should include index table in output."""
        formatter = MarkdownFormatter()
        result = formatter.format_with_index(sample_text, sample_metadata)

        assert "## Índice de Peças Processuais" in result
        assert "11111111" in result
        assert "22222222" in result

    def test_format_with_index_has_anchors(self, sample_metadata, sample_text):
        """Should include anchor links in output."""
        formatter = MarkdownFormatter()
        result = formatter.format_with_index(sample_text, sample_metadata)

        assert "#doc-11111111" in result
        assert "#doc-22222222" in result

    def test_format_with_index_has_document_headers(self, sample_metadata, sample_text):
        """Should include document headers with anchors."""
        formatter = MarkdownFormatter()
        result = formatter.format_with_index(sample_text, sample_metadata)

        assert '<a id="doc-11111111"></a>' in result
        assert '<a id="doc-22222222"></a>' in result

    def test_format_with_index_preserves_metadata(self, sample_metadata, sample_text):
        """Should preserve standard metadata section."""
        formatter = MarkdownFormatter()
        result = formatter.format_with_index(sample_text, sample_metadata)

        assert "**Processo:**" in result
        assert "0018456-36.2018.8.08.0012" in result
        assert "**Autor(a):**" in result
