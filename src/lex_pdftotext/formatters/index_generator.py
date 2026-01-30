"""Index generator for procedural pieces with cross-references."""

import re
from dataclasses import dataclass

from ..processors.metadata_parser import DocumentMetadata


@dataclass
class DocumentPiece:
    """Represents a procedural piece in the document."""

    doc_id: str
    doc_type: str
    line: int
    position: int
    date: str | None = None
    signatory: str | None = None
    anchor: str = ""

    def __post_init__(self):
        """Initialize computed fields after dataclass creation."""
        if not self.anchor:
            self.anchor = f"doc-{self.doc_id}"


class IndexGenerator:
    """Generate navigable index for procedural pieces.

    Creates markdown index with:
    - Table of documents with anchor links
    - Document headers with anchors
    - Cross-reference links between documents
    """

    # Document type icons
    ICONS = {
        "Petição Inicial": "📄",
        "Petição": "📄",
        "Petição Intermediária": "📄",
        "Decisão": "⚖️",
        "Sentença": "⚖️",
        "Despacho": "⚖️",
        "Certidão": "📋",
        "Termo": "📋",
        "Anexo": "📎",
        "Documento": "📎",
        "Intimação": "🔔",
        "Citação": "🔔",
        "Guia": "💰",
        "Custas": "💰",
    }

    # Patterns for document type detection
    TYPE_PATTERNS = [
        (r"peti[çc][ãa]o\s+inicial", "Petição Inicial"),
        (r"peti[çc][ãa]o", "Petição"),
        (r"senten[çc]a", "Sentença"),
        (r"decis[ãa]o", "Decisão"),
        (r"despacho", "Despacho"),
        (r"certid[ãa]o", "Certidão"),
        (r"termo", "Termo"),
        (r"intima[çc][ãa]o", "Intimação"),
        (r"cita[çc][ãa]o", "Citação"),
        (r"guia", "Guia"),
    ]

    def generate_anchor(self, doc_id: str) -> str:
        """Generate anchor ID for a document."""
        return f"doc-{doc_id}"

    def get_icon(self, doc_type: str) -> str:
        """Get icon for document type."""
        # Check exact match first
        if doc_type in self.ICONS:
            return self.ICONS[doc_type]

        # Check partial match
        doc_type_lower = doc_type.lower()
        for key, icon in self.ICONS.items():
            if key.lower() in doc_type_lower:
                return icon

        return "📎"  # Default icon

    def detect_type(self, context: str) -> str:
        """Detect document type from surrounding context."""
        context_lower = context.lower()

        for pattern, doc_type in self.TYPE_PATTERNS:
            if re.search(pattern, context_lower):
                return doc_type

        return "Documento"

    def generate_cross_reference(self, doc_id: str) -> str:
        """Generate markdown link to document."""
        anchor = self.generate_anchor(doc_id)
        return f"[#{doc_id}](#{anchor})"

    def generate_document_header(
        self,
        doc_id: str,
        doc_type: str,
        date: str | None = None,
        signatory: str | None = None,
    ) -> str:
        """Generate markdown header with anchor for a document piece.

        Returns:
            Markdown header with anchor, icon, type, and metadata
        """
        icon = self.get_icon(doc_type)
        anchor = self.generate_anchor(doc_id)

        header = f'### <a id="{anchor}"></a>{icon} {doc_type} (ID: {doc_id})'

        # Add metadata line if available
        meta_parts = []
        if date:
            meta_parts.append(f"**Data:** {date}")
        if signatory:
            meta_parts.append(f"**Assinado por:** {signatory}")

        if meta_parts:
            header += f"\n{' | '.join(meta_parts)}"

        return header

    def generate_index_table(self, metadata: DocumentMetadata) -> str:
        """Generate markdown index table for all document pieces.

        Args:
            metadata: Document metadata with positions

        Returns:
            Markdown table with linked document index
        """
        lines = [
            "## Índice de Peças Processuais",
            "",
            "| ID | Tipo | Linha | Link |",
            "|----|------|-------|------|",
        ]

        for pos in metadata.document_positions:
            doc_id = pos["id"]
            context = pos.get("context_before", "") + " " + pos.get("context_after", "")
            doc_type = self.detect_type(context)
            line_num = pos.get("line", "?")
            anchor = self.generate_anchor(doc_id)
            icon = self.get_icon(doc_type)

            row = f"| {icon} {doc_id} | {doc_type} | {line_num} | [Ver](#{anchor}) |"
            lines.append(row)

        return "\n".join(lines)

    def generate_full_index(
        self,
        metadata: DocumentMetadata,
        include_sections: bool = True,
    ) -> str:
        """Generate complete index with documents and sections.

        Args:
            metadata: Document metadata
            include_sections: Whether to include section links

        Returns:
            Complete markdown index
        """
        parts = [self.generate_index_table(metadata)]

        if include_sections and metadata.section_anchors:
            parts.append("")
            parts.append("### Seções")
            parts.append("")
            for section, anchor in metadata.section_anchors.items():
                parts.append(f"- [{section}](#{anchor})")

        return "\n".join(parts)
