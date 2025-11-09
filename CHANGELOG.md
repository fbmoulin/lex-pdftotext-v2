# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-09

### Added

- **Table Extraction**: Complete table extraction feature using pdfplumber
  - `TableExtractor` class for detecting and extracting tables from PDFs
  - `TableFormatter` class for converting tables to Markdown or CSV
  - New `extract-tables` CLI command with markdown and CSV output formats
  - Automatic column alignment detection (left/right for numeric columns)
  - 24 comprehensive tests for table extraction and formatting
- **JSON Export Format**: Structured JSON output for API integrations
  - `JSONFormatter` class with hierarchical and flat modes
  - `--format json` option in `extract`, `batch`, and `merge` commands
  - Includes document metadata, type detection, and section structure
- **Performance Monitoring**: Track and analyze processing performance
  - `PerformanceMonitor` class with decorator-based tracking
  - New `perf-report` CLI command to view metrics
  - Tracks: text_normalization, metadata_extraction, rag_chunking, table_extraction
  - JSON export option for metrics (`--json` flag)
- **Modern Package Structure**: PyPI-ready Python package
  - Created `pyproject.toml` with PEP 621 compliance
  - Backward-compatible `setup.py`
  - Entry points for CLI commands (`pdftotext-legal`, `pdftotext-gui`)
  - Package can be installed with `pip install -e .`
- **CI/CD Pipeline**: Automated testing and deployment
  - GitHub Actions workflows for testing (test.yml)
  - Code quality checks with linting (lint.yml)
  - Automated PyPI publishing (release.yml)
  - Matrix testing: Python 3.10-3.12 on Ubuntu/Windows/macOS
- **Pre-commit Hooks**: Automated code quality enforcement
  - Black code formatting (100 char line length)
  - isort import sorting
  - Ruff linting
  - MyPy type checking
  - Bandit security scanning
  - pydocstyle docstring checks
  - YAML and Markdown formatting

### Changed

- **Code Formatting**: Applied black and isort formatting across entire codebase
  - Consistent 100-character line length
  - Black-compatible import sorting
  - Fixed trailing whitespace and line endings
- **Updated Dependencies**: All pre-commit hooks updated to latest versions
  - black: 25.1.0 → 25.9.0
  - isort: 5.13.2 → 7.0.0
  - ruff: v0.9.1 → v0.14.4
  - mypy: v1.15.0 → v1.18.2
  - Other tools updated for compatibility

### Documentation

- Updated README.md with Sprint 3 features:
  - Table extraction commands and examples
  - JSON export format documentation
  - Performance monitoring usage
  - PyPI installation notes
- Updated CLAUDE.md with:
  - Table extraction architecture
  - JSON export implementation details
  - Performance monitoring system
  - New CLI commands reference
- Created CHANGELOG.md for version tracking

### Testing

- Added 24 comprehensive tests for table extraction (test_table_extraction.py)
- All tests passing: 100% success rate
- Tests cover:
  - Basic table formatting
  - Caption and metadata handling
  - Multiple table formatting
  - Alignment detection
  - Edge cases and error conditions

### Performance

- Added performance tracking decorators to core operations
- Zero overhead when metrics aren't being analyzed
- Detailed timing statistics available through `perf-report` command

## [0.2.0] - 2025-01-01

### Added

- Sprint 2: High priority improvements
- Sprint 1: Critical bug fixes and safety improvements
- Phase 4: Configuration management and production polish
- Modern dark theme UI with glassmorphism effects
- Image analysis with Google Gemini Vision

### Changed

- Improved error handling and validation
- Enhanced logging and monitoring
- Updated dependencies for stability

### Fixed

- Various bug fixes and stability improvements
- Security enhancements
- Performance optimizations

## [0.1.0] - 2024-12-15

### Added

- Initial release
- PDF text extraction with PyMuPDF
- Metadata extraction for Brazilian legal documents
- Markdown and plain text output formats
- Batch processing support
- Process merge functionality
- CLI interface with Click
- GUI interface with PyWebView
- Windows executable support

______________________________________________________________________

[0.1.0]: https://github.com/fbmoulin/pdftotext/releases/tag/v0.1.0
[0.2.0]: https://github.com/fbmoulin/pdftotext/compare/v0.1.0...v0.2.0
[0.3.0]: https://github.com/fbmoulin/pdftotext/compare/v0.2.0...v0.3.0
