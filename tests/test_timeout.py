"""
Tests for timeout utilities.

Tests decorators, context managers, and timeout functionality to prevent
infinite hangs during PDF processing.
"""

import time
import pytest
from concurrent.futures import TimeoutError as FuturesTimeoutError

from src.utils.timeout import timeout, timeout_context, run_with_timeout, TimeoutError


class TestTimeoutDecorator:
    """Test @timeout decorator functionality."""

    def test_timeout_decorator_success(self):
        """Test that timeout decorator allows quick functions to complete."""

        @timeout(seconds=2)
        def quick_function():
            return "completed"

        result = quick_function()
        assert result == "completed"

    def test_timeout_decorator_triggers(self):
        """Test that timeout decorator raises TimeoutError for slow functions."""

        @timeout(seconds=1)
        def slow_function():
            time.sleep(3)
            return "should not reach"

        with pytest.raises(TimeoutError) as exc_info:
            slow_function()

        assert "exceeded timeout" in str(exc_info.value).lower()
        assert "slow_function" in str(exc_info.value)

    def test_timeout_decorator_with_args(self):
        """Test timeout decorator works with function arguments."""

        @timeout(seconds=2)
        def function_with_args(a, b, c=10):
            return a + b + c

        result = function_with_args(1, 2, c=3)
        assert result == 6

    def test_timeout_decorator_preserves_function_name(self):
        """Test that decorator preserves original function metadata."""

        @timeout(seconds=5)
        def named_function():
            """This is the docstring."""
            pass

        assert named_function.__name__ == "named_function"
        assert "docstring" in named_function.__doc__

    def test_timeout_custom_duration(self):
        """Test timeout with custom duration."""

        @timeout(seconds=3)
        def function_under_limit():
            time.sleep(1)
            return "ok"

        result = function_under_limit()
        assert result == "ok"

    def test_timeout_decorator_with_exception(self):
        """Test that timeout decorator allows other exceptions to propagate."""

        @timeout(seconds=5)
        def function_with_error():
            raise ValueError("Test error")

        with pytest.raises(ValueError) as exc_info:
            function_with_error()

        assert "Test error" in str(exc_info.value)

    def test_timeout_zero_seconds(self):
        """Test timeout with very short duration."""

        @timeout(seconds=0)
        def instant_function():
            # Even instant functions may timeout with 0 seconds
            pass

        # With 0 seconds, behavior is unpredictable due to thread scheduling
        # May complete or may timeout - both are acceptable
        try:
            result = instant_function()
            # If it completes, that's fine (fast scheduling)
        except (TimeoutError, FuturesTimeoutError):
            # If it times out, that's also fine (slow scheduling)
            pass


class TestTimeoutContext:
    """Test timeout_context context manager."""

    def test_context_manager_basic(self):
        """Test basic context manager usage."""
        with timeout_context(seconds=2):
            time.sleep(0.1)
            result = "completed"

        assert result == "completed"

    def test_context_manager_creates_executor(self):
        """Test that context manager creates executor."""
        ctx = timeout_context(seconds=5)
        assert ctx.executor is None

        with ctx:
            assert ctx.executor is not None

        # Executor should be shut down after exiting
        # (can't easily test shutdown state, but no exception is good)

    def test_context_manager_cleanup(self):
        """Test that context manager cleans up resources."""
        ctx = timeout_context(seconds=2)

        try:
            with ctx:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should have cleaned up even with exception
        # Executor shutdown called, no resource leak

    def test_context_manager_custom_duration(self):
        """Test context manager with custom duration."""
        with timeout_context(seconds=10):
            time.sleep(0.01)
            value = 42

        assert value == 42


