"""API Key management routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import APIKey, Usage
from ..models.base import get_session
from .auth import require_admin

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# Pydantic models
class APIKeyCreate(BaseModel):
    """Request model for creating an API key."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    owner_email: EmailStr
    owner_name: str | None = Field(None, max_length=255)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=100000)
    monthly_quota: int = Field(default=10000, ge=1, le=10000000)
    monthly_quota_bytes: int = Field(default=1073741824, ge=1)  # 1GB default
    expires_in_days: int | None = Field(None, ge=1, le=365)
    is_admin: bool = False


class APIKeyUpdate(BaseModel):
    """Request model for updating an API key."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    rate_limit_per_minute: int | None = Field(None, ge=1, le=10000)
    rate_limit_per_hour: int | None = Field(None, ge=1, le=100000)
    monthly_quota: int | None = Field(None, ge=1, le=10000000)
    monthly_quota_bytes: int | None = Field(None, ge=1)
    is_active: bool | None = None


class APIKeyResponse(BaseModel):
    """Response model for API key."""

    id: int
    key: str
    name: str
    description: str | None
    owner_email: str
    owner_name: str | None
    rate_limit_per_minute: int
    rate_limit_per_hour: int
    monthly_quota: int
    monthly_quota_bytes: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Response model for API key list."""

    id: int
    name: str
    owner_email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_used_at: datetime | None

    class Config:
        from_attributes = True


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""

    api_key_id: int
    api_key_name: str
    total_requests: int
    total_request_bytes: int
    total_response_bytes: int
    avg_processing_time_ms: float
    period: str
    quota_remaining: int
    quota_bytes_remaining: int


# Routes
@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    admin: Annotated[APIKey, Depends(require_admin)],
    db: Annotated[Session, Depends(get_session)],
):
    """
    Create a new API key.

    Requires admin privileges.
    """
    api_key = APIKey.create(
        name=data.name,
        description=data.description,
        owner_email=data.owner_email,
        owner_name=data.owner_name,
        rate_limit_per_minute=data.rate_limit_per_minute,
        rate_limit_per_hour=data.rate_limit_per_hour,
        monthly_quota=data.monthly_quota,
        monthly_quota_bytes=data.monthly_quota_bytes,
        expires_in_days=data.expires_in_days,
        is_admin=data.is_admin,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return api_key


@router.get("", response_model=list[APIKeyListResponse])
async def list_api_keys(
    admin: Annotated[APIKey, Depends(require_admin)],
    db: Annotated[Session, Depends(get_session)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    active_only: bool = False,
):
    """
    List all API keys.

    Requires admin privileges.
    """
    query = db.query(APIKey)

    if active_only:
        query = query.filter(APIKey.is_active.is_(True))

    keys = query.order_by(APIKey.created_at.desc()).offset(skip).limit(limit).all()

    return keys


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    admin: Annotated[APIKey, Depends(require_admin)],
    db: Annotated[Session, Depends(get_session)],
):
    """
    Get an API key by ID.

    Requires admin privileges.
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    return api_key


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    data: APIKeyUpdate,
    admin: Annotated[APIKey, Depends(require_admin)],
    db: Annotated[Session, Depends(get_session)],
):
    """
    Update an API key.

    Requires admin privileges.
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(api_key, field, value)

    db.commit()
    db.refresh(api_key)

    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    admin: Annotated[APIKey, Depends(require_admin)],
    db: Annotated[Session, Depends(get_session)],
):
    """
    Delete an API key.

    Requires admin privileges.
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Prevent deleting the last admin key
    if api_key.is_admin:
        admin_count = db.query(APIKey).filter(APIKey.is_admin.is_(True)).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the last admin API key",
            )

    db.delete(api_key)
    db.commit()


@router.post("/{key_id}/regenerate", response_model=APIKeyResponse)
async def regenerate_api_key(
    key_id: int,
    admin: Annotated[APIKey, Depends(require_admin)],
    db: Annotated[Session, Depends(get_session)],
):
    """
    Regenerate an API key (create new key value).

    Requires admin privileges.
    """
    from ..models.api_key import generate_api_key

    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.key = generate_api_key()
    db.commit()
    db.refresh(api_key)

    return api_key


@router.get("/{key_id}/usage", response_model=UsageStatsResponse)
async def get_api_key_usage(
    key_id: int,
    admin: Annotated[APIKey, Depends(require_admin)],
    db: Annotated[Session, Depends(get_session)],
    year: Annotated[int | None, Query()] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
):
    """
    Get usage statistics for an API key.

    Requires admin privileges.
    """
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Default to current month
    now = datetime.utcnow()
    query_year = year or now.year
    query_month = month or now.month

    # Get usage stats
    stats = (
        db.query(
            func.count(Usage.id).label("total_requests"),
            func.sum(Usage.request_bytes).label("total_request_bytes"),
            func.sum(Usage.response_bytes).label("total_response_bytes"),
            func.avg(Usage.processing_time_ms).label("avg_processing_time_ms"),
        )
        .filter(
            Usage.api_key_id == key_id,
            Usage.year == query_year,
            Usage.month == query_month,
        )
        .first()
    )

    total_requests = stats.total_requests or 0
    total_bytes = (stats.total_request_bytes or 0) + (stats.total_response_bytes or 0)

    return UsageStatsResponse(
        api_key_id=key_id,
        api_key_name=api_key.name,
        total_requests=total_requests,
        total_request_bytes=stats.total_request_bytes or 0,
        total_response_bytes=stats.total_response_bytes or 0,
        avg_processing_time_ms=round(stats.avg_processing_time_ms or 0, 2),
        period=f"{query_year}-{query_month:02d}",
        quota_remaining=max(0, api_key.monthly_quota - total_requests),
        quota_bytes_remaining=max(0, api_key.monthly_quota_bytes - total_bytes),
    )
