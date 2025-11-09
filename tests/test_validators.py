"""Tests for PDF validation utilities."""

import platform
from unittest.mock import MagicMock, patch

import fitz
import pytest

from src.utils.exceptions import (
    InvalidPathError,
    PDFCorruptedError,
    PDFEmptyError,
    PDFEncryptedError,
    PDFTooLargeError,
)
from src.utils.validators import (
    PDFValidator,
    check_disk_space,
    estimate_output_size,
    sanitize_output_path,
    validate_chunk_size,
    validate_filename,
    validate_process_number,
)


class TestPDFValidatorValidatePath:
    """Test PDFValidator.validate_path() method."""

    def test_validate_path_valid_pdf(self, tmp_path):
        """Test validation passes for valid PDF path."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Should not raise
        PDFValidator.validate_path(pdf_file)

    def test_validate_path_file_not_found(self, tmp_path):
        """Test validation fails for non-existent file."""
        pdf_file = tmp_path / "nonexistent.pdf"

        with pytest.raises(InvalidPathError, match="Arquivo não encontrado"):
            PDFValidator.validate_path(pdf_file)

    def test_validate_path_not_a_file(self, tmp_path):
        """Test validation fails for directory."""
        with pytest.raises(InvalidPathError, match="Caminho não é um arquivo"):
            PDFValidator.validate_path(tmp_path)

    def test_validate_path_invalid_extension(self, tmp_path):
        """Test validation fails for non-PDF file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")

        with pytest.raises(InvalidPathError, match="Extensão inválida.*Esperado: .pdf"):
            PDFValidator.validate_path(txt_file)

    def test_validate_path_case_insensitive_extension(self, tmp_path):
        """Test validation accepts .PDF extension (uppercase)."""
        pdf_file = tmp_path / "test.PDF"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Should not raise
        PDFValidator.validate_path(pdf_file)


class TestPDFValidatorValidateSize:
    """Test PDFValidator.validate_size() method."""

    def test_validate_size_within_limit(self, tmp_path):
        """Test validation passes for file within size limit."""
        pdf_file = tmp_path / "small.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 1024 * 1024)  # 1MB

        # Should not raise
        PDFValidator.validate_size(pdf_file, max_size_mb=10)

    def test_validate_size_exceeds_limit(self, tmp_path):
        """Test validation fails for file exceeding size limit."""
        pdf_file = tmp_path / "large.pdf"
        # Create a 2MB file
        pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 2 * 1024 * 1024)

        with pytest.raises(PDFTooLargeError, match="Arquivo muito grande.*2\\..*MB.*máximo: 1MB"):
            PDFValidator.validate_size(pdf_file, max_size_mb=1)

    def test_validate_size_default_limit(self, tmp_path):
        """Test validation uses default 500MB limit."""
        pdf_file = tmp_path / "medium.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 100 * 1024 * 1024)  # 100MB

        # Should not raise with default limit (500MB)
        PDFValidator.validate_size(pdf_file)


