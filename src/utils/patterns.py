"""Regex patterns for extracting metadata from Brazilian legal documents (PJe format)."""

import re
from re import Pattern


class RegexPatterns:
    """Collection of regex patterns for PJe document parsing."""

    # Document ID patterns
    DOC_ID: Pattern = re.compile(r"Num\.?\s*(\d{8})", re.IGNORECASE)
    PROCESS_NUMBER: Pattern = re.compile(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})")

    # Digital signature patterns
    SIGNATURE_DATE: Pattern = re.compile(
        r"assinado\s+eletronicamente\s+em\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE
    )
    SIGNATURE_DATETIME: Pattern = re.compile(
        r"assinado\s+eletronicamente\s+em\s+(\d{2}/\d{2}/\d{4}\s+(?:às\s+)?"
        r"\d{2}:\d{2}(?::\d{2})?)",
        re.IGNORECASE,
    )

    # Lawyer/Signatory patterns
    LAWYER_OAB: Pattern = re.compile(
        r"([A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑ][a-zçáàâãéèêíïóôõöúüñ]+(?:\s+(?:de|da|do|dos|das|e|[A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑ][a-zçáàâãéèêíïóôõöúüñ]+))*)"
        r"\s*[-–—]\s*OAB(?:/|\s+)([A-Z]{2})\s*(\d+\.?\d*)",
        re.MULTILINE,
    )

    # Judge/Authority patterns
    JUDGE_NAME: Pattern = re.compile(
        r"([A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑ][a-zçáàâãéèêíïóôõöúüñ\s]+?)\s*[-–—]\s*"
        r"(?:Juiz|Juíza|Desembargador|Desembargadora)",
        re.MULTILINE,
    )

    # Party identification
    AUTHOR_PATTERN: Pattern = re.compile(
        r"(?:Autor|Autora|Requerente):\s*([A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑ][^\n]+)", re.IGNORECASE
    )
    DEFENDANT_PATTERN: Pattern = re.compile(
        r"(?:Réu|Ré|Requerido|Requerida):\s*([A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑ][^\n]+)", re.IGNORECASE
    )

    # Case value
    CASE_VALUE: Pattern = re.compile(r"Valor\s+da\s+causa:\s*R\$\s*([\d.,]+)", re.IGNORECASE)

    # Court/Vara identification
    COURT_NAME: Pattern = re.compile(r"(\d+ª\s+Vara\s+[^/\n]+)", re.IGNORECASE)

    # Document type detection
    INITIAL_PETITION: Pattern = re.compile(
        r"PETIÇÃO\s+INICIAL|EXCELENTÍSSIMO\s+SENHOR", re.IGNORECASE
    )
    DECISION: Pattern = re.compile(r"DECISÃO|DESPACHO|SENTENÇA", re.IGNORECASE)
    CERTIFICATE: Pattern = re.compile(r"CERTID[ÃA]O|CERTIFICO", re.IGNORECASE)

    # Section headers (common in PJe documents)
    SECTION_HEADER: Pattern = re.compile(
        r"^([IVX]+|[A-Z])\s*[-–—.]\s*([A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑ\s]+)$", re.MULTILINE
    )

    # Remove patterns (noise)
    PAGE_NUMBER: Pattern = re.compile(r"Página\s+\d+\s+de\s+\d+", re.IGNORECASE)
    SIGNATURE_URL: Pattern = re.compile(r"https?://[^\s]+", re.IGNORECASE)
    VERIFICATION_CODE: Pattern = re.compile(
        r"(?:Código\s+de\s+)?Verificação:\s*[\w\-]+", re.IGNORECASE
    )

    # PJe header/footer patterns (repetitive information)
    PJE_HEADER: Pattern = re.compile(
        r"(?:Tribunal\s+de\s+Justiça|Poder\s+Judiciário)\s+do\s+Estado\s+do\s+Espírito\s+Santo.*?"
        r"(?:PJe\s*-\s*Processo\s+Judicial\s+Eletrônico|CEP:\s*[\d\-]+)",
        re.IGNORECASE | re.DOTALL,
    )

    # Court address/contact (repetitive)
    COURT_ADDRESS: Pattern = re.compile(
        r"(?:Juízo\s+de\s+)?[A-Z][a-zà-ü\s]+-\s*Comarca.*?"
        r"(?:CEP:\s*[\d\-]+|Telefone:\s*\(\d+\)\s*\d+)",
        re.IGNORECASE | re.DOTALL,
    )

    # Document signature block (repetitive metadata at bottom of pages)
    DOC_SIGNATURE_BLOCK: Pattern = re.compile(
        r"Num\.\s*\d+\s*-\s*Pág\.\s*\d+\s*"
        r"Assinado\s+eletronicamente\s+por:.*?"
        r"(?:https?://[^\s]+|Número\s+do\s+documento:.*?)$",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )

    # Document ID with signature (simplified pattern for footer blocks)
    FOOTER_SIGNATURE: Pattern = re.compile(
        r"Assinado\s+eletronicamente\s+por:.*?(?:\n|$)", re.IGNORECASE
    )

    # Number of document footer
    DOC_NUMBER_FOOTER: Pattern = re.compile(r"Número\s+do\s+documento:\s*\d+", re.IGNORECASE)

    # Repetitive process header (appears on every page)
    PROCESS_HEADER_REPEAT: Pattern = re.compile(
        r"Processo\s+nº\s+\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\s*"
        r"Procedimento\s+[\w\s]+\(\d+\)\s*"
        r"Requerente:.*?"
        r"Requerido:.*?(?:\n|$)",
        re.IGNORECASE | re.DOTALL,
    )

    # Phone/Contact repetition
    PHONE_CONTACT: Pattern = re.compile(r"Telefone:\s*\(\d+\)\s*\d+", re.IGNORECASE)

    # Document metadata blocks (repetitive structured info)
    DOC_METADATA_BLOCK: Pattern = re.compile(
        r"Tipo\s+de\s+documento:.*?"
        r"Descrição\s+do\s+documento:.*?"
        r"Id:.*?"
        r"Data\s+da\s+assinatura:.*?(?:\n|$)",
        re.IGNORECASE | re.DOTALL,
    )

    # Table headers (Id, Expediente, etc.)
    TABLE_HEADER: Pattern = re.compile(
        r"^(?:Id|Expediente|ID\s+Documento|Vinculado|Nome|Prazo|Legal|Data\s+do|Data\s+da|"
        r"Ciência|Processual)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    # Standalone CEP
    CEP_STANDALONE: Pattern = re.compile(r",?\s*(?:CEP:\s*)?[\d\-]+\s*-\s*ES", re.IGNORECASE)

    # Uppercase detection (for normalization)
    ALL_CAPS_LINE: Pattern = re.compile(r'^[A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑ\s\d.,;:!?()\[\]{}/"\'–—-]+$')

    # Preserve acronyms (don't normalize these)
    LEGAL_ACRONYMS: Pattern = re.compile(
        r"\b(?:OAB|CPF|CNPJ|RG|STF|STJ|TST|TSE|TRT|TRF|CNJ|CPC|CF|CC|"
        r"CDC|CLT|CTN|LINDB|MP|PGR|AGU|DPU|PJe|GTT|PICC|CID|UTI|"
        r"SAMP|ES|SP|RJ|MG|DF|BA|PR|SC|RS|GO|MT|MS|PA|AM|RO|AC|"
        r"AP|RR|TO|MA|PI|CE|RN|PB|PE|AL|SE)\b"
    )

    @staticmethod
    def extract_document_ids(text: str) -> list[str]:
        """Extract all document IDs from text."""
        return RegexPatterns.DOC_ID.findall(text)

    @staticmethod
    def extract_process_number(text: str) -> str | None:
        """Extract process number (CNJ format)."""
        match = RegexPatterns.PROCESS_NUMBER.search(text)
        return match.group(1) if match else None

    @staticmethod
    def extract_signatures(text: str) -> list[dict[str, str]]:
        """Extract signature dates and times."""
        signatures = []
        for match in RegexPatterns.SIGNATURE_DATETIME.finditer(text):
            signatures.append({"datetime": match.group(1)})
        return signatures

    @staticmethod
    def extract_lawyers(text: str) -> list[dict[str, str]]:
        """Extract lawyer names and OAB numbers."""
        lawyers = []
        for match in RegexPatterns.LAWYER_OAB.finditer(text):
            lawyers.append(
                {"name": match.group(1).strip(), "state": match.group(2), "oab": match.group(3)}
            )
        return lawyers

    @staticmethod
    def clean_noise(text: str) -> str:
        """Remove page numbers, URLs, verification codes, and repetitive headers/footers."""
        # Remove page numbers
        text = RegexPatterns.PAGE_NUMBER.sub("", text)

        # Remove all URLs (including PJe signature links)
        text = RegexPatterns.SIGNATURE_URL.sub("", text)

        # Remove verification codes
        text = RegexPatterns.VERIFICATION_CODE.sub("", text)

        # Remove repetitive PJe headers
        text = RegexPatterns.PJE_HEADER.sub("", text)

        # Remove court address/contact info
        text = RegexPatterns.COURT_ADDRESS.sub("", text)

        # Remove document signature footers
        text = RegexPatterns.FOOTER_SIGNATURE.sub("", text)

        # Remove document number footers
        text = RegexPatterns.DOC_NUMBER_FOOTER.sub("", text)

        # Remove repetitive process headers
        text = RegexPatterns.PROCESS_HEADER_REPEAT.sub("", text)

        # Remove phone contacts
        text = RegexPatterns.PHONE_CONTACT.sub("", text)

        # Remove document metadata blocks
        text = RegexPatterns.DOC_METADATA_BLOCK.sub("", text)

        # Remove table headers
        text = RegexPatterns.TABLE_HEADER.sub("", text)

        # Remove standalone CEP
        text = RegexPatterns.CEP_STANDALONE.sub("", text)

        return text

    @staticmethod
    def is_all_caps(line: str) -> bool:
        """Check if a line is all uppercase (excluding numbers/symbols)."""
        # Remove numbers, spaces, and punctuation
        letters_only = re.sub(r"[^A-ZÇÁÀÂÃÉÈÊÍÏÓÔÕÖÚÜÑa-zçáàâãéèêíïóôõöúüñ]", "", line)
        if not letters_only:
            return False
        return letters_only.isupper()
