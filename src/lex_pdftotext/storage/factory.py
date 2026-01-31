"""Storage factory for creating storage backends."""

import os
from functools import lru_cache

from .base import Storage
from .local import LocalStorage
from .s3 import S3Storage


@lru_cache
def get_storage() -> Storage:
    """
    Get storage backend based on environment configuration.

    Returns:
        Storage instance (LocalStorage or S3Storage)
    """
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()

    if storage_type == "s3":
        return S3Storage()
    else:
        base_path = os.getenv("STORAGE_PATH", "/app/storage")
        return LocalStorage(base_path=base_path)