class TestPDFValidatorValidateIntegrity:
    """Test PDFValidator.validate_integrity() method."""

    @patch("src.utils.validators.fitz.open")
    def test_validate_integrity_valid_pdf(self, mock_fitz_open, tmp_path):
        """Test validation passes for valid PDF."""
        pdf_file = tmp_path / "valid.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest")

        # Mock PyMuPDF document
        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.__len__.return_value = 5
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text"
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        is_valid, message = PDFValidator.validate_integrity(pdf_file)

        assert is_valid is True
        assert message == "OK"
        mock_doc.close.assert_called()

    @patch("src.utils.validators.fitz.open")
    def test_validate_integrity_encrypted_pdf(self, mock_fitz_open, tmp_path):
        """Test validation fails for encrypted PDF."""
        pdf_file = tmp_path / "encrypted.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nencrypted")

        mock_doc = MagicMock()
        mock_doc.is_encrypted = True
        mock_fitz_open.return_value = mock_doc

        with pytest.raises(PDFEncryptedError, match="PDF está criptografado"):
            PDFValidator.validate_integrity(pdf_file)

        mock_doc.close.assert_called()

    @patch("src.utils.validators.fitz.open")
    def test_validate_integrity_empty_pdf(self, mock_fitz_open, tmp_path):
        """Test validation fails for PDF with 0 pages."""
        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nempty")

        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.__len__.return_value = 0
        mock_fitz_open.return_value = mock_doc

        with pytest.raises(PDFEmptyError, match="PDF vazio.*0 páginas"):
            PDFValidator.validate_integrity(pdf_file)

        mock_doc.close.assert_called()

    @patch("src.utils.validators.fitz.open")
    def test_validate_integrity_too_many_pages(self, mock_fitz_open, tmp_path):
        """Test validation fails for PDF with too many pages."""
        pdf_file = tmp_path / "large.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nlarge")

        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.__len__.return_value = 15000
        mock_fitz_open.return_value = mock_doc

        with pytest.raises(PDFTooLargeError, match="PDF tem muitas páginas.*15000.*máximo: 10000"):
            PDFValidator.validate_integrity(pdf_file, max_pages=10000)

        mock_doc.close.assert_called()

    @patch("src.utils.validators.fitz.open")
    def test_validate_integrity_unreadable_page(self, mock_fitz_open, tmp_path):
        """Test validation fails when first page cannot be read."""
        pdf_file = tmp_path / "corrupted.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ncorrupted")

        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.__len__.return_value = 5
        mock_page = MagicMock()
        mock_page.get_text.side_effect = Exception("Cannot read page")
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        with pytest.raises(PDFCorruptedError, match="Erro ao ler primeira página"):
            PDFValidator.validate_integrity(pdf_file)

        mock_doc.close.assert_called()

    @patch("src.utils.validators.fitz.open")
    def test_validate_integrity_corrupted_file(self, mock_fitz_open, tmp_path):
        """Test validation fails for corrupted PDF file."""
        pdf_file = tmp_path / "corrupted.pdf"
        pdf_file.write_bytes(b"not a pdf")

        mock_fitz_open.side_effect = fitz.FileDataError("Invalid PDF")

        with pytest.raises(PDFCorruptedError, match="Arquivo PDF corrompido"):
            PDFValidator.validate_integrity(pdf_file)


class TestPDFValidatorValidateAll:
    """Test PDFValidator.validate_all() method."""

    @patch("src.utils.validators.fitz.open")
    def test_validate_all_success(self, mock_fitz_open, tmp_path):
        """Test all validations pass for valid PDF."""
        pdf_file = tmp_path / "valid.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 1024 * 100)  # 100KB

        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.__len__.return_value = 10
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample text"
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        is_valid, message = PDFValidator.validate_all(pdf_file, max_size_mb=1, max_pages=100)

        assert is_valid is True
        assert message == "OK"

    def test_validate_all_fails_on_path(self, tmp_path):
        """Test validation fails at path check."""
        pdf_file = tmp_path / "nonexistent.pdf"

        with pytest.raises(InvalidPathError):
            PDFValidator.validate_all(pdf_file)

    def test_validate_all_fails_on_size(self, tmp_path):
        """Test validation fails at size check."""
        pdf_file = tmp_path / "large.pdf"
        # Create 2MB file
        pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 2 * 1024 * 1024)

        with pytest.raises(PDFTooLargeError):
            PDFValidator.validate_all(pdf_file, max_size_mb=1)


class TestSanitizeOutputPath:
    """Test sanitize_output_path() function."""

    def test_sanitize_output_path_valid(self, tmp_path):
        """Test sanitization accepts valid relative path."""
        base_dir = tmp_path / "output"
        base_dir.mkdir()

        result = sanitize_output_path("subdir/file.txt", base_dir)

        assert result.is_absolute()
        assert base_dir.resolve() in result.parents or result.parent == base_dir.resolve()

    def test_sanitize_output_path_traversal_attempt(self, tmp_path):
        """Test sanitization blocks path traversal attack."""
        base_dir = tmp_path / "output"
        base_dir.mkdir()

        with pytest.raises(InvalidPathError, match="tentativa de acesso fora do diretório"):
            sanitize_output_path("../../../etc/passwd", base_dir)

    def test_sanitize_output_path_absolute_outside(self, tmp_path):
        """Test sanitization blocks absolute path outside base."""
        base_dir = tmp_path / "output"
        base_dir.mkdir()

        with pytest.raises(InvalidPathError, match="tentativa de acesso fora do diretório"):
            sanitize_output_path("/etc/passwd", base_dir)

    def test_sanitize_output_path_within_base(self, tmp_path):
        """Test sanitization allows paths within base directory."""
        base_dir = tmp_path / "output"
        base_dir.mkdir()

        result = sanitize_output_path("valid/nested/file.txt", base_dir)

        assert str(base_dir.resolve()) in str(result)


