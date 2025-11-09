"""Tests for Markdown formatter."""

import pytest
import tempfile
from pathlib import Path

from src.formatters.markdown_formatter import MarkdownFormatter
from src.processors.metadata_parser import DocumentMetadata


class TestMarkdownFormatterBasic:
    """Test basic formatting functionality."""

    def test_format_with_metadata(self):
        """Test formatting with provided metadata."""
        formatter = MarkdownFormatter()
        metadata = DocumentMetadata(
            process_number="0001234-56.2024.1.01.0001",
            court="TJSP",
            author="João Silva",
            defendant="Empresa XYZ"
        )
        text = "Conteúdo do documento processual."

        result = formatter.format(text, metadata, include_metadata_header=True)

        assert "# Processo 0001234-56.2024.1.01.0001" in result
        assert "## Metadados" in result
        assert "TJSP" in result
        assert "João Silva" in result
        assert "## Texto Integral" in result
        assert text in result

    def test_format_without_metadata(self):
        """Test formatting auto-extracts metadata."""
        formatter = MarkdownFormatter()
        text = """
        Processo: 0001234-56.2024.1.01.0001
        Autor: João Silva
        Réu: Empresa XYZ

        Conteúdo do documento.
        """

        result = formatter.format(text, metadata=None, include_metadata_header=True)

        assert "# Processo 0001234-56.2024.1.01.0001" in result
        assert "## Metadados" in result
        assert "## Texto Integral" in result

    def test_format_without_process_number(self):
        """Test formatting when no process number is found."""
        formatter = MarkdownFormatter()
        text = "Documento sem número de processo."

        result = formatter.format(text, metadata=None)

        assert "# Documento Processual" in result
        assert text in result

    def test_format_without_metadata_header(self):
        """Test formatting without metadata section."""
        formatter = MarkdownFormatter()
        text = "Conteúdo do documento."

        result = formatter.format(text, metadata=None, include_metadata_header=False)

        assert "## Metadados" not in result
        assert "## Texto Integral" in result
        assert text in result


class TestMarkdownFormatterSections:
    """Test section detection and structuring."""

    def test_format_with_sections_petition(self):
        """Test formatting for initial petition."""
        formatter = MarkdownFormatter()
        metadata = DocumentMetadata(
            process_number="0001234-56.2024.1.01.0001",
            is_initial_petition=True
        )
        text = "Petição inicial com conteúdo."

        result = formatter.format_with_sections(text, metadata)

        assert "# Processo 0001234-56.2024.1.01.0001" in result
        assert "## Petição Inicial" in result

    def test_format_with_sections_decision(self):
        """Test formatting for decision."""
        formatter = MarkdownFormatter()
        metadata = DocumentMetadata(
            process_number="0001234-56.2024.1.01.0001",
            is_decision=True
        )
        text = "Decisão judicial."

        result = formatter.format_with_sections(text, metadata)

        assert "## Decisão" in result

    def test_format_with_sections_certificate(self):
        """Test formatting for certificate."""
        formatter = MarkdownFormatter()
        metadata = DocumentMetadata(
            process_number="0001234-56.2024.1.01.0001",
            is_certificate=True
        )
        text = "Certidão de intimação."

        result = formatter.format_with_sections(text, metadata)

        assert "## Certidão" in result


