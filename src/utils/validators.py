"""PDF validation utilities."""

import platform
import re
import shutil
from pathlib import Path

import fitz  # PyMuPDF

from .exceptions import (
    InvalidPathError,
    PDFCorruptedError,
    PDFEmptyError,
    PDFEncryptedError,
    PDFTooLargeError,
)
from .logger import get_logger

logger = get_logger(__name__)


class PDFValidator:
    """Validates PDF files before processing."""

    # Configurações padrão
    DEFAULT_MAX_SIZE_MB = 500
    DEFAULT_MAX_PAGES = 10000

    @staticmethod
    def validate_path(pdf_path: Path) -> None:
        """Validate that path exists and is a PDF file.

        Args:
            pdf_path: Path to PDF file

        Raises:
            InvalidPathError: If path is invalid
        """
        if not pdf_path.exists():
            raise InvalidPathError(f"Arquivo não encontrado: {pdf_path}")

        if not pdf_path.is_file():
            raise InvalidPathError(f"Caminho não é um arquivo: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise InvalidPathError(f"Extensão inválida: {pdf_path.suffix}. Esperado: .pdf")

    @staticmethod
    def validate_size(pdf_path: Path, max_size_mb: int = DEFAULT_MAX_SIZE_MB) -> None:
        """Validate PDF file size.

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
    def validate_integrity(pdf_path: Path, max_pages: int = DEFAULT_MAX_PAGES) -> tuple[bool, str]:
        """Validate PDF integrity and readability.

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
                raise PDFEmptyError(f"PDF vazio (0 páginas): {pdf_path.name}")

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
                raise PDFCorruptedError(f"Erro ao ler primeira página: {e}") from e

            doc.close()
            return True, "OK"

        except fitz.FileDataError as e:
            raise PDFCorruptedError(f"Arquivo PDF corrompido: {pdf_path.name} - {str(e)}") from e

    @classmethod
    def validate_all(
        cls,
        pdf_path: Path,
        max_size_mb: int = DEFAULT_MAX_SIZE_MB,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> tuple[bool, str]:
        """Run all validations on PDF file.

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
    """Sanitize output path to prevent path traversal attacks.

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
    except ValueError as e:
        raise InvalidPathError(
            "Caminho inválido: tentativa de acesso fora do diretório permitido"
        ) from e

    return output_path


def validate_process_number(process_number: str) -> bool:
    """Validate Brazilian process number in CNJ format.

    Format: NNNNNNN-DD.AAAA.J.TT.OOOO
    Example: 5022930-18.2025.8.08.0012

    Args:
        process_number: Process number to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If process number is invalid
    """
    if not process_number:
        raise ValueError("Process number cannot be empty")

    # CNJ format pattern: NNNNNNN-DD.AAAA.J.TT.OOOO
    # NNNNNNN: Sequential number (7 digits)
    # DD: Verification digits (2 digits)
    # AAAA: Year (4 digits)
    # J: Judicial segment (1 digit)
    # TT: Court (2 digits)
    # OOOO: Origin (4 digits)
    pattern = r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$"

    if not re.match(pattern, process_number):
        raise ValueError(
            f"Invalid process number format: {process_number}. "
            f"Expected format: NNNNNNN-DD.AAAA.J.TT.OOOO (e.g., 5022930-18.2025.8.08.0012)"
        )

    logger.debug(f"Process number validated: {process_number}")
    return True


def validate_filename(filename: str, allow_path: bool = False) -> str:
    """Validate and sanitize filename for cross-platform compatibility.

    Checks for:
    - Invalid characters (Windows/Linux)
    - Reserved names (Windows: CON, PRN, AUX, etc.)
    - Length limits (255 chars on most systems)
    - Path components (if allow_path=False)

    Args:
        filename: Filename to validate
        allow_path: Whether to allow path separators

    Returns:
        Sanitized filename

    Raises:
        ValueError: If filename is invalid
    """
    if not filename or filename.strip() == "":
        raise ValueError("Filename cannot be empty")

    filename = filename.strip()

    # Check for path separators if not allowed
    if not allow_path and ("/" in filename or "\\" in filename):
        raise ValueError(f"Filename cannot contain path separators: {filename}")

    # Windows reserved names
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    # Get base name without extension
    name_without_ext = Path(filename).stem.upper()
    if name_without_ext in reserved_names:
        raise ValueError(
            f"Filename uses reserved name: {filename}. "
            f"Reserved names: {', '.join(sorted(reserved_names))}"
        )

    # Invalid characters (Windows is more restrictive)
    if platform.system() == "Windows":
        invalid_chars = r'<>:"|?*'
    else:
        invalid_chars = "\0"  # Linux is very permissive

    for char in invalid_chars:
        if char in filename:
            raise ValueError(f"Filename contains invalid character '{char}': {filename}")

    # Check length (255 is common limit, use 250 to be safe)
    if len(filename) > 250:
        raise ValueError(f"Filename too long ({len(filename)} chars). Maximum: 250 characters")

    # Normalize extension to lowercase for consistency
    path = Path(filename)
    if path.suffix:
        sanitized = str(path.with_suffix(path.suffix.lower()))
        logger.debug(f"Filename validated and normalized: {filename} -> {sanitized}")
        return sanitized

    logger.debug(f"Filename validated: {filename}")
    return filename


def validate_chunk_size(chunk_size: int, min_size: int = 100, max_size: int = 10000) -> bool:
    """Validate chunk size for text chunking.

    Args:
        chunk_size: Chunk size in characters
        min_size: Minimum allowed size (default: 100)
        max_size: Maximum allowed size (default: 10000)

    Returns:
        True if valid

    Raises:
        ValueError: If chunk size is out of bounds
    """
    if not isinstance(chunk_size, int):
        raise ValueError(f"Chunk size must be an integer, got {type(chunk_size).__name__}")

    if chunk_size < min_size:
        raise ValueError(f"Chunk size too small: {chunk_size}. Minimum: {min_size} characters")

    if chunk_size > max_size:
        raise ValueError(f"Chunk size too large: {chunk_size}. Maximum: {max_size} characters")

    logger.debug(f"Chunk size validated: {chunk_size}")
    return True


def check_disk_space(path: Path, required_mb: int = 100) -> tuple[bool, int]:
    """Check if sufficient disk space is available.

    Args:
        path: Path to check (file or directory)
        required_mb: Required space in MB

    Returns:
        Tuple of (has_space, available_mb)

    Raises:
        ValueError: If required space is negative
        OSError: If path cannot be accessed
    """
    if required_mb < 0:
        raise ValueError(f"Required MB cannot be negative: {required_mb}")

    try:
        # Get the directory to check
        if path.is_file():
            check_path = path.parent
        else:
            check_path = path

        # Get disk usage stats
        stat = shutil.disk_usage(check_path)
        available_mb = stat.free / (1024 * 1024)

        has_space = available_mb >= required_mb

        if has_space:
            logger.debug(
                f"Disk space check passed: {available_mb:.1f}MB available, {required_mb}MB required"
            )
        else:
            logger.warning(
                f"Insufficient disk space: {available_mb:.1f}MB available, {required_mb}MB required"
            )

        return has_space, int(available_mb)

    except OSError as e:
        logger.error(f"Failed to check disk space for {path}: {e}")
        raise


def estimate_output_size(pdf_path: Path, multiplier: float = 1.5) -> int:
    """Estimate output file size based on PDF size.

    Text extraction typically produces files 1-2x the PDF size.

    Args:
        pdf_path: Path to PDF file
        multiplier: Size multiplier (default: 1.5x)

    Returns:
        Estimated size in MB
    """
    pdf_size_mb = pdf_path.stat().st_size / (1024 * 1024)
    estimated_mb = int(pdf_size_mb * multiplier)

    logger.debug(
        f"Estimated output size for {pdf_path.name}: "
        f"{pdf_size_mb:.1f}MB PDF -> ~{estimated_mb}MB output"
    )

    return estimated_mb
