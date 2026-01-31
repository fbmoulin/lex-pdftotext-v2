"""FastAPI application for lex-pdftotext."""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .. import __version__
from .deps import (
    MAX_UPLOAD_SIZE,
    check_redis_health,
    cleanup_job_files,
    generate_job_id,
    get_output_path,
    get_queue,
    get_redis,
    get_workers_count,
    save_uploaded_file,
)
from .models import (
    ErrorResponse,
    HealthResponse,
    JobResponse,
    JobStatus,
    JobStatusResponse,
    OutputFormat,
    PDFInfoResponse,
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting lex-pdftotext API server...")

    # Initialize database if SAAS mode enabled
    if os.getenv("SAAS_MODE", "false").lower() == "true":
        logger.info("SaaS mode enabled, initializing database...")
        from ..models import init_db

        init_db()
        logger.info("Database initialized")

    yield
    logger.info("Shutting down lex-pdftotext API server...")


app = FastAPI(
    title="lex-pdftotext API",
    description="Extract and structure text from Brazilian legal PDF documents (PJe format)",
    version=__version__,
    lifespan=lifespan,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SaaS middleware (rate limiting and usage tracking)
if os.getenv("SAAS_MODE", "false").lower() == "true":
    from .middleware import RateLimitMiddleware, UsageTrackingMiddleware
    from .routes_keys import router as keys_router

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    app.add_middleware(RateLimitMiddleware, redis_url=redis_url)
    app.add_middleware(UsageTrackingMiddleware)

    # Include API keys management routes
    app.include_router(keys_router)


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health status."""
    return HealthResponse(
        status="healthy",
        version=__version__,
        redis=check_redis_health(),
        workers=get_workers_count(),
    )


# Extract single PDF
@app.post("/extract", response_model=JobResponse, tags=["Extraction"])
async def extract_pdf(
    file: Annotated[UploadFile, File(description="PDF file to extract")],
    format: Annotated[OutputFormat, Query(description="Output format")] = OutputFormat.MARKDOWN,
    normalize: Annotated[bool, Query(description="Normalize text")] = True,
    include_metadata: Annotated[bool, Query(description="Include metadata")] = True,
    chunk_for_rag: Annotated[bool, Query(description="Split into RAG chunks")] = False,
    chunk_size: Annotated[int, Query(description="Chunk size", ge=100, le=10000)] = 1000,
):
    """
    Extract text from a PDF document.

    Returns a job ID for tracking the extraction progress.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Check file size
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // 1024 // 1024}MB",
        )

    # Create job
    job_id = generate_job_id()
    created_at = datetime.utcnow()

    # Save file
    filepath = save_uploaded_file(content, file.filename, job_id)

    # Queue job
    queue = get_queue()
    queue.enqueue(
        "src.lex_pdftotext.worker.tasks.extract_pdf_task",
        kwargs={
            "job_id": job_id,
            "filepath": str(filepath),
            "options": {
                "format": format.value,
                "normalize": normalize,
                "include_metadata": include_metadata,
                "chunk_for_rag": chunk_for_rag,
                "chunk_size": chunk_size,
            },
        },
        job_id=job_id,
        job_timeout="10m",
    )

    logger.info(f"Job {job_id} queued for file {file.filename}")

    return JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=created_at,
        message="Job queued successfully",
    )


# Batch extract multiple PDFs
@app.post("/batch", response_model=list[JobResponse], tags=["Extraction"])
async def batch_extract(
    files: Annotated[list[UploadFile], File(description="PDF files to extract")],
    format: Annotated[OutputFormat, Query(description="Output format")] = OutputFormat.MARKDOWN,
    normalize: Annotated[bool, Query(description="Normalize text")] = True,
):
    """
    Extract text from multiple PDF documents.

    Returns a list of job IDs for tracking each extraction.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if len(files) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 files per batch")

    results = []
    queue = get_queue()
    created_at = datetime.utcnow()

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            continue

        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            continue

        job_id = generate_job_id()
        filepath = save_uploaded_file(content, file.filename, job_id)

        queue.enqueue(
            "src.lex_pdftotext.worker.tasks.extract_pdf_task",
            kwargs={
                "job_id": job_id,
                "filepath": str(filepath),
                "options": {
                    "format": format.value,
                    "normalize": normalize,
                    "include_metadata": True,
                    "chunk_for_rag": False,
                },
            },
            job_id=job_id,
            job_timeout="10m",
        )

        results.append(
            JobResponse(
                job_id=job_id,
                status=JobStatus.QUEUED,
                created_at=created_at,
                message=f"Job queued for {file.filename}",
            )
        )

    return results


# Extract tables from PDF
@app.post("/tables", response_model=JobResponse, tags=["Extraction"])
async def extract_tables(
    file: Annotated[UploadFile, File(description="PDF file to extract tables from")],
    format: Annotated[str, Query(description="Output format: markdown or csv")] = "markdown",
):
    """
    Extract tables from a PDF document.

    Returns a job ID for tracking the extraction progress.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // 1024 // 1024}MB",
        )

    job_id = generate_job_id()
    created_at = datetime.utcnow()

    filepath = save_uploaded_file(content, file.filename, job_id)

    queue = get_queue()
    queue.enqueue(
        "src.lex_pdftotext.worker.tasks.extract_tables_task",
        kwargs={
            "job_id": job_id,
            "filepath": str(filepath),
            "options": {"format": format},
        },
        job_id=job_id,
        job_timeout="10m",
    )

    return JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=created_at,
        message="Table extraction job queued",
    )


