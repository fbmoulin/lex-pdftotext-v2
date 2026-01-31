"""
Caching utilities for PDF text extractor.

Provides hash-based caching for expensive operations like image analysis.
"""

import hashlib
import json
import time
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from .logger import get_logger

logger = get_logger(__name__)


class ImageDescriptionCache:
    """
    Cache for AI-generated image descriptions.

    Uses image content hash as key to avoid re-analyzing identical images.
    """

    def __init__(self, cache_dir: Path | None = None, max_entries: int = 1000):
        """
        Initialize image description cache.

        Args:
            cache_dir: Directory to store cache files (default: .cache/images)
            max_entries: Maximum number of cached entries
        """
        if cache_dir is None:
            cache_dir = Path.cwd() / ".cache" / "images"

        self.cache_dir = cache_dir
        self.max_entries = max_entries
        self.cache_file = self.cache_dir / "descriptions.json"

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing cache
        self._cache = self._load_cache()

        logger.info(f"ImageDescriptionCache initialized: {len(self._cache)} entries")

    def _load_cache(self) -> dict[Any, Any]:
        """Load cache from disk."""
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, encoding="utf-8") as f:
                cache: dict[Any, Any] = json.load(f)
            logger.debug(f"Loaded {len(cache)} entries from cache")
            return cache
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return {}

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            # Enforce max entries (LRU-like: keep most recent)
            if len(self._cache) > self.max_entries:
                # Sort by timestamp and keep newest entries
                sorted_items = sorted(
                    self._cache.items(), key=lambda x: x[1].get("timestamp", 0), reverse=True
                )
                self._cache = dict(sorted_items[: self.max_entries])
                logger.info(f"Cache trimmed to {self.max_entries} entries")

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self._cache)} entries to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _hash_image(self, image: Any) -> str:
        """
        Generate hash for PIL Image.

        Args:
            image: PIL Image object

        Returns:
            SHA256 hash of image data
        """
        import io

        # Convert image to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_data = img_bytes.getvalue()

        # Generate hash
        return hashlib.sha256(img_data).hexdigest()

    def get(self, image: Any, context: str | None = None) -> str | None:
        """
        Get cached description for image.

        Args:
            image: PIL Image object
            context: Optional context string (included in cache key)

        Returns:
            Cached description or None if not found
        """
        # Generate cache key
        img_hash = self._hash_image(image)
        cache_key = f"{img_hash}:{context}" if context else img_hash

        if cache_key in self._cache:
            entry = self._cache[cache_key]
            logger.debug(f"Cache hit for image {img_hash[:8]}...")
            return str(entry["description"])

        logger.debug(f"Cache miss for image {img_hash[:8]}...")
        return None

    def set(self, image: Any, description: str, context: str | None = None) -> None:
        """
        Cache image description.

        Args:
            image: PIL Image object
            description: AI-generated description
            context: Optional context string
        """
        # Generate cache key
        img_hash = self._hash_image(image)
        cache_key = f"{img_hash}:{context}" if context else img_hash

        # Store with timestamp
        self._cache[cache_key] = {
            "description": description,
            "timestamp": time.time(),
            "hash": img_hash,
        }

        logger.debug(f"Cached description for image {img_hash[:8]}...")

        # Save to disk
        self._save_cache()

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache = {}
        self._save_cache()
        logger.info("Cache cleared")

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "total_entries": len(self._cache),
            "cache_dir": str(self.cache_dir),
            "cache_file": str(self.cache_file),
            "max_entries": self.max_entries,
        }


class PerformanceMonitor:
    """
    Monitor and log performance metrics for operations.

    Tracks execution time, memory usage, and operation counts.
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}
        logger.info("PerformanceMonitor initialized")

    def track(self, operation: str):
        """
        Decorator to track operation performance.

        Args:
            operation: Operation name for logging

        Example:
            @monitor.track("pdf_extraction")
            def extract_pdf(path):
                ...
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    # Execute function
                    result = func(*args, **kwargs)

                    # Calculate metrics
                    duration = time.time() - start_time

                    # Store metrics
                    if operation not in self.metrics:
                        self.metrics[operation] = {
                            "count": 0,
                            "total_time": 0,
                            "avg_time": 0,
                            "min_time": float("inf"),
                            "max_time": 0,
                        }

                    metrics = self.metrics[operation]
                    metrics["count"] += 1
                    metrics["total_time"] += duration
                    metrics["avg_time"] = metrics["total_time"] / metrics["count"]
                    metrics["min_time"] = min(metrics["min_time"], duration)
                    metrics["max_time"] = max(metrics["max_time"], duration)

                    # Log performance
                    logger.info(
                        f"Performance [{operation}]: {duration:.3f}s "
                        f"(avg: {metrics['avg_time']:.3f}s, count: {metrics['count']})"
                    )

                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"Performance [{operation}]: FAILED after {duration:.3f}s - {e}")
                    raise

            return wrapper

        return decorator

    def get_metrics(self, operation: str | None = None) -> dict[str, Any]:
        """
        Get performance metrics.

        Args:
            operation: Specific operation name, or None for all metrics

        Returns:
            Dictionary of metrics
        """
        if operation:
            return dict(self.metrics.get(operation, {}))
        return dict(self.metrics.copy())

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics = {}
        logger.info("Performance metrics reset")

    def report(self) -> str:
        """
        Generate performance report.

        Returns:
            Formatted report string
        """
        if not self.metrics:
            return "No performance metrics collected"

        lines = ["Performance Report:", "=" * 60]

        for operation, metrics in sorted(self.metrics.items()):
            lines.append(f"\n{operation}:")
            lines.append(f"  Count:      {metrics['count']}")
            lines.append(f"  Total Time: {metrics['total_time']:.3f}s")
            lines.append(f"  Avg Time:   {metrics['avg_time']:.3f}s")
            lines.append(f"  Min Time:   {metrics['min_time']:.3f}s")
            lines.append(f"  Max Time:   {metrics['max_time']:.3f}s")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# Global instances
_image_cache: ImageDescriptionCache | None = None
_performance_monitor: PerformanceMonitor | None = None


def get_image_cache() -> ImageDescriptionCache:
    """Get global image cache instance."""
    global _image_cache
    if _image_cache is None:
        _image_cache = ImageDescriptionCache()
    return _image_cache


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
