"""API Key model for authentication."""

import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .usage import Usage


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"lex_{secrets.token_urlsafe(32)}"


class APIKey(Base):
    """API Key model for authentication and rate limiting."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, default=generate_api_key)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Owner information
    owner_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=1000)

    # Monthly quota
    monthly_quota: Mapped[int] = mapped_column(Integer, default=10000)  # requests per month
    monthly_quota_bytes: Mapped[int] = mapped_column(Integer, default=1073741824)  # 1GB per month

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    usages: Mapped[list["Usage"]] = relationship("Usage", back_populates="api_key")

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name='{self.name}', owner='{self.owner_email}')>"

    @property
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def update_last_used(self) -> None:
        """Update last used timestamp."""
        self.last_used_at = datetime.utcnow()

    @classmethod
    def create(
        cls,
        name: str,
        owner_email: str,
        owner_name: str | None = None,
        description: str | None = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_hour: int = 1000,
        monthly_quota: int = 10000,
        monthly_quota_bytes: int = 1073741824,
        expires_in_days: int | None = None,
        is_admin: bool = False,
    ) -> "APIKey":
        """Create a new API key with the given parameters."""
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        return cls(
            key=generate_api_key(),
            name=name,
            owner_email=owner_email,
            owner_name=owner_name,
            description=description,
            rate_limit_per_minute=rate_limit_per_minute,
            rate_limit_per_hour=rate_limit_per_hour,
            monthly_quota=monthly_quota,
            monthly_quota_bytes=monthly_quota_bytes,
            expires_at=expires_at,
            is_active=True,
            is_admin=is_admin,
        )
