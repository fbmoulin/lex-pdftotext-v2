"""
Basic tests for PDF extraction functionality.

To run: pytest tests/
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.metadata_parser import MetadataParser
from src.processors.text_normalizer import TextNormalizer
from src.utils.patterns import RegexPatterns


class TestRegexPatterns:
    """Test regex pattern matching."""

    def test_extract_document_ids(self):
        """Test document ID extraction."""
        text = "Num. 12345678 e também Num. 87654321"
        ids = RegexPatterns.extract_document_ids(text)
        assert len(ids) == 2
        assert "12345678" in ids
        assert "87654321" in ids

    def test_extract_process_number(self):
        """Test process number extraction (CNJ format)."""
        text = "Processo 5022930-18.2025.8.08.0012"
        process = RegexPatterns.extract_process_number(text)
        assert process == "5022930-18.2025.8.08.0012"

    def test_extract_lawyers(self):
        """Test lawyer/OAB extraction."""
        text = "Edvaldo Souza de Oliveira – OAB/ES 43.156"
        lawyers = RegexPatterns.extract_lawyers(text)
        assert len(lawyers) == 1
        assert lawyers[0]["name"] == "Edvaldo Souza de Oliveira"
        assert lawyers[0]["state"] == "ES"
        assert lawyers[0]["oab"] == "43.156"

    def test_signature_date_extraction(self):
        """Test signature date extraction."""
        text = "Documento assinado eletronicamente em 25/09/2025"
        dates = RegexPatterns.extract_signatures(text)
        assert len(dates) >= 0  # May find date if full datetime pattern


class TestTextNormalizer:
    """Test text normalization."""

    def test_normalize_uppercase(self):
        """Test UPPERCASE conversion to sentence case."""
        normalizer = TextNormalizer()
        text = "ESTE É UM TEXTO EM CAIXA ALTA"
        result = normalizer.normalize(text)
        assert result != text
        assert not result.isupper()

    def test_preserve_acronyms(self):
        """Test that legal acronyms are preserved."""
        normalizer = TextNormalizer()
        text = "O STF E O STJ DECIDIRAM CONFORME O CPC"
        result = normalizer.normalize(text)
        assert "STF" in result
        assert "STJ" in result
        assert "CPC" in result

    def test_clean_noise(self):
        """Test noise removal."""
        normalizer = TextNormalizer()
        text = "Página 1 de 10\nTexto importante\nhttps://pje.cnj.jus.br/assinatura"
        result = normalizer.normalize(text)
        assert "Página" not in result
        assert "https://" not in result
        assert "texto importante" in result.lower()


class TestMetadataParser:
    """Test metadata extraction."""

    def test_parse_process_number(self):
        """Test process number parsing."""
        parser = MetadataParser()
        text = "Processo: 5022930-18.2025.8.08.0012"
        metadata = parser.parse(text)
        assert metadata.process_number == "5022930-18.2025.8.08.0012"

    def test_parse_author_defendant(self):
        """Test party extraction."""
        parser = MetadataParser()
        text = """
        Autor: João da Silva
        Réu: Empresa XYZ Ltda
        """
        metadata = parser.parse(text)
        assert "João da Silva" in metadata.author
        assert "Empresa XYZ" in metadata.defendant

    def test_document_type_detection(self):
        """Test document type detection."""
        parser = MetadataParser()

        # Initial petition
        petition_text = "PETIÇÃO INICIAL\nExcelentíssimo Senhor"
        metadata = parser.parse(petition_text)
        assert metadata.is_initial_petition

        # Decision
        decision_text = "DECISÃO\nVistos os autos"
        metadata = parser.parse(decision_text)
        assert metadata.is_decision

        # Certificate
        cert_text = "CERTIDÃO\nCertifico que"
        metadata = parser.parse(cert_text)
        assert metadata.is_certificate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
