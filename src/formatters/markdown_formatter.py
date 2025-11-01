"""Markdown formatter for legal document text."""

from typing import Optional
from ..processors.metadata_parser import DocumentMetadata, MetadataParser


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

        Args:
            text: Processed document text
            metadata: Document metadata
            chunk_size: Approximate size of each chunk (characters)

        Returns:
            list[dict]: List of chunks with metadata
                Each dict contains:
                - 'text': The chunk text
                - 'metadata': Associated metadata
                - 'chunk_index': Sequential index
        """
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

        # Split into chunks (simple paragraph-based splitting for now)
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'metadata': {**base_metadata, 'chunk_index': chunk_index},
                        'chunk_index': chunk_index
                    })
                    chunk_index += 1
                current_chunk = para + "\n\n"

        # Add last chunk
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
        Save formatted content to file.

        Args:
            content: Markdown content
            output_path: Path to save file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
