"""Metadata extraction from legal document text."""

from dataclasses import dataclass, field

from ..utils.cache import get_performance_monitor
from ..utils.patterns import RegexPatterns

# Initialize performance monitor
performance = get_performance_monitor()


@dataclass
class DocumentMetadata:
    """Structured metadata extracted from a legal document."""

    # Process information
    process_number: str | None = None
    document_ids: list[str] = field(default_factory=list)

    # Parties
    author: str | None = None
    defendant: str | None = None

    # Court information
    court: str | None = None
    case_value: str | None = None

    # Signatures
    lawyers: list[dict[str, str]] = field(default_factory=list)
    judges: list[str] = field(default_factory=list)
    signature_dates: list[str] = field(default_factory=list)

    # Document type detection
    is_initial_petition: bool = False
    is_decision: bool = False
    is_certificate: bool = False

    # Section headers found
    sections: list[str] = field(default_factory=list)


class MetadataParser:
    """
    Extract structured metadata from legal document text.

    Uses regex patterns to identify:
    - Process numbers
    - Document IDs
    - Parties (author, defendant)
    - Court information
    - Lawyers and their OAB numbers
    - Judges
    - Signature dates
    - Document type
    """

    def __init__(self):
        """Initialize metadata parser."""
        self.patterns = RegexPatterns()

    @performance.track("metadata_extraction")
    def parse(self, text: str) -> DocumentMetadata:
        """
        Parse text and extract all metadata.

        Args:
            text: Legal document text

        Returns:
            DocumentMetadata: Structured metadata
        """
        metadata = DocumentMetadata()

        # Extract process number
        metadata.process_number = self._extract_process_number(text)

        # Extract document IDs
        metadata.document_ids = self._extract_document_ids(text)

        # Extract parties
        metadata.author = self._extract_author(text)
        metadata.defendant = self._extract_defendant(text)

        # Extract court info
        metadata.court = self._extract_court(text)
        metadata.case_value = self._extract_case_value(text)

        # Extract people
        metadata.lawyers = self._extract_lawyers(text)
        metadata.judges = self._extract_judges(text)
        metadata.signature_dates = self._extract_signature_dates(text)

        # Detect document type
        metadata.is_initial_petition = self._is_initial_petition(text)
        metadata.is_decision = self._is_decision(text)
        metadata.is_certificate = self._is_certificate(text)

        # Extract sections
        metadata.sections = self._extract_sections(text)

        return metadata

    def _extract_process_number(self, text: str) -> str | None:
        """Extract process number in CNJ format."""
        return RegexPatterns.extract_process_number(text)

    def _extract_document_ids(self, text: str) -> list[str]:
        """Extract all document IDs."""
        return RegexPatterns.extract_document_ids(text)

    def _extract_author(self, text: str) -> str | None:
        """Extract author/plaintiff name."""
        match = RegexPatterns.AUTHOR_PATTERN.search(text)
        return match.group(1).strip() if match else None

    def _extract_defendant(self, text: str) -> str | None:
        """Extract defendant name."""
        match = RegexPatterns.DEFENDANT_PATTERN.search(text)
        return match.group(1).strip() if match else None

    def _extract_court(self, text: str) -> str | None:
        """Extract court/vara name."""
        match = RegexPatterns.COURT_NAME.search(text)
        return match.group(1).strip() if match else None

    def _extract_case_value(self, text: str) -> str | None:
        """Extract case value."""
        match = RegexPatterns.CASE_VALUE.search(text)
        return match.group(1).strip() if match else None

    def _extract_lawyers(self, text: str) -> list[dict[str, str]]:
        """Extract lawyer names and OAB numbers."""
        return RegexPatterns.extract_lawyers(text)

    def _extract_judges(self, text: str) -> list[str]:
        """Extract judge names."""
        judges = []
        for match in RegexPatterns.JUDGE_NAME.finditer(text):
            judges.append(match.group(1).strip())
        return judges

    def _extract_signature_dates(self, text: str) -> list[str]:
        """Extract signature dates."""
        dates = []
        for match in RegexPatterns.SIGNATURE_DATE.finditer(text):
            dates.append(match.group(1))
        return dates

    def _is_initial_petition(self, text: str) -> bool:
        """Check if document is an initial petition."""
        return bool(RegexPatterns.INITIAL_PETITION.search(text))

    def _is_decision(self, text: str) -> bool:
        """Check if document is a decision/ruling."""
        return bool(RegexPatterns.DECISION.search(text))

    def _is_certificate(self, text: str) -> bool:
        """Check if document is a certificate."""
        return bool(RegexPatterns.CERTIFICATE.search(text))

    def _extract_sections(self, text: str) -> list[str]:
        """Extract section headers."""
        sections = []
        for match in RegexPatterns.SECTION_HEADER.finditer(text):
            section_title = match.group(2).strip()
            sections.append(section_title)
        return sections

    def format_metadata_as_markdown(self, metadata: DocumentMetadata) -> str:
        """
        Format metadata as Markdown section.

        Args:
            metadata: Extracted metadata

        Returns:
            str: Markdown formatted metadata
        """
        lines = []

        # Add each section
        lines.extend(self._format_basic_fields(metadata))
        lines.extend(self._format_parties(metadata))
        lines.extend(self._format_people(metadata))
        lines.extend(self._format_dates(metadata))
        lines.extend(self._format_document_types(metadata))

        return "\n".join(lines)

    def _format_basic_fields(self, metadata: DocumentMetadata) -> list[str]:
        """Format basic metadata fields (process, documents, court, value)."""
        lines = []

        if metadata.process_number:
            lines.append(f"**Processo:** {metadata.process_number}")

        if metadata.document_ids:
            ids_str = ", ".join(metadata.document_ids)
            lines.append(f"**IDs dos Documentos:** {ids_str}")

        if metadata.court:
            lines.append(f"**Órgão Julgador:** {metadata.court}")

        if metadata.case_value:
            lines.append(f"**Valor da Causa:** R$ {metadata.case_value}")

        return lines

    def _format_parties(self, metadata: DocumentMetadata) -> list[str]:
        """Format party information (author, defendant)."""
        lines = []

        if metadata.author:
            lines.append(f"**Autor(a):** {metadata.author}")

        if metadata.defendant:
            lines.append(f"**Réu/Ré:** {metadata.defendant}")

        return lines

    def _format_people(self, metadata: DocumentMetadata) -> list[str]:
        """Format people information (lawyers, judges)."""
        lines = []

        if metadata.lawyers:
            lines.append("\n**Advogados:**")
            for lawyer in metadata.lawyers:
                lines.append(f"- {lawyer['name']} – OAB/{lawyer['state']} {lawyer['oab']}")

        if metadata.judges:
            lines.append("\n**Magistrados:**")
            for judge in metadata.judges:
                lines.append(f"- {judge}")

        return lines

    def _format_dates(self, metadata: DocumentMetadata) -> list[str]:
        """Format signature dates."""
        lines = []

        if metadata.signature_dates:
            lines.append(f"\n**Datas de Assinatura:** {', '.join(metadata.signature_dates)}")

        return lines

    def _format_document_types(self, metadata: DocumentMetadata) -> list[str]:
        """Format document type information."""
        doc_types = []

        if metadata.is_initial_petition:
            doc_types.append("Petição Inicial")
        if metadata.is_decision:
            doc_types.append("Decisão/Despacho")
        if metadata.is_certificate:
            doc_types.append("Certidão")

        if doc_types:
            return [f"\n**Tipo de Documento:** {', '.join(doc_types)}"]

        return []
