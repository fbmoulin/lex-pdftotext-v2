"""Markdown formatter for legal document text."""

from typing import Optional
import os
import tempfile
from pathlib import Path
from ..processors.metadata_parser import DocumentMetadata, MetadataParser
from ..utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class MarkdownFormatter:
    """
    Format legal document text as structured Markdown.

    Creates hierarchical structure optimized for:
    - RAG pipelines (semantic chunking)
    - Legal analysis tools
    - Human readability
    """

    def __init__(self):
        """Initialize Markdown formatter."""
        self.metadata_parser = MetadataParser()

    def format(
        self,
        text: str,
        metadata: Optional[DocumentMetadata] = None,
        include_metadata_header: bool = True
    ) -> str:
        """
        Format text as structured Markdown.

        Args:
            text: Processed legal document text
            metadata: Pre-extracted metadata (optional, will auto-extract if None)
            include_metadata_header: Whether to include metadata section at top

        Returns:
            str: Markdown formatted document
        """
        # Extract metadata if not provided
        if metadata is None:
            metadata = self.metadata_parser.parse(text)

        # Build markdown document
        sections = []

        # Title
        if metadata.process_number:
            sections.append(f"# Processo {metadata.process_number}\n")
        else:
            sections.append("# Documento Processual\n")

        # Metadata section
        if include_metadata_header:
            metadata_md = self.metadata_parser.format_metadata_as_markdown(metadata)
            if metadata_md:
                sections.append("## Metadados\n")
                sections.append(metadata_md)
                sections.append("\n---\n")

        # Main content
        sections.append("## Texto Integral\n")
        sections.append(text)

        return "\n".join(sections)

    def format_with_sections(
        self,
        text: str,
        metadata: Optional[DocumentMetadata] = None
    ) -> str:
        """
        Format with automatic section detection and structuring.

        This method attempts to identify and structure the document
        into semantic sections (Petição Inicial, Fundamentação, Pedidos, etc.)

        Args:
            text: Processed legal document text
            metadata: Pre-extracted metadata (optional)

        Returns:
            str: Markdown with hierarchical sections
        """
        # Extract metadata if not provided
        if metadata is None:
            metadata = self.metadata_parser.parse(text)

        # Build markdown document
        sections = []

        # Title
        if metadata.process_number:
            sections.append(f"# Processo {metadata.process_number}\n")
        else:
            sections.append("# Documento Processual\n")

        # Metadata section
        metadata_md = self.metadata_parser.format_metadata_as_markdown(metadata)
        if metadata_md:
            sections.append("## Metadados\n")
            sections.append(metadata_md)
            sections.append("\n---\n")

        # Identify document type and structure accordingly
        if metadata.is_initial_petition:
            sections.append("## Petição Inicial\n")
            structured_text = self._structure_petition(text, metadata)
            sections.append(structured_text)
        elif metadata.is_decision:
            sections.append("## Decisão\n")
            sections.append(text)
        elif metadata.is_certificate:
            sections.append("## Certidão\n")
            sections.append(text)
        else:
            sections.append("## Texto Integral\n")
            sections.append(text)

        return "\n".join(sections)

    def _structure_petition(
        self,
        text: str,
        metadata: DocumentMetadata
    ) -> str:
        """
        Structure an initial petition into subsections.

        Common sections in Brazilian legal petitions:
        - Qualificação das partes
        - Pedido de justiça gratuita
        - Síntese fática
        - Fundamentação jurídica
        - Tutela de urgência
        - Danos morais
        - Pedidos finais

        Args:
            text: Petition text
            metadata: Document metadata

        Returns:
            str: Structured petition text
        """
        # For now, just add detected sections as subsections
        # This can be enhanced with more sophisticated NLP
        if metadata.sections:
            structured = []
            lines = text.split('\n')

            for section in metadata.sections:
                # Find section in text and convert to markdown header
                for i, line in enumerate(lines):
                    if section.upper() in line.upper():
                        lines[i] = f"\n### {section}\n"

            return '\n'.join(lines)

        return text

    def format_for_rag(
        self,
        text: str,
        metadata: Optional[DocumentMetadata] = None,
        chunk_size: int = 1000
    ) -> list[dict[str, str]]:
        """
        Format document optimized for RAG ingestion.

        Splits text into semantic chunks with metadata attached.
        Respects sentence and word boundaries for better semantic coherence.

        Args:
            text: Processed document text
            metadata: Document metadata
            chunk_size: Maximum size of each chunk (characters)

        Returns:
            list[dict]: List of chunks with metadata
                Each dict contains:
                - 'text': The chunk text
                - 'metadata': Associated metadata
                - 'chunk_index': Sequential index
        """
        # Handle empty or very short text
        if not text or not text.strip():
            return []

        # Extract metadata if not provided
        if metadata is None:
            metadata = self.metadata_parser.parse(text)

        # Prepare base metadata
        base_metadata = {
            'process_number': metadata.process_number or '',
            'document_ids': ','.join(metadata.document_ids),
            'court': metadata.court or '',
            'author': metadata.author or '',
            'defendant': metadata.defendant or '',
        }

        # If text is shorter than chunk size, return as single chunk
        if len(text.strip()) <= chunk_size:
            return [{
                'text': text.strip(),
                'metadata': {**base_metadata, 'chunk_index': 0},
                'chunk_index': 0
            }]

        # Split into sentences while preserving terminators
        # Match complete sentences including punctuation
        import re
        # Match sentences: text followed by terminator(s)
        sentence_pattern = r'([^.!?]*[.!?]+)'
        parts = re.findall(sentence_pattern, text)

        # Handle remaining text without terminator
        remaining = re.sub(sentence_pattern, '', text).strip()
        if remaining:
            parts.append(remaining)

        sentences = [s.strip() for s in parts if s.strip()]

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for sentence in sentences:
            # If adding this sentence keeps us under chunk_size, add it
            if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                # Current chunk is full, save it
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'metadata': {**base_metadata, 'chunk_index': chunk_index},
                        'chunk_index': chunk_index
                    })
                    chunk_index += 1

                # If the sentence itself is longer than chunk_size, split by words
                if len(sentence) > chunk_size:
                    words = sentence.split()
                    word_chunk = ""
                    for word in words:
                        if len(word_chunk) + len(word) + 1 <= chunk_size:
                            if word_chunk:
                                word_chunk += " " + word
                            else:
                                word_chunk = word
                        else:
                            # Save word chunk
                            if word_chunk:
                                chunks.append({
                                    'text': word_chunk.strip(),
                                    'metadata': {**base_metadata, 'chunk_index': chunk_index},
                                    'chunk_index': chunk_index
                                })
                                chunk_index += 1
                            word_chunk = word

                    # Start new chunk with remaining words
                    current_chunk = word_chunk
                else:
                    # Start new chunk with this sentence
                    current_chunk = sentence

        # Add final chunk
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'metadata': {**base_metadata, 'chunk_index': chunk_index},
                'chunk_index': chunk_index
            })

        return chunks

    @staticmethod
    def save_to_file(content: str, output_path: str) -> None:
        """
        Save formatted content to file using atomic write.

        Writes to a temporary file first, then renames to final path.
        This prevents file corruption if write fails midway.

        Args:
            content: Markdown content
            output_path: Path to save file

        Raises:
            OSError: If file write or rename fails
        """
        output_path = Path(output_path)
        logger.info(f"Saving content to: {output_path}")

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file in same directory (for atomic rename)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=output_path.parent,
            prefix=f".{output_path.stem}_",
            suffix=".tmp"
        )

        try:
            # Write content to temporary file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk

            # Atomic rename (overwrites if exists)
            os.replace(temp_path, str(output_path))
            logger.info(f"File saved successfully: {output_path} ({len(content)} bytes)")

        except Exception as e:
            # Clean up temp file on failure
            logger.error(f"Failed to save file {output_path}: {e}", exc_info=True)
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass  # Ignore cleanup errors
            raise
