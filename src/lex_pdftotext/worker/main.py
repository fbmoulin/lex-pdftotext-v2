"""RQ worker entry point."""

import logging
import os
import sys

from redis import Redis
from rq import Connection, Worker

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Queues to listen to
QUEUES = ["high", "default", "low"]


def run_worker():
    """Run the RQ worker."""
    logger.info(f"Connecting to Redis at {REDIS_URL}")

    redis_conn = Redis.from_url(REDIS_URL)

    # Test connection
    try:
        redis_conn.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        sys.exit(1)

    with Connection(redis_conn):
        worker = Worker(QUEUES)
        logger.info(f"Worker started, listening on queues: {QUEUES}")
        worker.work(with_scheduler=True)


if __name__ == "__main__":
    run_worker()