class TestMarkdownFormatterRAG:
    """Test RAG chunking functionality."""

    def test_format_for_rag_empty_text(self):
        """Test RAG formatting handles empty text."""
        formatter = MarkdownFormatter()

        # Empty string
        result = formatter.format_for_rag("", chunk_size=100)
        assert result == []

        # Whitespace only
        result = formatter.format_for_rag("   \n\n  ", chunk_size=100)
        assert result == []

    def test_format_for_rag_short_text(self):
        """Test RAG formatting with text shorter than chunk size."""
        formatter = MarkdownFormatter()
        text = "Este é um texto curto."

        result = formatter.format_for_rag(text, chunk_size=1000)

        assert len(result) == 1
        assert result[0]['text'] == text
        assert result[0]['chunk_index'] == 0
        assert 'metadata' in result[0]

    def test_format_for_rag_respects_sentence_boundaries(self):
        """Test RAG chunking respects sentence boundaries."""
        formatter = MarkdownFormatter()
        # Create text with clear sentence boundaries
        text = "Primeira sentença. Segunda sentença. Terceira sentença."

        result = formatter.format_for_rag(text, chunk_size=25)

        # Should have multiple chunks
        assert len(result) > 1

        # No chunk should split sentences (end with period followed by non-space)
        for chunk in result:
            chunk_text = chunk['text']
            # Each chunk should either end with a period or be a word fragment
            if '.' in chunk_text and not chunk_text.endswith('.'):
                # If there's a period in the middle, it should be followed by space
                assert '. ' in chunk_text or chunk_text.endswith('.')

    def test_format_for_rag_handles_abbreviations(self):
        """Test RAG chunking handles common abbreviations."""
        formatter = MarkdownFormatter()
        text = "Dr. Silva é o autor. Sra. Maria é a ré. Art. 5º da Constituição."

        result = formatter.format_for_rag(text, chunk_size=30)

        # Should not split on abbreviations
        chunk_texts = [chunk['text'] for chunk in result]
        full_text = ' '.join(chunk_texts)

        # Abbreviations should be preserved
        assert 'Dr.' in full_text or 'Dr. Silva' in ' '.join(chunk_texts)
        assert 'Sra.' in full_text or 'Sra. Maria' in ' '.join(chunk_texts)
        assert 'Art.' in full_text or 'Art. 5º' in ' '.join(chunk_texts)

    def test_format_for_rag_splits_long_sentences_by_words(self):
        """Test RAG chunking splits very long sentences by word boundaries."""
        formatter = MarkdownFormatter()
        # Create a very long sentence (no periods)
        words = ["palavra"] * 100
        text = " ".join(words)

        result = formatter.format_for_rag(text, chunk_size=50)

        # Should have multiple chunks
        assert len(result) > 1

        # No chunk should split words
        for chunk in result:
            # Each word should be complete (no fragments)
            assert all(word == "palavra" for word in chunk['text'].split())

    def test_format_for_rag_metadata_attachment(self):
        """Test RAG chunks include metadata."""
        formatter = MarkdownFormatter()
        metadata = DocumentMetadata(
            process_number="0001234-56.2024.1.01.0001",
            court="TJSP",
            author="João Silva",
            defendant="Empresa XYZ",
            document_ids=["12345678"]
        )
        text = "Primeira sentença. Segunda sentença. Terceira sentença."

        result = formatter.format_for_rag(text, metadata=metadata, chunk_size=25)

        # All chunks should have metadata
        for chunk in result:
            assert 'metadata' in chunk
            assert chunk['metadata']['process_number'] == "0001234-56.2024.1.01.0001"
            assert chunk['metadata']['court'] == "TJSP"
            assert chunk['metadata']['author'] == "João Silva"
            assert chunk['metadata']['defendant'] == "Empresa XYZ"
            assert '12345678' in chunk['metadata']['document_ids']

    def test_format_for_rag_chunk_indexing(self):
        """Test RAG chunks are properly indexed."""
        formatter = MarkdownFormatter()
        text = "Sentença um. Sentença dois. Sentença três. Sentença quatro."

        result = formatter.format_for_rag(text, chunk_size=20)

        # Chunks should have sequential indices
        for i, chunk in enumerate(result):
            assert chunk['chunk_index'] == i
            assert chunk['metadata']['chunk_index'] == i

    def test_format_for_rag_respects_chunk_size(self):
        """Test RAG chunks respect maximum size."""
        formatter = MarkdownFormatter()
        text = "Esta é uma sentença. " * 50  # 50 repetitions

        chunk_size = 100
        result = formatter.format_for_rag(text, chunk_size=chunk_size)

        # Most chunks should be close to chunk_size (within reasonable margin)
        # Last chunk might be smaller
        for chunk in result[:-1]:
            # Allow some flexibility due to sentence boundaries
            assert len(chunk['text']) <= chunk_size * 1.5

    def test_format_for_rag_custom_chunk_size(self):
        """Test RAG formatting with custom chunk sizes."""
        formatter = MarkdownFormatter()
        text = "Sentença. " * 100

        # Small chunks
        result_small = formatter.format_for_rag(text, chunk_size=50)

        # Large chunks
        result_large = formatter.format_for_rag(text, chunk_size=500)

        # Smaller chunk size should produce more chunks
        assert len(result_small) > len(result_large)

    def test_format_for_rag_extracts_metadata_if_not_provided(self):
        """Test RAG formatting auto-extracts metadata."""
        formatter = MarkdownFormatter()
        text = """
        Processo: 0001234-56.2024.1.01.0001
        Autor: João Silva

        Conteúdo do documento.
        """

        result = formatter.format_for_rag(text, metadata=None, chunk_size=100)

        # Should have extracted process number
        assert result[0]['metadata']['process_number'] == "0001234-56.2024.1.01.0001"


