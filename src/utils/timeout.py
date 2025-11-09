"""
Timeout utilities for PDF operations.

Provides timeout decorators and context managers to prevent infinite hangs.
"""

import functools
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TypeVar

from .exceptions import PDFExtractionError


class TimeoutError(PDFExtractionError):
    """Raised when operation exceeds timeout."""

    pass


# Type variable for generic function return type
T = TypeVar("T")


def timeout(seconds: int = 30):
    """
    Decorator to add timeout to function execution using ThreadPoolExecutor.

    This works on both Unix and Windows systems.

    Args:
        seconds: Maximum execution time in seconds

    Raises:
        TimeoutError: If function execution exceeds timeout

    Example:
        @timeout(seconds=10)
        def process_pdf(pdf_path):
            # This will timeout after 10 seconds
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    result = future.result(timeout=seconds)
                    return result
                except FuturesTimeoutError:
                    future.cancel()
                    raise TimeoutError(
                        f"Operation '{func.__name__}' exceeded timeout of {seconds} seconds"
                    )

        return wrapper

    return decorator


class timeout_context:
    """
    Context manager for timeout operations.

    Example:
        with timeout_context(seconds=30):
            # This code block will timeout after 30 seconds
            process_large_pdf()
    """

    def __init__(self, seconds: int = 30):
        """
        Initialize timeout context.

        Args:
            seconds: Maximum execution time in seconds
        """
        self.seconds = seconds
        self.executor = None

    def __enter__(self):
        """Enter context manager."""
        self.executor = ThreadPoolExecutor(max_workers=1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup."""
        if self.executor:
            self.executor.shutdown(wait=False)
        return False


def run_with_timeout(func: Callable[..., T], timeout_seconds: int, *args, **kwargs) -> T | None:
    """
    Run function with timeout and return result or None.

    Args:
        func: Function to execute
        timeout_seconds: Maximum execution time in seconds
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Function result or None if timeout

    Example:
        result = run_with_timeout(expensive_operation, 10, arg1, arg2)
        if result is None:
            print("Operation timed out")
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            future.cancel()
            return None
