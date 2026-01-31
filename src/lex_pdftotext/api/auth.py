"""Authentication utilities for the API."""

from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..models import APIKey, Usage
from ..models.base import get_session

# API Key header configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthError(HTTPException):
    """Authentication error."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "ApiKey"},
        )


class QuotaExceededError(HTTPException):
    """Quota exceeded error."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


def get_api_key_from_header(
    api_key: Annotated[str | None, Security(API_KEY_HEADER)],
) -> str:
    """Extract API key from header."""
    if not api_key:
        raise AuthError("API key is required. Provide X-API-Key header.")
    return api_key


def get_current_api_key(
    api_key: Annotated[str, Depends(get_api_key_from_header)],
    db: Annotated[Session, Depends(get_session)],
) -> APIKey:
    """
    Validate API key and return the APIKey object.

    Raises:
        AuthError: If API key is invalid, inactive, or expired.
    """
    db_key = db.query(APIKey).filter(APIKey.key == api_key).first()

    if not db_key:
        raise AuthError("Invalid API key")

    if not db_key.is_active:
        raise AuthError("API key is inactive")

    if db_key.is_expired:
        raise AuthError("API key has expired")

    # Update last used timestamp
    db_key.update_last_used()
    db.commit()

    return db_key


def get_optional_api_key(
    api_key: Annotated[str | None, Security(API_KEY_HEADER)],
    db: Annotated[Session, Depends(get_session)],
) -> APIKey | None:
    """
    Get API key if provided, otherwise return None.

    Used for endpoints that work with or without authentication.
    """
    if not api_key:
        return None

    db_key = db.query(APIKey).filter(APIKey.key == api_key).first()

    if db_key and db_key.is_valid:
        db_key.update_last_used()
        db.commit()
        return db_key

    return None


def require_admin(
    api_key: Annotated[APIKey, Depends(get_current_api_key)],
) -> APIKey:
    """Require admin API key."""
    if not api_key.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return api_key


def check_monthly_quota(
    api_key: Annotated[APIKey, Depends(get_current_api_key)],
    db: Annotated[Session, Depends(get_session)],
) -> APIKey:
    """
    Check if API key has exceeded monthly quota.

    Raises:
        QuotaExceededError: If monthly quota is exceeded.
    """
    now = datetime.utcnow()

    # Count requests this month
    request_count = (
        db.query(Usage)
        .filter(
            Usage.api_key_id == api_key.id,
            Usage.year == now.year,
            Usage.month == now.month,
        )
        .count()
    )

    if request_count >= api_key.monthly_quota:
        raise QuotaExceededError(
            f"Monthly request quota exceeded ({api_key.monthly_quota} requests)"
        )

    # Sum bytes this month
    from sqlalchemy import func

    total_bytes = (
        db.query(func.sum(Usage.request_bytes + Usage.response_bytes))
        .filter(
            Usage.api_key_id == api_key.id,
            Usage.year == now.year,
            Usage.month == now.month,
        )
        .scalar()
        or 0
    )

    if total_bytes >= api_key.monthly_quota_bytes:
        raise QuotaExceededError(
            f"Monthly data quota exceeded ({api_key.monthly_quota_bytes // 1024 // 1024}MB)"
        )

    return api_key


def record_usage(
    db: Session,
    api_key: APIKey,
    endpoint: str,
    method: str,
    status_code: int,
    request_bytes: int = 0,
    response_bytes: int = 0,
    processing_time_ms: int = 0,
) -> Usage:
    """Record API usage for an API key."""
    usage = Usage.create(
        api_key_id=api_key.id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        request_bytes=request_bytes,
        response_bytes=response_bytes,
        processing_time_ms=processing_time_ms,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage
