"""
Tests for caching and performance monitoring utilities.

To run: pytest tests/test_cache.py -v
"""

# Add src to path
import sys
import tempfile
import time
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.cache import ImageDescriptionCache, PerformanceMonitor


class TestImageDescriptionCache:
    """Test image description caching."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def test_image(self):
        """Create a test PIL image."""
        img = Image.new("RGB", (100, 100), color="red")
        return img

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance with temp directory."""
        return ImageDescriptionCache(cache_dir=temp_cache_dir, max_entries=10)

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initialization."""
        cache = ImageDescriptionCache(cache_dir=temp_cache_dir)

        assert cache.cache_dir == temp_cache_dir
        assert cache.cache_dir.exists()
        assert cache.cache_file == temp_cache_dir / "descriptions.json"

    def test_cache_miss(self, cache, test_image):
        """Test cache miss returns None."""
        result = cache.get(test_image, context="legal document")
        assert result is None

    def test_cache_hit(self, cache, test_image):
        """Test cache hit returns stored description."""
        description = "Test image description"

        # Store in cache
        cache.set(test_image, description, context="legal document")

        # Retrieve from cache
        result = cache.get(test_image, context="legal document")
        assert result == description

    def test_cache_different_contexts(self, cache, test_image):
        """Test that different contexts are cached separately."""
        desc1 = "Description for context 1"
        desc2 = "Description for context 2"

        cache.set(test_image, desc1, context="context1")
        cache.set(test_image, desc2, context="context2")

        assert cache.get(test_image, context="context1") == desc1
        assert cache.get(test_image, context="context2") == desc2

    def test_cache_persistence(self, temp_cache_dir, test_image):
        """Test that cache persists across instances."""
        description = "Persisted description"

        # Create cache and store data
        cache1 = ImageDescriptionCache(cache_dir=temp_cache_dir)
        cache1.set(test_image, description)

        # Create new cache instance (should load from disk)
        cache2 = ImageDescriptionCache(cache_dir=temp_cache_dir)
        result = cache2.get(test_image)

        assert result == description

    def test_cache_max_entries(self, temp_cache_dir, test_image):
        """Test that cache enforces max entries limit."""
        cache = ImageDescriptionCache(cache_dir=temp_cache_dir, max_entries=5)

        # Add more entries than max
        for i in range(10):
            # Create slightly different images
            img = Image.new("RGB", (100, 100), color=(i * 25, 0, 0))
            cache.set(img, f"Description {i}")

        # Cache should be trimmed to max_entries
        assert len(cache._cache) <= cache.max_entries

    def test_cache_clear(self, cache, test_image):
        """Test clearing the cache."""
        cache.set(test_image, "Test description")
        assert cache.get(test_image) is not None

        cache.clear()
        assert cache.get(test_image) is None
        assert len(cache._cache) == 0

    def test_cache_stats(self, cache, test_image):
        """Test cache statistics."""
        # Add some entries
        cache.set(test_image, "Description 1")

        stats = cache.stats()

        assert isinstance(stats, dict)
        assert "total_entries" in stats
        assert "cache_dir" in stats
        assert "max_entries" in stats
        assert stats["total_entries"] >= 1

    def test_identical_images_same_hash(self, cache):
        """Test that identical images produce same cache key."""
        img1 = Image.new("RGB", (50, 50), color="blue")
        img2 = Image.new("RGB", (50, 50), color="blue")

        description = "Blue square"
        cache.set(img1, description)

        # img2 should hit cache since it's identical to img1
        result = cache.get(img2)
        assert result == description

    def test_different_images_different_hash(self, cache):
        """Test that different images don't share cache entries."""
        img1 = Image.new("RGB", (50, 50), color="red")
        img2 = Image.new("RGB", (50, 50), color="blue")

        cache.set(img1, "Red square")

        # img2 should miss cache
        result = cache.get(img2)
        assert result is None


class TestPerformanceMonitor:
    """Test performance monitoring."""

    @pytest.fixture
    def monitor(self):
        """Create fresh performance monitor."""
        pm = PerformanceMonitor()
        pm.reset()  # Ensure clean state
        return pm

    def test_monitor_initialization(self, monitor):
        """Test monitor initialization."""
        assert isinstance(monitor.metrics, dict)
        assert len(monitor.metrics) == 0

    def test_track_decorator(self, monitor):
        """Test performance tracking decorator."""

        @monitor.track("test_operation")
        def test_function():
            time.sleep(0.01)  # Small delay
            return "result"

        result = test_function()

        assert result == "result"
        assert "test_operation" in monitor.metrics

        metrics = monitor.metrics["test_operation"]
        assert metrics["count"] == 1
        assert metrics["total_time"] > 0
        assert metrics["avg_time"] > 0
        assert metrics["min_time"] > 0
        assert metrics["max_time"] > 0

    def test_track_multiple_calls(self, monitor):
        """Test tracking multiple calls to same operation."""

        @monitor.track("multi_call")
        def test_function():
            time.sleep(0.001)

        # Call multiple times
        for _ in range(5):
            test_function()

        metrics = monitor.metrics["multi_call"]
        assert metrics["count"] == 5
        assert metrics["avg_time"] > 0

    def test_track_with_exception(self, monitor):
        """Test that decorator handles exceptions."""

        @monitor.track("failing_operation")
        def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Metrics should still be partially recorded
        # (depends on implementation)

    def test_get_metrics(self, monitor):
        """Test retrieving metrics."""

        @monitor.track("operation1")
        def func1():
            pass

        @monitor.track("operation2")
        def func2():
            pass

        func1()
        func2()

        # Get all metrics
        all_metrics = monitor.get_metrics()
        assert "operation1" in all_metrics
        assert "operation2" in all_metrics

        # Get specific operation
        op1_metrics = monitor.get_metrics("operation1")
        assert op1_metrics["count"] == 1

    def test_reset_metrics(self, monitor):
        """Test resetting metrics."""

        @monitor.track("test_op")
        def test_function():
            pass

        test_function()
        assert len(monitor.metrics) > 0

        monitor.reset()
        assert len(monitor.metrics) == 0

    def test_performance_report(self, monitor):
        """Test generating performance report."""

        @monitor.track("report_test")
        def test_function():
            time.sleep(0.001)

        test_function()

        report = monitor.report()

        assert isinstance(report, str)
        assert "Performance Report" in report
        assert "report_test" in report
        assert "Count" in report
        assert "Avg Time" in report

    def test_empty_report(self, monitor):
        """Test report with no metrics."""
        report = monitor.report()

        assert "No performance metrics" in report

    def test_min_max_times(self, monitor):
        """Test that min/max times are tracked correctly."""

        @monitor.track("varying_time")
        def test_function(duration):
            time.sleep(duration)

        # Call with different durations
        test_function(0.001)
        test_function(0.005)
        test_function(0.002)

        metrics = monitor.metrics["varying_time"]
        assert metrics["min_time"] < metrics["max_time"]
        assert metrics["count"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
