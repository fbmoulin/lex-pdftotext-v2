"""JSON formatter for legal document text."""

import json
from pathlib import Path
from typing import Any

from ..processors.metadata_parser import DocumentMetadata, MetadataParser
from ..utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class JSONFormatter:
    """
    Format legal document text as structured JSON.

    Exports document metadata and content in a machine-readable JSON format,
    suitable for:
    - API integrations
    - Database storage
    - Data pipelines
    - Machine learning applications
    """

    def __init__(self):
        """Initialize JSON formatter."""
        self.metadata_parser = MetadataParser()

    def format(
        self,
        text: str,
        metadata: DocumentMetadata | None = None,
        include_metadata: bool = True,
        hierarchical: bool = False,
    ) -> dict[str, Any]:
        """
        Format text as structured JSON dictionary.

        Args:
            text: Processed legal document text
            metadata: Pre-extracted metadata (optional, will auto-extract if None)
            include_metadata: Whether to include metadata fields
            hierarchical: If True, structure as nested sections (experimental)

        Returns:
            dict: Structured JSON data
        """
        # Extract metadata if not provided
        if metadata is None:
            metadata = self.metadata_parser.parse(text)

        # Build base structure
        result: dict[str, Any] = {
            "format_version": "1.0",
            "document_type": self._determine_document_type(metadata),
        }

        # Add metadata
        if include_metadata:
            result["metadata"] = self._format_metadata(metadata)

        # Add content
        if hierarchical:
            result["content"] = self._format_hierarchical(text, metadata)
        else:
            result["content"] = {
                "text": text,
                "character_count": len(text),
                "word_count": len(text.split()),
            }

        return result

    def format_to_string(
        self,
        text: str,
        metadata: DocumentMetadata | None = None,
        include_metadata: bool = True,
        hierarchical: bool = False,
        indent: int | None = 2,
    ) -> str:
        """
        Format text as JSON string.

        Args:
            text: Processed document text
            metadata: Document metadata
            include_metadata: Include metadata fields
            hierarchical: Structure as nested sections
            indent: JSON indentation (None for compact)

        Returns:
            str: JSON formatted string
        """
        data = self.format(text, metadata, include_metadata, hierarchical)
        return json.dumps(data, ensure_ascii=False, indent=indent)

    def _format_metadata(self, metadata: DocumentMetadata) -> dict[str, Any]:
        """
        Convert metadata to JSON-serializable dictionary.

        Args:
            metadata: Document metadata

        Returns:
            dict: Metadata as dictionary
        """
        return {
            "process_number": metadata.process_number,
            "document_ids": metadata.document_ids,
            "court": metadata.court,
            "case_value": metadata.case_value,
            "parties": {"author": metadata.author, "defendant": metadata.defendant},
            "lawyers": [
                {"name": lawyer["name"], "oab": lawyer["oab"], "state": lawyer["state"]}
                for lawyer in metadata.lawyers
            ],
            "dates": {"signatures": metadata.signature_dates},
            "classification": {
                "is_initial_petition": metadata.is_initial_petition,
                "is_decision": metadata.is_decision,
                "is_certificate": metadata.is_certificate,
            },
            "sections": metadata.sections,
        }

    def _determine_document_type(self, metadata: DocumentMetadata) -> str:
        """
        Determine primary document type.

        Args:
            metadata: Document metadata

        Returns:
            str: Document type identifier
        """
        if metadata.is_initial_petition:
            return "initial_petition"
        elif metadata.is_decision:
            return "decision"
        elif metadata.is_certificate:
            return "certificate"
        else:
            return "legal_document"

    def _format_hierarchical(self, text: str, metadata: DocumentMetadata) -> dict[str, Any]:
        """
        Format content with hierarchical structure (experimental).

        Attempts to structure the document into logical sections.

        Args:
            text: Document text
            metadata: Document metadata

        Returns:
            dict: Hierarchical content structure
        """
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        result: dict[str, Any] = {
            "text": text,
            "character_count": len(text),
            "word_count": len(text.split()),
            "paragraph_count": len(paragraphs),
            "paragraphs": paragraphs,
        }

        # Add sections if detected
        if metadata.sections:
            result["detected_sections"] = metadata.sections

        return result

    @staticmethod
    def save_to_file(data: dict, output_path: str | Path, indent: int | None = 2) -> None:
        """
        Save JSON data to file.

        Args:
            data: JSON-serializable dictionary
            output_path: Path to save file
            indent: JSON indentation (None for compact)

        Raises:
            OSError: If file write fails
        """
        output_path = Path(output_path) if isinstance(output_path, str) else output_path
        logger.info(f"Saving JSON to: {output_path}")

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)

            logger.info(f"JSON saved successfully: {output_path}")

        except Exception as e:
            logger.error(f"Failed to save JSON {output_path}: {e}", exc_info=True)
            raise
