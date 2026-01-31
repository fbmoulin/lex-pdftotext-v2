"""RQ task definitions for PDF processing."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from redis import Redis

# Configure logging
logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def get_redis() -> Redis:
    """Get Redis connection."""
    return Redis.from_url(REDIS_URL)


def update_job_status(
    job_id: str,
    status: str,
    progress: float = 0,
    message: str | None = None,
    **extra,
):
    """Update job status in Redis."""
    redis = get_redis()
    data = {
        "status": status,
        "progress": str(progress),
        "updated_at": datetime.utcnow().isoformat(),
    }

    if message:
        data["message"] = message

    if status == "started":
        data["started_at"] = datetime.utcnow().isoformat()
    elif status in ("finished", "failed"):
        data["finished_at"] = datetime.utcnow().isoformat()

    data.update({k: str(v) for k, v in extra.items()})

    redis.hset(f"job:{job_id}", mapping=data)


def save_result(job_id: str, result: dict, ttl: int = 86400):
    """Save job result to Redis with TTL."""
    redis = get_redis()
    redis.setex(f"result:{job_id}", ttl, json.dumps(result))


def extract_pdf_task(job_id: str, filepath: str, options: dict) -> dict:
    """
    Extract text from a PDF document.

    Args:
        job_id: Unique job identifier
        filepath: Path to the PDF file
        options: Extraction options (format, normalize, include_metadata, chunk_for_rag)

    Returns:
        Extraction result dictionary
    """
    start_time = time.time()
    update_job_status(job_id, "started", progress=0, message="Starting extraction")

    try:
        # Import here to avoid circular imports and ensure proper initialization
        from ..extractors import PyMuPDFExtractor
        from ..formatters import JSONFormatter, MarkdownFormatter
        from ..processors import MetadataParser, TextNormalizer

        filepath_obj = Path(filepath)

        # Validate file exists
        if not filepath_obj.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        update_job_status(job_id, "started", progress=10, message="Reading PDF")

        # Extract raw text
        with PyMuPDFExtractor(str(filepath_obj)) as extractor:
            raw_text = extractor.extract_text()
            page_count = extractor.page_count

        update_job_status(job_id, "started", progress=40, message="Processing text")

        # Normalize text
        text = raw_text
        if options.get("normalize", True):
            normalizer = TextNormalizer()
            text = normalizer.normalize(raw_text)

        update_job_status(job_id, "started", progress=60, message="Extracting metadata")

        # Extract metadata
        metadata = None
        if options.get("include_metadata", True):
            parser = MetadataParser()
            metadata = parser.parse(text)

        update_job_status(job_id, "started", progress=80, message="Formatting output")

        # Format output
        output_format = options.get("format", "markdown")
        result: dict[str, Any] = {}

        if output_format == "json":
            formatter = JSONFormatter()
            result = formatter.format(text, metadata)
        elif output_format == "markdown":
            formatter = MarkdownFormatter()
            if options.get("chunk_for_rag", False):
                chunk_size = options.get("chunk_size", 1000)
                chunks = formatter.format_for_rag(text, metadata, chunk_size=chunk_size)
                result = {
                    "chunks": chunks,
                    "total_chunks": len(chunks),
                    "metadata": metadata.to_dict() if metadata else None,
                }
            else:
                result = {
                    "text": formatter.format(text, metadata),
                    "metadata": metadata.to_dict() if metadata else None,
                }
        else:  # text
            result = {
                "text": text,
                "metadata": metadata.to_dict() if metadata else None,
            }

        # Add processing info
        processing_time = time.time() - start_time
        result["processing"] = {
            "pages": page_count,
            "processing_time_seconds": round(processing_time, 2),
            "original_filename": filepath_obj.name,
        }

        # Save result
        save_result(job_id, result)

        update_job_status(
            job_id,
            "finished",
            progress=100,
            message="Extraction complete",
            processing_time=round(processing_time, 2),
        )

        logger.info(f"Job {job_id} completed in {processing_time:.2f}s")

        return result

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_job_status(job_id, "failed", message=str(e))
        raise


def extract_tables_task(job_id: str, filepath: str, options: dict) -> dict:
    """
    Extract tables from a PDF document.

    Args:
        job_id: Unique job identifier
        filepath: Path to the PDF file
        options: Extraction options (format)

    Returns:
        Tables extraction result
    """
    start_time = time.time()
    update_job_status(job_id, "started", progress=0, message="Starting table extraction")

    try:
        from ..extractors.table_extractor import TableExtractor
        from ..formatters import TableFormatter

        filepath_obj = Path(filepath)

        if not filepath_obj.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        update_job_status(job_id, "started", progress=20, message="Detecting tables")

        # Extract tables
        extractor = TableExtractor(str(filepath_obj))
        tables = extractor.extract_tables()

        update_job_status(job_id, "started", progress=60, message="Formatting tables")

        # Format tables
        output_format = options.get("format", "markdown")
        formatter = TableFormatter()

        formatted_tables = []
        for i, table in enumerate(tables):
            if output_format == "csv":
                # Convert to CSV format
                rows = [",".join(str(cell) for cell in row) for row in table.get("data", [])]
                formatted = "\n".join(rows)
            else:
                formatted = formatter.format_table(table.get("data", []))

            formatted_tables.append(
                {
                    "index": i,
                    "page": table.get("page", 1),
                    "rows": table.get("rows", 0),
                    "cols": table.get("cols", 0),
                    "content": formatted,
                }
            )

        processing_time = time.time() - start_time

        result = {
            "tables": formatted_tables,
            "total_tables": len(formatted_tables),
            "processing": {
                "processing_time_seconds": round(processing_time, 2),
                "original_filename": filepath_obj.name,
            },
        }

        save_result(job_id, result)

        update_job_status(
            job_id,
            "finished",
            progress=100,
            message=f"Extracted {len(formatted_tables)} tables",
            processing_time=round(processing_time, 2),
        )

        return result

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_job_status(job_id, "failed", message=str(e))
        raise


def merge_pdfs_task(job_id: str, filepaths: list[str], options: dict) -> dict:
    """
    Merge and extract text from multiple PDF documents.

    Args:
        job_id: Unique job identifier
        filepaths: List of paths to PDF files
        options: Processing options (format)

    Returns:
        Merged extraction result
    """
    start_time = time.time()
    update_job_status(
        job_id, "started", progress=0, message=f"Starting merge of {len(filepaths)} files"
    )

    try:
        from ..extractors import PyMuPDFExtractor
        from ..formatters import MarkdownFormatter
        from ..processors import MetadataParser, TextNormalizer

        all_texts = []
        all_metadata = []
        total_pages = 0

        for i, filepath in enumerate(filepaths):
            filepath_obj = Path(filepath)

            if not filepath_obj.exists():
                logger.warning(f"File not found: {filepath}")
                continue

            progress = int((i / len(filepaths)) * 80)
            update_job_status(
                job_id,
                "started",
                progress=progress,
                message=f"Processing file {i + 1}/{len(filepaths)}",
            )

            # Extract text
            with PyMuPDFExtractor(str(filepath_obj)) as extractor:
                raw_text = extractor.extract_text()
                total_pages += extractor.page_count

            # Normalize
            normalizer = TextNormalizer()
            text = normalizer.normalize(raw_text)
            all_texts.append(text)

            # Extract metadata
            parser = MetadataParser()
            metadata = parser.parse(text)
            if metadata:
                all_metadata.append({"filename": filepath_obj.name, "metadata": metadata.to_dict()})

        update_job_status(job_id, "started", progress=90, message="Merging results")

        # Combine all texts
        merged_text = "\n\n---\n\n".join(all_texts)

        # Format output
        output_format = options.get("format", "markdown")
        formatter = MarkdownFormatter()

        if output_format == "json":
            result = {
                "documents": all_metadata,
                "merged_text": merged_text,
                "total_files": len(filepaths),
                "total_pages": total_pages,
            }
        else:
            result = {
                "text": formatter.format(merged_text, None),
                "documents": all_metadata,
                "total_files": len(filepaths),
                "total_pages": total_pages,
            }

        processing_time = time.time() - start_time
        result["processing"] = {
            "processing_time_seconds": round(processing_time, 2),
            "files_processed": len(all_texts),
        }

        save_result(job_id, result)

        update_job_status(
            job_id,
            "finished",
            progress=100,
            message=f"Merged {len(all_texts)} files",
            processing_time=round(processing_time, 2),
        )

        return result

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        update_job_status(job_id, "failed", message=str(e))
        raise
