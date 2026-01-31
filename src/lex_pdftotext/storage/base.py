"""Base storage interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class Storage(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(self, content: bytes | BinaryIO, path: str) -> str:
        """
        Save content to storage.

        Args:
            content: File content as bytes or file-like object
            path: Destination path within storage

        Returns:
            URL or path to the saved file
        """
        pass

    @abstractmethod
    def load(self, path: str) -> bytes:
        """
        Load content from storage.

        Args:
            path: Path to the file

        Returns:
            File content as bytes
        """
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            path: Path to the file

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            path: Path to the file

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def get_url(self, path: str, expires: int = 3600) -> str:
        """
        Get a URL for accessing the file.

        Args:
            path: Path to the file
            expires: URL expiration in seconds (for presigned URLs)

        Returns:
            URL to access the file
        """
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in storage.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of file paths
        """
        pass
