"""Local filesystem storage backend."""

import shutil
from pathlib import Path
from typing import BinaryIO

from .base import Storage


class LocalStorage(Storage):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str | Path = "/app/storage"):
        """
        Initialize local storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve and sanitize path."""
        # Prevent directory traversal
        safe_path = Path(path).name if ".." in path else path
        return self.base_path / safe_path

    def save(self, content: bytes | BinaryIO, path: str) -> str:
        """Save content to local filesystem."""
        filepath = self._resolve_path(path)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            filepath.write_bytes(content)
        else:
            with open(filepath, "wb") as f:
                shutil.copyfileobj(content, f)

        return str(filepath)

    def load(self, path: str) -> bytes:
        """Load content from local filesystem."""
        filepath = self._resolve_path(path)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return filepath.read_bytes()

    def delete(self, path: str) -> bool:
        """Delete file from local filesystem."""
        filepath = self._resolve_path(path)

        if filepath.exists():
            if filepath.is_dir():
                shutil.rmtree(filepath)
            else:
                filepath.unlink()
            return True

        return False

    def exists(self, path: str) -> bool:
        """Check if file exists in local filesystem."""
        return self._resolve_path(path).exists()

    def get_url(self, path: str, expires: int = 3600) -> str:
        """Get local file path as URL."""
        filepath = self._resolve_path(path)
        return f"file://{filepath}"

    def list_files(self, prefix: str = "") -> list[str]:
        """List files in local filesystem."""
        search_path = self._resolve_path(prefix) if prefix else self.base_path
        files = []

        if search_path.is_dir():
            for item in search_path.rglob("*"):
                if item.is_file():
                    # Return relative path
                    files.append(str(item.relative_to(self.base_path)))

        return files