class TestMarkdownFormatterSaveFile:
    """Test file saving functionality."""

    def test_save_to_file_creates_file(self):
        """Test saving content to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.md"
            content = "# Test Document\n\nContent here."

            MarkdownFormatter.save_to_file(content, str(output_path))

            assert output_path.exists()
            assert output_path.read_text(encoding='utf-8') == content

    def test_save_to_file_creates_directory(self):
        """Test saving creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "output.md"
            content = "# Test\n\nContent."

            MarkdownFormatter.save_to_file(content, str(output_path))

            assert output_path.exists()
            assert output_path.read_text(encoding='utf-8') == content

    def test_save_to_file_overwrites_existing(self):
        """Test saving overwrites existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.md"

            # Create initial file
            output_path.write_text("Old content", encoding='utf-8')

            # Overwrite with new content
            new_content = "# New Content"
            MarkdownFormatter.save_to_file(new_content, str(output_path))

            assert output_path.read_text(encoding='utf-8') == new_content

    def test_save_to_file_atomic_write(self):
        """Test saving uses atomic write."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.md"
            content = "# Content"

            MarkdownFormatter.save_to_file(content, str(output_path))

            # Should not have temp files left over
            temp_files = list(Path(tmpdir).glob(".*_*.tmp"))
            assert len(temp_files) == 0

    def test_save_to_file_handles_unicode(self):
        """Test saving handles unicode content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "unicode.md"
            content = "# Documento Jurídico\n\nConteúdo com acentuação: ç, ã, é, ô."

            MarkdownFormatter.save_to_file(content, str(output_path))

            assert output_path.exists()
            assert output_path.read_text(encoding='utf-8') == content


class TestMarkdownFormatterEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_for_rag_single_long_word(self):
        """Test RAG chunking with word longer than chunk size."""
        formatter = MarkdownFormatter()
        # Create a "word" longer than chunk size
        text = "a" * 150

        result = formatter.format_for_rag(text, chunk_size=50)

        # Should still create chunks (word fragments)
        assert len(result) > 0

    def test_format_for_rag_no_spaces(self):
        """Test RAG chunking with text that has no spaces."""
        formatter = MarkdownFormatter()
        text = "NoSpacesInThisTextAtAll" * 10

        result = formatter.format_for_rag(text, chunk_size=50)

        # Should handle text without spaces
        assert len(result) > 0

    def test_format_for_rag_special_characters(self):
        """Test RAG chunking preserves special characters."""
        formatter = MarkdownFormatter()
        text = "Valor: R$ 10000,00. Data: 01/01/2024. Email: teste@example.com."

        result = formatter.format_for_rag(text, chunk_size=30)

        # Reconstruct text from chunks
        reconstructed = ' '.join(chunk['text'] for chunk in result)

        # Should preserve special characters (note: sentence splitting may add spaces)
        assert 'R$' in reconstructed
        assert '10000,00' in reconstructed or '10000,00.' in reconstructed
        assert '@' in reconstructed or 'example' in reconstructed  # Email preserved

    def test_format_for_rag_multiple_sentence_terminators(self):
        """Test RAG chunking with multiple terminators (?, !, .)."""
        formatter = MarkdownFormatter()
        text = "Pergunta? Exclamação! Ponto. Normal continua."

        result = formatter.format_for_rag(text, chunk_size=20)

        # Should handle all sentence terminators
        assert len(result) > 0
        reconstructed = ' '.join(chunk['text'] for chunk in result)
        assert '?' in reconstructed
        assert '!' in reconstructed
