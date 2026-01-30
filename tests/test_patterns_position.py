"""Tests for position-aware document ID extraction."""

from src.lex_pdftotext.utils.patterns import RegexPatterns


class TestDocumentIDPositions:
    """Test extraction of document IDs with position information."""

    def test_extract_single_id_with_position(self):
        """Should extract document ID with line number."""
        text = "Primeira linha\nSegunda linha\nNum. 12345678 - documento"
        result = RegexPatterns.extract_document_ids_with_positions(text)

        assert len(result) == 1
        assert result[0]["id"] == "12345678"
        assert result[0]["line"] == 3
        assert result[0]["position"] == text.find("12345678")

    def test_extract_multiple_ids_with_positions(self):
        """Should extract multiple document IDs with their positions."""
        text = """Num. 11111111 - primeiro documento

Continuação do texto...

Conforme Num. 22222222, temos que considerar.

E também o Num. 33333333."""
        result = RegexPatterns.extract_document_ids_with_positions(text)

        assert len(result) == 3
        assert result[0]["id"] == "11111111"
        assert result[0]["line"] == 1
        assert result[1]["id"] == "22222222"
        assert result[1]["line"] == 5
        assert result[2]["id"] == "33333333"
        assert result[2]["line"] == 7

    def test_extract_id_with_context(self):
        """Should extract surrounding context for each ID."""
        text = "Conforme documento Num. 12345678 anexado aos autos"
        result = RegexPatterns.extract_document_ids_with_positions(text)

        assert len(result) == 1
        assert "documento" in result[0]["context_before"]
        assert "anexado" in result[0]["context_after"]

    def test_empty_text_returns_empty_list(self):
        """Should return empty list for text without IDs."""
        result = RegexPatterns.extract_document_ids_with_positions("")
        assert result == []

    def test_backwards_compatible_extract(self):
        """Original extract_document_ids should still work."""
        text = "Num. 12345678 e Num. 87654321"
        result = RegexPatterns.extract_document_ids(text)

        assert result == ["12345678", "87654321"]
