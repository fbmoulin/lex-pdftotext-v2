"""Tests for SaaS features (API keys, rate limiting, quotas)."""

import os
from datetime import datetime, timedelta

import pytest

# Set test database before imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class TestAPIKeyModel:
    """Tests for APIKey model."""

    def test_create_api_key(self):
        """Test creating an API key."""
        from src.lex_pdftotext.models import APIKey

        key = APIKey.create(
            name="Test Key",
            owner_email="test@example.com",
            owner_name="Test User",
        )

        assert key.name == "Test Key"
        assert key.owner_email == "test@example.com"
        assert key.key.startswith("lex_")
        assert key.is_active is True
        assert key.is_admin is False

    def test_api_key_expiration(self):
        """Test API key expiration check."""
        from src.lex_pdftotext.models import APIKey

        # Non-expiring key
        key1 = APIKey.create(name="Key1", owner_email="test@example.com")
        assert key1.is_expired is False

        # Expiring key (already expired)
        key2 = APIKey.create(
            name="Key2", owner_email="test@example.com", expires_in_days=1
        )
        key2.expires_at = datetime.utcnow() - timedelta(days=1)
        assert key2.is_expired is True

    def test_api_key_validity(self):
        """Test API key validity check."""
        from src.lex_pdftotext.models import APIKey

        key = APIKey.create(name="Key", owner_email="test@example.com")

        # Active and not expired
        assert key.is_valid is True

        # Inactive
        key.is_active = False
        assert key.is_valid is False

    def test_generate_api_key_format(self):
        """Test generated API key format."""
        from src.lex_pdftotext.models.api_key import generate_api_key

        key = generate_api_key()
        assert key.startswith("lex_")
        assert len(key) > 40  # lex_ + 32+ chars


class TestUsageModel:
    """Tests for Usage model."""

    def test_create_usage(self):
        """Test creating a usage record."""
        from src.lex_pdftotext.models import Usage

        usage = Usage.create(
            api_key_id=1,
            endpoint="/extract",
            method="POST",
            status_code=200,
            request_bytes=1024,
            response_bytes=2048,
            processing_time_ms=500,
        )

        assert usage.endpoint == "/extract"
        assert usage.method == "POST"
        assert usage.status_code == 200
        assert usage.year == datetime.utcnow().year
        assert usage.month == datetime.utcnow().month


class TestDatabaseSetup:
    """Tests for database setup."""

    def test_init_db_creates_tables(self):
        """Test that init_db creates tables."""
        from src.lex_pdftotext.models import Base, init_db
        from src.lex_pdftotext.models.base import get_engine

        # Clear cache
        get_engine.cache_clear()

        init_db()

        # Check tables exist
        engine = get_engine()
        tables = Base.metadata.tables.keys()
        assert "api_keys" in tables
        assert "usages" in tables

    def test_session_scope_commits(self):
        """Test that session_scope commits changes."""
        from src.lex_pdftotext.models import APIKey, init_db
        from src.lex_pdftotext.models.base import get_engine, session_scope

        get_engine.cache_clear()
        init_db()

        # Create key in one session
        with session_scope() as db:
            key = APIKey.create(name="Test", owner_email="test@test.com")
            db.add(key)

        # Verify in another session
        with session_scope() as db:
            found = db.query(APIKey).filter(APIKey.name == "Test").first()
            assert found is not None


class TestAuthDependencies:
    """Tests for authentication dependencies."""

    def test_auth_error_has_correct_status(self):
        """Test AuthError returns 401."""
        from src.lex_pdftotext.api.auth import AuthError

        error = AuthError("Test error")
        assert error.status_code == 401
        assert error.detail == "Test error"

    def test_quota_exceeded_error_has_correct_status(self):
        """Test QuotaExceededError returns 429."""
        from src.lex_pdftotext.api.auth import QuotaExceededError

        error = QuotaExceededError("Quota exceeded")
        assert error.status_code == 429


class TestAPIKeyRoutes:
    """Tests for API key route models."""

    def test_api_key_create_model(self):
        """Test APIKeyCreate validation."""
        from src.lex_pdftotext.api.routes_keys import APIKeyCreate

        data = APIKeyCreate(
            name="Test Key",
            owner_email="valid@email.com",
        )
        assert data.name == "Test Key"
        assert data.rate_limit_per_minute == 60
        assert data.monthly_quota == 10000

    def test_api_key_create_invalid_email(self):
        """Test APIKeyCreate rejects invalid email."""
        from pydantic import ValidationError

        from src.lex_pdftotext.api.routes_keys import APIKeyCreate

        with pytest.raises(ValidationError):
            APIKeyCreate(
                name="Test",
                owner_email="not-an-email",
            )

    def test_api_key_update_model(self):
        """Test APIKeyUpdate allows partial updates."""
        from src.lex_pdftotext.api.routes_keys import APIKeyUpdate

        # Only name
        data1 = APIKeyUpdate(name="New Name")
        assert data1.name == "New Name"
        assert data1.is_active is None

        # Only is_active
        data2 = APIKeyUpdate(is_active=False)
        assert data2.is_active is False
        assert data2.name is None


class TestMiddleware:
    """Tests for middleware components."""

    def test_rate_limit_middleware_init(self):
        """Test RateLimitMiddleware initialization."""
        from fastapi import FastAPI

        from src.lex_pdftotext.api.middleware import RateLimitMiddleware

        app = FastAPI()
        middleware = RateLimitMiddleware(app, redis_url=None)

        assert middleware.redis_url is None
        assert middleware.redis is None

    def test_usage_tracking_middleware_init(self):
        """Test UsageTrackingMiddleware initialization."""
        from fastapi import FastAPI

        from src.lex_pdftotext.api.middleware import UsageTrackingMiddleware

        app = FastAPI()
        middleware = UsageTrackingMiddleware(app)

        assert middleware is not None