# Merge PDFs by process number
@app.post("/merge", response_model=JobResponse, tags=["Processing"])
async def merge_pdfs(
    files: Annotated[list[UploadFile], File(description="PDF files to merge")],
    format: Annotated[OutputFormat, Query(description="Output format")] = OutputFormat.MARKDOWN,
):
    """
    Merge multiple PDF documents by process number.

    Combines related documents and extracts unified text.
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 files required for merge")

    if len(files) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 files per merge")

    job_id = generate_job_id()
    created_at = datetime.utcnow()

    filepaths = []
    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            continue

        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            continue

        filepath = save_uploaded_file(content, file.filename, job_id)
        filepaths.append(str(filepath))

    if len(filepaths) < 2:
        raise HTTPException(status_code=400, detail="At least 2 valid PDF files required")

    queue = get_queue()
    queue.enqueue(
        "src.lex_pdftotext.worker.tasks.merge_pdfs_task",
        kwargs={
            "job_id": job_id,
            "filepaths": filepaths,
            "options": {"format": format.value},
        },
        job_id=job_id,
        job_timeout="30m",
    )

    return JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=created_at,
        message=f"Merge job queued for {len(filepaths)} files",
    )


# Get PDF info without full extraction
@app.post("/info", response_model=PDFInfoResponse, tags=["Information"])
async def get_pdf_info(
    file: Annotated[UploadFile, File(description="PDF file to analyze")],
):
    """
    Get information about a PDF document without full extraction.

    Returns page count, file size, detected tables, and basic metadata.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()

    # Import here to avoid circular imports
    import tempfile
    from pathlib import Path

    from ..extractors import PyMuPDFExtractor
    from ..extractors.table_extractor import TableExtractor
    from ..processors import MetadataParser

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # Extract basic info
        with PyMuPDFExtractor(str(tmp_path)) as extractor:
            pages = extractor.page_count
            text = extractor.extract_text()

        # Check for tables
        table_extractor = TableExtractor(str(tmp_path))
        has_tables = table_extractor.has_tables()

        # Parse metadata
        parser = MetadataParser()
        metadata = parser.parse(text)

        return PDFInfoResponse(
            filename=file.filename,
            pages=pages,
            size_bytes=len(content),
            has_tables=has_tables,
            metadata=metadata.to_dict() if metadata else {},
            document_type=metadata.document_type if metadata else None,
        )

    finally:
        tmp_path.unlink(missing_ok=True)


# Get job status
@app.get("/jobs/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status(job_id: str):
    """Get the status of a job."""
    redis = get_redis()

    # Check job metadata
    job_data = redis.hgetall(f"job:{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    # Decode redis data
    job_data = {k.decode(): v.decode() for k, v in job_data.items()}

    status = JobStatus(job_data.get("status", "queued"))
    created_at = datetime.fromisoformat(job_data.get("created_at", datetime.utcnow().isoformat()))

    started_at = None
    if job_data.get("started_at"):
        started_at = datetime.fromisoformat(job_data["started_at"])

    finished_at = None
    if job_data.get("finished_at"):
        finished_at = datetime.fromisoformat(job_data["finished_at"])

    result_url = None
    if status == JobStatus.FINISHED:
        result_url = f"/jobs/{job_id}/result"

    return JobStatusResponse(
        job_id=job_id,
        status=status,
        created_at=created_at,
        started_at=started_at,
        finished_at=finished_at,
        progress=float(job_data.get("progress", 0)),
        message=job_data.get("message"),
        result_url=result_url,
    )


# Get job result
@app.get("/jobs/{job_id}/result", tags=["Jobs"])
async def get_job_result(
    job_id: str,
    download: Annotated[bool, Query(description="Download as file")] = False,
):
    """Get the result of a completed job."""
    redis = get_redis()

    # Check job metadata
    job_data = redis.hgetall(f"job:{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = {k.decode(): v.decode() for k, v in job_data.items()}
    status = JobStatus(job_data.get("status", "queued"))

    if status != JobStatus.FINISHED:
        raise HTTPException(
            status_code=400, detail=f"Job is not finished. Current status: {status.value}"
        )

    # Get result from Redis or file
    result = redis.get(f"result:{job_id}")

    if download:
        # Check for file result
        output_path = get_output_path(job_id, ".md")
        if output_path.exists():
            return FileResponse(
                path=str(output_path),
                filename=f"{job_id}.md",
                media_type="text/markdown",
            )

    if result:
        import json

        return JSONResponse(content=json.loads(result))

    raise HTTPException(status_code=404, detail="Result not found")


# Delete job and cleanup files
@app.delete("/jobs/{job_id}", tags=["Jobs"])
async def delete_job(job_id: str):
    """Delete a job and clean up associated files."""
    redis = get_redis()

    # Check job exists
    if not redis.exists(f"job:{job_id}"):
        raise HTTPException(status_code=404, detail="Job not found")

    # Clean up Redis
    redis.delete(f"job:{job_id}")
    redis.delete(f"result:{job_id}")

    # Clean up files
    cleanup_job_files(job_id)

    return {"message": f"Job {job_id} deleted successfully"}
