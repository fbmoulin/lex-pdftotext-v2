"""
Comprehensive tests for validation utilities.

To run: pytest tests/test_validators.py -v
"""

# Add src to path
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.validators import (
    check_disk_space,
    estimate_output_size,
    sanitize_output_path,
    validate_chunk_size,
    validate_filename,
    validate_process_number,
)


class TestProcessNumberValidation:
    """Test Brazilian process number (CNJ format) validation."""

    def test_valid_process_number(self):
        """Test validation of valid CNJ format process numbers."""
        valid_numbers = [
            "5022930-18.2025.8.08.0012",
            "0000865-32.2016.8.08.0012",
            "1234567-89.2020.1.01.0001",
        ]

        for number in valid_numbers:
            assert validate_process_number(number) == True

    def test_invalid_process_number_format(self):
        """Test rejection of invalid format."""
        invalid_numbers = [
            "invalid-format",
            "123-45.2020.1.01.0001",  # Wrong digit count
            "1234567-89-2020-1-01-0001",  # Wrong separators
            "1234567-89.2020.8.08",  # Incomplete
            "",  # Empty
            "abcdefg-hi.jklm.n.op.qrst",  # Letters
        ]

        for number in invalid_numbers:
            with pytest.raises(ValueError):
                validate_process_number(number)

    def test_empty_process_number(self):
        """Test that empty process number raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_process_number("")


class TestFilenameValidation:
    """Test filename validation and sanitization."""

    def test_valid_filename(self):
        """Test validation of valid filenames."""
        assert validate_filename("document.pdf") == "document.pdf"
        assert validate_filename("report_2024.docx") == "report_2024.docx"
        assert validate_filename("file-name_123.txt") == "file-name_123.txt"

    def test_extension_normalization(self):
        """Test that extensions are normalized to lowercase."""
        assert validate_filename("Document.PDF") == "Document.pdf"
        assert validate_filename("Report.TXT") == "Report.txt"
        assert validate_filename("file.DOCX") == "file.docx"

    def test_reserved_names(self):
        """Test rejection of Windows reserved names."""
        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]

        for name in reserved_names:
            with pytest.raises(ValueError, match="reserved name"):
                validate_filename(f"{name}.txt")

    def test_invalid_characters(self):
        """Test rejection of invalid characters."""
        # These tests will run on Linux where only null byte is invalid
        # On Windows, more characters would fail
        with pytest.raises(ValueError):
            validate_filename("file\x00name.txt")  # Null byte

    def test_path_separator_rejection(self):
        """Test that path separators are rejected by default."""
        with pytest.raises(ValueError, match="path separators"):
            validate_filename("path/to/file.txt")

        with pytest.raises(ValueError, match="path separators"):
            validate_filename("path\\to\\file.txt")

    def test_path_separator_allowed(self):
        """Test that path separators can be allowed."""
        result = validate_filename("path/to/file.txt", allow_path=True)
        assert result == "path/to/file.txt"

    def test_empty_filename(self):
        """Test that empty filename raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_filename("")

        with pytest.raises(ValueError, match="cannot be empty"):
            validate_filename("   ")

    def test_filename_too_long(self):
        """Test rejection of very long filenames."""
        long_name = "a" * 300 + ".txt"
        with pytest.raises(ValueError, match="too long"):
            validate_filename(long_name)


class TestChunkSizeValidation:
    """Test chunk size validation."""

    def test_valid_chunk_size(self):
        """Test validation of valid chunk sizes."""
        assert validate_chunk_size(1000) == True
        assert validate_chunk_size(100) == True  # Minimum
        assert validate_chunk_size(10000) == True  # Maximum

    def test_chunk_size_too_small(self):
        """Test rejection of too-small chunk size."""
        with pytest.raises(ValueError, match="too small"):
            validate_chunk_size(50)

        with pytest.raises(ValueError, match="too small"):
            validate_chunk_size(0)

    def test_chunk_size_too_large(self):
        """Test rejection of too-large chunk size."""
        with pytest.raises(ValueError, match="too large"):
            validate_chunk_size(20000)

    def test_custom_bounds(self):
        """Test validation with custom min/max bounds."""
        assert validate_chunk_size(500, min_size=200, max_size=1000) == True

        with pytest.raises(ValueError):
            validate_chunk_size(100, min_size=200, max_size=1000)

        with pytest.raises(ValueError):
            validate_chunk_size(2000, min_size=200, max_size=1000)

    def test_non_integer_chunk_size(self):
        """Test rejection of non-integer values."""
        with pytest.raises(ValueError, match="must be an integer"):
            validate_chunk_size(1000.5)

        with pytest.raises(ValueError, match="must be an integer"):
            validate_chunk_size("1000")


class TestDiskSpaceValidation:
    """Test disk space checking."""

    def test_check_disk_space_sufficient(self):
        """Test disk space check with sufficient space."""
        has_space, available_mb = check_disk_space(Path.cwd(), required_mb=10)

        assert isinstance(has_space, bool)
        assert isinstance(available_mb, int)
        assert available_mb > 0
        # Most systems will have > 10MB free
        assert has_space == True

    def test_check_disk_space_insufficient(self):
        """Test disk space check with insufficient space."""
        # Request absurdly large amount
        has_space, available_mb = check_disk_space(Path.cwd(), required_mb=999999999)

        assert has_space == False
        assert available_mb > 0

    def test_check_disk_space_for_file(self):
        """Test disk space check for a file path."""
        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            temp_path = Path(tf.name)

        try:
            has_space, available_mb = check_disk_space(temp_path, required_mb=10)
            assert isinstance(has_space, bool)
            assert available_mb > 0
        finally:
            temp_path.unlink()

    def test_negative_required_space(self):
        """Test that negative required space raises error."""
        with pytest.raises(ValueError, match="cannot be negative"):
            check_disk_space(Path.cwd(), required_mb=-100)


class TestOutputSizeEstimation:
    """Test PDF output size estimation."""

    def test_estimate_output_size(self):
        """Test estimation of output file size."""
        # Create a temp file of known size (1MB)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
            tf.write(b"x" * (1024 * 1024))  # 1MB
            temp_path = Path(tf.name)

        try:
            estimated_mb = estimate_output_size(temp_path, multiplier=1.5)

            # Should be roughly 1.5MB
            assert isinstance(estimated_mb, int)
            assert estimated_mb == 1  # int(1.5) = 1
        finally:
            temp_path.unlink()

    def test_estimate_with_custom_multiplier(self):
        """Test estimation with custom multiplier."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
            tf.write(b"x" * (2 * 1024 * 1024))  # 2MB
            temp_path = Path(tf.name)

        try:
            estimated_mb = estimate_output_size(temp_path, multiplier=2.0)

            # Should be roughly 4MB
            assert estimated_mb >= 3  # Account for int rounding
        finally:
            temp_path.unlink()


class TestPathSanitization:
    """Test output path sanitization."""

    def test_sanitize_valid_path(self):
        """Test sanitization of valid relative path."""
        base_dir = Path("/tmp/test")
        result = sanitize_output_path("output/file.txt", base_dir)

        assert isinstance(result, Path)
        assert str(result).startswith(str(base_dir.resolve()))

    def test_sanitize_prevents_traversal(self):
        """Test that path traversal attacks are prevented."""
        base_dir = Path("/tmp/test")

        # Attempt path traversal
        from src.utils.exceptions import InvalidPathError

        with pytest.raises(InvalidPathError, match="fora do diretório"):
            sanitize_output_path("../../../etc/passwd", base_dir)

        with pytest.raises(InvalidPathError):
            sanitize_output_path("/etc/passwd", base_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