class TestValidateProcessNumber:
    """Test validate_process_number() function."""

    def test_validate_process_number_valid(self):
        """Test validation passes for valid CNJ format."""
        valid_number = "5022930-18.2025.8.08.0012"
        assert validate_process_number(valid_number) is True

    def test_validate_process_number_another_valid(self):
        """Test validation passes for another valid format."""
        valid_number = "1234567-89.2024.1.00.0000"
        assert validate_process_number(valid_number) is True

    def test_validate_process_number_empty(self):
        """Test validation fails for empty string."""
        with pytest.raises(ValueError, match="Process number cannot be empty"):
            validate_process_number("")

    def test_validate_process_number_invalid_format(self):
        """Test validation fails for invalid format."""
        with pytest.raises(ValueError, match="Invalid process number format"):
            validate_process_number("123-45.678.9.01.2345")

    def test_validate_process_number_missing_dashes(self):
        """Test validation fails when dashes are missing."""
        with pytest.raises(ValueError, match="Invalid process number format"):
            validate_process_number("5022930.18.2025.8.08.0012")

    def test_validate_process_number_wrong_digit_count(self):
        """Test validation fails when digit counts are wrong."""
        with pytest.raises(ValueError, match="Invalid process number format"):
            validate_process_number("502293-18.2025.8.08.0012")  # Only 6 digits instead of 7


