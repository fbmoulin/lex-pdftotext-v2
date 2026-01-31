"""Storage abstraction for lex-pdftotext."""

from .base import Storage
from .factory import get_storage
from .local import LocalStorage
from .s3 import S3Storage

__all__ = ["Storage", "LocalStorage", "S3Storage", "get_storage"]
