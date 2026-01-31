"""
Application-wide constants.

This module defines magic numbers and constant values used throughout
the application to improve code readability and maintainability.
"""

# Extraction constants
PAGE_LOG_INTERVAL = 50  # Log progress every N pages during extraction

# Output formatting constants
MAX_SUMMARY_ITEMS = 3  # Maximum items to show in CLI summaries
MAX_DETAILED_ITEMS = 5  # Maximum items to show in detailed views
FILENAME_DISPLAY_LENGTH = 30  # Truncate filenames to this length in progress bars

# File size constants
BYTES_PER_MB = 1024 * 1024  # Bytes in a megabyte

# RAG chunking constants
DEFAULT_CHUNK_SIZE = 1000  # Default chunk size for RAG (from config)
MIN_CHUNK_SIZE = 100  # Minimum chunk size
MAX_CHUNK_SIZE = 10000  # Maximum chunk size
