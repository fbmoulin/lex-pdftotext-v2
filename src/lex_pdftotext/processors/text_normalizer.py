"""Text normalization for legal documents."""

import re

from ..utils.cache import get_performance_monitor
from ..utils.patterns import RegexPatterns

# Initialize performance monitor
performance = get_performance_monitor()


class TextNormalizer:
    """
    Normalize text from legal PDFs, especially PJe documents.

    Main functions:
    - Convert excessive UPPERCASE to sentence case
    - Preserve legal acronyms (OAB, STF, CPC, etc.)
    - Clean noise (page numbers, URLs, verification codes)
    - Normalize whitespace and line breaks
    """

    def __init__(self, preserve_acronyms: bool = True):
        """
        Initialize text normalizer.

        Args:
            preserve_acronyms: Whether to preserve legal acronyms in uppercase
        """
        self.preserve_acronyms = preserve_acronyms
        self.patterns = RegexPatterns()

    @performance.track("text_normalization")
    def normalize(self, text: str) -> str:
        """
        Apply all normalization steps to text.

        Args:
            text: Raw text extracted from PDF

        Returns:
            str: Normalized text
        """
        # 1. Remove repetitive footers/headers (law firm info, addresses)
        text = self._remove_repetitive_content(text)

        # 2. Remove noise (page numbers, URLs, codes)
        text = self._clean_noise(text)

        # 3. Normalize UPPERCASE lines
        text = self._normalize_uppercase(text)

        # 4. Clean whitespace
        text = self._normalize_whitespace(text)

        # 5. Final aggressive cleanup of blank lines
        text = self._final_cleanup(text)

        return text

    def _remove_repetitive_content(self, text: str, threshold: int = 3) -> str:
        """
        Remove repetitive footers/headers that appear across multiple pages.

        Common examples:
        - Law firm names and addresses
        - Phone numbers, emails, websites
        - CEP (postal codes)
        - Repeated disclaimers

        Args:
            text: Raw text from PDF
            threshold: Minimum number of occurrences to be considered repetitive

        Returns:
            str: Text with repetitive content removed
        """
        lines = text.split("\n")

        # Count line frequencies (ignoring empty lines and very short lines)
        line_counts: dict[str, int] = {}
        for line in lines:
            stripped = line.strip()
            # Only count substantial lines (more than 10 chars)
            if len(stripped) > 10:
                line_counts[stripped] = line_counts.get(stripped, 0) + 1

        # Identify repetitive lines (appear more than threshold times)
        repetitive_lines = {line for line, count in line_counts.items() if count >= threshold}

        # Additional patterns to remove (common footer/header indicators)
        footer_patterns = [
            r"\b\d{5}-?\d{3}\b",  # CEP format (12345-678 or 12345678)
            r"\(\d{2}\)\s*\d{4,5}-?\d{4}",  # Phone numbers (11) 98765-4321
            r"www\.",  # Websites
            r"@\w+\.\w+",  # Email addresses
            r"\b[Aa]v\.|[Rr]ua\s+",  # Street addresses (Av. / Rua)
            r"\b[Ee]scritor[ií]o\s+de\s+[Aa]dvocacia\b",  # "Escritório de Advocacia"
            r"\b[Aa]dvocacia\s+e\s+[Cc]onsultoria\b",  # "Advocacia e Consultoria"
            r"\bOAB/[A-Z]{2}\s+\d+",  # OAB registration
        ]

        # Filter out repetitive lines and footer patterns
        filtered_lines = []
        for line in lines:
            stripped = line.strip()

            # Skip if it's a repetitive line
            if stripped in repetitive_lines:
                continue

            # Skip if matches footer patterns
            is_footer = False
            for pattern in footer_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Double check it's repetitive or very footer-like
                    # Allow it if it appears only once (might be legitimate content)
                    if line_counts.get(stripped, 0) >= 2:
                        is_footer = True
                        break

            if not is_footer:
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _final_cleanup(self, text: str) -> str:
        """
        Final aggressive cleanup to remove excessive blank lines.

        This is needed because PDFs often have blank pages or large whitespace areas.
        """
        # First, collapse all whitespace-only lines to truly empty lines
        text = re.sub(r"^\s+$", "", text, flags=re.MULTILINE)

        # Split into lines
        lines = text.split("\n")

        # Remove sequences of blank lines - keep max 1
        cleaned = []
        blank_count = 0

        for line in lines:
            if line == "":  # Truly empty line
                blank_count += 1
                # Keep max 1 consecutive blank line (for paragraph breaks)
                if blank_count <= 1:
                    cleaned.append(line)
            else:
                blank_count = 0
                cleaned.append(line)

        # Join
        text = "\n".join(cleaned)

        # Final pass: remove any remaining excessive blanks
        # This ensures no more than 2 newlines in a row (one blank line between paragraphs)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _clean_noise(self, text: str) -> str:
        """Remove page numbers, URLs, verification codes, and repetitive content."""
        # Use RegexPatterns to clean basic noise
        text = RegexPatterns.clean_noise(text)

        # Remove repetitive "Num. XXXXX - Pág. X" lines
        text = re.sub(r"Num\.\s*\d+\s*-\s*Pág\.\s*\d+", "", text, flags=re.IGNORECASE)

        # Remove standalone page markers
        text = re.sub(r"---\s*página\s*\{\}\s*---", "", text, flags=re.IGNORECASE)

        return text

    def _normalize_uppercase(self, text: str) -> str:
        """
        Convert excessive UPPERCASE to sentence case.

        Preserves:
        - Legal acronyms (OAB, STF, CPC, etc.)
        - Proper names at start of sentences
        - Roman numerals
        """
        lines = text.split("\n")
        normalized_lines = []

        for line in lines:
            # Skip empty lines
            if not line.strip():
                normalized_lines.append(line)
                continue

            # Check if line is all caps
            if RegexPatterns.is_all_caps(line.strip()):
                normalized_line = self._convert_to_sentence_case(line)
                normalized_lines.append(normalized_line)
            else:
                normalized_lines.append(line)

        return "\n".join(normalized_lines)

    def _convert_to_sentence_case(self, line: str) -> str:
        """
        Convert a line to sentence case while preserving acronyms.

        Args:
            line: Line in uppercase

        Returns:
            str: Line in sentence case
        """
        # Temporarily replace acronyms with placeholders (do this before lowercasing)
        acronym_map: dict[str, str] = {}
        if self.preserve_acronyms:
            # Find all acronyms and replace them with unique placeholders
            def replace_acronym(match):
                acronym = match.group(0)
                placeholder = f"__ACRONYM{len(acronym_map)}__"
                acronym_map[placeholder] = acronym
                return placeholder

            line = RegexPatterns.LEGAL_ACRONYMS.sub(replace_acronym, line)

        # Convert to lowercase then capitalize first letter
        line = line.lower()

        # Capitalize first letter of line
        if line:
            line = line[0].upper() + line[1:]

        # Capitalize after sentence-ending punctuation
        line = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), line)

        # Restore acronyms (placeholders are still in the format we set)
        for placeholder, acronym in acronym_map.items():
            line = line.replace(placeholder.lower(), acronym)

        return line

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace while preserving paragraph structure.

        - Remove trailing whitespace
        - Normalize multiple spaces to single space
        - Preserve paragraph breaks (double newlines)
        - Remove excessive blank lines (more than 2 consecutive)
        - Remove duplicate consecutive lines
        """
        # Remove trailing/leading whitespace from each line
        lines = [line.rstrip() for line in text.split("\n")]

        # Normalize spaces within lines
        lines = [re.sub(r" +", " ", line) for line in lines]

        # Remove consecutive duplicate lines (keep only first occurrence)
        deduped_lines = []
        prev_line = None
        consecutive_empty = 0

        for line in lines:
            # Count consecutive empty lines
            if line.strip() == "":
                consecutive_empty += 1
                # Allow max 1 consecutive empty line (for paragraph breaks)
                if consecutive_empty <= 1:
                    deduped_lines.append(line)
            else:
                consecutive_empty = 0
                # For non-empty lines, skip exact duplicates
                if line != prev_line:
                    deduped_lines.append(line)
                prev_line = line

        # Join back
        text = "\n".join(deduped_lines)

        # Reduce any excessive blank lines to single blank line
        text = re.sub(r"\n\n+", "\n\n", text)

        # Remove leading/trailing whitespace from entire text
        text = text.strip()

        return text

    def remove_page_markers(self, text: str) -> str:
        """
        Remove page marker comments (e.g., '--- PÁGINA 1 ---').

        Args:
            text: Text with page markers

        Returns:
            str: Text without page markers
        """
        return re.sub(r"\n*---\s*PÁGINA\s+\d+\s*---\n*", "\n\n", text, flags=re.IGNORECASE)

    def clean_line_breaks(self, text: str) -> str:
        """
        Fix broken words across line breaks.

        Example: "desenvolvi-\nmento" becomes "desenvolvimento"
        """
        # Fix hyphenated words split across lines
        text = re.sub(r"-\s*\n\s*", "", text)

        return text
