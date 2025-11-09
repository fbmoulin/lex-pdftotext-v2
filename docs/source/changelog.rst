Changelog
=========

All notable changes to this project will be documented in this file.

[0.3.0] - 2025-11-09
--------------------

Added
~~~~~
* Comprehensive type hints across entire codebase (100% MyPy compliance)
* JSON formatter tests (24 tests, 94% coverage)
* Bandit security scanning configuration
* Radon complexity analysis
* Comprehensive Sphinx documentation
* Table extraction functionality with CSV export
* Performance monitoring utilities
* Image description caching

Changed
~~~~~~~
* Updated pdfplumber dependency (0.11.0 → 0.11.8)
* Improved import structure (removed sys.path hacks)
* Refactored format_for_rag complexity (D → A rating)
* Updated license format to PEP 621 standard
* Enhanced docstring formatting (Google style)

Fixed
~~~~~
* Fixed all 22 MyPy type errors
* Fixed 14 Ruff linting warnings
* Fixed image analyzer test failures
* Fixed exception handling (added proper chaining)
* Fixed docstring D212 violations (22 fixes)

Security
~~~~~~~~
* Configured Bandit to skip intentional patterns
* Zero security issues in final scan

[0.2.0] - 2024-11-01
--------------------

Added
~~~~~
* PyMuPDF extractor with context manager support
* Text normalization with UPPERCASE conversion
* Metadata parsing for Brazilian legal documents
* Markdown formatter with RAG optimization
* Table formatter for Markdown and CSV output
* CLI with click framework
* Batch processing support
* PDF validation utilities

Changed
~~~~~~~
* Switched to PyMuPDF for 60x speed improvement
* Improved metadata extraction accuracy

[0.1.0] - 2024-10-15
--------------------

Added
~~~~~
* Initial release
* Basic PDF text extraction
* Simple Markdown output
* Command-line interface

Development Metrics
-------------------

Version 0.3.0 Quality Metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Tests**: 170 passing
* **Coverage**: 77.35%
* **Type Safety**: 100% (0 MyPy errors)
* **Security**: 0 Bandit issues
* **Linting**: 0 Ruff violations
* **Complexity**: Average A rating

Files with 90%+ Coverage
~~~~~~~~~~~~~~~~~~~~~~~~~

* json_formatter.py: 94%
* cache.py: 96%
* config.py: 93%
* logger.py: 93%
* patterns.py: 97%
* timeout.py: 100%
* text_normalizer.py: 91%
* metadata_parser.py: 89%
* markdown_formatter.py: 87%
* image_analyzer.py: 86%
