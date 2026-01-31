"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"


class OutputFormat(str, Enum):
    """Output format options."""

    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"


class ExtractRequest(BaseModel):
    """Request model for extraction settings."""

    format: OutputFormat = Field(default=OutputFormat.MARKDOWN, description="Output format")
    normalize: bool = Field(default=True, description="Normalize text (uppercase to sentence case)")
    include_metadata: bool = Field(default=True, description="Include document metadata")
    chunk_for_rag: bool = Field(default=False, description="Split into RAG-optimized chunks")
    chunk_size: int = Field(
        default=1000, description="Chunk size for RAG splitting", ge=100, le=10000
    )


class TableExtractRequest(BaseModel):
    """Request model for table extraction settings."""

    format: str = Field(default="markdown", description="Output format: markdown or csv")
    include_metadata: bool = Field(default=True, description="Include table metadata")


class MergeRequest(BaseModel):
    """Request model for merge operation."""

    format: OutputFormat = Field(default=OutputFormat.MARKDOWN, description="Output format")
    normalize: bool = Field(default=True, description="Normalize text")


class JobResponse(BaseModel):
    """Response model for job creation."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    message: str = Field(default="Job queued successfully", description="Status message")


class JobStatusResponse(BaseModel):
    """Response model for job status query."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: datetime | None = Field(None, description="Job start timestamp")
    finished_at: datetime | None = Field(None, description="Job completion timestamp")
    progress: float = Field(default=0.0, description="Job progress (0-100)", ge=0, le=100)
    message: str | None = Field(None, description="Status message or error details")
    result_url: str | None = Field(None, description="URL to download result when finished")


class JobResultResponse(BaseModel):
    """Response model for job result."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Job status")
    result: Any = Field(None, description="Extraction result")
    metadata: dict | None = Field(None, description="Document metadata")
    processing_time: float | None = Field(None, description="Processing time in seconds")


class PDFInfoResponse(BaseModel):
    """Response model for PDF information."""

    filename: str = Field(..., description="Original filename")
    pages: int = Field(..., description="Number of pages")
    size_bytes: int = Field(..., description="File size in bytes")
    has_tables: bool = Field(..., description="Whether PDF contains tables")
    metadata: dict = Field(default_factory=dict, description="PDF metadata")
    document_type: str | None = Field(None, description="Detected document type")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    redis: str = Field(..., description="Redis connection status")
    workers: int = Field(..., description="Number of active workers")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict | None = Field(None, description="Additional error details")
