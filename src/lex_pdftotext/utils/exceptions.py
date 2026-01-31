"""
Custom exceptions for PDF extraction.
"""


class PDFExtractionError(Exception):
    """Base exception for PDF extraction errors."""

    pass


class PDFCorruptedError(PDFExtractionError):
    """Raised when PDF file is corrupted or unreadable."""

    pass


class PDFEncryptedError(PDFExtractionError):
    """Raised when PDF is encrypted/password-protected."""

    pass


class PDFTooLargeError(PDFExtractionError):
    """Raised when PDF exceeds maximum allowed size."""

    pass


class PDFEmptyError(PDFExtractionError):
    """Raised when PDF has no pages or no content."""

    pass


class InvalidPathError(PDFExtractionError):
    """Raised when file path is invalid or doesn't exist."""

    pass
