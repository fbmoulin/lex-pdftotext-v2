"""Tests for the FastAPI application."""

import pytest
from fastapi.testclient import TestClient

# Skip tests if dependencies not available
pytest.importorskip("fastapi")
pytest.importorskip("redis")


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_check_returns_version(self):
        """Test that health endpoint returns API version."""
        from src.lex_pdftotext.api.main import app

        # Mock Redis
        import unittest.mock as mock

        with mock.patch("src.lex_pdftotext.api.deps.get_redis") as mock_redis:
            mock_redis.return_value.ping.return_value = True
            mock_redis.return_value.smembers.return_value = set()

            client = TestClient(app)
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data


class TestExtractEndpoint:
    """Tests for the extract endpoint."""

    def test_extract_rejects_non_pdf(self):
        """Test that non-PDF files are rejected."""
        from src.lex_pdftotext.api.main import app

        import unittest.mock as mock

        with mock.patch("src.lex_pdftotext.api.deps.get_redis"):
            client = TestClient(app)
            response = client.post(
                "/extract",
                files={"file": ("test.txt", b"not a pdf", "text/plain")},
            )

            assert response.status_code == 400
            assert "PDF" in response.json()["detail"]


class TestModels:
    """Tests for Pydantic models."""

    def test_job_status_enum(self):
        """Test JobStatus enumeration."""
        from src.lex_pdftotext.api.models import JobStatus

        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.STARTED.value == "started"
        assert JobStatus.FINISHED.value == "finished"
        assert JobStatus.FAILED.value == "failed"

    def test_output_format_enum(self):
        """Test OutputFormat enumeration."""
        from src.lex_pdftotext.api.models import OutputFormat

        assert OutputFormat.MARKDOWN.value == "markdown"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.TEXT.value == "text"

    def test_extract_request_defaults(self):
        """Test ExtractRequest default values."""
        from src.lex_pdftotext.api.models import ExtractRequest, OutputFormat

        request = ExtractRequest()
        assert request.format == OutputFormat.MARKDOWN
        assert request.normalize is True
        assert request.include_metadata is True
        assert request.chunk_for_rag is False
        assert request.chunk_size == 1000


class TestDeps:
    """Tests for API dependencies."""

    def test_generate_job_id_is_unique(self):
        """Test that job IDs are unique."""
        from src.lex_pdftotext.api.deps import generate_job_id

        ids = [generate_job_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_get_upload_path_sanitizes_filename(self, tmp_path, monkeypatch):
        """Test that upload path sanitizes filename."""
        # Mock UPLOAD_DIR to use temp directory
        import src.lex_pdftotext.api.deps as deps

        monkeypatch.setattr(deps, "UPLOAD_DIR", tmp_path / "uploads")

        from src.lex_pdftotext.api.deps import get_upload_path

        path = get_upload_path("../../../etc/passwd", "job123")
        assert "etc/passwd" not in str(path)
        assert "job123" in str(path)


class TestStorage:
    """Tests for storage backends."""

    def test_local_storage_save_and_load(self, tmp_path):
        """Test LocalStorage save and load."""
        from src.lex_pdftotext.storage import LocalStorage

        storage = LocalStorage(base_path=tmp_path)

        # Save
        content = b"test content"
        path = storage.save(content, "test/file.txt")
        assert path.endswith("test/file.txt")

        # Load
        loaded = storage.load("test/file.txt")
        assert loaded == content

    def test_local_storage_exists(self, tmp_path):
        """Test LocalStorage exists check."""
        from src.lex_pdftotext.storage import LocalStorage

        storage = LocalStorage(base_path=tmp_path)

        assert not storage.exists("nonexistent.txt")

        storage.save(b"content", "exists.txt")
        assert storage.exists("exists.txt")

    def test_local_storage_delete(self, tmp_path):
        """Test LocalStorage delete."""
        from src.lex_pdftotext.storage import LocalStorage

        storage = LocalStorage(base_path=tmp_path)

        storage.save(b"content", "to_delete.txt")
        assert storage.exists("to_delete.txt")

        result = storage.delete("to_delete.txt")
        assert result is True
        assert not storage.exists("to_delete.txt")

    def test_local_storage_list_files(self, tmp_path):
        """Test LocalStorage list files."""
        from src.lex_pdftotext.storage import LocalStorage

        storage = LocalStorage(base_path=tmp_path)

        storage.save(b"1", "a/file1.txt")
        storage.save(b"2", "a/file2.txt")
        storage.save(b"3", "b/file3.txt")

        files = storage.list_files()
        assert len(files) == 3

        files_a = storage.list_files("a")
        assert len(files_a) == 2

    def test_storage_factory_returns_local_by_default(self, monkeypatch):
        """Test that storage factory returns LocalStorage by default."""
        # Clear cache
        from src.lex_pdftotext.storage.factory import get_storage

        get_storage.cache_clear()

        monkeypatch.setenv("STORAGE_TYPE", "local")
        monkeypatch.setenv("STORAGE_PATH", "/tmp/test-storage")

        storage = get_storage()

        from src.lex_pdftotext.storage import LocalStorage

        assert isinstance(storage, LocalStorage)

        # Clear cache again
        get_storage.cache_clear()
