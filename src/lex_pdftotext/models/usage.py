"""Usage tracking model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .api_key import APIKey


class Usage(Base):
    """Usage tracking for API keys."""

    __tablename__ = "usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("api_keys.id"), nullable=False, index=True
    )

    # Request details
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)

    # Resource usage
    request_bytes: Mapped[int] = mapped_column(Integer, default=0)
    response_bytes: Mapped[int] = mapped_column(Integer, default=0)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Period tracking (for aggregation)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    month: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Relationships
    api_key: Mapped["APIKey"] = relationship("APIKey", back_populates="usages")

    def __repr__(self) -> str:
        return f"<Usage(id={self.id}, endpoint='{self.endpoint}', status={self.status_code})>"

    @classmethod
    def create(
        cls,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        request_bytes: int = 0,
        response_bytes: int = 0,
        processing_time_ms: int = 0,
    ) -> "Usage":
        """Create a usage record."""
        now = datetime.utcnow()
        return cls(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            request_bytes=request_bytes,
            response_bytes=response_bytes,
            processing_time_ms=processing_time_ms,
            year=now.year,
            month=now.month,
        )
