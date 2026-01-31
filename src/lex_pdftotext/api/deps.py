"""API dependencies and utilities."""

import os
import uuid
from functools import lru_cache
from pathlib import Path

from redis import Redis
from rq import Queue

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/outputs"))
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 52428800))  # 50MB


@lru_cache
def get_redis() -> Redis:
    """Get Redis connection (cached)."""
    return Redis.from_url(REDIS_URL)


def get_queue() -> Queue:
    """Get RQ queue."""
    return Queue(connection=get_redis())


def get_high_priority_queue() -> Queue:
    """Get high priority RQ queue."""
    return Queue("high", connection=get_redis())


def generate_job_id() -> str:
    """Generate unique job ID."""
    return str(uuid.uuid4())


def get_upload_path(filename: str, job_id: str) -> Path:
    """Get path for uploaded file."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(filename).name  # Sanitize filename
    return UPLOAD_DIR / job_id / safe_filename


def get_output_path(job_id: str, extension: str = ".md") -> Path:
    """Get path for output file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / f"{job_id}{extension}"


def save_uploaded_file(content: bytes, filename: str, job_id: str) -> Path:
    """Save uploaded file to disk."""
    filepath = get_upload_path(filename, job_id)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(content)
    return filepath


def cleanup_job_files(job_id: str) -> None:
    """Clean up files associated with a job."""
    import shutil

    upload_path = UPLOAD_DIR / job_id
    if upload_path.exists():
        shutil.rmtree(upload_path)


def get_workers_count() -> int:
    """Get number of active workers."""
    try:
        redis = get_redis()
        workers = redis.smembers("rq:workers")
        return len(workers)
    except Exception:
        return 0


def check_redis_health() -> str:
    """Check Redis connection health."""
    try:
        redis = get_redis()
        redis.ping()
        return "healthy"
    except Exception as e:
        return f"unhealthy: {e}"