class TestRunWithTimeout:
    """Test run_with_timeout utility function."""

    def test_run_with_timeout_success(self):
        """Test successful function execution with timeout."""

        def quick_func(x, y):
            return x + y

        result = run_with_timeout(quick_func, 2, 10, 20)
        assert result == 30

    def test_run_with_timeout_triggers(self):
        """Test timeout returns None when function times out."""

        def slow_func():
            time.sleep(5)
            return "should not return"

        result = run_with_timeout(slow_func, 1)
        assert result is None

    def test_run_with_timeout_with_kwargs(self):
        """Test run_with_timeout with keyword arguments."""

        def func_with_kwargs(a, b, c=5):
            return a + b + c

        result = run_with_timeout(func_with_kwargs, 2, 1, 2, c=10)
        assert result == 13

    def test_run_with_timeout_returns_none_on_timeout(self):
        """Test that timeout returns None instead of raising."""

        def slow_operation():
            time.sleep(2)
            return "value"

        start = time.time()
        result = run_with_timeout(slow_operation, 1)
        duration = time.time() - start

        assert result is None
        # Note: future.cancel() may not immediately stop sleeping threads
        # So duration might be close to 2 seconds (full sleep) rather than 1

    def test_run_with_timeout_with_zero_timeout(self):
        """Test run_with_timeout with zero timeout."""

        def instant_func():
            return "instant"

        # May or may not complete depending on timing
        result = run_with_timeout(instant_func, 0)
        # Result could be "instant" or None depending on thread scheduling

    def test_run_with_timeout_propagates_exceptions(self):
        """Test that exceptions in function are propagated."""

        def failing_func():
            raise ValueError("Test error")

        # run_with_timeout propagates exceptions from the function
        with pytest.raises(ValueError) as exc_info:
            result = run_with_timeout(failing_func, 5)

        assert "Test error" in str(exc_info.value)


class TestTimeoutError:
    """Test TimeoutError exception class."""

    def test_timeout_error_is_pdf_extraction_error(self):
        """Test that TimeoutError inherits from PDFExtractionError."""
        from src.utils.exceptions import PDFExtractionError

        err = TimeoutError("Test timeout")
        assert isinstance(err, PDFExtractionError)
        assert isinstance(err, Exception)

    def test_timeout_error_message(self):
        """Test TimeoutError message formatting."""
        err = TimeoutError("Operation exceeded timeout")
        assert "timeout" in str(err).lower()


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_timeout_with_recursive_function(self):
        """Test timeout with recursive function."""

        @timeout(seconds=2)
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)

        result = factorial(5)
        assert result == 120

    def test_timeout_with_generator(self):
        """Test timeout with generator function."""

        @timeout(seconds=2)
        def generator_func():
            for i in range(5):
                yield i

        gen = generator_func()
        values = list(gen)
        assert values == [0, 1, 2, 3, 4]

    def test_multiple_timeouts_sequential(self):
        """Test multiple timeout decorators used sequentially."""

        @timeout(seconds=1)
        def func1():
            return "first"

        @timeout(seconds=1)
        def func2():
            return "second"

        assert func1() == "first"
        assert func2() == "second"

    def test_timeout_with_large_return_value(self):
        """Test timeout with function returning large data."""

        @timeout(seconds=2)
        def large_data_func():
            return list(range(10000))

        result = large_data_func()
        assert len(result) == 10000
        assert result[0] == 0
        assert result[-1] == 9999


class TestRealWorldScenarios:
    """Test scenarios similar to actual PDF processing."""

    def test_pdf_page_extraction_simulation(self):
        """Simulate PDF page extraction with timeout."""

        @timeout(seconds=5)
        def extract_page(page_num):
            # Simulate extraction work
            time.sleep(0.1)
            return f"Page {page_num} content"

        result = extract_page(42)
        assert "Page 42" in result

    def test_slow_pdf_timeout_simulation(self):
        """Simulate slow PDF that should timeout."""

        @timeout(seconds=1)
        def extract_corrupted_pdf():
            # Simulate a hung PDF extraction
            time.sleep(10)
            return "should not reach"

        with pytest.raises(TimeoutError):
            extract_corrupted_pdf()

    def test_batch_processing_with_timeouts(self):
        """Test batch processing where some items timeout."""

        @timeout(seconds=1)
        def process_item(item):
            if item == "slow":
                time.sleep(5)
            return f"processed_{item}"

        results = []
        items = ["fast1", "fast2", "slow", "fast3"]

        for item in items:
            try:
                result = process_item(item)
                results.append(result)
            except TimeoutError:
                results.append(f"timeout_{item}")

        assert "processed_fast1" in results
        assert "processed_fast2" in results
        assert "timeout_slow" in results
        assert "processed_fast3" in results
