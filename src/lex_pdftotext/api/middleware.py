"""API middleware for rate limiting and usage tracking."""

import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..models import APIKey, Usage
from ..models.base import session_scope


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis.

    Implements sliding window rate limiting per API key.
    """

    def __init__(self, app: FastAPI, redis_url: str | None = None):
        super().__init__(app)
        self.redis_url = redis_url
        self._redis = None

    @property
    def redis(self):
        """Get Redis connection."""
        if self._redis is None and self.redis_url:
            from redis import Redis

            self._redis = Redis.from_url(self.redis_url)
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting if Redis is not configured
        if not self.redis:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)

        # Check rate limits
        now = int(time.time())
        minute_key = f"rate:{api_key}:minute:{now // 60}"
        hour_key = f"rate:{api_key}:hour:{now // 3600}"

        # Get current counts
        pipe = self.redis.pipeline()
        pipe.get(minute_key)
        pipe.get(hour_key)
        results = pipe.execute()

        minute_count = int(results[0] or 0)
        hour_count = int(results[1] or 0)

        # Get limits from database (cached)
        limits = self._get_limits(api_key)
        if limits:
            rate_per_minute, rate_per_hour = limits

            if minute_count >= rate_per_minute:
                return Response(
                    content='{"error": "Rate limit exceeded (per minute)"}',
                    status_code=429,
                    headers={
                        "Content-Type": "application/json",
                        "X-RateLimit-Limit": str(rate_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str((now // 60 + 1) * 60),
                    },
                )

            if hour_count >= rate_per_hour:
                return Response(
                    content='{"error": "Rate limit exceeded (per hour)"}',
                    status_code=429,
                    headers={
                        "Content-Type": "application/json",
                        "X-RateLimit-Limit": str(rate_per_hour),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str((now // 3600 + 1) * 3600),
                    },
                )

        # Process request
        response = await call_next(request)

        # Increment counters
        if self.redis:
            pipe = self.redis.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            pipe.execute()

        # Add rate limit headers
        if limits:
            rate_per_minute, _ = limits
            response.headers["X-RateLimit-Limit"] = str(rate_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                max(0, rate_per_minute - minute_count - 1)
            )
            response.headers["X-RateLimit-Reset"] = str((now // 60 + 1) * 60)

        return response

    def _get_limits(self, api_key: str) -> tuple[int, int] | None:
        """Get rate limits for API key (with caching)."""
        cache_key = f"limits:{api_key}"

        # Check cache
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                parts = cached.decode().split(":")
                return int(parts[0]), int(parts[1])

        # Query database
        with session_scope() as db:
            key = db.query(APIKey).filter(APIKey.key == api_key).first()
            if key and key.is_valid:
                limits = (key.rate_limit_per_minute, key.rate_limit_per_hour)

                # Cache for 5 minutes
                if self.redis:
                    self.redis.setex(cache_key, 300, f"{limits[0]}:{limits[1]}")

                return limits

        return None


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API usage per request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track request usage."""
        start_time = time.time()

        # Get API key
        api_key_str = request.headers.get("X-API-Key")

        # Get request size
        request_bytes = 0
        if request.headers.get("content-length"):
            request_bytes = int(request.headers["content-length"])

        # Process request
        response = await call_next(request)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Get response size
        response_bytes = 0
        if response.headers.get("content-length"):
            response_bytes = int(response.headers["content-length"])

        # Record usage if API key provided
        if api_key_str and request.url.path not in ("/health", "/docs", "/openapi.json"):
            try:
                self._record_usage(
                    api_key_str=api_key_str,
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    request_bytes=request_bytes,
                    response_bytes=response_bytes,
                    processing_time_ms=processing_time_ms,
                )
            except Exception:
                pass  # Don't fail request on usage tracking errors

        return response

    def _record_usage(
        self,
        api_key_str: str,
        endpoint: str,
        method: str,
        status_code: int,
        request_bytes: int,
        response_bytes: int,
        processing_time_ms: int,
    ) -> None:
        """Record usage in database."""
        with session_scope() as db:
            api_key = db.query(APIKey).filter(APIKey.key == api_key_str).first()
            if api_key:
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
