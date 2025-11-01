"""
PDF validation utilities.
"""

from pathlib import Path
from typing import Tuple
import fitz  # PyMuPDF

from .exceptions import (
    PDFCorruptedError,
    PDFEncryptedError,
    PDFTooLargeError,
    PDFEmptyError,
    InvalidPathError
)


class PDFValidator:
    """Validates PDF files before processing."""

    # Configurações padrão
    DEFAULT_MAX_SIZE_MB = 500
    DEFAULT_MAX_PAGES = 10000

    @staticmethod
    def validate_path(pdf_path: Path) -> None:
        """
        Validate that path exists and is a PDF file.

        Args:
            pdf_path: Path to PDF file

        Raises:
            InvalidPathError: If path is invalid
        """
        if not pdf_path.exists():
            raise InvalidPathError(f"Arquivo não encontrado: {pdf_path}")

        if not pdf_path.is_file():
            raise InvalidPathError(f"Caminho não é um arquivo: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            raise InvalidPathError(
                f"Extensão inválida: {pdf_path.suffix}. Esperado: .pdf"
            )

    @staticmethod
    def validate_size(pdf_path: Path, max_size_mb: int = DEFAULT_MAX_SIZE_MB) -> None:
        """
        Validate PDF file size.

        Args:
            pdf_path: Path to PDF file
            max_size_mb: Maximum allowed size in MB

        Raises:
            PDFTooLargeError: If file exceeds maximum size
        """
        size_bytes = pdf_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)

        if size_mb > max_size_mb:
            raise PDFTooLargeError(
                f"Arquivo muito grande: {size_mb:.2f}MB (máximo: {max_size_mb}MB)"
            )

    @staticmethod
    def validate_integrity(pdf_path: Path, max_pages: int = DEFAULT_MAX_PAGES) -> Tuple[bool, str]:
        """
        Validate PDF integrity and readability.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum allowed pages

        Returns:
            Tuple of (is_valid, message)

        Raises:
            PDFCorruptedError: If PDF is corrupted
            PDFEncryptedError: If PDF is encrypted
            PDFEmptyError: If PDF has no pages
        """
        try:
            doc = fitz.open(pdf_path)

            # Check if encrypted
            if doc.is_encrypted:
                doc.close()
                raise PDFEncryptedError(
                    f"PDF está criptografado/protegido por senha: {pdf_path.name}"
                )

            # Check page count
            page_count = len(doc)

            if page_count == 0:
                doc.close()
                raise PDFEmptyError(
                    f"PDF vazio (0 páginas): {pdf_path.name}"
                )

            if page_count > max_pages:
                doc.close()
                raise PDFTooLargeError(
                    f"PDF tem muitas páginas: {page_count} (máximo: {max_pages})"
                )

            # Try to read first page
            try:
                first_page = doc[0]
                _ = first_page.get_text()
            except Exception as e:
                doc.close()
                raise PDFCorruptedError(
                    f"Erro ao ler primeira página: {e}"
                )

            doc.close()
            return True, "OK"

        except (fitz.FileDataError, fitz.FitzError) as e:
            raise PDFCorruptedError(
                f"Arquivo PDF corrompido: {pdf_path.name} - {str(e)}"
            )

    @classmethod
    def validate_all(
        cls,
        pdf_path: Path,
        max_size_mb: int = DEFAULT_MAX_SIZE_MB,
        max_pages: int = DEFAULT_MAX_PAGES
    ) -> Tuple[bool, str]:
        """
        Run all validations on PDF file.

        Args:
            pdf_path: Path to PDF file
            max_size_mb: Maximum allowed size in MB
            max_pages: Maximum allowed pages

        Returns:
            Tuple of (is_valid, message)

        Raises:
            PDFExtractionError subclass if validation fails
        """
        # Validate path
        cls.validate_path(pdf_path)

        # Validate size
        cls.validate_size(pdf_path, max_size_mb)

        # Validate integrity
        return cls.validate_integrity(pdf_path, max_pages)


def sanitize_output_path(user_input: str, base_dir: Path) -> Path:
    """
    Sanitize output path to prevent path traversal attacks.

    Args:
        user_input: User-provided path
        base_dir: Base directory (trusted)

    Returns:
        Sanitized absolute path

    Raises:
        InvalidPathError: If path traversal detected
    """
    # Resolve to absolute path
    output_path = (base_dir / user_input).resolve()

    # Ensure it's within base directory
    try:
        output_path.relative_to(base_dir.resolve())
    except ValueError:
        raise InvalidPathError(
            f"Caminho inválido: tentativa de acesso fora do diretório permitido"
        )

    return output_path