class TestValidateFilename:
    """Test validate_filename() function."""

    def test_validate_filename_valid(self):
        """Test validation passes for valid filename."""
        filename = "document.pdf"
        result = validate_filename(filename)
        assert result == filename

    def test_validate_filename_normalize_extension(self):
        """Test validation normalizes extension to lowercase."""
        filename = "document.PDF"
        result = validate_filename(filename)
        assert result == "document.pdf"

    def test_validate_filename_empty(self):
        """Test validation fails for empty filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            validate_filename("")

    def test_validate_filename_whitespace_only(self):
        """Test validation fails for whitespace-only filename."""
        with pytest.raises(ValueError, match="Filename cannot be empty"):
            validate_filename("   ")

    def test_validate_filename_path_separator_not_allowed(self):
        """Test validation fails for path separators when not allowed."""
        with pytest.raises(ValueError, match="cannot contain path separators"):
            validate_filename("path/to/file.pdf", allow_path=False)

    def test_validate_filename_backslash_not_allowed(self):
        """Test validation fails for backslash when not allowed."""
        with pytest.raises(ValueError, match="cannot contain path separators"):
            validate_filename("path\\to\\file.pdf", allow_path=False)

    def test_validate_filename_path_allowed(self):
        """Test validation passes for path when explicitly allowed."""
        filename = "path/to/file.pdf"
        result = validate_filename(filename, allow_path=True)
        assert result == filename

    def test_validate_filename_reserved_name_con(self):
        """Test validation fails for Windows reserved name CON."""
        with pytest.raises(ValueError, match="Filename uses reserved name"):
            validate_filename("CON.pdf")

    def test_validate_filename_reserved_name_prn(self):
        """Test validation fails for Windows reserved name PRN."""
        with pytest.raises(ValueError, match="Filename uses reserved name"):
            validate_filename("prn.txt")  # Case insensitive

    def test_validate_filename_reserved_name_com1(self):
        """Test validation fails for Windows reserved name COM1."""
        with pytest.raises(ValueError, match="Filename uses reserved name"):
            validate_filename("com1.pdf")

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_validate_filename_invalid_chars_windows(self):
        """Test validation fails for Windows invalid characters."""
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in invalid_chars:
            with pytest.raises(ValueError, match="contains invalid character"):
                validate_filename(f"file{char}name.pdf")

    def test_validate_filename_too_long(self):
        """Test validation fails for filename exceeding 250 chars."""
        long_filename = "a" * 251 + ".pdf"
        with pytest.raises(ValueError, match="Filename too long.*Maximum: 250"):
            validate_filename(long_filename)

    def test_validate_filename_within_length_limit(self):
        """Test validation passes for filename at 250 char limit."""
        filename = "a" * 246 + ".pdf"  # Exactly 250 chars
        result = validate_filename(filename)
        assert result == filename.lower()  # Extension normalized


class TestValidateChunkSize:
    """Test validate_chunk_size() function."""

    def test_validate_chunk_size_valid(self):
        """Test validation passes for valid chunk size."""
        assert validate_chunk_size(1000) is True

    def test_validate_chunk_size_at_min_boundary(self):
        """Test validation passes at minimum boundary."""
        assert validate_chunk_size(100, min_size=100) is True

    def test_validate_chunk_size_at_max_boundary(self):
        """Test validation passes at maximum boundary."""
        assert validate_chunk_size(10000, max_size=10000) is True

    def test_validate_chunk_size_too_small(self):
        """Test validation fails for chunk size below minimum."""
        with pytest.raises(ValueError, match="Chunk size too small.*Minimum: 100"):
            validate_chunk_size(50, min_size=100)

    def test_validate_chunk_size_too_large(self):
        """Test validation fails for chunk size above maximum."""
        with pytest.raises(ValueError, match="Chunk size too large.*Maximum: 10000"):
            validate_chunk_size(15000, max_size=10000)

    def test_validate_chunk_size_not_integer(self):
        """Test validation fails for non-integer chunk size."""
        with pytest.raises(ValueError, match="Chunk size must be an integer"):
            validate_chunk_size(1000.5)  # type: ignore

    def test_validate_chunk_size_string(self):
        """Test validation fails for string chunk size."""
        with pytest.raises(ValueError, match="Chunk size must be an integer.*got str"):
            validate_chunk_size("1000")  # type: ignore


class TestCheckDiskSpace:
    """Test check_disk_space() function."""

    def test_check_disk_space_sufficient(self, tmp_path):
        """Test disk space check passes when sufficient space available."""
        has_space, available_mb = check_disk_space(tmp_path, required_mb=1)

        assert has_space is True
        assert available_mb > 0

    def test_check_disk_space_insufficient(self, tmp_path):
        """Test disk space check fails when insufficient space."""
        # Request more space than available (100TB)
        has_space, available_mb = check_disk_space(tmp_path, required_mb=100_000_000)

        assert has_space is False
        assert available_mb > 0  # Still returns available space

    def test_check_disk_space_for_file_path(self, tmp_path):
        """Test disk space check works for file path (checks parent dir)."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"test")

        has_space, available_mb = check_disk_space(test_file, required_mb=1)

        assert has_space is True
        assert available_mb > 0

    def test_check_disk_space_negative_required(self, tmp_path):
        """Test validation fails for negative required space."""
        with pytest.raises(ValueError, match="Required MB cannot be negative"):
            check_disk_space(tmp_path, required_mb=-100)

    def test_check_disk_space_nonexistent_path(self, tmp_path):
        """Test disk space check raises OSError for nonexistent path."""
        nonexistent = tmp_path / "nonexistent" / "deep" / "path"

        with pytest.raises(OSError):
            check_disk_space(nonexistent, required_mb=100)


class TestEstimateOutputSize:
    """Test estimate_output_size() function."""

    def test_estimate_output_size_default_multiplier(self, tmp_path):
        """Test output size estimation with default 1.5x multiplier."""
        pdf_file = tmp_path / "test.pdf"
        # Create 10MB file
        pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 10 * 1024 * 1024)

        estimated_mb = estimate_output_size(pdf_file)

        # 10MB * 1.5 = 15MB
        assert estimated_mb == 15

    def test_estimate_output_size_custom_multiplier(self, tmp_path):
        """Test output size estimation with custom multiplier."""
        pdf_file = tmp_path / "test.pdf"
        # Create 20MB file
        pdf_file.write_bytes(b"%PDF-1.4\n" + b"x" * 20 * 1024 * 1024)

        estimated_mb = estimate_output_size(pdf_file, multiplier=2.0)

        # 20MB * 2.0 = 40MB
        assert estimated_mb == 40

    def test_estimate_output_size_small_file(self, tmp_path):
        """Test output size estimation for small file."""
        pdf_file = tmp_path / "small.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\nsmall")

        estimated_mb = estimate_output_size(pdf_file)

        # Should be 0 MB (rounds down)
        assert estimated_mb == 0
